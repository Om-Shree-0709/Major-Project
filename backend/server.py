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
                logger.warning(f"⚠️  {provider['name']}: {str(e)[:60]}")
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

# ==================== GLOBAL STATE ====================

SERVERS: Dict[str, IMCPExternalServer] = {}
LLM = LLMManager()

def init_llm():
    """Initialize LLM providers."""
    if HAVE_GROQ and os.getenv("GROQ_API_KEY"):
        LLM.add_provider("Groq (Llama 3.3 70B)", call_groq)
    
    if os.getenv("GITHUB_TOKEN"):
        LLM.add_provider("GitHub (GPT-4o-mini)", call_github)
    
    if not LLM.providers:
        logger.error("❌ No API keys found in .env")
        return False
    
    logger.info(f"🎯 {len(LLM.providers)} providers ready")
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
    
    SERVERS["filesystem"] = FilesystemMCPServer()
    SERVERS["browser"] = BrowserMCPServer()
    SERVERS["github"] = GitHubMCPServer()
    logger.info(f"✅ {len(SERVERS)} servers loaded")

    logger.info("=" * 50)
    logger.info("✅ READY - http://127.0.0.1:8000")
    logger.info("=" * 50)
    
    yield
    logger.info("🛑 Shutdown complete")

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
    """
    Process user query with swarm intelligence and multi-persona coordination.
    
    Supports complex workflows:
    - Research (Browser MCP Server)
    - Code Implementation (Filesystem MCP Server)
    - GitHub Operations (GitHub MCP Server)
    """
    
    if not LLM.providers:
        raise HTTPException(500, "No LLM configured")

    context = SwarmContext()
    context.add_event("User", f"New query: {q.user_query}")
    context.workflow_phase = "analysis"
    tool_calls = []
    
    # Detect if this query requires file creation
    requires_file_creation = any(keyword in q.user_query.lower() for keyword in 
                                  ['create', 'save', 'write', '.txt', '.md', '.json', '.csv', 'file'])
    
    # ==================== PHASE 1: ANALYSIS & TASK DECOMPOSITION ====================
    logger.info("📋 PHASE 1: Analyzing query and decomposing into tasks...")
    
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
        logger.info(f"📤 Analysis Response: {analysis_resp[:200]}")
        analysis = extract_json_from_response(analysis_resp)
        
        if analysis:
            task_type = analysis.get("task_type", "simple")
            subtasks = analysis.get("subtasks", [q.user_query])
            context.add_event("Manager", f"Query classified as: {task_type}")
            logger.info(f"📌 Task Type: {task_type}")
        else:
            logger.warning("⚠️  Analysis returned empty, using defaults")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        context.add_event("Manager", "Analysis failed, using simple mode")

    # ==================== PHASE 2: EXECUTE SUBTASKS ====================
    context.workflow_phase = "execution"
    
    # Process each subtask, utilizing the appropriate persona
    for idx, subtask in enumerate(subtasks):
        logger.info(f"🔄 Executing Subtask {idx+1}/{len(subtasks)}: {subtask}")
        context.add_event("Manager", f"Delegating Subtask: {subtask}")
        
        # Determine which persona to use
        current_persona = "Manager"
        if task_type == "research" or (task_type == "complex" and ("search" in subtask.lower() or "find" in subtask.lower() or "research" in subtask.lower())):
            current_persona = "Researcher"
        elif task_type in ["code", "github"] or (task_type == "complex" and ("code" in subtask.lower() or "create" in subtask.lower() or "write" in subtask.lower() or "file" in subtask.lower())):
            current_persona = "Coder"
        elif task_type == "simple":
             # For simple tasks, we can just skip to final phase if no tools are needed,
             # but we'll run one iteration with the Manager just to get it answered quickly.
             pass

        logger.info(f"🎭 Using Persona: {current_persona}")
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
            
            logger.info(f"🛠️  Executing: {tool_name} on server {srv_name}")
            
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
                    logger.info(f"✅ {tool_name} succeeded")
                except Exception as e:
                    error_msg = str(e)[:100]
                    context.add_event("Error", f"{tool_name} failed: {error_msg}")
                    logger.error(f"❌ {tool_name}: {error_msg}")
            else:
                logger.warning(f"⚠️  Unknown server: {srv_name}")

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

    return Response(
        final_answer=final_answer,
        tool_calls_executed=tool_calls
    )

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



if __name__ == "__main__":
    import datetime
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )