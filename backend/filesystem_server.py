import os
from typing import Dict, Any, List

# FIX: Robust Import
try:
    from mcp_core import IMCPExternalServer, MCPTool 
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

# --- Configuration ---
SANDBOX_DIR = "mcp_sandbox" 

class FilesystemMCPServer(IMCPExternalServer):
    """MCP Server providing tools for controlled file system access."""
    def __init__(self):
        super().__init__(name="Filesystem")
        self._ensure_sandbox()
        print(f"Filesystem MCP Server initialized. Sandbox: {os.path.abspath(SANDBOX_DIR)}")

    def _ensure_sandbox(self):
        if not os.path.exists(SANDBOX_DIR):
            os.makedirs(SANDBOX_DIR, exist_ok=True)
        readme_path = os.path.join(SANDBOX_DIR, "README.txt")
        if not os.path.exists(readme_path):
             with open(readme_path, "w") as f:
                f.write("This is the Filesystem MCP Server sandbox.")

    def _get_absolute_path(self, relative_path: str) -> str:
        if ".." in relative_path:
            raise ValueError("Path traversal attempts (using '..') are forbidden.")
        absolute_path = os.path.abspath(os.path.join(SANDBOX_DIR, relative_path))
        if not absolute_path.startswith(os.path.abspath(SANDBOX_DIR)):
            raise ValueError("Security violation: Path traversal detected!")
        return absolute_path

    def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(name="filesystem.read_file", description="Reads content of a file.", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
            MCPTool(name="filesystem.write_file", description="Writes content to a file.", parameters={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}),
            MCPTool(name="filesystem.list_dir", description="Lists directory contents.", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]})
        ]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "filesystem.read_file":
                path = self._get_absolute_path(args.get("path", ""))
                with open(path, 'r') as f: content = f.read()
                return {"path": args["path"], "content_length": len(content), "content_snippet": content[:1000]}
            elif tool_name == "filesystem.write_file":
                path = self._get_absolute_path(args.get("path", ""))
                with open(path, 'w') as f: f.write(args.get("content", ""))
                return {"path": args["path"], "status": "success"}
            elif tool_name == "filesystem.list_dir":
                path = self._get_absolute_path(args.get("path", "."))
                return {"path": args["path"], "items": os.listdir(path)}
            raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            return {"error": str(e), "tool": tool_name}