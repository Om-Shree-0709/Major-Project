import json
import os
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import nest_asyncio
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
nest_asyncio.apply()

# --- Import Core Structures ---
try:
    from mcp_core import IMCPExternalServer, MCPTool
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

# --------------------------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# --------------------------------------------------------------------------------

class HostQuery(BaseModel):
    user_query: str
    session_id: str = Field(default="default-session")

class HostResponse(BaseModel):
    final_answer: str
    tool_calls_executed: List[Dict[str, Any]] = Field(default_factory=list)

app = FastAPI(title="B.Tech MCP Host Agent", version="2.0 (Smart Mode)")

# Allow Frontend Connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONNECTED_SERVERS: Dict[str, IMCPExternalServer] = {}

# Import Tools (Robust Import Strategy)
try:
    from filesystem_server import FilesystemMCPServer
    from browser_server import BrowserMCPServer
    from github_server import GitHubMCPServer
except ImportError:
    # Fallback if running as a package
    try:
        from .filesystem_server import FilesystemMCPServer
        from .browser_server import BrowserMCPServer
        from .github_server import GitHubMCPServer
    except ImportError as e:
        print(f"⚠️ Critical Import Error: {e}")

def initialize_host():
    """Initializes and registers all connected MCP servers."""
    print("Initializing Smart MCP Host...")
    try:
        CONNECTED_SERVERS["filesystem"] = FilesystemMCPServer()
        CONNECTED_SERVERS["browser"] = BrowserMCPServer()
        CONNECTED_SERVERS["github"] = GitHubMCPServer()
        print(f"✅ Servers Online: {list(CONNECTED_SERVERS.keys())}")
    except Exception as e:
        print(f"❌ Server Init Error: {e}")

# --------------------------------------------------------------------------------
# 2. INTELLIGENT AGENT LOGIC (GEMINI API)
# --------------------------------------------------------------------------------

def clean_json_string(json_str: str) -> str:
    """Cleans Markdown formatting (```json ... ```) from LLM response."""
    cleaned = json_str.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def smart_tool_selection(user_query: str, available_tools: List[MCPTool]) -> Optional[Dict[str, Any]]:
    """
    Sends the user query and tool definitions to Gemini to decide the best action.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ CRITICAL ERROR: GEMINI_API_KEY is missing in .env")
        return None

    genai.configure(api_key=api_key)
    # UPDATED MODEL NAME
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Prepare Tool Descriptions for the AI
    tools_json = json.dumps([t.dict() for t in available_tools], indent=2)
    
    system_prompt = f"""
    You are an AI Agent Orchestrator. You have access to the following tools:
    {tools_json}

    USER REQUEST: "{user_query}"

    YOUR GOAL:
    1. Decide if any tool is needed to fulfill the request.
    2. If YES: Return a STRICT JSON object with "server_name", "tool_name", and "args".
    3. If NO (or if you can answer directly): Return an empty JSON object {{}}.
    
    IMPORTANT: Return ONLY valid JSON. Do not write explanation text outside the JSON.
    """

    try:
        print("🤖 Asking Gemini for a plan...")
        response = model.generate_content(system_prompt)
        cleaned_response = clean_json_string(response.text)
        
        if not cleaned_response or cleaned_response == "{}":
            return None
            
        tool_decision = json.loads(cleaned_response)
        return tool_decision

    except Exception as e:
        print(f"⚠️ Gemini Decision Error: {e}")
        return None

def generate_final_answer(user_query: str, tool_result: Dict[str, Any]) -> str:
    """Generates a natural language summary after the tool has finished."""
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    # UPDATED MODEL NAME
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    User Query: "{user_query}"
    Tool Execution Result: {json.dumps(tool_result)}
    
    Please provide a helpful, natural language response to the user based on this result.
    """
    response = model.generate_content(prompt)
    return response.text

# --------------------------------------------------------------------------------
# 3. ORCHESTRATION & ENDPOINT
# --------------------------------------------------------------------------------

@app.post("/query", response_model=HostResponse)
async def process_user_query(query: HostQuery):
    
    # 1. Gather all tools
    all_tools = []
    for s in CONNECTED_SERVERS.values():
        all_tools.extend(s.list_tools())

    # 2. Ask AI to pick a tool
    decision = smart_tool_selection(query.user_query, all_tools)

    if decision:
        server_name = decision.get("server_name")
        tool_name = decision.get("tool_name")
        args = decision.get("args", {})
        
        server = CONNECTED_SERVERS.get(server_name)
        if server:
            # 3. Execute the Tool
            print(f"⚡ Executing {tool_name} on {server_name}...")
            try:
                tool_result = server.execute_tool(tool_name, args)
                
                # 4. Generate Final Answer based on Tool Result
                final_text = generate_final_answer(query.user_query, tool_result)
                
                return HostResponse(
                    final_answer=final_text, 
                    tool_calls_executed=[{"tool": tool_name, "result": tool_result}]
                )
            except Exception as e:
                return HostResponse(final_answer=f"Tool Error: {str(e)}")
        else:
             return HostResponse(final_answer=f"Error: Server '{server_name}' not found.")

    else:
        # 5. No tool needed (Chat Mode)
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(query.user_query)
            return HostResponse(final_answer=response.text)
        else:
            return HostResponse(final_answer="I am online, but GEMINI_API_KEY is missing, so I can't think.")

if __name__ == "__main__":
    initialize_host()
    print("\n--- 🧠 Smart MCP Host Agent Online ---")
    uvicorn.run(app, host="127.0.0.1", port=8000)