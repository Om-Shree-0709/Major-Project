import asyncio
from multi_agent_swarm import MultiAgentSwarm
from execution_comparator import ExecutionComparison

async def test():
    print("=" * 60)
    print("QUICK TEST: Multi-Agent System")
    print("=" * 60)
    
    swarm = MultiAgentSwarm()
    print("\n1. Swarm initialized OK")
    
    available_tools = [
        "browser.search_web", "browser.browse_website",
        "filesystem.read_file", "filesystem.write_file",
        "filesystem.create_directory"
    ]
    
    query = "find AI news and create file called news.md"
    print(f"\n2. Test query: {query}")
    
    agents = swarm.analyze_task_and_spawn_agents(query, available_tools)
    print(f"\n3. Spawned {len(agents)} agents:")
    for agent in agents:
        print(f"   - {agent.name} ({agent.role.value})")
    
    tasks = swarm.decompose_task(query, agents)
    print(f"\n4. Created {len(tasks)} tasks:")
    for i, (task_id, task) in enumerate(tasks.items(), 1):
        print(f"   Task {i}: {task.description}")
    
    print("\n5. Testing execution comparator...")
    comparator = ExecutionComparison(
        swarm=swarm,
        agents=swarm.agents,
        tasks=swarm.tasks,
        llm_providers=[]
    )
    
    result = await comparator.compare_execution(query)
    print(f"\n6. Comparison result received with {len(result.get('strategies', []))} strategies")
    
    print("\n" + "=" * 60)
    print("QUICK TEST PASSED")
    print("=" * 60)

asyncio.run(test())
