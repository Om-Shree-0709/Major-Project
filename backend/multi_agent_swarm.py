#!/usr/bin/env python3
"""
Advanced Multi-Agent Swarm Orchestration System
With Dynamic Agent Spawning and JSON-RPC Communication
"""

import json
import logging
import uuid
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio

logger = logging.getLogger("multi_agent_swarm")

# ==================== ENUMS ====================

class AgentRole(Enum):
    """Available agent roles"""
    RESEARCHER = "researcher"  # Uses browser for research
    DEVELOPER = "developer"    # Uses filesystem & github for coding
    ORCHESTRATOR = "orchestrator"  # Coordinates other agents
    ANALYST = "analyst"  # Analyzes data and creates reports
    EXECUTOR = "executor"  # General purpose executor

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class ExecutionStrategy(Enum):
    """Execution strategy for multi-task workflows"""
    LINEAR = "linear"  # Execute tasks sequentially
    HIERARCHICAL = "hierarchical"  # Execute with dependencies
    PARALLEL = "parallel"  # Execute independent tasks together

# ==================== DATA CLASSES ====================

@dataclass
class AgentConfig:
    """Configuration for an agent"""
    role: AgentRole
    name: str
    description: str
    available_tools: List[str]  # List of tool names this agent can use
    memory_size: int = 10
    timeout: int = 300

@dataclass
class TaskDependency:
    """Dependency information for a task"""
    task_id: str
    required_output_fields: List[str] = field(default_factory=list)

@dataclass
class Task:
    """Represents a single task to be executed"""
    id: str
    description: str
    assigned_to: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    agent_role: Optional[AgentRole] = None
    required_tools: List[str] = field(default_factory=list)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    dependencies: List[TaskDependency] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time_ms: Optional[float] = None

@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 Request"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 Response"""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: str = ""

@dataclass
class DataFlow:
    """Track data flow between agents"""
    source_agent: str
    target_agent: str
    data_type: str
    data_size_bytes: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tool_used: Optional[str] = None

@dataclass
class ExecutionMetrics:
    """Metrics for execution comparison"""
    strategy: ExecutionStrategy
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_time_ms: float
    average_task_time_ms: float
    data_flows: List[DataFlow] = field(default_factory=list)
    tool_invocations: Dict[str, int] = field(default_factory=dict)

# ==================== MULTI-AGENT SWARM ====================

class Agent:
    """Represents an intelligent agent in the swarm"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = str(uuid.uuid4())
        self.memory: List[Dict[str, Any]] = []
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.current_task: Optional[Task] = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary"""
        return {
            "id": self.id,
            "role": self.config.role.value,
            "name": self.config.name,
            "description": self.config.description,
            "available_tools": self.config.available_tools,
            "memory_entries": len(self.memory),
            "completed_tasks": len(self.completed_tasks),
            "current_task": self.current_task.id if self.current_task else None
        }

class MultiAgentSwarm:
    """Orchestrates multiple agents working together"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.data_flows: List[DataFlow] = []
        self.execution_metrics: Dict[ExecutionStrategy, ExecutionMetrics] = {}
        
    def spawn_agent(self, role: AgentRole, task_description: str, all_available_tools: List[str]) -> Agent:
        """
        Dynamically spawn an agent based on task requirements
        Uses LLM-like logic to determine appropriate role and tools
        """
        # Determine which tools this agent should have access to
        assigned_tools = self._determine_tools_for_role(role, all_available_tools)
        
        # Create agent config
        config = AgentConfig(
            role=role,
            name=f"{role.value.capitalize()}-{uuid.uuid4().hex[:8]}",
            description=f"Agent for task: {task_description}",
            available_tools=assigned_tools
        )
        
        agent = Agent(config)
        self.agents[agent.id] = agent
        
        logger.info(f"🤖 Spawned Agent: {agent.config.name} ({role.value})")
        logger.info(f"   Tools: {', '.join(assigned_tools)}")
        
        return agent
    
    def _determine_tools_for_role(self, role: AgentRole, all_tools: List[str]) -> List[str]:
        """Determine which tools a role should have access to"""
        
        role_tool_mapping = {
            AgentRole.RESEARCHER: [t for t in all_tools if "browser" in t or "search" in t.lower()],
            AgentRole.DEVELOPER: [t for t in all_tools if "filesystem" in t or "github" in t],
            AgentRole.ANALYST: [t for t in all_tools if "filesystem" in t or "browser" in t],
            AgentRole.EXECUTOR: all_tools,  # Full access
            AgentRole.ORCHESTRATOR: all_tools,  # Full access
        }
        
        return role_tool_mapping.get(role, all_tools)
    
    def analyze_task_and_spawn_agents(self, user_query: str, all_available_tools: List[str]) -> List[Agent]:
        """
        Analyze the query and spawn appropriate agents
        This simulates LLM-based task decomposition
        """
        logger.info(f"📊 Analyzing task: {user_query}")
        
        agents = []
        
        # Task analysis - determine if we need multiple agents
        if "search" in user_query.lower() and "file" in user_query.lower():
            # Multi-step: prefer a single orchestration agent with full-stack access
            logger.info("🎯 Multi-step task detected: Research + File Creation - spawning full-stack agent")
            
            # Spawn an orchestrator/executor agent with access to all available tools
            orchestrator = self.spawn_agent(AgentRole.ORCHESTRATOR, "Orchestrate research and file creation", all_available_tools)
            agents.append(orchestrator)
            
            # Also provide an optional researcher helper for deep browsing if needed
            researcher = self.spawn_agent(AgentRole.RESEARCHER, "Search for information (helper)", all_available_tools)
            agents.append(researcher)
            
        elif "search" in user_query.lower():
            # Only need researcher
            researcher = self.spawn_agent(AgentRole.RESEARCHER, user_query, all_available_tools)
            agents.append(researcher)
            
        elif "file" in user_query.lower() or "code" in user_query.lower():
            # Only need developer
            developer = self.spawn_agent(AgentRole.DEVELOPER, user_query, all_available_tools)
            agents.append(developer)
            
        else:
            # Default executor
            executor = self.spawn_agent(AgentRole.EXECUTOR, user_query, all_available_tools)
            agents.append(executor)
        
        return agents
    
    def decompose_task(self, user_query: str) -> List[Task]:
        """Break down user query into subtasks with proper chaining"""
        tasks = []
        query_lower = user_query.lower()
        
        # Task decomposition with proper step-by-step chaining
        if ("search" in query_lower or "find" in query_lower) and ("file" in query_lower or "create" in query_lower):
            # Multi-step: Search -> Format -> Create File -> Verify
            
            # Step 1: Research task
            search_task = Task(
                id=str(uuid.uuid4()),
                description=f"Search for: {user_query[:100]}",
                required_tools=["browser.search_web"],
                agent_role=AgentRole.RESEARCHER,
                input_data={"query": user_query}
            )
            tasks.append(search_task)
            
            # Step 2: Format task
            format_task = Task(
                id=str(uuid.uuid4()),
                description="Format search results into markdown content",
                required_tools=["python"],  # Internal formatting
                agent_role=AgentRole.ANALYST,
                dependencies=[TaskDependency(
                    task_id=search_task.id,
                    required_output_fields=["results"]
                )]
            )
            tasks.append(format_task)
            
            # Step 3: File creation task
            file_task = Task(
                id=str(uuid.uuid4()),
                description="Create markdown file with formatted content",
                required_tools=["filesystem.write_file"],
                agent_role=AgentRole.DEVELOPER,
                dependencies=[TaskDependency(
                    task_id=format_task.id,
                    required_output_fields=["formatted_content", "filename"]
                )]
            )
            tasks.append(file_task)
            
            # Step 4: Verification task
            verify_task = Task(
                id=str(uuid.uuid4()),
                description="Verify file was created successfully",
                required_tools=["filesystem.file_exists", "filesystem.list_dir"],
                agent_role=AgentRole.DEVELOPER,
                dependencies=[TaskDependency(
                    task_id=file_task.id,
                    required_output_fields=["path", "status"]
                )]
            )
            tasks.append(verify_task)
            
        elif "search" in query_lower or "find" in query_lower:
            # Single research task
            search_task = Task(
                id=str(uuid.uuid4()),
                description=user_query,
                required_tools=["browser.search_web"],
                agent_role=AgentRole.RESEARCHER
            )
            tasks.append(search_task)
            
        elif "file" in query_lower or "create" in query_lower:
            # Single file creation task
            file_task = Task(
                id=str(uuid.uuid4()),
                description=user_query,
                required_tools=["filesystem.write_file"],
                agent_role=AgentRole.DEVELOPER
            )
            tasks.append(file_task)
            
            # Add verification step
            verify_task = Task(
                id=str(uuid.uuid4()),
                description="Verify file creation",
                required_tools=["filesystem.file_exists"],
                agent_role=AgentRole.DEVELOPER,
                dependencies=[TaskDependency(
                    task_id=file_task.id,
                    required_output_fields=["path"]
                )]
            )
            tasks.append(verify_task)
        else:
            # Generic task
            task = Task(
                id=str(uuid.uuid4()),
                description=user_query,
                agent_role=AgentRole.EXECUTOR
            )
            tasks.append(task)
        
        # Register all tasks
        for task in tasks:
            self.tasks[task.id] = task
        
        logger.info(f"📋 Decomposed query into {len(tasks)} tasks")
        return tasks
    
    def assign_tasks_to_agents(self, tasks: List[Task], agents: List[Agent]) -> Dict[str, str]:
        """Assign tasks to appropriate agents with proper chaining"""
        task_to_agent = {}
        
        for task in tasks:
            # Find best agent for this task
            best_agent = None
            
            if task.agent_role:
                for agent in agents:
                    if agent.config.role == task.agent_role:
                        best_agent = agent
                        break
            
            # Fallback to executor or first agent
            if not best_agent:
                executors = [a for a in agents if a.config.role == AgentRole.EXECUTOR]
                best_agent = executors[0] if executors else (agents[0] if agents else None)
            
            if best_agent:
                task.assigned_to = best_agent.id
                task.status = TaskStatus.ASSIGNED
                best_agent.task_queue.append(task)
                task_to_agent[task.id] = best_agent.id
                
                logger.info(f"✅ Task {task.id[:8]} assigned to {best_agent.config.name}")
                logger.info(f"   Dependencies: {len(task.dependencies)} task(s)")
                logger.info(f"   Tools needed: {', '.join(task.required_tools)}")
        
        return task_to_agent
    
    def get_task_execution_order(self) -> List[str]:
        """Get tasks in proper execution order based on dependencies"""
        executed = set()
        order = []
        
        while len(executed) < len(self.tasks):
            for task_id, task in self.tasks.items():
                if task_id in executed:
                    continue
                
                # Check if all dependencies are executed
                deps_satisfied = all(
                    dep.task_id in executed
                    for dep in task.dependencies
                )
                
                if deps_satisfied:
                    order.append(task_id)
                    executed.add(task_id)
                    break
            else:
                # Circular dependency or no more executable tasks
                break
        
        return order
    
    def chain_task_outputs(self, source_task_id: str, target_task_id: str, output_fields: List[str]) -> bool:
        """Chain output from one task as input to another"""
        if source_task_id not in self.tasks or target_task_id not in self.tasks:
            return False
        
        source_task = self.tasks[source_task_id]
        target_task = self.tasks[target_task_id]
        
        # Copy required output fields from source to target input
        for field in output_fields:
            if field in source_task.output_data:
                target_task.input_data[field] = source_task.output_data[field]
        
        logger.info(f"🔗 Chained {len(output_fields)} fields from task {source_task_id[:8]} -> {target_task_id[:8]}")
        
        return True
    
    def rpc_call(self, source_agent_id: str, method: str, params: Dict[str, Any]) -> JSONRPCResponse:
        """
        JSON-RPC method invocation between agents
        """
        request = JSONRPCRequest(method=method, params=params)
        
        logger.info(f"📡 RPC Call from {source_agent_id[:8]}: {method}")
        
        # Execute the RPC method
        if method == "get_task_output":
            task_id = params.get("task_id")
            if task_id in self.tasks:
                return JSONRPCResponse(
                    result=self.tasks[task_id].output_data,
                    id=request.id
                )
        
        elif method == "report_progress":
            task_id = params.get("task_id")
            if task_id in self.tasks:
                self.tasks[task_id].status = TaskStatus(params.get("status", "in_progress"))
                return JSONRPCResponse(result={"status": "ok"}, id=request.id)
        
        elif method == "store_output":
            task_id = params.get("task_id")
            output = params.get("output", {})
            if task_id in self.tasks:
                self.tasks[task_id].output_data = output
                return JSONRPCResponse(result={"stored": True}, id=request.id)
        
        return JSONRPCResponse(
            error={"code": -32601, "message": "Method not found"},
            id=request.id
        )
    
    def record_data_flow(self, source_agent: str, target_agent: str, data: Dict[str, Any], tool_used: Optional[str] = None):
        """Record data flow between agents"""
        flow = DataFlow(
            source_agent=source_agent,
            target_agent=target_agent,
            data_type=type(data).__name__,
            data_size_bytes=len(json.dumps(data).encode()),
            tool_used=tool_used
        )
        self.data_flows.append(flow)
    
    def get_execution_plan(self, strategy: ExecutionStrategy) -> Dict[str, Any]:
        """Get execution plan based on strategy"""
        if strategy == ExecutionStrategy.LINEAR:
            return self._get_linear_plan()
        elif strategy == ExecutionStrategy.HIERARCHICAL:
            return self._get_hierarchical_plan()
        elif strategy == ExecutionStrategy.PARALLEL:
            return self._get_parallel_plan()
        
        return {}
    
    def _get_linear_plan(self) -> Dict[str, Any]:
        """Get linear execution plan"""
        sorted_tasks = sorted(self.tasks.values(), key=lambda t: len(t.dependencies))
        
        return {
            "strategy": "linear",
            "execution_order": [
                {
                    "step": i + 1,
                    "task_id": task.id,
                    "description": task.description,
                    "agent": self.agents[task.assigned_to].config.name if task.assigned_to else "unassigned"
                }
                for i, task in enumerate(sorted_tasks)
            ]
        }
    
    def _get_hierarchical_plan(self) -> Dict[str, Any]:
        """Get hierarchical execution plan with dependencies"""
        plan = {
            "strategy": "hierarchical",
            "task_tree": {},
            "levels": {}
        }
        
        # Build dependency tree
        for task in self.tasks.values():
            if not task.dependencies:
                level = 0
            else:
                level = 1 + max([
                    self._get_task_depth(dep.task_id)
                    for dep in task.dependencies
                ])
            
            if level not in plan["levels"]:
                plan["levels"][level] = []
            
            plan["levels"][level].append({
                "task_id": task.id,
                "description": task.description,
                "dependencies": [d.task_id for d in task.dependencies]
            })
        
        return plan
    
    def _get_parallel_plan(self) -> Dict[str, Any]:
        """Get parallel execution plan"""
        independent_tasks = [
            task for task in self.tasks.values()
            if not task.dependencies
        ]
        
        return {
            "strategy": "parallel",
            "independent_tasks": [
                {"task_id": task.id, "description": task.description}
                for task in independent_tasks
            ]
        }
    
    def _get_task_depth(self, task_id: str) -> int:
        """Calculate task depth in dependency tree"""
        if task_id not in self.tasks:
            return 0
        
        task = self.tasks[task_id]
        if not task.dependencies:
            return 0
        
        return 1 + max([
            self._get_task_depth(dep.task_id)
            for dep in task.dependencies
        ], default=0)
    
    async def execute_tasks(self, strategy: ExecutionStrategy) -> ExecutionMetrics:
        """Execute all tasks in the swarm using specified strategy"""
        import time
        start_time = time.time()
        
        execution_order = self.get_task_execution_order()
        metrics = ExecutionMetrics(
            strategy=strategy,
            total_tasks=len(self.tasks),
            completed_tasks=0,
            failed_tasks=0,
            total_time_ms=0,
            average_task_time_ms=0
        )
        
        if strategy == ExecutionStrategy.LINEAR:
            await self._execute_linear(execution_order, metrics)
        elif strategy == ExecutionStrategy.HIERARCHICAL:
            await self._execute_hierarchical(execution_order, metrics)
        elif strategy == ExecutionStrategy.PARALLEL:
            await self._execute_parallel(execution_order, metrics)
        
        end_time = time.time()
        metrics.total_time_ms = (end_time - start_time) * 1000
        metrics.average_task_time_ms = metrics.total_time_ms / max(metrics.completed_tasks, 1)
        
        return metrics
    
    async def _execute_linear(self, execution_order: List[str], metrics: ExecutionMetrics):
        """Execute tasks sequentially"""
        logger.info("📊 Executing tasks in LINEAR mode (sequential)")
        
        for task_id in execution_order:
            task = self.tasks[task_id]
            await self._execute_task(task, metrics)
    
    async def _execute_hierarchical(self, execution_order: List[str], metrics: ExecutionMetrics):
        """Execute tasks hierarchically respecting dependencies"""
        logger.info("📊 Executing tasks in HIERARCHICAL mode")
        
        executed = set()
        
        while len(executed) < len(self.tasks):
            batch = []
            
            for task_id, task in self.tasks.items():
                if task_id in executed:
                    continue
                
                # Check if dependencies are met
                deps_satisfied = all(
                    dep.task_id in executed
                    for dep in task.dependencies
                )
                
                if deps_satisfied:
                    batch.append(task)
                    executed.add(task_id)
            
            # Execute batch in parallel
            if batch:
                await asyncio.gather(*[
                    self._execute_task(task, metrics)
                    for task in batch
                ])
    
    async def _execute_parallel(self, execution_order: List[str], metrics: ExecutionMetrics):
        """Execute all independent tasks in parallel"""
        logger.info("📊 Executing tasks in PARALLEL mode")
        
        # Execute all tasks concurrently
        await asyncio.gather(*[
            self._execute_task(self.tasks[task_id], metrics)
            for task_id in execution_order
        ])
    
    async def _execute_task(self, task: Task, metrics: ExecutionMetrics):
        """Execute a single task"""
        import time
        
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now().isoformat()
        start_time = time.time()
        
        # Chain dependencies
        for dep in task.dependencies:
            if dep.task_id in self.tasks:
                self.chain_task_outputs(
                    dep.task_id,
                    task.id,
                    dep.required_output_fields
                )
        
        try:
            # Simulate task execution
            await asyncio.sleep(0.1)
            
            # Mark tools as used
            for tool in task.required_tools:
                metrics.tool_invocations[tool] = metrics.tool_invocations.get(tool, 0) + 1
                self.record_data_flow(
                    source_agent=task.assigned_to or "unknown",
                    target_agent="mcp_server",
                    data=task.input_data,
                    tool_used=tool
                )
            
            # Set output
            task.output_data = {
                "status": "completed",
                "result": f"Task completed: {task.description[:50]}",
                "tools_used": task.required_tools
            }
            
            task.status = TaskStatus.COMPLETED
            metrics.completed_tasks += 1
            
            logger.info(f"✅ Task {task.id[:8]} completed")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            metrics.failed_tasks += 1
            logger.error(f"❌ Task {task.id[:8]} failed: {e}")
        
        finally:
            task.completed_at = datetime.now().isoformat()
            task.execution_time_ms = (time.time() - start_time) * 1000
    
    def get_data_flow_visualization(self) -> Dict[str, Any]:
        """Get data flow information for visualization"""
        return {
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.config.name,
                    "role": agent.config.role.value
                }
                for agent in self.agents.values()
            ],
            "data_flows": [
                {
                    "source": flow.source_agent,
                    "target": flow.target_agent,
                    "type": flow.data_type,
                    "size": flow.data_size_bytes,
                    "tool": flow.tool_used,
                    "timestamp": flow.timestamp
                }
                for flow in self.data_flows
            ],
            "task_dependencies": [
                {
                    "task_id": task.id,
                    "description": task.description,
                    "dependencies": [d.task_id for d in task.dependencies],
                    "status": task.status.value
                }
                for task in self.tasks.values()
            ]
        }
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get current swarm status"""
        return {
            "agents": {
                agent_id: agent.to_dict()
                for agent_id, agent in self.agents.items()
            },
            "tasks": {
                task_id: {
                    "id": task.id,
                    "status": task.status.value,
                    "description": task.description,
                    "assigned_to": task.assigned_to
                }
                for task_id, task in self.tasks.items()
            },
            "data_flows": len(self.data_flows),
            "total_agents": len(self.agents),
            "total_tasks": len(self.tasks)
        }


# ==================== EXECUTION COMPARISON ====================

class ExecutionComparator:
    """Compare different execution strategies"""
    
    def __init__(self):
        self.results = {}
    
    def compare_strategies(self, task_query: str, all_tools: List[str]) -> Dict[str, Any]:
        """Compare linear vs hierarchical execution"""
        
        comparison = {
            "query": task_query,
            "results": {}
        }
        
        for strategy in [ExecutionStrategy.LINEAR, ExecutionStrategy.HIERARCHICAL]:
            swarm = MultiAgentSwarm()
            
            # Spawn agents
            agents = swarm.analyze_task_and_spawn_agents(task_query, all_tools)
            
            # Decompose tasks
            tasks = swarm.decompose_task(task_query)
            
            # Assign tasks
            task_to_agent = swarm.assign_tasks_to_agents(tasks, agents)
            
            # Get execution plan
            plan = swarm.get_execution_plan(strategy)
            
            comparison["results"][strategy.value] = {
                "agents_spawned": len(agents),
                "tasks_created": len(tasks),
                "agent_details": [agent.to_dict() for agent in agents],
                "execution_plan": plan,
                "swarm_status": swarm.get_swarm_status()
            }
        
        return comparison
