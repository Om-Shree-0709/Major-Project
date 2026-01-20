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

from swarm_manager import PERSONAS, SwarmContext
from multi_agent_swarm import MultiAgentSwarm, ExecutionStrategy
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

def load_servers():
    """Load MCP tool servers."""
    from filesystem_server import FilesystemMCPServer
    from browser_server import BrowserMCPServer
    from github_server import GitHubMCPServer
    
    SERVERS["filesystem"] = FilesystemMCPServer()
    SERVERS["browser"] = BrowserMCPServer()
    SERVERS["github"] = GitHubMCPServer()
    logger.info(f"✅ {len(SERVERS)} servers loaded")


# Global swarm manager instance (created at startup)
swarm_manager: MultiAgentSwarm = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("🚀 UNIFIED MCP FRAMEWORK")
    logger.info("=" * 50)
    
    if not init_llm():
        logger.warning("⚠️  Starting without LLM!")
    
    load_servers()
    # instantiate global swarm manager after servers are available
    global swarm_manager
    swarm_manager = MultiAgentSwarm()
    
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
    
    # Get available tools for context
    tools = []
    for srv in SERVERS.values():
        try:
            tools.extend(srv.list_tools())
        except:
            continue

    tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in tools])
    
    analysis_system = """You are a task analyzer. Respond ONLY with valid JSON (no other text).

Task: Classify the user query into a task type and identify required tools.

RESPOND WITH EXACTLY THIS JSON FORMAT (and nothing else):
{
  "task_type": "simple",
  "explanation": "brief explanation",
  "subtasks": ["task1", "task2"]
}

Task types:
- simple: General questions/reasoning
- research: Needs web search (Browser MCP)
- code: Needs file operations (Filesystem MCP)
- github: Needs repo operations (GitHub MCP)
- complex: Multiple servers needed"""

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
    max_iterations = 5 if task_type in ["complex", "research_and_code"] else 3
    
    for iteration in range(max_iterations):
        logger.info(f"🔄 Iteration {iteration+1}/{max_iterations}")
        
        # Build list of ALL available tools
        all_tools = []
        for srv in SERVERS.values():
            try:
                for tool in srv.list_tools():
                    all_tools.append(tool.name)
            except:
                pass
        
        tools_list = "\n".join([f"  - {t}" for t in all_tools])
        
        # Enhanced system prompt with tool parameter examples
        system = f"""You are a tool executor. You MUST respond with ONLY valid JSON, no other text.

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
  - github.list_repos: {{"}}
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

Option 2 - Provide final answer:
{{
  "action": "answer",
  "answer": "Your final answer text here"
}}

CRITICAL RULES:
1. ALWAYS include "path" for filesystem operations - NEVER leave it empty or missing
2. Use EXACT tool names including the server prefix (e.g., "filesystem.write_file")
3. Include ALL required parameters in "args" 
4. Do NOT invent parameters or tool names
5. Respond with ONLY the JSON object - NO markdown, NO explanations, NO extra text"""

        context_str = context.get_full_context(max_events=15)
        
        user = f"""Current query: {q.user_query}

Recent context:
{context_str}

What is your next action? Respond with ONLY valid JSON.
Use EXACT tool names from the list above."""

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
        
        if action == "answer":
            final_answer = decision.get("answer", "No answer provided")
            logger.info("✅ Answer ready")
            context.add_event("Manager", f"Final Answer: {final_answer}")
            return Response(
                final_answer=final_answer,
                tool_calls_executed=tool_calls
            )

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

        # Check if all tasks are done
        if context.is_all_tasks_completed():
            logger.info("✅ All tasks completed")
            break

    # ==================== FINAL RESPONSE ====================
    logger.info("📋 Generating final response...")
    context.add_event("Manager", "Generating final response...")
    
    final_system = """You are a response synthesizer. Provide a clear, helpful final answer.
Do NOT include JSON or any special formatting. Just provide the answer."""

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

# Multi-Agent Comparison Endpoints
@app.post("/multi-agent/compare")
async def compare_execution_strategies(request: dict):
    """Compare LINEAR vs HIERARCHICAL execution strategies for a task."""
    try:
        query = request.get("query", "")
        if not query:
            return {"error": "Query is required"}, 400

        # Build a list of available tool names from loaded servers
        all_tools = []
        for srv in SERVERS.values():
            try:
                for t in srv.list_tools():
                    all_tools.append(t.name)
            except Exception:
                continue

        # Run comparison using two fresh swarm instances to avoid cross-contamination
        linear_swarm = MultiAgentSwarm()
        hierarchical_swarm = MultiAgentSwarm()

        # Spawn agents for each swarm
        linear_agents = linear_swarm.analyze_task_and_spawn_agents(query, all_tools)
        hierarchical_agents = hierarchical_swarm.analyze_task_and_spawn_agents(query, all_tools)

        # Decompose and assign tasks
        linear_tasks = linear_swarm.decompose_task(query)
        hierarchical_tasks = hierarchical_swarm.decompose_task(query)

        linear_swarm.assign_tasks_to_agents(linear_tasks, linear_agents)
        hierarchical_swarm.assign_tasks_to_agents(hierarchical_tasks, hierarchical_agents)

        # Execute both strategies and collect metrics and data flows
        linear_metrics = await linear_swarm.execute_tasks(ExecutionStrategy.LINEAR)
        hierarchical_metrics = await hierarchical_swarm.execute_tasks(ExecutionStrategy.HIERARCHICAL)

        return {
            "success": True,
            "query": query,
            "comparison": {
                "linear": {
                    "metrics": linear_metrics.__dict__,
                    "data_flow": linear_swarm.get_data_flow_visualization(),
                    "agents": [a.to_dict() for a in linear_agents],
                    "tasks": [{
                        "id": t.id,
                        "description": t.description,
                        "status": t.status.value,
                        "dependencies": [d.task_id for d in t.dependencies]
                    } for t in linear_tasks],
                    "execution_plan": linear_swarm.get_execution_plan(ExecutionStrategy.LINEAR)
                },
                "hierarchical": {
                    "metrics": hierarchical_metrics.__dict__,
                    "data_flow": hierarchical_swarm.get_data_flow_visualization(),
                    "agents": [a.to_dict() for a in hierarchical_agents],
                    "tasks": [{
                        "id": t.id,
                        "description": t.description,
                        "status": t.status.value,
                        "dependencies": [d.task_id for d in t.dependencies]
                    } for t in hierarchical_tasks],
                    "execution_plan": hierarchical_swarm.get_execution_plan(ExecutionStrategy.HIERARCHICAL)
                }
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }, 500


@app.post("/multi-agent/fetch-news")
async def fetch_and_save_news(request: dict):
    """Fetch Bollywood/pop culture news and save to file with execution flow visualization"""
    try:
        from news_fetcher import fetch_bollywood_news, save_news_to_file, format_news_as_markdown
        import time
        import os

        execution_logs = []
        start_time = time.time()

        # Step 1: Spawn agents
        log_entry = f"[{datetime.now().isoformat()}] [ORCHESTRATOR] Analyzing task: fetch and format news"
        execution_logs.append(log_entry)
        logger.info(log_entry)

        all_tools = []
        for srv in SERVERS.values():
            try:
                for t in srv.list_tools():
                    all_tools.append(t.name)
            except Exception:
                continue

        # Create a fresh swarm for this task
        swarm = MultiAgentSwarm()
        agents = swarm.analyze_task_and_spawn_agents("fetch latest news and create file", all_tools)

        log_entry = f"[{datetime.now().isoformat()}] [SPAWN] {len(agents)} agents spawned"
        execution_logs.append(log_entry)
        logger.info(log_entry)
        for agent in agents:
            log_entry = f"[{datetime.now().isoformat()}] [AGENT] {agent.config.name} ({agent.config.role.value}) ready with {len(agent.config.available_tools)} tools"
            execution_logs.append(log_entry)
            logger.info(log_entry)

        # Step 2: Decompose tasks
        tasks = swarm.decompose_task("fetch news and save to file")
        log_entry = f"[{datetime.now().isoformat()}] [TASKS] {len(tasks)} subtasks decomposed"
        execution_logs.append(log_entry)
        logger.info(log_entry)

        # Step 3: Assign tasks to agents
        swarm.assign_tasks_to_agents(tasks, agents)
        log_entry = f"[{datetime.now().isoformat()}] [ASSIGN] Tasks assigned to agents"
        execution_logs.append(log_entry)
        logger.info(log_entry)

        # Step 4: Fetch news data
        log_entry = f"[{datetime.now().isoformat()}] [BROWSER] Fetching news from sources..."
        execution_logs.append(log_entry)
        logger.info(log_entry)

        news_items = fetch_bollywood_news()
        log_entry = f"[{datetime.now().isoformat()}] [BROWSER] ✅ Fetched {len(news_items)} news items"
        execution_logs.append(log_entry)
        logger.info(log_entry)

        swarm.record_data_flow(
            source_agent=agents[0].id if agents else "unknown",
            target_agent="mcp_server",
            data={"count": len(news_items)},
            tool_used="browser.search_web"
        )

        # Step 5: Format news
        log_entry = f"[{datetime.now().isoformat()}] [FORMATTER] Formatting {len(news_items)} news items as markdown..."
        execution_logs.append(log_entry)
        logger.info(log_entry)

        formatted_content = format_news_as_markdown(news_items, "Latest Bollywood & Pop Culture News")
        log_entry = f"[{datetime.now().isoformat()}] [FORMATTER] ✅ Formatted {len(formatted_content)} bytes of content"
        execution_logs.append(log_entry)
        logger.info(log_entry)

        # Step 6: Save to file in mcp_sandbox
        log_entry = f"[{datetime.now().isoformat()}] [FILESYSTEM] Writing file to mcp_sandbox..."
        execution_logs.append(log_entry)
        logger.info(log_entry)

        success, file_path = save_news_to_file(news_items, "news.md", "Latest Bollywood & Pop Culture News")

        if success:
            log_entry = f"[{datetime.now().isoformat()}] [FILESYSTEM] ✅ File created: {file_path}"
            execution_logs.append(log_entry)
            logger.info(log_entry)

            swarm.record_data_flow(
                source_agent=agents[0].id if agents else "unknown",
                target_agent="mcp_server",
                data={"file": file_path},
                tool_used="filesystem.write_file"
            )
        else:
            log_entry = f"[{datetime.now().isoformat()}] [FILESYSTEM] ❌ Failed: {file_path}"
            execution_logs.append(log_entry)
            logger.error(log_entry)

        # Step 7: Verify
        log_entry = f"[{datetime.now().isoformat()}] [VERIFY] Verifying file..."
        execution_logs.append(log_entry)
        logger.info(log_entry)

        if success and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            log_entry = f"[{datetime.now().isoformat()}] [VERIFY] ✅ File verified: {file_size} bytes"
            execution_logs.append(log_entry)
            logger.info(log_entry)
        else:
            log_entry = f"[{datetime.now().isoformat()}] [VERIFY] ⚠️ File verification failed"
            execution_logs.append(log_entry)
            logger.warning(log_entry)

        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000

        log_entry = f"[{datetime.now().isoformat()}] [COMPLETE] Task finished in {total_time_ms:.2f}ms"
        execution_logs.append(log_entry)
        logger.info(log_entry)

        return {
            "success": success,
            "file_path": file_path if success else None,
            "news_count": len(news_items),
            "formatted_content": formatted_content,
            "execution_logs": execution_logs,
            "total_time_ms": total_time_ms,
            "agents": [a.to_dict() for a in agents],
            "data_flow": swarm.get_data_flow_visualization()
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error in fetch-news: {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": error_msg,
            "execution_logs": execution_logs
        }, 500


@app.post("/multi-agent/spawn-and-execute")
async def spawn_and_execute(request: dict):
    """Spawn dynamic agents for a task and execute it."""
    try:
        query = request.get("query", "")
        execution_mode = request.get("execution_mode", "hierarchical")  # linear, hierarchical, parallel

        if not query:
            return {"error": "Query is required"}, 400

        # Build list of available tool names
        all_tools = []
        for srv in SERVERS.values():
            try:
                for t in srv.list_tools():
                    all_tools.append(t.name)
            except Exception:
                continue

        # Spawn agents based on task analysis
        agents = swarm_manager.analyze_task_and_spawn_agents(query, all_tools)

        # Optionally use LLM to refine the orchestrator agent's persona (name/description/tools)
        try:
            for agent in agents:
                # Only refine orchestrator agents
                if agent.config.role.name == 'ORCHESTRATOR':
                    system = "You are an agent persona generator. Respond with JSON only."
                    user = (
                        "Create a concise agent persona for handling this user query: '{}' . "
                        "Respond with JSON in the form {\"name\": string, \"description\": string, \"primary_tools\": [string]} "
                    ).format(query)
                    if LLM.providers:
                        resp = LLM.call(system, user)
                        try:
                            persona = extract_json_from_response(resp)
                            if persona:
                                # Update agent metadata if provided
                                if persona.get("name"):
                                    agent.config.name = persona.get("name")
                                if persona.get("description"):
                                    agent.config.description = persona.get("description")
                                if persona.get("primary_tools") and isinstance(persona.get("primary_tools"), list):
                                    # Keep only tools that exist in all_tools
                                    chosen = [t for t in all_tools if any(p in t for p in persona.get("primary_tools"))]
                                    if chosen:
                                        agent.config.available_tools = chosen
                        except Exception:
                            pass
        except Exception:
            pass

        # Decompose task into steps
        tasks = swarm_manager.decompose_task(query)

        # Assign tasks to agents
        swarm_manager.assign_tasks_to_agents(tasks, agents)

        # Execute with specified strategy
        # Map string to ExecutionStrategy enum if needed
        if isinstance(execution_mode, str):
            try:
                exec_mode = ExecutionStrategy(execution_mode.lower())
            except Exception:
                exec_mode = ExecutionStrategy.HIERARCHICAL
        else:
            exec_mode = execution_mode

        metrics = await swarm_manager.execute_tasks(exec_mode)

        # Get data flow visualization
        data_flow = swarm_manager.get_data_flow_visualization()

        return {
            "success": True,
            "query": query,
            "execution_mode": exec_mode.value,
            "agents_spawned": len(agents),
            "tasks_created": len(tasks),
            "metrics": metrics.__dict__ if hasattr(metrics, '__dict__') else metrics,
            "data_flow": data_flow
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }, 500

@app.get("/multi-agent/data-flow")
async def get_data_flow():
    """Get current data flow visualization between agents and servers."""
    try:
        data_flow = swarm_manager.get_data_flow_visualization()
        return {
            "success": True,
            "data_flow": data_flow
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }, 500

if __name__ == "__main__":
    import datetime
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )