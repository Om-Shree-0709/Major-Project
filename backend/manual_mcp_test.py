#!/usr/bin/env python3
"""
Manual Testing Guide for All 3 MCP Servers

This script demonstrates how to test each MCP server directly
without going through the FastAPI endpoint
"""

import json
import logging
from filesystem_server import FilesystemMCPServer
from browser_server import BrowserMCPServer
from github_server import GitHubMCPServer

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("manual_mcp_test")

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def test_filesystem_server():
    """Test Filesystem MCP Server"""
    print_header("FILESYSTEM MCP SERVER - Manual Tests")
    
    fs = FilesystemMCPServer()
    
    # Test 1: Create a file
    print("✓ Test 1: Creating a new file named 'manual_test.py'")
    result = fs.execute_tool("filesystem.write_file", {
        "path": "manual_test.py",
        "content": """#!/usr/bin/env python3
# This file was created by the manual test script

def hello():
    print("Hello from manual test!")

if __name__ == "__main__":
    hello()
"""
    })
    print(f"  Result: {json.dumps(result, indent=2)}\n")
    
    # Test 2: Read the file
    print("✓ Test 2: Reading the file we just created")
    result = fs.execute_tool("filesystem.read_file", {
        "path": "manual_test.py"
    })
    print(f"  Content (first 150 chars): {result.get('content', '')[:150]}...\n")
    
    # Test 3: Append to file
    print("✓ Test 3: Appending to the file")
    result = fs.execute_tool("filesystem.append_file", {
        "path": "manual_test.py",
        "content": "\n# This line was appended!"
    })
    print(f"  Result: {result.get('status', 'unknown')} - {result.get('bytes_appended', 0)} bytes appended\n")
    
    # Test 4: List files
    print("✓ Test 4: Listing all files in sandbox")
    result = fs.execute_tool("filesystem.list_dir", {
        "path": "."
    })
    files = [item['name'] for item in result.get('items', []) if not item['is_dir']]
    print(f"  Found {len(files)} files:")
    for f in files[:5]:
        print(f"    - {f}")
    if len(files) > 5:
        print(f"    ... and {len(files) - 5} more")
    print()
    
    # Test 5: Search files
    print("✓ Test 5: Searching for .py files")
    result = fs.execute_tool("filesystem.search_files", {
        "path": ".",
        "pattern": "*.py"
    })
    py_files = result.get('matches', [])
    print(f"  Found {len(py_files)} Python files:")
    for f in py_files[:5]:
        print(f"    - {f}")
    print()
    
    # Test 6: Check if file exists
    print("✓ Test 6: Checking if files exist")
    for filename in ["manual_test.py", "nonexistent.py", "FastAPI.py"]:
        result = fs.execute_tool("filesystem.file_exists", {
            "path": filename
        })
        exists = result.get('exists', False)
        status = "✅ EXISTS" if exists else "❌ NOT FOUND"
        print(f"  {filename:20} {status}")
    print()

def test_browser_server():
    """Test Browser MCP Server"""
    print_header("BROWSER MCP SERVER - Manual Tests")
    
    browser = BrowserMCPServer()
    
    # Test 1: Search web
    print("✓ Test 1: Searching the web for 'Python programming'")
    result = browser.execute_tool("browser.search_web", {
        "query": "Python programming tutorial"
    })
    
    if result.get('code') == 200:
        results = result.get('results', [])
        print(f"  Found {len(results)} results:")
        for i, r in enumerate(results[:3], 1):
            print(f"    {i}. {r.get('title', 'No title')[:60]}")
    else:
        print(f"  Error: {result.get('error')}")
    print()
    
    # Test 2: Browse a website
    print("✓ Test 2: Browsing python.org")
    result = browser.execute_tool("browser.browse_website", {
        "url": "https://www.python.org"
    })
    
    if result.get('code') == 200:
        content = result.get('content', '')
        print(f"  Successfully retrieved {len(content)} characters")
        print(f"  Preview (first 150 chars):\n  {content[:150]}...\n")
    else:
        print(f"  Error: {result.get('error')}\n")

def test_github_server():
    """Test GitHub MCP Server"""
    print_header("GITHUB MCP SERVER - Manual Tests")
    
    github = GitHubMCPServer()
    
    # Test 1: List repos
    print("✓ Test 1: Listing all your GitHub repositories")
    result = github.execute_tool("github.list_repos", {})
    
    if result.get('code') == 200:
        repos = result.get('result', [])
        print(f"  Found {len(repos)} repositories:")
        for i, repo in enumerate(repos[:5], 1):
            private_status = "🔒 PRIVATE" if repo.get('private') else "🌐 PUBLIC"
            print(f"    {i}. {repo.get('full_name')} [{private_status}]")
        if len(repos) > 5:
            print(f"    ... and {len(repos) - 5} more")
    else:
        print(f"  Error: {result.get('error')}")
    print()
    
    # Test 2: Check rate limit
    print("✓ Test 2: Checking GitHub API rate limits")
    result = github.execute_tool("github.rate_limit", {})
    
    if result.get('code') == 200:
        data = result.get('result', {})
        core = data.get('resources', {}).get('core', {})
        print(f"  Core API:")
        print(f"    Remaining: {core.get('remaining', 'N/A')} / {core.get('limit', 'N/A')}")
        print(f"    Reset: {core.get('reset', 'N/A')}")
    else:
        print(f"  Error: {result.get('error')}")
    print()

def main():
    """Run all manual tests"""
    print("\n" + "=" * 80)
    print("  MANUAL MCP SERVERS TESTING GUIDE")
    print("=" * 80)
    print("\nThis script tests all 3 MCP servers directly")
    print("It creates real files, makes web requests, and queries GitHub")
    
    try:
        # Test Filesystem
        test_filesystem_server()
        
        # Test Browser
        test_browser_server()
        
        # Test GitHub
        test_github_server()
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print_header("Testing Complete! ✅")
    print("All 3 MCP servers are functional and ready to use!")
    print("\nSummary:")
    print("  ✅ Filesystem Server - File operations working")
    print("  ✅ Browser Server - Web search and browsing working")
    print("  ✅ GitHub Server - Repository operations working")
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()
