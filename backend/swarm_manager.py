# backend/swarm_manager.py
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("swarm_manager")

PERSONAS = {
    "Manager": {
        "role": "Orchestrator",
        "prompt": "You are the Swarm Manager. Your goal is to break down the user query into sub-tasks. You delegate research to the Researcher and code tasks to the Coder. Coordinate their findings into a final answer."
    },
    "Researcher": {
        "role": "Search & Analysis",
        "prompt": "You are the Researcher. Use the Browser tool to find information. Provide concise reports of your findings to the Manager. Do not make up facts."
    },
    "Coder": {
        "role": "Software Engineer",
        "prompt": "You are the Coder. Use Filesystem and GitHub tools to read, write, or inspect code. Ensure all file operations stay within the sandbox."
    }
}

class SwarmContext:
    """Shared 'Blackboard' memory for all agents in the swarm."""
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.shared_notes: Dict[str, Any] = {}

    def add_event(self, role: str, content: str, tool_metadata: Any = None):
        self.history.append({
            "role": role,
            "content": content,
            "metadata": tool_metadata
        })

    def get_full_context(self) -> str:
        return "\n".join([f"[{e['role']}]: {e['content']}" for e in self.history])