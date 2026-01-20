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

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("🚀 UNIFIED MCP FRAMEWORK")
    logger.info("=" * 50)
    
    if not init_llm():
        logger.warning("⚠️  Starting without LLM!")
    
    load_servers()
    
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
    """Remove markdown from JSON."""
    s = text.strip()
    if s.startswith("```json"): s = s[7:]
    if s.startswith("```"): s = s[3:]
    if s.endswith("```"): s = s[:-3]
    return s.strip()

@app.post("/query", response_model=Response)
async def query(q: Query):
    """Process user query with swarm intelligence."""
    
    if not LLM.providers:
        raise HTTPException(500, "No LLM configured")

    context = SwarmContext()
    context.add_event("User", q.user_query)
    tool_calls = []
    
    # Reduced iterations to save API calls
    for i in range(3):
        logger.info(f"🔄 Iteration {i+1}/3")
        
        # Get available tools
        tools = []
        for srv in SERVERS.values():
            try:
                tools.extend(srv.list_tools())
            except:
                continue

        tools_desc = "\n".join([
            f"- {t.name}: {t.description}"
            for t in tools
        ])

        system = f"""You are an AI orchestrator managing tools.

CONTEXT:
{context.get_full_context()}

ROLE: {PERSONAS['Manager']['prompt']}

TOOLS:
{tools_desc}

Return ONLY valid JSON:
{{"tool_call": {{"server_name": "...", "tool_name": "...", "args": {{...}}}}, "final_answer": null}}
OR
{{"tool_call": null, "final_answer": "..."}}"""

        user = f"Query: {q.user_query}\nIteration: {i+1}/3"

        try:
            resp_text = LLM.call(system, user)
            decision = json.loads(clean_json(resp_text))
            
        except json.JSONDecodeError:
            return Response(
                final_answer=f"Error: Invalid AI response",
                tool_calls_executed=tool_calls
            )
        except Exception as e:
            return Response(
                final_answer=f"Error: {str(e)[:100]}",
                tool_calls_executed=tool_calls
            )

        # Check for final answer
        if decision.get("final_answer"):
            logger.info("✅ Answer complete")
            return Response(
                final_answer=decision["final_answer"],
                tool_calls_executed=tool_calls
            )

        # Execute tool
        call = decision.get("tool_call")
        if call:
            srv_name = call.get("server_name")
            tool_name = call.get("tool_name")
            args = call.get("args", {})
            
            if srv_name in SERVERS:
                try:
                    result = SERVERS[srv_name].execute_tool(tool_name, args)
                    context.add_event(f"Tool:{tool_name}", json.dumps(result))
                    tool_calls.append({
                        "server": srv_name,
                        "tool": tool_name,
                        "result": result
                    })
                    logger.info(f"✅ {tool_name}")
                except Exception as e:
                    context.add_event("Error", str(e))
                    logger.error(f"❌ {tool_name}: {e}")
        else:
            break

    return Response(
        final_answer="Task completed",
        tool_calls_executed=tool_calls
    )

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "online",
        "providers": [p["name"] for p in LLM.providers],
        "stats": LLM.stats,
        "servers": list(SERVERS.keys())
    }

@app.get("/health")
async def health():
    """Detailed health."""
    return {
        "status": "healthy",
        "llm": {
            "count": len(LLM.providers),
            "providers": [p["name"] for p in LLM.providers],
            "stats": LLM.stats
        },
        "servers": list(SERVERS.keys())
    }

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
