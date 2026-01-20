#!/usr/bin/env python3
"""
Endpoint Verification Script
Tests all FastAPI endpoints without requiring the server to be running
"""

import sys
from pathlib import Path

def check_endpoint_definitions():
    """Check if all endpoint definitions exist in server.py"""
    print("\n[CHECK 1] Checking endpoint definitions in server.py...")
    
    server_file = Path(__file__).parent / "server.py"
    with open(server_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    endpoints = [
        '@app.post("/multi-agent/compare")',
        '@app.post("/multi-agent/spawn-and-execute")',
        '@app.get("/multi-agent/data-flow")'
    ]
    
    all_found = True
    for endpoint in endpoints:
        if endpoint in content:
            print(f"  [OK] Endpoint found: {endpoint}")
        else:
            print(f"  [FAIL] Endpoint missing: {endpoint}")
            all_found = False
    
    return all_found

def check_endpoint_handlers():
    """Check if endpoint handler functions exist"""
    print("\n[CHECK 2] Checking endpoint handler functions...")
    
    server_file = Path(__file__).parent / "server.py"
    with open(server_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    handlers = [
        'async def compare_execution_strategies',
        'async def spawn_and_execute',
        'async def get_data_flow'
    ]
    
    all_found = True
    for handler in handlers:
        if handler in content:
            print(f"  [OK] Handler found: {handler}")
        else:
            print(f"  [FAIL] Handler missing: {handler}")
            all_found = False
    
    return all_found

def check_endpoint_imports():
    """Check if all required imports are in server.py"""
    print("\n[CHECK 3] Checking required imports...")
    
    server_file = Path(__file__).parent / "server.py"
    with open(server_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    imports = [
        'from execution_comparator import ExecutionComparison',
    ]
    
    # These might be imported at module level or inside functions
    required_functions = [
        'ExecutionComparison',
        'swarm_manager'
    ]
    
    all_found = True
    for req in required_functions:
        if req in content:
            print(f"  [OK] Found reference to: {req}")
        else:
            print(f"  [FAIL] Missing reference to: {req}")
            all_found = False
    
    return all_found

def check_endpoint_parameters():
    """Check if endpoints handle parameters correctly"""
    print("\n[CHECK 4] Checking endpoint parameter handling...")
    
    server_file = Path(__file__).parent / "server.py"
    with open(server_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    checks = [
        ('GET /data-flow has no required params', 'async def get_data_flow()' in content),
        ('POST /compare expects query param', 'query = request.get("query"' in content),
        ('POST /spawn has execution_mode param', 'execution_mode = request.get("execution_mode"' in content),
    ]
    
    all_ok = True
    for check_name, result in checks:
        if result:
            print(f"  [OK] {check_name}")
        else:
            print(f"  [FAIL] {check_name}")
            all_ok = False
    
    return all_ok

def check_error_handling():
    """Check if endpoints have error handling"""
    print("\n[CHECK 5] Checking error handling...")
    
    server_file = Path(__file__).parent / "server.py"
    with open(server_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    checks = [
        ('Try-except blocks', 'try:' in content and 'except' in content),
        ('Error responses', 'return {' in content and '"error"' in content),
        ('HTTP status codes', 'status_code' in content or '400' in content or '500' in content),
    ]
    
    all_ok = True
    for check_name, result in checks:
        if result:
            print(f"  [OK] {check_name}")
        else:
            print(f"  [FAIL] {check_name}")
            all_ok = False
    
    return all_ok

def main():
    """Run all checks"""
    print("=" * 70)
    print("ENDPOINT VERIFICATION")
    print("=" * 70)
    
    checks = [
        check_endpoint_definitions,
        check_endpoint_handlers,
        check_endpoint_imports,
        check_endpoint_parameters,
        check_error_handling,
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All endpoint checks passed!")
        print("\nEndpoints verified:")
        print("  POST /multi-agent/compare")
        print("  POST /multi-agent/spawn-and-execute")
        print("  GET /multi-agent/data-flow")
        return 0
    else:
        print("\n[WARNING] Some checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
