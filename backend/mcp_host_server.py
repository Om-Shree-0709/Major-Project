import json
import time
import asyncio
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
import nest_asyncio
from dotenv import load_dotenv

# Load environment variables from .env file immediately
load_dotenv() 

# Apply nest_asyncio to handle async operations (like Playwright) within the sync FastAPI/Uvicorn environment
nest_asyncio.apply()

# --- Import Core Structures ---
from .mcp_core import IMCPExternalServer, MCPTool

# --------------------------------------------------------------------------------
# 1. FASTAPI SCHEMAS AND APP SETUP
# --------------------------------------------------------------------------------

class HostQuery(BaseModel):
    """Schema for the incoming user query."""
    user_query: str
    session_id: str = Field(default="default-session", description="Used to maintain conversation state.")

class HostResponse(BaseModel):
    """Schema for the outgoing response."""
    final_answer: str
    tool_calls_executed: List[Dict[str, Any]] = Field(default_factory=list, description="Trace of tools called and their results.")

app = FastAPI(title="B.Tech MCP Host Server", version="1.0", description="Orchestrates AI tool calls across specialized MCP Servers.")
CONNECTED_SERVERS: Dict[str, IMCPExternalServer] = {}

# --- Server Imports ---
# CORRECT
try:
    from .filesystem_server import FilesystemMCPServer
    from .browser_server import BrowserMCPServer
    from .github_server import GitHubMCPServer
except ImportError as e:
    # ...
    # This block is for debugging if the files were not found
    print(f"CRITICAL ERROR: Could not import a server file. Ensure all server files are in the same directory. Error: {e}")
    # Define dummy classes to allow basic startup for debugging
    FilesystemMCPServer = type('FilesystemMCPServer', (IMCPExternalServer,), {'list_tools': lambda self: [], 'execute_tool': lambda self, n, a: {"error": "Server not loaded"}})
    BrowserMCPServer = FilesystemMCPServer
    GitHubMCPServer = FilesystemMCPServer
    
# Placeholder Server Definition
class PlaceholderMCPServer(IMCPExternalServer):
    def list_tools(self) -> List[MCPTool]:
        return [MCPTool(name="example.get_status", description="Returns the current operational status of the host server.", parameters={"type": "object", "properties": {}})]
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "example.get_status":
            return {"status": f"Host operational. Servers registered: {list(CONNECTED_SERVERS.keys())}."}
        return {"error": f"Tool '{tool_name}' not found."}


def initialize_host():
    """Initializes and registers all connected MCP servers."""
    print("Initializing MCP Host...")
    
    # 1. Register Placeholder (Always available)
    CONNECTED_SERVERS["placeholder"] = PlaceholderMCPServer(name="Placeholder")
    
    # 2. Register Filesystem Server
    try:
        CONNECTED_SERVERS["filesystem"] = FilesystemMCPServer()
    except Exception as e:
        print(f"Error initializing FilesystemMCPServer: {e}")

    # 3. Register Browser Server
    try:
        CONNECTED_SERVERS["browser"] = BrowserMCPServer()
    except Exception as e:
        print(f"Error initializing BrowserMCPServer: {e}")
        
    # 4. Register GitHub Server
    try:
        CONNECTED_SERVERS["github"] = GitHubMCPServer()
    except Exception as e:
        print(f"Error initializing GitHubMCPServer: {e}")

    print(f"Registered {len(CONNECTED_SERVERS)} servers: {list(CONNECTED_SERVERS.keys())}")


# --------------------------------------------------------------------------------
# 2. CORE ORCHESTRATION LOGIC (SIMULATED LLM)
# --------------------------------------------------------------------------------

def simulate_llm_tool_selection(user_query: str, available_tools: List[MCPTool]) -> Optional[Dict[str, Any]]:
    """
    Simulates the LLM's decision-making process for tool selection based on keywords.
    (To be replaced by real LLM API in Phase B)
    """
    query = user_query.lower()
    
    # 1. Filesystem Simulations
    if "list files" in query or "directory contents" in query:
        return {"server_name": "filesystem", "tool_name": "filesystem.list_dir", "args": {"path": "."}}
    if "read file" in query or "content of" in query:
        path = query.split("file", 1)[-1].strip().split()[0].replace("?", "").replace(".", "") or "README.txt"
        return {"server_name": "filesystem", "tool_name": "filesystem.read_file", "args": {"path": path}}
    if "write file" in query or "create file" in query:
        if "content" in query:
            parts = query.split("content", 1)
            content = parts[1].strip()
            path = query.split("write file")[1].split("with content")[0].strip() or "test.txt"
            return {"server_name": "filesystem", "tool_name": "filesystem.write_file", "args": {"path": path, "content": content}}

    # 2. Browser Simulations
    if "browse" in query or "navigate to" in query:
        url_match = next((t.strip() for t in query.split() if t.startswith("http")), "https://modelcontextprotocol.io")
        return {"server_name": "browser", "tool_name": "browser.navigate_and_get_text", "args": {"url": url_match}}
    if "search website" in query and "for" in query:
        url_match = next((t.strip() for t in query.split() if t.startswith("http")), "https://en.wikipedia.org")
        keyword_match = query.split("for", 1)[-1].strip().split()[0]
        return {"server_name": "browser", "tool_name": "browser.search_page_for_keyword", "args": {"url": url_match, "keyword": keyword_match}}

    # 3. GitHub Simulations
    if "list my repos" in query or "check my issues" in query:
        return {"server_name": "github", "tool_name": "github.list_repos", "args": {}}
    if "get file from repo" in query:
        return {"server_name": "github", "tool_name": "github.get_repo_contents", "args": {"repo_name": "Major-Project", "path": "README.md"}}

    # 4. Placeholder status
    if "status" in query or "host state" in query:
        return {"server_name": "placeholder", "tool_name": "example.get_status", "args": {}}
    
    return None

def orchestrate_request(query: HostQuery) -> HostResponse:
    """The orchestration layer: LLM decision -> Tool execution -> Final LLM response."""
    
    # 1. Discover all tools
    available_tools = []
    for server_name, server in CONNECTED_SERVERS.items():
        try:
            tools = server.list_tools()
            available_tools.extend(tools)
        except NotImplementedError:
            continue
    
    # 2. LLM Tool Selection Phase
    tool_call = simulate_llm_tool_selection(query.user_query, available_tools)
    
    if tool_call:
        server_name = tool_call["server_name"]
        tool_name = tool_call["tool_name"]
        tool_args = tool_call["args"]
        
        server = CONNECTED_SERVERS.get(server_name)
        
        if not server:
            result = {"error": f"Server '{server_name}' not found."}
        else:
            try:
                # 3. Tool Execution Phase 
                print(f"\n--- Executing Tool: {tool_name} on {server_name} ---")
                tool_result = server.execute_tool(tool_name, tool_args)
                result = {"success": tool_result}
            except Exception as e:
                result = {"error": f"Tool execution failed on {server.name} ({tool_name}): {e!s}"}

        # 4. LLM Response Generation (Simulated)
        final_answer = f"I executed the tool '{tool_name}' on server '{server_name}' and got the following result:\n\n```json\n{json.dumps(result, indent=2)}\n```\n\n(This is a simulated final answer based on the tool result. Proceed to Phase B to integrate a real LLM.)"
        
        return HostResponse(
            final_answer=final_answer,
            tool_calls_executed=[{"tool": tool_name, "result": result}]
        )
        
    else:
        # 5. Direct LLM Response (Simulated)
        final_answer = f"I cannot find a specialized tool to help with '{query.user_query}'. I only have access to tools from: {list(CONNECTED_SERVERS.keys())}."
        return HostResponse(final_answer=final_answer)


# --------------------------------------------------------------------------------
# 3. FASTAPI ENDPOINT & LOCAL RUNNER
# --------------------------------------------------------------------------------

@app.post("/query", response_model=HostResponse, summary="Process a user query using available MCP tools.")
async def process_user_query(query: HostQuery):
    """
    Receives a user query and orchestrates the LLM decision and tool execution 
    across all connected MCP servers.
    """
    return orchestrate_request(query)

# --- Server Startup ---
if __name__ == "__main__":
    initialize_host()
    print("\n--- B.Tech MCP Host Server Running Locally ---")
    print("Access the API docs at: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)