# backend/swarm_manager.py
"""
Unified Swarm Manager for MCP Framework
Handles multi-persona coordination for complex tasks involving:
- Research (Browser MCP Server)
- Code Implementation (Filesystem MCP Server)
- GitHub Operations (GitHub MCP Server)
"""
import json
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger("swarm_manager")

# ==================== PERSONAS ====================

PERSONAS = {
    "Manager": {
        "role": "Orchestrator & Coordinator",
        "prompt": """You are the Swarm Manager - the orchestrator of a multi-agent team.

YOUR RESPONSIBILITIES:
1. Analyze the user query and break it down into sequential subtasks
2. Delegate research tasks to the Researcher persona
3. Delegate code tasks to the Coder persona
4. Coordinate findings and ensure consistency
5. Provide a final synthesized answer to the user

TASK DECOMPOSITION STRATEGY:
- For "Research & Implement & Push" tasks:
  1. First: Delegate to Researcher to gather bug/requirement info
  2. Second: Delegate to Coder to implement solution in sandbox
  3. Third: Delegate to Coder to push code to GitHub
  
COMMUNICATION:
- Be explicit about what you're delegating and why
- Wait for team members to report back before proceeding
- Ensure all subtasks are completed before finalizing
- If a task fails, suggest alternatives or workarounds""",
        "tools": ["all"]  # Can coordinate all tools
    },
    "Researcher": {
        "role": "Search & Analysis Specialist",
        "prompt": """You are the Researcher - your expertise is finding and analyzing information.

YOUR TOOLS: Browser MCP Server
- browser.search_web: Search the internet for information
- browser.browse_website: Extract detailed content from specific URLs

YOUR RESPONSIBILITIES:
1. Search for information requested by the Manager
2. Analyze findings thoroughly and provide context
3. Report back with:
   - Key facts and findings
   - Source URLs/references
   - Potential solutions or implications
   - Any limitations or caveats
4. Do NOT invent or hallucinate facts
5. Always cite your sources

BEST PRACTICES:
- Use specific, targeted search queries
- Visit multiple sources if needed
- Summarize findings clearly for the team
- Flag uncertainty - don't claim confidence you don't have""",
        "tools": ["browser"]
    },
    "Coder": {
        "role": "Software Engineer & DevOps",
        "prompt": """You are the Coder - your expertise is writing, debugging, and deploying code.

YOUR TOOLS:
- Filesystem MCP Server: Read/write/manage code files in sandbox
- GitHub MCP Server: Create repos, push code, manage branches, create PRs

YOUR RESPONSIBILITIES:
1. Implement code changes based on requirements/bugs found by Researcher
2. Ensure code quality and proper structure
3. Test implementations within the sandbox
4. Push code to GitHub with proper commits and documentation
5. Create branches, pull requests when needed

WORKFLOW FOR CODE IMPLEMENTATION:
1. Read existing files to understand structure
2. Implement fixes/features
3. Write/update documentation
4. Push to GitHub with descriptive commit messages
5. Create PR if it's a significant change

WORKFLOW FOR PUSHING TO GITHUB:
1. Create a new repository if needed
2. Initialize git structure
3. Write README with setup instructions
4. Make initial commit
5. Push to GitHub (you handle auth)

SECURITY:
- All file operations stay within the sandbox
- Validate file paths before operations
- Never overwrite critical files without backup""",
        "tools": ["filesystem", "github"]
    }
}

# ==================== ENUMS & DATA CLASSES ====================

class TaskStatus(Enum):
    """Status of a task in the swarm."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DELEGATED = "delegated"

@dataclass
class Task:
    """Represents a subtask in the swarm workflow."""
    id: str
    description: str
    assigned_to: str  # persona name
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class PersonaMessage:
    """Message from a persona to the swarm."""
    sender: str
    message: str
    tool_calls: List[Dict[str, Any]] = None
    task_id: Optional[str] = None
    
    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []

# ==================== SWARM CONTEXT ====================

class SwarmContext:
    """
    Shared 'Blackboard' memory for all agents in the swarm.
    Tracks: history, tasks, persona states, shared knowledge.
    """
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.tasks: Dict[str, Task] = {}
        self.shared_notes: Dict[str, Any] = {}
        self.persona_states: Dict[str, Dict[str, Any]] = {
            persona: {"status": "ready", "current_task": None}
            for persona in PERSONAS.keys()
        }
        self.workflow_phase: str = "initialization"
        self.task_counter = 0
    
    def add_event(self, role: str, content: str, tool_metadata: Any = None, tool_calls: List = None):
        """Log an event from a persona or system."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "metadata": tool_metadata,
            "tool_calls": tool_calls or []
        }
        self.history.append(event)
        logger.info(f"[{role}] {content[:80]}")
    
    def create_task(self, description: str, assigned_to: str) -> str:
        """Create a new task and assign to a persona."""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        task = Task(
            id=task_id,
            description=description,
            assigned_to=assigned_to
        )
        self.tasks[task_id] = task
        self.persona_states[assigned_to]["current_task"] = task_id
        self.add_event("System", f"Created task '{task_id}' for {assigned_to}: {description}")
        return task_id
    
    def update_task(self, task_id: str, status: TaskStatus, result: str = None, error: str = None):
        """Update task status and result."""
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found")
            return
        
        task = self.tasks[task_id]
        task.status = status
        if result:
            task.result = result
        if error:
            task.error = error
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now().isoformat()
        
        persona = task.assigned_to
        if status == TaskStatus.COMPLETED:
            self.persona_states[persona]["current_task"] = None
        
        self.add_event("System", f"Task '{task_id}' status: {status.value}")
    
    def get_task_summary(self) -> str:
        """Get summary of all tasks and their status."""
        summary = []
        for task_id, task in self.tasks.items():
            summary.append(
                f"- {task_id} ({task.assigned_to}): {task.status.value} - {task.description[:60]}"
            )
        return "\n".join(summary) if summary else "No tasks yet"
    
    def get_full_context(self, max_events: int = 50) -> str:
        """Get recent context from the swarm."""
        recent = self.history[-max_events:]
        context = []
        for e in recent:
            timestamp = e.get("timestamp", "")[:19]  # YYYY-MM-DD HH:MM:SS
            context.append(f"[{timestamp}] [{e['role']}]: {e['content']}")
        return "\n".join(context)
    
    def get_persona_context(self, persona_name: str) -> str:
        """Get context specific to a persona (their task + recent history)."""
        current_task_id = self.persona_states[persona_name]["current_task"]
        task_desc = ""
        if current_task_id and current_task_id in self.tasks:
            task = self.tasks[current_task_id]
            task_desc = f"CURRENT TASK: {task.description}\n"
        
        return task_desc + self.get_full_context(max_events=20)
    
    def get_state_dump(self) -> Dict[str, Any]:
        """Get full state as JSON-serializable dict."""
        return {
            "workflow_phase": self.workflow_phase,
            "tasks": {
                task_id: {
                    "description": task.description,
                    "assigned_to": task.assigned_to,
                    "status": task.status.value,
                    "result": task.result,
                    "error": task.error,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at
                }
                for task_id, task in self.tasks.items()
            },
            "shared_notes": self.shared_notes,
            "persona_states": self.persona_states
        }
    
    def is_all_tasks_completed(self) -> bool:
        """Check if all delegated tasks are completed."""
        if not self.tasks:
            return True
        return all(
            task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            for task in self.tasks.values()
        )