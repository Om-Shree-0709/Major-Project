import json
import time
import asyncio
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # <--- CRITICAL IMPORT
from pydantic import BaseModel, Field
import uvicorn
import nest_asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Apply nest_asyncio
nest_asyncio.apply()

# --- Import Core Structures ---
try:
    from .mcp_core import IMCPExternalServer, MCPTool
except ImportError:
    # Fallback for running script directly
    from mcp_core import IMCPExternalServer, MCPTool

# --------------------------------------------------------------------------------
# 1. FASTAPI SCHEMAS AND APP SETUP
# --------------------------------------------------------------------------------

class HostQuery(BaseModel):
    user_query: str
    session_id: str = Field(default="default-session")

class HostResponse(BaseModel):
    final_answer: str
    tool_calls_executed: List[Dict[str, Any]] = Field(default_factory=list)

app = FastAPI(title="B.Tech MCP Host Server", version="1.0")

# --- CRITICAL: CORS MIDDLEWARE ---
# This allows the React Frontend (port 5173) to communicate with this Backend (port 8000)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------

CONNECTED_SERVERS: Dict[str, IMCPExternalServer] = {}

# --- Server Imports ---
try:
    from .filesystem_server import FilesystemMCPServer
    from .browser_server import BrowserMCPServer
    from .github_server import GitHubMCPServer
except ImportError as e:
    print(f"⚠️  Import Warning: Could not import one or more servers. {e}")
    # We continue, but some tools won't be available
    FilesystemMCPServer = None
    BrowserMCPServer = None
    GitHubMCPServer = None

# Placeholder Server
class PlaceholderMCPServer(IMCPExternalServer):
    def list_tools(self) -> List[MCPTool]:
        return [MCPTool(name="example.get_status", description="Checks host status.", parameters={"type": "object", "properties": {}})]
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "Host Online", "servers_active": list(CONNECTED_SERVERS.keys())}

def initialize_host():
    """Initializes and registers all connected MCP servers."""
    print("Initializing MCP Host...")
    
    # 1. Register Placeholder
    CONNECTED_SERVERS["placeholder"] = PlaceholderMCPServer(name="Placeholder")
    
    # 2. Register Specialized Servers (if imports worked)
    if FilesystemMCPServer:
        try:
            CONNECTED_SERVERS["filesystem"] = FilesystemMCPServer()
        except Exception as e:
            print(f"❌ Filesystem Init Failed: {e}")

    if BrowserMCPServer:
        try:
            CONNECTED_SERVERS["browser"] = BrowserMCPServer()
        except Exception as e:
            print(f"❌ Browser Init Failed: {e}")
        
    if GitHubMCPServer:
        try:
            CONNECTED_SERVERS["github"] = GitHubMCPServer()
        except Exception as e:
            print(f"❌ GitHub Init Failed: {e}")

    print(f"✅ Registered {len(CONNECTED_SERVERS)} servers: {list(CONNECTED_SERVERS.keys())}")


# --------------------------------------------------------------------------------
# 2. CORE ORCHESTRATION LOGIC (SIMULATED FOR PHASE B TESTING)
# --------------------------------------------------------------------------------

def simulate_llm_tool_selection(user_query: str, available_tools: List[MCPTool]) -> Optional[Dict[str, Any]]:
    """
    SIMULATED DECISION ENGINE.
    This replaces the real Gemini API for the initial connectivity test.
    """
    query = user_query.lower()
    
    # Filesystem Triggers
    if "list files" in query:
        return {"server_name": "filesystem", "tool_name": "filesystem.list_dir", "args": {"path": "."}}
    if "read file" in query:
        # Extract filename roughly
        path = "README.txt" # Default for test
        words = query.split()
        for w in words:
            if "." in w and len(w) > 2: path = w
        return {"server_name": "filesystem", "tool_name": "filesystem.read_file", "args": {"path": path}}
    if "write file" in query or "create file" in query:
        return {"server_name": "filesystem", "tool_name": "filesystem.write_file", "args": {"path": "test_log.txt", "content": "System Online"}}

    # Browser Triggers
    if "browse" in query:
        url = "https://example.com"
        for word in query.split():
            if word.startswith("http"): url = word
        return {"server_name": "browser", "tool_name": "browser.navigate_and_get_text", "args": {"url": url}}

    # GitHub Triggers
    if "repos" in query:
        return {"server_name": "github", "tool_name": "github.list_repos", "args": {}}

    # Status Trigger
    if "status" in query:
        return {"server_name": "placeholder", "tool_name": "example.get_status", "args": {}}
    
    return None

def orchestrate_request(query: HostQuery) -> HostResponse:
    """Orchestration: Query -> Tool Selection -> Execution -> Response"""
    
    # 1. Discover Tools
    available_tools = []
    for s in CONNECTED_SERVERS.values():
        try:
            available_tools.extend(s.list_tools())
        except: pass
    
    # 2. Select Tool (Simulated)
    tool_call = simulate_llm_tool_selection(query.user_query, available_tools)
    
    if tool_call:
        server_name = tool_call["server_name"]
        tool_name = tool_call["tool_name"]
        args = tool_call["args"]
        server = CONNECTED_SERVERS.get(server_name)
        
        if server:
            print(f"--- 🛠️ Executing {tool_name} on {server_name} ---")
            try:
                # 3. Execute Tool
                result = server.execute_tool(tool_name, args)
                final_text = f"I successfully executed '{tool_name}'. \n\n**Result:**\n{str(result)[:300]}..."
                return HostResponse(final_answer=final_text, tool_calls_executed=[{"tool": tool_name, "result": result}])
            except Exception as e:
                return HostResponse(final_answer=f"Tool Execution Failed: {e}", tool_calls_executed=[])
        else:
            return HostResponse(final_answer="Server not found internal error.")
            
    else:
        return HostResponse(final_answer=f"I received your query: '{query.user_query}'. \n(No specific tool trigger detected in Simulation Mode).")


# --------------------------------------------------------------------------------
# 3. FASTAPI ENDPOINT
# --------------------------------------------------------------------------------

@app.post("/query", response_model=HostResponse)
async def process_user_query(query: HostQuery):
    return orchestrate_request(query)

if __name__ == "__main__":
    initialize_host()
    print("\n--- 🚀 B.Tech MCP Host Server Online ---")
    uvicorn.run(app, host="127.0.0.1", port=8000)