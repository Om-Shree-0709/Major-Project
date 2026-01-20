#!/usr/bin/env python3
"""
Multi-Agent Execution Comparison System
Compares LINEAR vs HIERARCHICAL execution strategies
"""

import json
import logging
import asyncio
from typing import Dict, Any
from multi_agent_swarm import (
    MultiAgentSwarm, 
    ExecutionStrategy,
    ExecutionMetrics
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("execution_comparator")

class ExecutionComparison:
    """Compare different execution strategies"""
    
    def __init__(self, available_tools: list):
        self.available_tools = available_tools
        self.results = {}
    
    async def compare_execution(self, user_query: str) -> Dict[str, Any]:
        """
        Compare LINEAR vs HIERARCHICAL execution for the same task
        Returns detailed metrics for both approaches
        """
        
        logger.info("=" * 80)
        logger.info(f"🔬 EXECUTION COMPARISON: {user_query}")
        logger.info("=" * 80)
        
        comparison_results = {
            "query": user_query,
            "strategies": {}
        }
        
        # Execute with LINEAR strategy
        logger.info("\n📋 LINEAR EXECUTION")
        logger.info("-" * 80)
        linear_result = await self._execute_with_strategy(
            user_query,
            ExecutionStrategy.LINEAR
        )
        comparison_results["strategies"]["linear"] = linear_result
        
        # Execute with HIERARCHICAL strategy
        logger.info("\n📋 HIERARCHICAL EXECUTION")
        logger.info("-" * 80)
        hierarchical_result = await self._execute_with_strategy(
            user_query,
            ExecutionStrategy.HIERARCHICAL
        )
        comparison_results["strategies"]["hierarchical"] = hierarchical_result
        
        # Calculate comparison metrics
        comparison_results["comparison"] = self._calculate_comparison(
            linear_result,
            hierarchical_result
        )
        
        return comparison_results
    
    async def _execute_with_strategy(
        self,
        query: str,
        strategy: ExecutionStrategy
    ) -> Dict[str, Any]:
        """Execute tasks using specified strategy"""
        
        # Create new swarm for this strategy
        swarm = MultiAgentSwarm()
        
        # Step 1: Analyze and spawn agents
        logger.info(f"1️⃣ Spawning agents for: {strategy.value} mode")
        agents = swarm.analyze_task_and_spawn_agents(query, self.available_tools)
        
        logger.info(f"   ✅ Spawned {len(agents)} agents")
        for agent in agents:
            logger.info(f"      - {agent.config.name} ({agent.config.role.value})")
        
        # Step 2: Decompose task into subtasks
        logger.info(f"2️⃣ Decomposing task into subtasks")
        tasks = swarm.decompose_task(query)
        
        logger.info(f"   ✅ Created {len(tasks)} tasks")
        for task in tasks:
            logger.info(f"      - {task.description[:60]}")
            if task.dependencies:
                logger.info(f"        Dependencies: {len(task.dependencies)}")
        
        # Step 3: Assign tasks to agents
        logger.info(f"3️⃣ Assigning tasks to agents")
        task_to_agent = swarm.assign_tasks_to_agents(tasks, agents)
        
        # Step 4: Execute tasks
        logger.info(f"4️⃣ Executing tasks in {strategy.value.upper()} mode")
        metrics = await swarm.execute_tasks(strategy)
        
        logger.info(f"   ✅ Execution complete")
        logger.info(f"      - Completed: {metrics.completed_tasks}/{metrics.total_tasks}")
        logger.info(f"      - Failed: {metrics.failed_tasks}")
        logger.info(f"      - Total time: {metrics.total_time_ms:.2f}ms")
        logger.info(f"      - Avg task time: {metrics.average_task_time_ms:.2f}ms")
        
        # Step 5: Get execution plan
        execution_plan = swarm.get_execution_plan(strategy)
        
        # Step 6: Get data flow info
        data_flow = swarm.get_data_flow_visualization()
        
        return {
            "strategy": strategy.value,
            "agents_spawned": len(agents),
            "agent_details": [
                {
                    "id": agent.id,
                    "name": agent.config.name,
                    "role": agent.config.role.value,
                    "tools": agent.config.available_tools,
                    "tasks_assigned": len(agent.task_queue)
                }
                for agent in agents
            ],
            "tasks_created": len(tasks),
            "task_details": [
                {
                    "id": task.id,
                    "description": task.description,
                    "status": task.status.value,
                    "assigned_to": task.assigned_to,
                    "dependencies": [d.task_id for d in task.dependencies],
                    "execution_time_ms": task.execution_time_ms,
                    "output": task.output_data
                }
                for task in tasks
            ],
            "metrics": {
                "total_time_ms": metrics.total_time_ms,
                "avg_task_time_ms": metrics.average_task_time_ms,
                "completed_tasks": metrics.completed_tasks,
                "failed_tasks": metrics.failed_tasks,
                "tool_invocations": metrics.tool_invocations
            },
            "execution_plan": execution_plan,
            "data_flow": data_flow,
            "swarm_status": swarm.get_swarm_status()
        }
    
    def _calculate_comparison(
        self,
        linear_result: Dict[str, Any],
        hierarchical_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comparison metrics between strategies"""
        
        linear_time = linear_result["metrics"]["total_time_ms"]
        hierarchical_time = hierarchical_result["metrics"]["total_time_ms"]
        
        time_difference = linear_time - hierarchical_time
        time_percentage = (time_difference / linear_time * 100) if linear_time > 0 else 0
        
        faster_strategy = "linear" if linear_time < hierarchical_time else "hierarchical"
        
        return {
            "linear_time_ms": linear_time,
            "hierarchical_time_ms": hierarchical_time,
            "time_difference_ms": abs(time_difference),
            "time_difference_percent": abs(time_percentage),
            "faster_strategy": faster_strategy,
            "linear_avg_task_time": linear_result["metrics"]["avg_task_time_ms"],
            "hierarchical_avg_task_time": hierarchical_result["metrics"]["avg_task_time_ms"],
            "linear_tool_invocations": sum(linear_result["metrics"]["tool_invocations"].values()),
            "hierarchical_tool_invocations": sum(hierarchical_result["metrics"]["tool_invocations"].values()),
            "recommendation": f"Use {faster_strategy} strategy for {time_percentage:.1f}% better performance"
        }

# Testing function
async def test_comparison():
    """Test the execution comparison system"""
    
    available_tools = [
        "browser.search_web",
        "browser.browse_website",
        "filesystem.write_file",
        "filesystem.read_file",
        "filesystem.list_dir",
        "filesystem.file_exists",
        "github.list_repos",
        "github.get_repo"
    ]
    
    comparator = ExecutionComparison(available_tools)
    
    # Test query
    query = "find all latest AI related news and create a file news.md with properly formatted content"
    
    result = await comparator.compare_execution(query)
    
    # Print results
    print("\n" + "=" * 80)
    print("🎯 COMPARISON RESULTS")
    print("=" * 80)
    print(json.dumps(result["comparison"], indent=2))
    
    return result

if __name__ == "__main__":
    # Run comparison
    result = asyncio.run(test_comparison())
