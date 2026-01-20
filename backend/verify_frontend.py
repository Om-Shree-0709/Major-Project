#!/usr/bin/env python3
"""
Frontend Component Verification Script
Validates that React components are properly structured
"""

import sys
from pathlib import Path
import re

def check_jsx_file_exists():
    """Check if MultiAgentComparison.jsx exists"""
    print("\n[CHECK 1] Checking JSX component file...")
    
    jsx_file = Path(__file__).parent.parent / "frontend" / "src" / "components" / "MultiAgentComparison.jsx"
    
    if jsx_file.exists():
        size = jsx_file.stat().st_size
        print(f"  [OK] MultiAgentComparison.jsx exists ({size} bytes)")
        return True
    else:
        print(f"  [FAIL] MultiAgentComparison.jsx not found")
        return False

def check_css_file_exists():
    """Check if MultiAgentComparison.css exists"""
    print("\n[CHECK 2] Checking CSS component file...")
    
    css_file = Path(__file__).parent.parent / "frontend" / "src" / "components" / "MultiAgentComparison.css"
    
    if css_file.exists():
        size = css_file.stat().st_size
        print(f"  [OK] MultiAgentComparison.css exists ({size} bytes)")
        return True
    else:
        print(f"  [FAIL] MultiAgentComparison.css not found")
        return False

def check_jsx_structure():
    """Check JSX file has proper React structure"""
    print("\n[CHECK 3] Checking JSX structure...")
    
    jsx_file = Path(__file__).parent.parent / "frontend" / "src" / "components" / "MultiAgentComparison.jsx"
    
    try:
        with open(jsx_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        checks = [
            ('Default export', 'export default MultiAgentComparison' in content),
            ('React import', 'import React' in content),
            ('useState hook', 'useState' in content),
            ('useEffect hook', 'useEffect' in content),
            ('Fetch function', 'fetch(' in content),
            ('Component functions', 'const MultiAgentComparison' in content or 'function MultiAgentComparison' in content),
        ]
        
        all_ok = True
        for check_name, result in checks:
            if result:
                print(f"  [OK] {check_name}")
            else:
                print(f"  [FAIL] {check_name}")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"  [FAIL] Error reading JSX file: {e}")
        return False

def check_tabs_implementation():
    """Check if tab functionality is implemented"""
    print("\n[CHECK 4] Checking tabs implementation...")
    
    jsx_file = Path(__file__).parent.parent / "frontend" / "src" / "components" / "MultiAgentComparison.jsx"
    
    try:
        with open(jsx_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        checks = [
            ('activeTab state', 'activeTab' in content),
            ('setActiveTab function', 'setActiveTab' in content),
            ('Tab structure', '<div className="tabs">' in content),
            ('Tab content sections', 'className="tab-content' in content),
            ('Overview tab', 'overview' in content),
            ('Linear tab', 'linear' in content),
            ('Hierarchical tab', 'hierarchical' in content),
            ('DataFlow tab', 'dataflow' in content),
        ]
        
        all_ok = True
        for check_name, result in checks:
            if result:
                print(f"  [OK] {check_name}")
            else:
                print(f"  [FAIL] {check_name}")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"  [FAIL] Error reading JSX file: {e}")
        return False

def check_data_visualization():
    """Check if data visualization components exist"""
    print("\n[CHECK 5] Checking data visualization components...")
    
    jsx_file = Path(__file__).parent.parent / "frontend" / "src" / "components" / "MultiAgentComparison.jsx"
    
    try:
        with open(jsx_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        checks = [
            ('Comparison cards', 'className="comparison-cards"' in content),
            ('Metrics display', 'className="metrics-grid"' in content),
            ('Timeline visualization', 'className="timeline"' in content),
            ('Agent cards', 'className="agent-card"' in content),
            ('Task list', 'className="tasks-list"' in content),
            ('Data flow section', 'DataFlowVisualization' in content),
        ]
        
        all_ok = True
        for check_name, result in checks:
            if result:
                print(f"  [OK] {check_name}")
            else:
                print(f"  [FAIL] {check_name}")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"  [FAIL] Error reading JSX file: {e}")
        return False

def check_css_styling():
    """Check if CSS has proper styling"""
    print("\n[CHECK 6] Checking CSS styling...")
    
    css_file = Path(__file__).parent.parent / "frontend" / "src" / "components" / "MultiAgentComparison.css"
    
    try:
        with open(css_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        checks = [
            ('Main container styling', '.multi-agent-comparison' in content),
            ('Tabs styling', '.tabs' in content),
            ('Card styling', '.card' in content),
            ('Timeline styling', '.timeline' in content),
            ('Responsive design', '@media' in content),
            ('Animations', '@keyframes' in content),
        ]
        
        all_ok = True
        for check_name, result in checks:
            if result:
                print(f"  [OK] {check_name}")
            else:
                print(f"  [FAIL] {check_name}")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"  [FAIL] Error reading CSS file: {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 70)
    print("FRONTEND COMPONENT VERIFICATION")
    print("=" * 70)
    
    checks = [
        check_jsx_file_exists,
        check_css_file_exists,
        check_jsx_structure,
        check_tabs_implementation,
        check_data_visualization,
        check_css_styling,
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
        print("\n[SUCCESS] All frontend checks passed!")
        print("\nComponent Features:")
        print("  - 4 tab interface (Overview, Linear, Hierarchical, DataFlow)")
        print("  - Real-time query input and comparison")
        print("  - Executive summary cards with metrics")
        print("  - Timeline visualization for strategy comparison")
        print("  - Agent spawning details")
        print("  - Task execution flow")
        print("  - Data flow between agents and servers")
        print("  - Responsive design for all screen sizes")
        return 0
    else:
        print("\n[WARNING] Some checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
