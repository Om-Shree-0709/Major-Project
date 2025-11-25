import os
import glob
from typing import Dict, Any, List

try:
    from mcp_core import IMCPExternalServer, MCPTool 
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

SANDBOX_DIR = "mcp_sandbox" 

class FilesystemMCPServer(IMCPExternalServer):
    """MCP Server providing tools for controlled file system access."""
    def __init__(self):
        super().__init__(name="Filesystem")
        self._ensure_sandbox()
        print(f"Filesystem MCP Server initialized.")

    def _ensure_sandbox(self):
        if not os.path.exists(SANDBOX_DIR):
            os.makedirs(SANDBOX_DIR, exist_ok=True)

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
            MCPTool(name="filesystem.list_dir", description="Lists directory contents.", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
            # NEW TOOLS
            MCPTool(name="filesystem.make_directory", description="Creates a new directory.", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
            MCPTool(name="filesystem.file_exists", description="Checks if a file or directory exists.", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
        ]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self._get_absolute_path(args.get("path", ""))
            
            if tool_name == "filesystem.read_file":
                if not os.path.exists(path): return {"error": "File not found"}
                with open(path, 'r', encoding='utf-8') as f: content = f.read()
                return {"path": args["path"], "content": content[:2000]} # Limit size
                
            elif tool_name == "filesystem.write_file":
                with open(path, 'w', encoding='utf-8') as f: f.write(args.get("content", ""))
                return {"status": "success", "message": f"File written to {args['path']}"}
                
            elif tool_name == "filesystem.list_dir":
                if not os.path.exists(path): return {"error": "Directory not found"}
                return {"items": os.listdir(path)}
            
            elif tool_name == "filesystem.make_directory":
                os.makedirs(path, exist_ok=True)
                return {"status": "success", "message": f"Directory created: {args['path']}"}
                
            elif tool_name == "filesystem.file_exists":
                return {"exists": os.path.exists(path)}
                
            raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            return {"error": str(e)}