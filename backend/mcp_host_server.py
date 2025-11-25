# backend/mcp_host_server.py
"""
MCP Host Server - production-ready version.

Improvements over original:
- Uses async-safe run_tool wrapper from mcp_core for executing tools.
- Robust model discovery with graceful fallback when Google Generative API is unavailable.
- LLM-driven tool selection when available, otherwise a heuristic fallback.
- Health and tools endpoints.
- Graceful startup/shutdown of connected servers (calls optional shutdown/stop/close).
- Structured logging and error handling.
"""

from __future__ import annotations
import sys
import asyncio
import logging
import json
import os
import time
from typing import Dict, Any, List, Optional, Callable, Coroutine

# Windows-specific event loop policy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv
load_dotenv()

# Optional Google Generative AI
try:
    import google.generativeai as genai  # type: ignore
    HAVE_GENAI = True
except Exception:
    HAVE_GENAI = False

# Import core and servers (robust imports)
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

# Default model preferences (for Google Generative API)
MODEL_PREFERENCES = [
    "models/gemini-2.0-flash-lite",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-flash-latest",
    "models/gemini-2.0-flash",
]


# -------------------------
# Model discovery & setup
# -------------------------
def configure_genai_from_env() -> Optional[str]:
    """Configure google.generativeai if API key present and return selected model name."""
    if not HAVE_GENAI:
        logger.info("google.generativeai not available; skipping model discovery.")
        return None

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Google API key found (GEMINI_API_KEY / GOOGLE_API_KEY).")
        return None

    try:
        genai.configure(api_key=api_key.strip())
    except Exception as e:
        logger.exception("Failed to configure google.generativeai: %s", e)
        return None

    try:
        available_models = []
        for m in genai.list_models():
            # Only include generation-capable models
            try:
                if hasattr(m, "supported_generation_methods") and "generateContent" in m.supported_generation_methods:
                    available_models.append(m.name)
            except Exception:
                continue

        # Select preferred model if available
        for pref in MODEL_PREFERENCES:
            if pref in available_models:
                logger.info("Selected model: %s", pref)
                return pref

        if available_models:
            logger.info("No preferred model found, using first available: %s", available_models[0])
            return available_models[0]
    except Exception as e:
        logger.exception("Model discovery failed: %s", e)

    return None


# -------------------------
# Tool discovery & loading
# -------------------------
def load_tools() -> None:
    """Import and initialize MCP servers; register them in CONNECTED_SERVERS."""
    logger.info("Loading MCP tools...")
    # Try top-level imports first, then package-relative
    candidates = [
        ("filesystem", "filesystem_server", "FilesystemMCPServer"),
        ("browser", "browser_server", "BrowserMCPServer"),
        ("github", "github_server", "GitHubMCPServer"),
    ]

    for key, module_name, class_name in candidates:
        try:
            module = __import__(module_name)
        except Exception:
            try:
                module = __import__(f".{module_name}", fromlist=[class_name])
            except Exception as e:
                logger.warning("Module %s not found: %s", module_name, e)
                continue

        try:
            cls = getattr(module, class_name)
            instance = cls()
            CONNECTED_SERVERS[key] = instance
            logger.info("Loaded server '%s' -> %s", key, class_name)
        except Exception as e:
            logger.exception("Failed to initialize %s: %s", class_name, e)


# -------------------------
# Lifespan management
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(">>> STARTING MCP HOST SERVER <<<")
    global ACTIVE_MODEL_NAME
    ACTIVE_MODEL_NAME = configure_genai_from_env()
    # load servers (may call Playwright, GitHub auth etc.)
    load_tools()
    yield
    logger.info(">>> SHUTTING DOWN MCP HOST SERVER <<<")
    # Attempt graceful shutdown of connected servers (if they expose stop/shutdown)
    for name, srv in CONNECTED_SERVERS.items():
        try:
            # If server has async 'stop' or 'shutdown', await it. If sync, call directly.
            shutdown_candidates = ["shutdown", "stop", "close"]
            for attr in shutdown_candidates:
                fn = getattr(srv, attr, None)
                if callable(fn):
                    if asyncio.iscoroutinefunction(fn):
                        await fn()
                    else:
                        # run sync call in threadpool to avoid blocking
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, fn)
                    logger.info("Graceful shutdown called for %s (%s)", name, attr)
                    break
        except Exception:
            logger.exception("Error during shutdown of server %s", name)


# -------------------------
# FastAPI app & models
# -------------------------
class HostQuery(BaseModel):
    user_query: str = Field(..., description="Natural language user query")
    session_id: str = Field(default="default-session")


class ToolCallRecord(BaseModel):
    server: str
    tool: str
    args: Dict[str, Any]
    result: Dict[str, Any]


class HostResponse(BaseModel):
    final_answer: str
    tool_calls_executed: List[Dict[str, Any]] = Field(default_factory=list)


app = FastAPI(title="MCP Host Agent", version="1.0", lifespan=lifespan)

# CORS - adjust origins for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Tool selection helpers
# -------------------------
def clean_json_string(json_str: str) -> str:
    """Strip common code fences from the LLM output."""
    if not isinstance(json_str, str):
        return ""
    s = json_str.strip()
    if s.startswith("```json"):
        s = s[7:]
    if s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


async def llm_select_tool(user_query: str, available_tools: List[MCPTool]) -> Optional[Dict[str, Any]]:
    """Ask the LLM (Gemini via google.generativeai) to map query -> tool call.
    Returns a dict: {'server_name':..., 'tool_name':..., 'args': {...}} or None.
    Gracefully falls back to heuristic if genai not configured / errors.
    """
    if not HAVE_GENAI or not ACTIVE_MODEL_NAME:
        return None

    try:
        # Build a concise tools list for the LLM
        tools_desc = [t.dict() for t in available_tools]
        tools_json = json.dumps(tools_desc, indent=2)

        system_prompt = f"""
You are an assistant mapping user queries to a single tool call. 
Available tools (JSON): {tools_json}

User query: "{user_query}"

Return ONLY a JSON object with one of:
- {{ "server_name": "...", "tool_name": "...", "args": {{...}} }} 
- {{}} (if no tool necessary)

Use existing tool names exactly (e.g., "browser.perform_google_search" or "filesystem.read_file").
"""
        model = genai.GenerativeModel(ACTIVE_MODEL_NAME)
        resp = model.generate_content(system_prompt)
        text = clean_json_string(resp.text)
        if not text or text == "{}":
            return None
        parsed = json.loads(text)
        return parsed
    except Exception as e:
        logger.exception("LLM tool selection failed: %s", e)
        return None


def heuristic_select_tool(user_query: str, available_tools: List[MCPTool]) -> Optional[Dict[str, Any]]:
    """Lightweight heuristic when LLM isn't available: map queries to likely tools."""
    q = user_query.lower()
    # simple heuristics - extend as needed
    if any(word in q for word in ["search", "google", "bing", "news", "look up", "find"]):
        return {"server_name": "browser", "tool_name": "browser.perform_google_search", "args": {"query": user_query}}
    if any(word in q for word in ["read file", "open file", "show file", "cat file"]):
        # expects 'path:' in query or followup will be needed; attempt to extract a path token
        # If no path provided, return None to let fallback chat mode run
        # quick extraction: look for "path " or "path:"
        if " path " in q or "path:" in q:
            # crude extraction - find token after 'path' or 'path:'
            if "path:" in q:
                path_token = q.split("path:")[1].strip().split()[0]
            else:
                path_token = q.split("path")[1].strip().split()[0]
            return {"server_name": "filesystem", "tool_name": "filesystem.read_file", "args": {"path": path_token}}
        return None
    if any(word in q for word in ["repo", "github", "file in repo", "read repo"]):
        # try to map to github.read_file if user provided owner/repo/path patterns
        # look for pattern owner/repo
        tokens = q.split()
        for t in tokens:
            if "/" in t and len(t.split("/")) == 2:
                # If there is a slash, guess it's owner/repo; require path in query for file reading
                if "path:" in q:
                    # extract path value after path:
                    try:
                        path_token = q.split("path:")[1].strip().split()[0]
                        return {"server_name": "github", "tool_name": "github.read_file", "args": {"repo_full_name": t, "path": path_token}}
                    except Exception:
                        continue
        return None
    # default: no tool
    return None


# -------------------------
# AI summarization helper
# -------------------------
async def generate_final_answer(user_query: str, tool_result: Dict[str, Any]) -> str:
    """Summarize tool_result into a natural language answer using LLM if available."""
    # If genai available, ask model to summarize; otherwise return compact summary
    if HAVE_GENAI and ACTIVE_MODEL_NAME:
        try:
            model = genai.GenerativeModel(ACTIVE_MODEL_NAME)
            prompt = f"Query: {user_query}\nTool result (JSON): {json.dumps(tool_result, default=str)}\nProvide a short, user-friendly summary of the result."
            resp = model.generate_content(prompt)
            return resp.text
        except Exception:
            logger.exception("LLM summarization failed; falling back to simple summary.")
    # Fallback simple summary
    try:
        # try to produce a short string representation
        if isinstance(tool_result, dict):
            # if result contains 'result' top-level (from our MCP servers), present it
            if "result" in tool_result:
                summary = tool_result["result"]
            else:
                summary = tool_result
            return f"Tool execution finished. Output (truncated): {json.dumps(summary)[:1000]}"
        return str(tool_result)
    except Exception:
        return "Task completed."


# -------------------------
# Endpoints
# -------------------------
@app.post("/query", response_model=HostResponse)
async def process_user_query(query: HostQuery):
    """Main entrypoint. Decide whether to call a tool or chat directly with LLM."""
    # lightweight health bypass
    if query.session_id == "health-check" or query.user_query.lower() in ["status check", "host status check", "health check"]:
        return HostResponse(final_answer="Online", tool_calls_executed=[])

    if not CONNECTED_SERVERS:
        raise HTTPException(status_code=503, detail="Backend running but no tools loaded.")

    # gather all tool descriptors
    available_tools: List[MCPTool] = []
    for name, srv in CONNECTED_SERVERS.items():
        try:
            available_tools.extend(srv.list_tools())
        except Exception:
            logger.exception("Failed to list tools for server %s", name)

    # Ask LLM to pick a tool if available
    decision = await llm_select_tool(query.user_query, available_tools) if HAVE_GENAI and ACTIVE_MODEL_NAME else None

    # If LLM couldn't decide, use heuristic fallback
    if decision is None:
        decision = heuristic_select_tool(query.user_query, available_tools)

    if decision:
        server_name = decision.get("server_name")
        tool_name = decision.get("tool_name")
        args = decision.get("args", {}) or {}

        # Auto-correct missing server or tool prefixes
        if server_name is None:
            if tool_name and tool_name.startswith("filesystem."):
                server_name = "filesystem"
            elif tool_name and tool_name.startswith("browser."):
                server_name = "browser"
            elif tool_name and tool_name.startswith("github."):
                server_name = "github"

        # Normalize tool_name to have prefix if necessary
        if server_name and tool_name and not tool_name.startswith(f"{server_name}."):
            tool_name = f"{server_name}.{tool_name.split('.', 1)[-1]}"

        if server_name not in CONNECTED_SERVERS:
            return HostResponse(final_answer=f"Server '{server_name}' not found.", tool_calls_executed=[])

        server = CONNECTED_SERVERS[server_name]

        # Execute tool via mcp_core.run_tool (async-safe)
        try:
            logger.info("Executing tool %s on server %s with args: %s", tool_name, server_name, args)
            # run_tool handles validation and sync/async differences
            result = await server.run_tool(tool_name, args)
            final_text = await generate_final_answer(query.user_query, result)
            record = {"server": server_name, "tool": tool_name, "args": args, "result": result}
            return HostResponse(final_answer=final_text, tool_calls_executed=[record])
        except ToolExecutionError as te:
            logger.warning("ToolExecutionError: %s", te)
            return HostResponse(final_answer=f"Tool error: {str(te)}", tool_calls_executed=[])
        except Exception as e:
            logger.exception("Unhandled error executing tool")
            return HostResponse(final_answer=f"Tool execution failed: {e}", tool_calls_executed=[])

    # Chat mode fallback (no tool)
    try:
        if HAVE_GENAI and ACTIVE_MODEL_NAME:
            model = genai.GenerativeModel(ACTIVE_MODEL_NAME)
            resp = model.generate_content(query.user_query)
            return HostResponse(final_answer=resp.text, tool_calls_executed=[])
        # fallback simple echo/chat
        return HostResponse(final_answer=f"Chat fallback: {query.user_query}", tool_calls_executed=[])
    except Exception as e:
        logger.exception("Chat fallback failed")
        return HostResponse(final_answer=f"AI Error: {e}", tool_calls_executed=[])


@app.get("/health")
async def health():
    return {"status": "ok", "tools": list(CONNECTED_SERVERS.keys()), "model": ACTIVE_MODEL_NAME}


@app.get("/tools")
async def list_all_tools():
    """Return all registered tools and their parameter schemas for client discovery."""
    out = {}
    for name, srv in CONNECTED_SERVERS.items():
        try:
            out[name] = [t.dict() for t in srv.list_tools()]
        except Exception:
            out[name] = {"error_listing_tools": True}
    return out


# -------------------------
# CLI entrypoint
# -------------------------
if __name__ == "__main__":
    # Recommended to run under process manager in production; keep reload for dev
    uvicorn.run("mcp_host_server:app", host="127.0.0.1", port=8000, reload=True)
