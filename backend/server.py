"""
Unified MCP Framework - Production Server
Free LLM-powered AI Agent System with Tool Support
"""
from __future__ import annotations
import logging
import json
import os
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv
import requests

# Groq Integration
try:
    from groq import Groq
    HAVE_GROQ = True
except ImportError:
    HAVE_GROQ = False

from swarm_manager import PERSONAS, SwarmContext, TaskStatus
from mcp_core import IMCPExternalServer, MCPTool

load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("mcp_server")

# ==================== LLM MANAGER ====================

class LLMManager:
    """Multi-provider LLM with automatic fallback."""
    
    def __init__(self):
        self.providers = []
        self.stats = {}
        
    def add_provider(self, name: str, func):
        self.providers.append({"name": name, "func": func})
        self.stats[name] = {"calls": 0, "failures": 0}
        logger.info(f"✅ {name}")
        
    def call(self, system_prompt: str, user_message: str) -> str:
        if not self.providers:
            raise Exception("No LLM providers configured!")
        
        for provider in self.providers:
            try:
                result = provider['func'](system_prompt, user_message)
                self.stats[provider['name']]["calls"] += 1
                return result
            except Exception as e:
                self.stats[provider['name']]["failures"] += 1
                logger.error(f"[LLM] {provider['name']} failed: {str(e)[:100]}, trying fallback")
                continue
        
        raise Exception("All LLM providers failed")

# ==================== LLM PROVIDERS ====================

def call_groq(system: str, user: str) -> str:
    """Groq - 30 req/min FREE"""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.3,
        max_tokens=2048
    )
    return resp.choices[0].message.content

def call_github(system: str, user: str) -> str:
    """GitHub Models - 15 req/min FREE"""
    resp = requests.post(
        "https://models.inference.ai.azure.com/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": 0.3,
            "max_tokens": 2048
        },
        timeout=30
    )
    if resp.status_code != 200:
        raise Exception(f"HTTP {resp.status_code}")
    return resp.json()['choices'][0]['message']['content']

def call_openai(system: str, user: str) -> str:
    import requests
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": float(os.getenv("AGENT_TEMPERATURE", "0.3")),
            "max_tokens": int(os.getenv("AGENT_MAX_TOKENS", "2048"))
        },
        timeout=30
    )
    if resp.status_code != 200:
        raise Exception(f"OpenAI error {resp.status_code}: {resp.text[:100]}")
    return resp.json()['choices'][0]['message']['content']

def call_anthropic(system: str, user: str) -> str:
    import requests
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "max_tokens": int(os.getenv("AGENT_MAX_TOKENS", "2048")),
            "system": system,
            "messages": [{"role": "user", "content": user}]
        },
        timeout=30
    )
    if resp.status_code != 200:
        raise Exception(f"Anthropic error {resp.status_code}: {resp.text[:100]}")
    return resp.json()['content'][0]['text']

def call_gemini(system: str, user: str) -> str:
    import requests
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    api_key = os.getenv("GEMINI_API_KEY")
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}],
            "generationConfig": {
                "temperature": float(os.getenv("AGENT_TEMPERATURE", "0.3")),
                "maxOutputTokens": int(os.getenv("AGENT_MAX_TOKENS", "2048"))
            }
        },
        timeout=30
    )
    if resp.status_code != 200:
        raise Exception(f"Gemini error {resp.status_code}: {resp.text[:100]}")
    return resp.json()['candidates'][0]['content']['parts'][0]['text']

def call_ollama(system: str, user: str) -> str:
    import requests
    model = os.getenv("OLLAMA_MODEL", "llama3")
    resp = requests.post(
        f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "stream": False
        },
        timeout=60
    )
    if resp.status_code != 200:
        raise Exception(f"Ollama error {resp.status_code}")
    return resp.json()['message']['content']

# ==================== GLOBAL STATE ====================

SERVERS: Dict[str, IMCPExternalServer] = {}
LLM = LLMManager()

def init_llm():
    LLM.providers = []
    LLM.stats = {}

    primary = os.getenv("PRIMARY_PROVIDER", "groq")
    fallback = os.getenv("FALLBACK_PROVIDER", "github")

    provider_map = {
        "groq": ("Groq (Llama 3.3 70B)", call_groq, "GROQ_API_KEY"),
        "openai": ("OpenAI", call_openai, "OPENAI_API_KEY"),
        "anthropic": ("Anthropic", call_anthropic, "ANTHROPIC_API_KEY"),
        "gemini": ("Gemini", call_gemini, "GEMINI_API_KEY"),
        "github": ("GitHub Models", call_github, "GITHUB_TOKEN"),
        "ollama": ("Ollama (Local)", call_ollama, "OLLAMA_MODEL"),
    }

    order = [primary, fallback]
    for key in provider_map:
        if key not in order:
            order.append(key)

    for key in order:
        if key not in provider_map:
            continue
        name, func, key_env = provider_map[key]
        if key == "ollama":
            LLM.add_provider(name, func)
            continue
        if os.getenv(key_env):
            LLM.add_provider(name, func)

    if not LLM.providers:
        logger.error("[STARTUP] No LLM providers configured")
        return False

    logger.info(f"[STARTUP] {len(LLM.providers)} providers ready: {[p['name'] for p in LLM.providers]}")
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    logger.info("🚀 Starting Unified MCP Framework...")
    init_llm()
    
    # Load MCP tool servers
    from filesystem_server import FilesystemMCPServer
    from browser_server import BrowserMCPServer
    from github_server import GitHubMCPServer
    from weather_server import WeatherMCPServer
    from code_executor_server import CodeExecutorMCPServer
    from system_info_server import SystemInfoMCPServer
    
    SERVERS["filesystem"] = FilesystemMCPServer()
    SERVERS["browser"] = BrowserMCPServer()
    SERVERS["github"] = GitHubMCPServer()
    SERVERS["weather"] = WeatherMCPServer()
    SERVERS["code_executor"] = CodeExecutorMCPServer()
    SERVERS["system_info"] = SystemInfoMCPServer()
    logger.info(f"[STARTUP] {len(SERVERS)} servers loaded: {list(SERVERS.keys())}")

    logger.info("=" * 50)
    logger.info("[STARTUP] READY - http://127.0.0.1:8000")
    logger.info("=" * 50)
    
    yield
    logger.info("[SHUTDOWN] Shutdown complete")

# ==================== FASTAPI APP ====================

class Query(BaseModel):
    user_query: str
    session_id: str = "default"

class Response(BaseModel):
    final_answer: str
    tool_calls_executed: List[Dict[str, Any]] = []

app = FastAPI(title="MCP Framework", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_json(text: str) -> str:
    """Remove markdown and clean JSON response from LLM."""
    if not text:
        return "{}"
    
    s = text.strip()
    
    # Remove markdown code blocks
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    
    if s.endswith("```"):
        s = s[:-3]
    
    s = s.strip()
    
    # If empty, return empty JSON object
    if not s:
        return "{}"
    
    return s

def extract_json_from_response(text: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from LLM response.
    Handles various formats and returns safe defaults.
    """
    if not text:
        return {}
    
    # Try direct parsing first
    try:
        cleaned = clean_json(text)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object in text
    text = text.strip()
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            json_str = text[start_idx:end_idx+1]
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Return safe defaults based on context
    logger.warning(f"⚠️  Could not parse JSON from: {text[:100]}")
    return {}

@app.post("/query", response_model=Response)
async def query(q: Query):
    import time
    start_time = time.time()
    
    logger.info(f"[QUERY] Incoming: '{q.user_query[:100]}'")
    
    if not LLM.providers:
        logger.error("[QUERY] Failed: No LLM configured")
        raise HTTPException(500, "No LLM configured")

    context = SwarmContext()
    context.add_event("User", f"New query: {q.user_query}")
    context.workflow_phase = "analysis"
    tool_calls = []
    
    requires_file_creation = any(keyword in q.user_query.lower() for keyword in 
                                  ['create', 'save', 'write', '.txt', '.md', '.json', '.csv', 'file'])
    
    try:
    
    # Manager Persona context
    manager_prompt = PERSONAS["Manager"]["prompt"]
    
    analysis_system = f"""{manager_prompt}

You are analyzing the user query. Respond ONLY with valid JSON (no other text).

Task: Classify the user query into a task type and identify the precise required tools, then outline the necessary subtasks.

RESPOND WITH EXACTLY THIS JSON FORMAT (and nothing else):
{{
  "task_type": "simple",
  "explanation": "brief explanation",
  "subtasks": ["task1", "task2"]
}}

Task types:
- simple: General questions/reasoning
- research: Needs web search (Browser MCP)
- code: Needs file operations (Filesystem MCP)
- github: Needs repo operations (GitHub MCP)
- complex: Needs both research and code operations"""

    analysis_user = f"""User Query: {q.user_query}

Respond with ONLY valid JSON (no markdown, no extra text)."""

    task_type = "simple"
    subtasks = [q.user_query]
    
    try:
        analysis_resp = LLM.call(analysis_system, analysis_user)
        analysis = extract_json_from_response(analysis_resp)
        
        if analysis:
            task_type = analysis.get("task_type", "simple")
            subtasks = analysis.get("subtasks", [q.user_query])
            context.add_event("Manager", f"Query classified as: {task_type}")
            logger.info(f"[QUERY] Task Type: {task_type}")
        else:
            logger.warning("[QUERY] Analysis returned empty, using defaults")
    except Exception as e:
        logger.error(f"[QUERY] Analysis failed: {e}")
        context.add_event("Manager", "Analysis failed, using simple mode")

    # ==================== PHASE 2: EXECUTE SUBTASKS ====================
    context.workflow_phase = "execution"
    
    for idx, subtask in enumerate(subtasks):
        # Determine which persona to use
        current_persona = "Manager"
        if task_type == "research" or (task_type == "complex" and ("search" in subtask.lower() or "find" in subtask.lower() or "research" in subtask.lower())):
            current_persona = "Researcher"
        elif task_type in ["code", "github"] or (task_type == "complex" and ("code" in subtask.lower() or "create" in subtask.lower() or "write" in subtask.lower() or "file" in subtask.lower())):
            current_persona = "Coder"
        elif task_type == "simple":
             pass

        logger.info(f"[QUERY] Persona Selected: {current_persona} for subtask: {subtask[:50]}")
        persona = PERSONAS[current_persona]
        
        # Build list of tools ALOWED for this persona
        allowed_servers = persona.get("tools", [])
        available_tools = []
        for srv_name, srv in SERVERS.items():
            if "all" in allowed_servers or srv_name in allowed_servers:
                try:
                    for tool in srv.list_tools():
                        available_tools.append(tool.name)
                except:
                    pass
        
        tools_list = "\n".join([f"  - {t}" for t in available_tools])
        
        # System prompt using Persona's core prompt + JSON execution instructions
        system = f"""{persona['prompt']}

You must execute the current subtask. Respond with ONLY valid JSON, no other text.

AVAILABLE TOOLS (use EXACT names):
{tools_list}

REQUIRED TOOL PARAMETERS:

Filesystem Tools:
  - filesystem.read_file: {{"path": "filename.txt"}}
  - filesystem.write_file: {{"path": "filename.txt", "content": "file content"}}
  - filesystem.append_file: {{"path": "filename.txt", "content": "text to append"}}
  - filesystem.list_dir: {{"path": "."}}
  - filesystem.make_directory: {{"path": "dirname"}}
  - filesystem.delete: {{"path": "filename_or_dir"}}
  - filesystem.file_exists: {{"path": "filename"}}
  - filesystem.get_metadata: {{"path": "filename"}}
  - filesystem.search_files: {{"path": ".", "pattern": "*.txt"}}

Browser Tools:
  - browser.search_web: {{"query": "search term"}}
  - browser.browse_website: {{"url": "https://example.com"}}

GitHub Tools:
  - github.list_repos: {{}}
  - github.get_repo: {{"repo_name": "repo-name"}}
  - github.read_file: {{"repo_name": "repo", "path": "file.py"}}
  - github.create_or_update_file: {{"repo_name": "repo", "path": "file.py", "content": "code", "message": "commit message"}}

RESPOND WITH EXACTLY ONE OF:

Option 1 - Execute a tool (include ALL required args):
{{
  "action": "tool",
  "server": "filesystem|browser|github",
  "tool": "exact.tool.name.from.list",
  "args": {{"required_param": "value", "another_param": "value"}}
}}

Option 2 - Provide answer/result for this subtask:
{{
  "action": "answer",
  "answer": "Your detailed findings/results for this subtask"
}}

CRITICAL RULES:
1. ALWAYS include "path" for filesystem operations - NEVER leave it empty or missing
2. Use EXACT tool names including the server prefix (e.g., "filesystem.write_file")
3. Include ALL required parameters in "args" 
4. Do NOT invent parameters or tool names
5. Respond with ONLY the JSON object - NO markdown, NO explanations, NO extra text"""

        context_str = context.get_full_context(max_events=15)
        
        # Build user prompt with context about file creation if needed
        file_guidance = ""
        if requires_file_creation and current_persona == "Coder":
            file_guidance = "\n\n⚠️ IMPORTANT: You must use filesystem.write_file to create the file requested."
        
        user = f"""Original query: {q.user_query}
Current Subtask to execute: {subtask}

Recent context:
{context_str}{file_guidance}

What is your next action for this subtask? Respond with ONLY valid JSON."""

        try:
            exec_resp = LLM.call(system, user)
            logger.info(f"📤 Execution Response: {exec_resp[:200]}")
            decision = extract_json_from_response(exec_resp)
            
            if not decision:
                logger.warning("⚠️  Empty decision, moving to next iteration")
                continue
            
        except Exception as e:
            logger.error(f"Execution call failed: {e}")
            continue

        # Check if final answer provided
        action = decision.get("action", "")
        
        # Extract filename if file creation was requested
        extracted_filename = None
        if requires_file_creation and action == "answer":
            # Try to extract filename from query
            import re
            filename_match = re.search(r'([a-zA-Z0-9_-]+\.(?:txt|md|json|csv))', q.user_query)
            if filename_match:
                extracted_filename = filename_match.group(1)
                logger.info(f"📝 Extracted filename from query: {extracted_filename}")
            
            # Check if write_file was already called
            write_file_called = any(
                tc.get("tool") == "filesystem.write_file" 
                for tc in tool_calls
            )
            
            # If file wasn't written and we have content, write it now
            if not write_file_called and extracted_filename and tool_calls:
                # Get the last successful tool result (likely the search results)
                last_result = tool_calls[-1].get("result", {})
                if last_result:
                    # Format content from search results
                    if isinstance(last_result, dict) and "results" in last_result:
                        content = f"# {q.user_query}\n\n"
                        for item in last_result["results"][:5]:
                            title = item.get("title", "No title")
                            url = item.get("url", "")
                            content += f"## {title}\n[{url}]({url})\n\n"
                        
                        # Auto-write the file
                        logger.info(f"🛠️  Auto-writing file {extracted_filename} with search results")
                        try:
                            result = SERVERS["filesystem"].execute_tool("filesystem.write_file", {
                                "path": extracted_filename,
                                "content": content
                            })
                            tool_calls.append({
                                "server": "filesystem",
                                "tool": "filesystem.write_file",
                                "args": {"path": extracted_filename, "content": f"{len(content)} bytes"},
                                "result": result
                            })
                            context.add_event("Filesystem", f"File written: {extracted_filename}")
                            logger.info(f"✅ Auto-created: {extracted_filename}")
                        except Exception as e:
                            logger.error(f"❌ Failed to auto-write file: {e}")
        
        if action == "answer":
            subtask_answer = decision.get("answer", "No result provided for this subtask")
            logger.info(f"✅ Subtask {idx+1} complete")
            context.add_event(current_persona, f"Subtask Result: {subtask_answer}")
            continue # Move on to the next subtask

        # Execute tool if requested
        if action == "tool":
            srv_name = decision.get("server")
            tool_name = decision.get("tool")
            args = decision.get("args", {})
            
            if not srv_name or not tool_name:
                logger.warning("⚠️  Invalid tool specification")
                context.add_event("Error", "Tool call missing server or tool name")
                continue
            
            # If tool name doesn't have the server prefix, add it
            if "." not in tool_name:
                tool_name = f"{srv_name}.{tool_name}"
            
            # Validate args for common file operations
            validation_error = ""
            if "write_file" in tool_name or "read_file" in tool_name or "append_file" in tool_name or "delete" in tool_name:
                if "path" not in args or not args.get("path"):
                    validation_error = "Missing or empty 'path' parameter. File operations REQUIRE a path (e.g., {'path': 'filename.txt', 'content': '...'})"
            
            if "write_file" in tool_name and "content" not in args:
                validation_error = "write_file requires both 'path' and 'content' parameters"
            
            if validation_error:
                logger.warning(f"⚠️  Parameter validation failed: {validation_error}")
                context.add_event("Error", validation_error)
                continue
            
            logger.info(f"[TOOL] {tool_name} | {str(args)[:100]}")
            
            if srv_name in SERVERS:
                try:
                    result = SERVERS[srv_name].execute_tool(tool_name, args)
                    context.add_event(
                        f"Tool[{tool_name}]",
                        f"Success: {str(result)[:150]}"
                    )
                    tool_calls.append({
                        "server": srv_name,
                        "tool": tool_name,
                        "result": result
                    })
                    logger.info(f"[TOOL] Result: Success for {tool_name}")
                except Exception as e:
                    error_msg = str(e)[:100]
                    context.add_event("Error", f"{tool_name} failed: {error_msg}")
                    logger.error(f"[TOOL] Result: Error for {tool_name} - {error_msg}")
            else:
                logger.warning(f"[TOOL] Unknown server: {srv_name}")

        # Give the agent a few tries to complete the subtask if it opted to use a tool
        # In a real swarm system we could nest a while loop here, but for simplicity
        # we assume one tool call per subtask iteration, or we loop max 3 times per subtask.
        # We can simulate letting the subtask continue slightly by iterating on the tool results:
        # Just append it and let the next subtask or final synthesis handle it.
        context.add_event(current_persona, f"Completed tool execution for subtask: {subtask}")

    # ==================== FINAL RESPONSE ====================
    logger.info("📋 Generating final response...")
    context.add_event("Manager", "Generating final response...")
    
    final_system_prompt = PERSONAS["Manager"]["prompt"]
    final_system = f"""{final_system_prompt}

You are synthesizing the final response for the user after all subtasks have been completed by your team. 
Provide a clear, helpful final answer based on the context and work completed.
Do NOT include JSON or any special formatting just provide the direct answer to the user."""

    final_user = f"""Original query: {q.user_query}

Work completed:
{context.get_full_context(max_events=30)}

Provide a clear final answer based on the work completed."""
    
    try:
        final_resp = LLM.call(final_system, final_user)
        final_answer = final_resp.strip()
    except Exception as e:
        final_answer = f"Task completed. {len(tool_calls)} tools executed."

    if not final_answer:
        final_answer = f"Task completed successfully. {len(tool_calls)} tools were used."

    total_time = time.time() - start_time
    logger.info(f"[QUERY] Finished in {total_time:.2f}s with {len(tool_calls)} tool calls")

    return Response(
        final_answer=final_answer,
        tool_calls_executed=tool_calls
    )

    except Exception as e:
        logger.exception(f"[QUERY] Exception during request handling. Payload: {str(q.user_query)[:100]}")
        raise HTTPException(500, str(e))

@app.get("/")
async def root():
    """Health check and status."""
    return {
        "status": "online",
        "service": "Unified MCP Framework with Swarm Intelligence",
        "version": "2.0",
        "providers": [p["name"] for p in LLM.providers],
        "servers": list(SERVERS.keys()),
        "stats": LLM.stats
    }

@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "llm": {
            "count": len(LLM.providers),
            "providers": [p["name"] for p in LLM.providers],
            "stats": LLM.stats
        },
        "servers": {
            name: {"status": "active"}
            for name in SERVERS.keys()
        }
    }

@app.get("/swarm/status")
async def swarm_status():
    """Get swarm framework status and info."""
    return {
        "framework": "Unified MCP Framework with Swarm Intelligence",
        "personas": {
            name: {
                "role": p["role"],
                "tools": p.get("tools", [])
            }
            for name, p in PERSONAS.items()
        },
        "mcp_servers": list(SERVERS.keys()),
        "llm_providers": [p["name"] for p in LLM.providers]
    }

ENV_FILE_PATH = Path(__file__).parent / ".env"

def read_env_file() -> dict:
    result = {}
    if not ENV_FILE_PATH.exists():
        return result
    for line in ENV_FILE_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            result[key.strip()] = val.strip()
    return result

def write_env_file(data: dict):
    lines = []
    for key, val in data.items():
        if val:
            lines.append(f"{key}={val}")
    ENV_FILE_PATH.write_text("\n".join(lines) + "\n")

@app.get("/settings")
async def get_settings():
    env = read_env_file()
    from filesystem_server import get_sandbox_dir
    sd = get_sandbox_dir()
    return {
        "sandbox_path": env.get("MCP_SANDBOX_PATH", str(sd) if sd else ""),
        "github_path": env.get("GITHUB_PATH", ""),
        "primary_provider": env.get("PRIMARY_PROVIDER", "groq"),
        "fallback_provider": env.get("FALLBACK_PROVIDER", "github"),
        "groq_api_key": env.get("GROQ_API_KEY", ""),
        "groq_model": env.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "openai_api_key": env.get("OPENAI_API_KEY", ""),
        "openai_model": env.get("OPENAI_MODEL", "gpt-4o-mini"),
        "anthropic_api_key": env.get("ANTHROPIC_API_KEY", ""),
        "anthropic_model": env.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022"),
        "gemini_api_key": env.get("GEMINI_API_KEY", ""),
        "gemini_model": env.get("GEMINI_MODEL", "gemini-1.5-flash"),
        "github_token": env.get("GITHUB_TOKEN", ""),
        "github_model": env.get("GITHUB_MODEL", "gpt-4o-mini"),
        "ollama_host": env.get("OLLAMA_HOST", "http://localhost:11434"),
        "ollama_model": env.get("OLLAMA_MODEL", "llama3"),
        "browser_enabled": env.get("BROWSER_ENABLED", "true") == "true",
        "filesystem_enabled": env.get("FILESYSTEM_ENABLED", "true") == "true",
        "github_enabled": env.get("GITHUB_ENABLED", "true") == "true",
        "weather_enabled": env.get("WEATHER_ENABLED", "true") == "true",
        "code_runner_enabled": env.get("CODE_RUNNER_ENABLED", "true") == "true",
        "system_info_enabled": env.get("SYSTEM_INFO_ENABLED", "true") == "true",
        "agent_temperature": float(env.get("AGENT_TEMPERATURE", "0.3")),
        "agent_max_tokens": int(env.get("AGENT_MAX_TOKENS", "2048")),
        "agent_max_iterations": int(env.get("AGENT_MAX_ITERATIONS", "5")),
    }

class SettingsPayload(BaseModel):
    primary_provider: str = "groq"
    fallback_provider: str = "github"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-20241022"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    github_token: str = ""
    github_model: str = "gpt-4o-mini"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    browser_enabled: bool = True
    filesystem_enabled: bool = True
    github_enabled: bool = True
    weather_enabled: bool = True
    code_runner_enabled: bool = True
    system_info_enabled: bool = True
    agent_temperature: float = 0.3
    agent_max_tokens: int = 2048
    agent_max_iterations: int = 5
    sandbox_path: str = ""
    github_path: str = ""

@app.post("/settings")
async def save_settings(payload: SettingsPayload):
    env = read_env_file()

    env["PRIMARY_PROVIDER"] = payload.primary_provider
    env["FALLBACK_PROVIDER"] = payload.fallback_provider
    if payload.groq_api_key:
        env["GROQ_API_KEY"] = payload.groq_api_key
    env["GROQ_MODEL"] = payload.groq_model
    if payload.openai_api_key:
        env["OPENAI_API_KEY"] = payload.openai_api_key
    env["OPENAI_MODEL"] = payload.openai_model
    if payload.anthropic_api_key:
        env["ANTHROPIC_API_KEY"] = payload.anthropic_api_key
    env["ANTHROPIC_MODEL"] = payload.anthropic_model
    if payload.gemini_api_key:
        env["GEMINI_API_KEY"] = payload.gemini_api_key
    env["GEMINI_MODEL"] = payload.gemini_model
    if payload.github_token:
        if env.get("GITHUB_TOKEN") != payload.github_token:
            logger.info("[SETTINGS] API Key changed for: GITHUB")
        env["GITHUB_TOKEN"] = payload.github_token
        if "GITHUB_PAT" not in env or env["GITHUB_PAT"] == env.get("GITHUB_TOKEN"):
            env["GITHUB_PAT"] = payload.github_token
    env["GITHUB_MODEL"] = payload.github_model
    env["OLLAMA_HOST"] = payload.ollama_host
    env["OLLAMA_MODEL"] = payload.ollama_model
    env["BROWSER_ENABLED"] = str(payload.browser_enabled).lower()
    env["FILESYSTEM_ENABLED"] = str(payload.filesystem_enabled).lower()
    env["GITHUB_ENABLED"] = str(payload.github_enabled).lower()
    env["WEATHER_ENABLED"] = str(payload.weather_enabled).lower()
    env["CODE_RUNNER_ENABLED"] = str(payload.code_runner_enabled).lower()
    env["SYSTEM_INFO_ENABLED"] = str(payload.system_info_enabled).lower()
    env["AGENT_TEMPERATURE"] = str(payload.agent_temperature)
    env["AGENT_MAX_TOKENS"] = str(payload.agent_max_tokens)
    env["AGENT_MAX_ITERATIONS"] = str(payload.agent_max_iterations)

    if payload.sandbox_path:
        env["MCP_SANDBOX_PATH"] = payload.sandbox_path
    if payload.github_path:
        env["GITHUB_PATH"] = payload.github_path

    if payload.groq_api_key and env.get("GROQ_API_KEY") != payload.groq_api_key:
        logger.info("[SETTINGS] API Key changed for: GROQ")
    if payload.openai_api_key and env.get("OPENAI_API_KEY") != payload.openai_api_key:
        logger.info("[SETTINGS] API Key changed for: OPENAI")
    if payload.anthropic_api_key and env.get("ANTHROPIC_API_KEY") != payload.anthropic_api_key:
        logger.info("[SETTINGS] API Key changed for: ANTHROPIC")
    if payload.gemini_api_key and env.get("GEMINI_API_KEY") != payload.gemini_api_key:
        logger.info("[SETTINGS] API Key changed for: GEMINI")

    logger.info(f"[SETTINGS] Primary provider changed: {env.get('PRIMARY_PROVIDER', 'unknown')} -> {payload.primary_provider}")

    write_env_file(env)

    for key, val in env.items():
        os.environ[key] = val

    load_dotenv(override=True)
    init_llm()

    logger.info("[SETTINGS] Reloading MCP servers based on new settings...")
    
    if env.get("BROWSER_ENABLED", "true") == "true":
        if "browser" not in SERVERS:
            from browser_server import BrowserMCPServer
            SERVERS["browser"] = BrowserMCPServer()
            logger.info("[SETTINGS] MCP Server enabled: browser")
    else:
        if "browser" in SERVERS:
            del SERVERS["browser"]
            logger.info("[SETTINGS] MCP Server disabled: browser")

    if env.get("FILESYSTEM_ENABLED", "true") == "true":
        if "filesystem" not in SERVERS:
            from filesystem_server import FilesystemMCPServer
            SERVERS["filesystem"] = FilesystemMCPServer()
            logger.info("[SETTINGS] MCP Server enabled: filesystem")
    else:
        if "filesystem" in SERVERS:
            del SERVERS["filesystem"]
            logger.info("[SETTINGS] MCP Server disabled: filesystem")

    if env.get("GITHUB_ENABLED", "true") == "true":
        if "github" not in SERVERS:
            from github_server import GitHubMCPServer
            SERVERS["github"] = GitHubMCPServer()
            logger.info("[SETTINGS] MCP Server enabled: github")
    else:
        if "github" in SERVERS:
            del SERVERS["github"]
            logger.info("[SETTINGS] MCP Server disabled: github")

    if env.get("WEATHER_ENABLED", "true") == "true":
        if "weather" not in SERVERS:
            from weather_server import WeatherMCPServer
            SERVERS["weather"] = WeatherMCPServer()
            logger.info("[SETTINGS] MCP Server enabled: weather")
    else:
        if "weather" in SERVERS:
            del SERVERS["weather"]
            logger.info("[SETTINGS] MCP Server disabled: weather")

    if env.get("CODE_RUNNER_ENABLED", "true") == "true":
        if "code_executor" not in SERVERS:
            from code_executor_server import CodeExecutorMCPServer
            SERVERS["code_executor"] = CodeExecutorMCPServer()
            logger.info("[SETTINGS] MCP Server enabled: code_executor")
    else:
        if "code_executor" in SERVERS:
            del SERVERS["code_executor"]
            logger.info("[SETTINGS] MCP Server disabled: code_executor")

    if env.get("SYSTEM_INFO_ENABLED", "true") == "true":
        if "system_info" not in SERVERS:
            from system_info_server import SystemInfoMCPServer
            SERVERS["system_info"] = SystemInfoMCPServer()
            logger.info("[SETTINGS] MCP Server enabled: system_info")
    else:
        if "system_info" in SERVERS:
            del SERVERS["system_info"]
            logger.info("[SETTINGS] MCP Server disabled: system_info")

    return {
        "status": "saved",
        "active_providers": [p["name"] for p in LLM.providers],
        "active_servers": list(SERVERS.keys())
    }

@app.post("/settings/test")
async def test_provider(payload: dict):
    provider = payload.get("provider")
    api_key = payload.get("api_key")
    model = payload.get("model", "")

    if not provider or not api_key:
        raise HTTPException(400, "provider and api_key required")

    try:
        if provider == "groq":
            from groq import Groq
            client = Groq(api_key=api_key)
            client.chat.completions.create(
                model=model or "llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )

        elif provider == "openai":
            import requests
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"},
                json={"model": model or "gpt-4o-mini",
                      "messages": [{"role": "user", "content": "hi"}],
                      "max_tokens": 5},
                timeout=10
            )
            if r.status_code != 200:
                raise Exception(r.text[:100])

        elif provider == "anthropic":
            import requests
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key,
                         "anthropic-version": "2023-06-01",
                         "Content-Type": "application/json"},
                json={"model": model or "claude-3-5-haiku-20241022",
                      "max_tokens": 5,
                      "messages": [{"role": "user", "content": "hi"}]},
                timeout=10
            )
            if r.status_code != 200:
                raise Exception(r.text[:100])

        elif provider == "gemini":
            import requests
            m = model or "gemini-1.5-flash"
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}",
                json={"contents": [{"parts": [{"text": "hi"}]}]},
                timeout=10
            )
            if r.status_code != 200:
                raise Exception(r.text[:100])

        elif provider == "github":
            import requests
            r = requests.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"},
                json={"model": model or "gpt-4o-mini",
                      "messages": [{"role": "user", "content": "hi"}],
                      "max_tokens": 5},
                timeout=10
            )
            if r.status_code != 200:
                raise Exception(r.text[:100])

        elif provider == "ollama":
            import requests
            host = payload.get("ollama_host", "http://localhost:11434")
            r = requests.get(f"{host}/api/tags", timeout=5)
            if r.status_code != 200:
                raise Exception("Ollama not reachable")

        return {"status": "ok", "provider": provider}

    except Exception as e:
        raise HTTPException(400, str(e))

@app.delete("/sandbox")
async def clear_sandbox():
    from filesystem_server import get_sandbox_dir
    SANDBOX_DIR = get_sandbox_dir()
    if not SANDBOX_DIR:
        return {"status": "error", "message": "Sandbox path not configured"}
    import shutil
    cleared = []
    if SANDBOX_DIR.exists():
        for item in SANDBOX_DIR.iterdir():
            if item.name != "README.md":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                cleared.append(item.name)
    return {"status": "cleared", "files_removed": cleared}

if __name__ == "__main__":
    import datetime
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )