# backend/filesystem_server.py
import os
import shutil
import glob
import logging
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from mcp_core import IMCPExternalServer, MCPTool
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

# -------------------------
# Configuration
# -------------------------
SANDBOX_DIR = Path("mcp_sandbox").resolve()
MAX_READ_CHARS = 2000       # default truncation for read_file
MAX_WRITE_BYTES = 2 * 1024 * 1024  # 2 MB max single write by default
ALLOWED_TOPDIRS: Optional[List[str]] = None  # Example: ["projects", "uploads"] or None to allow all inside SANDBOX_DIR

# -------------------------
# Logging
# -------------------------
logger = logging.getLogger("filesystem_mcp_server")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# -------------------------
# Helpers
# -------------------------
def _ensure_sandbox():
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

def _is_within_sandbox(path: Path) -> bool:
    try:
        path = path.resolve()
        return str(path).startswith(str(SANDBOX_DIR))
    except Exception:
        return False

def _get_safe_path(relative_path: str) -> Path:
    """
    Resolve a relative path under the sandbox and validate it.
    - Disallow absolute paths
    - Disallow usage of '..' segments
    - Ensure final resolved path is inside SANDBOX_DIR
    """
    if not relative_path or relative_path.strip() == "":
        raise ValueError("Path is required and cannot be empty.")

    # Normalize separators and strip leading/trailing whitespace
    rel = relative_path.strip().replace("\\", "/")

    # Disallow absolute paths
    if os.path.isabs(rel):
        raise ValueError("Absolute paths are not allowed. Provide a sandbox-relative path.")

    # Disallow path traversal token
    if ".." in rel.split("/"):
        raise ValueError("Path traversal detected (.. not allowed).")

    candidate = (SANDBOX_DIR / rel).resolve()

    if not _is_within_sandbox(candidate):
        raise ValueError("Resolved path is outside the sandbox and is forbidden.")

    # Optional top-level allowlist
    if ALLOWED_TOPDIRS:
        # top part of rel: the first path component
        top = rel.split("/", 1)[0]
        if top not in ALLOWED_TOPDIRS:
            raise ValueError(f"Top level directory '{top}' is not allowed by server policy.")

    return candidate

def _truncate_text(text: str, max_chars: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rsplit(" ", 1)[0] + "…"

# -------------------------
# Filesystem MCP Server
# -------------------------
class FilesystemMCPServer(IMCPExternalServer):
    """MCP Server providing safe, sandboxed filesystem access."""

    def __init__(self):
        super().__init__(name="Filesystem")
        _ensure_sandbox()
        logger.info("Filesystem MCP Server initialized. Sandbox: %s", SANDBOX_DIR)

    def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(name="filesystem.read_file",
                    description="Read a file (truncated by default).",
                    parameters={"type": "object", "properties": {"path": {"type": "string"}, "max_chars": {"type": "integer"}}, "required": ["path"]}),
            MCPTool(name="filesystem.write_file",
                    description="Write (overwrite) a file. Performs atomic write and enforces max size.",
                    parameters={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "max_bytes": {"type": "integer"}}, "required": ["path", "content"]}),
            MCPTool(name="filesystem.append_file",
                    description="Append content to existing file (creates file if missing).",
                    parameters={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "max_append_bytes": {"type": "integer"}}, "required": ["path", "content"]}),
            MCPTool(name="filesystem.list_dir",
                    description="List directory contents (files and directories).",
                    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
            MCPTool(name="filesystem.make_directory",
                    description="Create directory (recursively).",
                    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
            MCPTool(name="filesystem.file_exists",
                    description="Check if file/directory exists.",
                    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
            MCPTool(name="filesystem.delete",
                    description="Delete a file or empty directory.",
                    parameters={"type": "object", "properties": {"path": {"type": "string"}, "recursive": {"type": "boolean"}}, "required": ["path"]}),
            MCPTool(name="filesystem.move",
                    description="Move/rename a file or directory inside sandbox.",
                    parameters={"type": "object", "properties": {"src": {"type": "string"}, "dst": {"type": "string"}}, "required": ["src", "dst"]}),
            MCPTool(name="filesystem.copy",
                    description="Copy a file inside sandbox.",
                    parameters={"type": "object", "properties": {"src": {"type": "string"}, "dst": {"type": "string"}}, "required": ["src", "dst"]}),
            MCPTool(name="filesystem.get_metadata",
                    description="Get file metadata (size, is_dir, modified_time).",
                    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
            MCPTool(name="filesystem.search_files",
                    description="Search files with glob pattern under a directory.",
                    parameters={"type": "object", "properties": {"path": {"type": "string"}, "pattern": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["path", "pattern"]}),
        ]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # route tools
            if tool_name == "filesystem.read_file":
                rel = args.get("path", "")
                max_chars = int(args.get("max_chars", MAX_READ_CHARS))
                p = _get_safe_path(rel)
                if not p.exists():
                    return {"error": "File not found", "code": 404}
                if p.is_dir():
                    return {"error": "Path is a directory, not a file", "code": 400}
                # read with size guard
                with p.open("r", encoding="utf-8", errors="replace") as f:
                    txt = f.read(max_chars + 1024)  # read a bit more to allow clean truncation
                return {"path": rel, "content": _truncate_text(txt, max_chars), "code": 200}

            elif tool_name == "filesystem.write_file":
                rel = args.get("path", "")
                content = args.get("content", "")
                max_bytes = int(args.get("max_bytes", MAX_WRITE_BYTES))
                p = _get_safe_path(rel)

                # enforce parent exist
                p.parent.mkdir(parents=True, exist_ok=True)

                content_bytes = content.encode("utf-8")
                if len(content_bytes) > max_bytes:
                    return {"error": f"Content too large (>{max_bytes} bytes)", "code": 413}

                # atomic write using temporary file
                try:
                    with tempfile.NamedTemporaryFile(delete=False, dir=str(p.parent), prefix=".tmp_write_", mode="wb") as tmp:
                        tmp.write(content_bytes)
                        tmp.flush()
                        os.fsync(tmp.fileno())
                    # move into place
                    shutil.move(tmp.name, str(p))
                finally:
                    # cleanup leftover tmp if any (safe)
                    if os.path.exists(tmp.name):
                        try:
                            os.remove(tmp.name)
                        except Exception:
                            pass
                return {"status": "success", "path": rel, "bytes_written": len(content_bytes), "code": 200}

            elif tool_name == "filesystem.append_file":
                rel = args.get("path", "")
                content = args.get("content", "")
                max_append = int(args.get("max_append_bytes", MAX_WRITE_BYTES))
                p = _get_safe_path(rel)
                p.parent.mkdir(parents=True, exist_ok=True)
                append_bytes = content.encode("utf-8")
                if len(append_bytes) > max_append:
                    return {"error": f"Append content too large (>{max_append} bytes)", "code": 413}
                with p.open("ab") as f:
                    f.write(append_bytes)
                    f.flush()
                    os.fsync(f.fileno())
                return {"status": "success", "path": rel, "bytes_appended": len(append_bytes), "code": 200}

            elif tool_name == "filesystem.list_dir":
                rel = args.get("path", "")
                p = _get_safe_path(rel)
                if not p.exists():
                    return {"error": "Directory not found", "code": 404}
                if not p.is_dir():
                    return {"error": "Path is not a directory", "code": 400}
                entries = []
                for entry in sorted(p.iterdir()):
                    entries.append({
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size": entry.stat().st_size if entry.is_file() else None
                    })
                return {"path": rel, "items": entries, "code": 200}

            elif tool_name == "filesystem.make_directory":
                rel = args.get("path", "")
                p = _get_safe_path(rel)
                p.mkdir(parents=True, exist_ok=True)
                return {"status": "success", "path": rel, "code": 200}

            elif tool_name == "filesystem.file_exists":
                rel = args.get("path", "")
                p = _get_safe_path(rel)
                return {"path": rel, "exists": p.exists(), "code": 200}

            elif tool_name == "filesystem.delete":
                rel = args.get("path", "")
                recursive = bool(args.get("recursive", False))
                p = _get_safe_path(rel)
                if not p.exists():
                    return {"error": "Path not found", "code": 404}
                if p.is_dir():
                    if recursive:
                        shutil.rmtree(p)
                    else:
                        # only allow deletion of empty dirs
                        try:
                            p.rmdir()
                        except OSError:
                            return {"error": "Directory not empty; use recursive=true to remove", "code": 400}
                else:
                    p.unlink()
                return {"status": "deleted", "path": rel, "code": 200}

            elif tool_name == "filesystem.move":
                src_rel = args.get("src", "")
                dst_rel = args.get("dst", "")
                src = _get_safe_path(src_rel)
                dst = _get_safe_path(dst_rel)
                if not src.exists():
                    return {"error": "Source not found", "code": 404}
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                return {"status": "moved", "src": src_rel, "dst": dst_rel, "code": 200}

            elif tool_name == "filesystem.copy":
                src_rel = args.get("src", "")
                dst_rel = args.get("dst", "")
                src = _get_safe_path(src_rel)
                dst = _get_safe_path(dst_rel)
                if not src.exists():
                    return {"error": "Source not found", "code": 404}
                if src.is_dir():
                    # careful: copytree requires dst to not exist
                    if dst.exists():
                        return {"error": "Destination already exists for directory copy", "code": 400}
                    shutil.copytree(str(src), str(dst))
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                return {"status": "copied", "src": src_rel, "dst": dst_rel, "code": 200}

            elif tool_name == "filesystem.get_metadata":
                rel = args.get("path", "")
                p = _get_safe_path(rel)
                if not p.exists():
                    return {"error": "Path not found", "code": 404}
                st = p.stat()
                return {
                    "path": rel,
                    "is_dir": p.is_dir(),
                    "size_bytes": st.st_size,
                    "modified_time": int(st.st_mtime),
                    "created_time": int(st.st_ctime),
                    "code": 200
                }

            elif tool_name == "filesystem.search_files":
                rel = args.get("path", "")
                pattern = args.get("pattern", "*")
                max_results = int(args.get("max_results", 100))
                base = _get_safe_path(rel)
                if not base.exists() or not base.is_dir():
                    return {"error": "Base directory not found", "code": 404}
                # Use glob under base path
                glob_expr = str(base / pattern)
                matches = glob.glob(glob_expr, recursive=True)
                # normalize relative to sandbox
                rel_matches = []
                for m in matches[:max_results]:
                    mp = Path(m).resolve()
                    if _is_within_sandbox(mp):
                        rel_matches.append(str(mp.relative_to(SANDBOX_DIR)))
                return {"base": rel, "pattern": pattern, "matches": rel_matches, "count": len(rel_matches), "code": 200}

            else:
                return {"error": f"Unknown tool: {tool_name}", "code": 404}

        except ValueError as ve:
            logger.warning("Filesystem request validation error: %s", ve)
            return {"error": str(ve), "code": 400}
        except Exception as e:
            logger.exception("Filesystem tool error")
            return {"error": str(e), "code": 500}
