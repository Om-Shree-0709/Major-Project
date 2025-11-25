import sys
import asyncio

# --- CRITICAL FIX FOR WINDOWS + PLAYWRIGHT ---
# This forces Python to use the SelectorEventLoop, which is required 
# for Playwright to work inside uvicorn on Windows.
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# ---------------------------------------------

import json
import os
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
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
    try:
        from .mcp_core import IMCPExternalServer, MCPTool
    except ImportError:
        pass

# --------------------------------------------------------------------------------
# 2. AUTO-DISCOVERY & STATE
# --------------------------------------------------------------------------------

CONNECTED_SERVERS: Dict[str, Any] = {}
ACTIVE_MODEL_NAME = "models/gemini-2.0-flash-lite" # Default

def find_best_model():
    """Queries Google API to find the best available model."""
    global ACTIVE_MODEL_NAME
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ CRITICAL: No API Key found in .env")
        return

    try:
        genai.configure(api_key=api_key.strip())
        print("🔍 Optimizing AI Model Selection...")
        
        # Priority: Flash models are faster and have higher rate limits
        preferences = [
            'models/gemini-2.0-flash-lite',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-flash-latest',
            'models/gemini-2.0-flash',
        ]
        
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception:
            pass

        for pref in preferences:
            if pref in available_models:
                ACTIVE_MODEL_NAME = pref
                print(f"✅ Optimized Model Selected: {ACTIVE_MODEL_NAME}")
                return

        if available_models:
            ACTIVE_MODEL_NAME = available_models[0]
            print(f"⚠️ Using Fallback Model: {ACTIVE_MODEL_NAME}")

    except Exception as e:
        print(f"⚠️ Model Discovery Failed: {e}")

def load_tools():
    """Imports and initializes tools."""
    print("🛠️  Loading MCP Tools...")
    try:
        from filesystem_server import FilesystemMCPServer
        from browser_server import BrowserMCPServer
        from github_server import GitHubMCPServer
        
        CONNECTED_SERVERS["filesystem"] = FilesystemMCPServer()
        CONNECTED_SERVERS["browser"] = BrowserMCPServer()
        CONNECTED_SERVERS["github"] = GitHubMCPServer()
        print(f"✅ Tools Online: {list(CONNECTED_SERVERS.keys())}")
    except ImportError:
        # Fallback for relative imports
        try:
            from .filesystem_server import FilesystemMCPServer
            from .browser_server import BrowserMCPServer
            from .github_server import GitHubMCPServer
            
            CONNECTED_SERVERS["filesystem"] = FilesystemMCPServer()
            CONNECTED_SERVERS["browser"] = BrowserMCPServer()
            CONNECTED_SERVERS["github"] = GitHubMCPServer()
            print(f"✅ Tools Online (Relative): {list(CONNECTED_SERVERS.keys())}")
        except Exception as e:
            print(f"⚠️ Tool Load Error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n>>> STARTING MCP HOST SERVER <<<")
    find_best_model() 
    load_tools()
    yield
    print(">>> SHUTTING DOWN <<<")

# --------------------------------------------------------------------------------
# 3. FASTAPI APP
# --------------------------------------------------------------------------------

class HostQuery(BaseModel):
    user_query: str
    session_id: str = Field(default="default-session")

class HostResponse(BaseModel):
    final_answer: str
    tool_calls_executed: List[Dict[str, Any]] = Field(default_factory=list)

app = FastAPI(title="B.Tech MCP Host Agent", version="3.5 (Final)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------------
# 4. AI LOGIC
# --------------------------------------------------------------------------------

def clean_json_string(json_str: str) -> str:
    cleaned = json_str.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    if cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    return cleaned.strip()

def smart_tool_selection(user_query: str, available_tools: List[Any]) -> Optional[Dict[str, Any]]:
    try:
        model = genai.GenerativeModel(ACTIVE_MODEL_NAME)
        
        tools_desc = []
        for t in available_tools:
            if hasattr(t, 'dict'): tools_desc.append(t.dict())
            else: tools_desc.append(str(t))

        tools_json = json.dumps(tools_desc, indent=2)
        
        system_prompt = f"""
        You are an AI Agent. Available Tools:
        {tools_json}

        USER: "{user_query}"

        DECISION:
        Return ONLY a JSON object. 
        1. If a tool matches, output: {{ "server_name": "...", "tool_name": "...", "args": {{...}} }}
        2. If multiple tools apply, pick the best one.
        3. If no tool needed, return {{}}
        
        IMPORTANT: 
        - Use 'filesystem.read_file' to read.
        - Use 'browser.perform_google_search' for news/queries.
        """

        response = model.generate_content(system_prompt)
        cleaned = clean_json_string(response.text)
        if not cleaned or cleaned == "{}": return None
        return json.loads(cleaned)
    except Exception as e:
        print(f"⚠️ AI Decision Error: {e}")
        return None

def generate_final_answer(user_query: str, tool_result: Dict[str, Any]) -> str:
    try:
        time.sleep(1) # Rate limit safety
        model = genai.GenerativeModel(ACTIVE_MODEL_NAME)
        prompt = f"Query: {user_query}\nResult: {json.dumps(tool_result)}\nSummarize the result in natural language."
        return model.generate_content(prompt).text
    except Exception:
        return "Task completed."

# --------------------------------------------------------------------------------
# 5. ENDPOINT
# --------------------------------------------------------------------------------

@app.post("/query", response_model=HostResponse)
async def process_user_query(query: HostQuery):
    # Bypass health checks to save quota
    if query.session_id == "health-check" or query.user_query.lower() in ["status check", "host status check"]:
        return HostResponse(final_answer="Online", tool_calls_executed=[])

    if not CONNECTED_SERVERS:
        return HostResponse(final_answer="Backend Running, but Tools Failed to Load.")

    all_tools = []
    for s in CONNECTED_SERVERS.values():
        try: all_tools.extend(s.list_tools())
        except: pass

    decision = smart_tool_selection(query.user_query, all_tools)

    if decision:
        tool_name = decision.get("tool_name", "")
        server_name = decision.get("server_name")
        args = decision.get("args", {})

        # --- AUTO-CORRECT SERVER NAME ---
        if not server_name:
            if "filesystem" in tool_name: server_name = "filesystem"
            elif "browser" in tool_name: server_name = "browser"
            elif "github" in tool_name: server_name = "github"
        
        # --- AUTO-CORRECT TOOL NAME ---
        if server_name == "filesystem" and not tool_name.startswith("filesystem."):
            tool_name = f"filesystem.{tool_name}"
        if server_name == "browser" and not tool_name.startswith("browser."):
            tool_name = f"browser.{tool_name}"
        
        if server_name in CONNECTED_SERVERS:
            try:
                print(f"⚡ Executing {tool_name} on {server_name}...")
                result = CONNECTED_SERVERS[server_name].execute_tool(tool_name, args)
                final_text = generate_final_answer(query.user_query, result)
                return HostResponse(final_answer=final_text, tool_calls_executed=[{"tool": tool_name, "result": result}])
            except Exception as e:
                return HostResponse(final_answer=f"Tool Execution Error: {e}")
        
        return HostResponse(final_answer=f"Server '{server_name}' not found. (Tool: {tool_name})")
    
    # Chat Mode
    try:
        model = genai.GenerativeModel(ACTIVE_MODEL_NAME)
        return HostResponse(final_answer=model.generate_content(query.user_query).text)
    except Exception as e:
        return HostResponse(final_answer=f"AI Error ({ACTIVE_MODEL_NAME}): {e}")

if __name__ == "__main__":
    uvicorn.run("mcp_host_server:app", host="127.0.0.1", port=8000, reload=True)