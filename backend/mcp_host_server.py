from __future__ import annotations
import sys
import asyncio
import logging
import json
import os
import time
from typing import Dict, Any, List, Optional, Callable, Coroutine

# Windows-specific event loop policy (Critical for Playwright)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

# Swarm Integration
try:
    from swarm_manager import PERSONAS, SwarmContext
except ImportError:
    # Fallback if module is relative
    from .swarm_manager import PERSONAS, SwarmContext

load_dotenv()

# Optional Google Generative AI
try:
    import google.generativeai as genai  # type: ignore
    HAVE_GENAI = True
except Exception:
    HAVE_GENAI = False

# Import core and servers
try:
    from mcp_core import IMCPExternalServer, MCPTool, ToolExecutionError
except Exception:
    from .mcp_core import IMCPExternalServer, MCPTool, ToolExecutionError  # type: ignore

# Configure logging
logger = logging.getLogger("mcp_host_server")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Global state
CONNECTED_SERVERS: Dict[str, IMCPExternalServer] = {}
ACTIVE_MODEL_NAME: Optional[str] = None

# Default model preferences
MODEL_PREFERENCES = [
    "models/gemini-1.5-flash",       
    "models/gemini-1.5-flash-latest",
]

# -------------------------
# Model discovery & setup
# -------------------------
def configure_genai_from_env() -> Optional[str]:
    if not HAVE_GENAI:
        logger.info("google.generativeai not available; skipping model discovery.")
        return None

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Google API key found.")
        return None

    try:
        genai.configure(api_key=api_key.strip())
        available_models = [m.name for m in genai.list_models() 
                            if "generateContent" in m.supported_generation_methods]
        
        for pref in MODEL_PREFERENCES:
            if pref in available_models:
                return pref
        return available_models[0] if available_models else None
    except Exception as e:
        logger.exception("Model discovery failed: %s", e)
    return None

# -------------------------
# Tool discovery & loading
# -------------------------
def load_tools() -> None:
    logger.info("Loading MCP tools...")
    candidates = [
        ("filesystem", "filesystem_server", "FilesystemMCPServer"),
        ("browser", "browser_server", "BrowserMCPServer"),
        ("github", "github_server", "GitHubMCPServer"),
    ]

    for key, module_name, class_name in candidates:
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
            CONNECTED_SERVERS[key] = cls()
            logger.info(f"Loaded server '{key}'")
        except Exception as e:
            logger.warning(f"Failed to load {class_name}: {e}")

# -------------------------
# Lifespan management
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global ACTIVE_MODEL_NAME
    ACTIVE_MODEL_NAME = configure_genai_from_env()
    load_tools()
    yield
    for name, srv in CONNECTED_SERVERS.items():
        for attr in ["shutdown", "stop", "close"]:
            fn = getattr(srv, attr, None)
            if callable(fn):
                if asyncio.iscoroutinefunction(fn): await fn()
                else: await asyncio.get_running_loop().run_in_executor(None, fn)
                break

# -------------------------
# FastAPI app & models
# -------------------------
class HostQuery(BaseModel):
    user_query: str = Field(..., description="Natural language user query")
    session_id: str = Field(default="default-session")

class HostResponse(BaseModel):
    final_answer: str
    tool_calls_executed: List[Dict[str, Any]] = Field(default_factory=list)

app = FastAPI(title="Unified Swarm MCP Host", version="1.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_json_string(json_str: str) -> str:
    s = json_str.strip()
    if s.startswith("```json"): s = s[7:]
    if s.startswith("```"): s = s[3:]
    if s.endswith("```"): s = s[:-3]
    return s.strip()

# -------------------------
# Swarm Orchestration Endpoint
# -------------------------
@app.post("/query", response_model=HostResponse)
async def process_user_query(query: HostQuery):
    if not query.user_query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if query.session_id == "health-check" or query.user_query.lower() in ["status check", "health check"]:
        return HostResponse(final_answer="Online", tool_calls_executed=[])

    if not CONNECTED_SERVERS:
        raise HTTPException(status_code=503, detail="No tools loaded.")

    # Initialize Swarm Memory
    context = SwarmContext()
    context.add_event("User", query.user_query)
    executed_tool_calls = []
    max_iterations = 5 

    for i in range(max_iterations):
        available_tools: List[MCPTool] = []
        for srv in CONNECTED_SERVERS.values():
            try: available_tools.extend(srv.list_tools())
            except: continue

        # System Prompt enforces Persona-based behavior
        system_prompt = f"""
        Current Swarm Context: {context.get_full_context()}
        Persona: {PERSONAS['Manager']['prompt']}
        Available Tools: {json.dumps([t.dict() for t in available_tools])}

        Return ONLY a JSON object:
        {{ "tool_call": {{ "server_name": "...", "tool_name": "...", "args": {{...}} }}, "final_answer": null }}
        OR
        {{ "tool_call": null, "final_answer": "your summary here" }}
        """

        try:
            model = genai.GenerativeModel(ACTIVE_MODEL_NAME)
            resp = model.generate_content(system_prompt)
            decision = json.loads(clean_json_string(resp.text))
        except Exception as e:
            logger.error(f"Reasoning Error: {e}")
            return HostResponse(final_answer="Orchestrator encountered a reasoning error.", tool_calls_executed=executed_tool_calls)

        if decision.get("final_answer"):
            return HostResponse(final_answer=decision["final_answer"], tool_calls_executed=executed_tool_calls)

        t_call = decision.get("tool_call")
        if t_call:
            server_name = t_call.get("server_name")
            tool_name = t_call.get("tool_name")
            args = t_call.get("args", {})

            # Security Guardrail: Check Server Registration
            if server_name not in CONNECTED_SERVERS:
                context.add_event("System", f"Security Block: Unregistered server '{server_name}'")
                continue

            server = CONNECTED_SERVERS[server_name]
            try:
                logger.info(f"Step {i}: Executing {tool_name}")
                result = await server.run_tool(tool_name, args)

                # Error Detection within Tool Payloads
                if isinstance(result, dict) and (result.get("error") or result.get("code", 200) >= 400):
                    context.add_event(f"Tool:{tool_name}", f"Error: {result.get('error')}")
                else:
                    context.add_event(f"Tool:{tool_name}", json.dumps(result))
                
                executed_tool_calls.append({"server": server_name, "tool": tool_name, "args": args, "result": result})
            except Exception as e:
                context.add_event("System", f"Execution Failure: {str(e)}")
                executed_tool_calls.append({"server": server_name, "tool": tool_name, "args": args, "result": {"error": str(e)}})
        else:
            break

    return HostResponse(final_answer="Processing limit reached. Review steps taken.", tool_calls_executed=executed_tool_calls)

@app.get("/health")
async def health():
    return {"status": "ok", "tools": list(CONNECTED_SERVERS.keys()), "model": ACTIVE_MODEL_NAME}

@app.get("/tools")
async def list_all_tools():
    out = {}
    for name, srv in CONNECTED_SERVERS.items():
        try: out[name] = [t.dict() for t in srv.list_tools()]
        except: out[name] = {"error": True}
    return out

if __name__ == "__main__":
    uvicorn.run("mcp_host_server:app", host="127.0.0.1", port=8000, reload=True)