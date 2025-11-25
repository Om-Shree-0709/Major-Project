from typing import Dict, Any, List
from pydantic import BaseModel, Field

# --- Core MCP Structures ---

class MCPTool(BaseModel):
    """Schema for a single tool exposed by an MCP Server (maps to LLM Function Calling)."""
    name: str = Field(description="Unique name for the tool (e.g., 'filesystem.read_file').")
    description: str = Field(description="Detailed description for the LLM to understand the tool's purpose.")
    parameters: Dict[str, Any] = Field(description="JSON schema defining the tool's input parameters (OpenAPI/JSON Schema format).")

class IMCPExternalServer:
    """
    Abstract Interface for all specialized MCP Servers (Filesystem, Browser, GitHub).
    All concrete servers must inherit from and implement these methods.
    """
    def __init__(self, name: str):
        self.name = name

    def list_tools(self) -> List[MCPTool]:
        """Returns the list of tools available on this server for LLM discovery."""
        raise NotImplementedError

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a specific tool on this server based on the LLM's request."""
        raise NotImplementedError