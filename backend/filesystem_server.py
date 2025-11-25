import os
from typing import Dict, Any, List
# Import core structures to break the circular dependency
from backend.mcp_core import IMCPExternalServer, MCPTool 

# --- Configuration ---
SANDBOX_DIR = "mcp_sandbox" 

class FilesystemMCPServer(IMCPExternalServer):
    """
    MCP Server providing tools for controlled file system access (read, write, list).
    Operations are strictly limited to the SANDBOX_DIR for security.
    """
    def __init__(self):
        super().__init__(name="Filesystem")
        self._ensure_sandbox()
        print(f"Filesystem MCP Server initialized. Sandbox: {os.path.abspath(SANDBOX_DIR)}")

    def _ensure_sandbox(self):
        """Ensures the sandbox directory exists and creates a test file."""
        if not os.path.exists(SANDBOX_DIR):
            os.makedirs(SANDBOX_DIR, exist_ok=True)
        
        readme_path = os.path.join(SANDBOX_DIR, "README.txt")
        if not os.path.exists(readme_path):
             with open(readme_path, "w") as f:
                f.write("This is the Filesystem MCP Server sandbox. Use tools to interact with this directory.")

    def _get_absolute_path(self, relative_path: str) -> str:
        """Translates a relative path to a secure, absolute path within the sandbox."""
        if ".." in relative_path:
            raise ValueError("Path traversal attempts (using '..') are forbidden.")
            
        absolute_path = os.path.abspath(os.path.join(SANDBOX_DIR, relative_path))
        
        # CRITICAL SECURITY CHECK
        if not absolute_path.startswith(os.path.abspath(SANDBOX_DIR)):
            raise ValueError("Security violation: Path traversal detected! Operation denied.")
            
        return absolute_path

    def list_tools(self) -> List[MCPTool]:
        """Exposes the filesystem capabilities as MCP Tools."""
        return [
            MCPTool(
                name="filesystem.read_file",
                description="Reads the content of a file from the sandbox directory. Useful for inspecting code or data.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "The path to the file relative to the sandbox (e.g., 'data.txt')."}
                    },
                    "required": ["path"]
                }
            ),
            MCPTool(
                name="filesystem.write_file",
                description="Writes content to a new file or overwrites an existing file in the sandbox directory. Requires user permission.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "The path to the file relative to the sandbox."},
                        "content": {"type": "string", "description": "The content to write to the file."}
                    },
                    "required": ["path", "content"]
                }
            ),
            MCPTool(
                name="filesystem.list_dir",
                description="Lists all files and directories in a given path within the sandbox. Use '.' for the root.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "The directory path relative to the sandbox (use '.' for the root)."}
                    },
                    "required": ["path"]
                }
            )
        ]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handles the execution of the requested filesystem tool."""
        
        try:
            if tool_name == "filesystem.read_file":
                path = self._get_absolute_path(args.get("path", ""))
                with open(path, 'r') as f:
                    content = f.read()
                return {"path": args["path"], "content_length": len(content), "content_snippet": content[:500]}

            elif tool_name == "filesystem.write_file":
                path = self._get_absolute_path(args.get("path", ""))
                content = args.get("content", "")
                with open(path, 'w') as f:
                    f.write(content)
                return {"path": args["path"], "size": len(content), "status": "content written successfully"}

            elif tool_name == "filesystem.list_dir":
                path = self._get_absolute_path(args.get("path", "."))
                items = os.listdir(path)
                return {"path": args["path"], "items": items, "count": len(items), "status": "success"}

            raise ValueError(f"Unknown tool: {tool_name}")

        except ValueError as e:
            return {"error": str(e), "tool": tool_name}
        except FileNotFoundError:
            return {"error": f"File or directory not found: {args.get('path')}", "tool": tool_name}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e!s}", "tool": tool_name}