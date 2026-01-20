#!/usr/bin/env python3
"""
System Validation Script
Validates all core components are working correctly
"""

import sys
from pathlib import Path

def validate_imports():
    """Validate all required imports work"""
    print("\n[CHECK 1] Validating imports...")
    try:
        from multi_agent_swarm import MultiAgentSwarm
        print("  [OK] MultiAgentSwarm imported")
        
        from execution_comparator import ExecutionComparison
        print("  [OK] ExecutionComparison imported")
        
        import server
        print("  [OK] FastAPI server imported")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Import error: {e}")
        return False

def validate_core_classes():
    """Validate core classes are instantiable"""
    print("\n[CHECK 2] Validating core classes...")
    try:
        from multi_agent_swarm import MultiAgentSwarm
        swarm = MultiAgentSwarm()
        print("  [OK] MultiAgentSwarm instantiated")
        
        from execution_comparator import ExecutionComparison
        comparator = ExecutionComparison([])
        print("  [OK] ExecutionComparison instantiated")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Class instantiation error: {e}")
        return False

def validate_methods():
    """Validate key methods exist"""
    print("\n[CHECK 3] Validating key methods...")
    try:
        from multi_agent_swarm import MultiAgentSwarm
        swarm = MultiAgentSwarm()
        
        methods = [
            'analyze_task_and_spawn_agents',
            'decompose_task',
            'assign_tasks_to_agents',
            'execute_tasks',
            'get_data_flow_visualization'
        ]
        
        for method in methods:
            if hasattr(swarm, method):
                print(f"  [OK] Method '{method}' exists")
            else:
                print(f"  [FAIL] Method '{method}' missing")
                return False
        
        return True
    except Exception as e:
        print(f"  [FAIL] Method check error: {e}")
        return False

def validate_files():
    """Validate all required files exist"""
    print("\n[CHECK 4] Validating file structure...")
    required_files = [
        Path("multi_agent_swarm.py"),
        Path("execution_comparator.py"),
        Path("server.py"),
        Path("mcp_core.py"),
        Path("../frontend/src/components/MultiAgentComparison.jsx"),
        Path("../frontend/src/components/MultiAgentComparison.css"),
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  [OK] {file_path} ({size} bytes)")
        else:
            print(f"  [FAIL] {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all validations"""
    print("=" * 70)
    print("SYSTEM VALIDATION")
    print("=" * 70)
    
    checks = [
        validate_imports,
        validate_core_classes,
        validate_methods,
        validate_files
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All validations passed!")
        print("\nNext steps:")
        print("  1. Start backend: python server.py")
        print("  2. Start frontend: cd ../frontend && npm run dev")
        print("  3. Open browser: http://localhost:5173")
        return 0
    else:
        print("\n[WARNING] Some validations failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
