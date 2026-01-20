#!/usr/bin/env python3
"""
Comprehensive Test Suite for All MCP Servers
Tests: Filesystem, Browser, and GitHub MCP servers
"""
import asyncio
import json
import logging
from filesystem_server import FilesystemMCPServer
from browser_server import BrowserMCPServer
from github_server import GitHubMCPServer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("test_mcp_servers")

# ==================== FILESYSTEM TESTS ====================

def test_filesystem_server():
    """Test Filesystem MCP Server"""
    logger.info("=" * 60)
    logger.info("🔧 TESTING FILESYSTEM MCP SERVER")
    logger.info("=" * 60)
    
    fs = FilesystemMCPServer()
    
    # Test 1: List tools
    logger.info("\n1️⃣  Testing list_tools()...")
    try:
        tools = fs.list_tools()
        logger.info(f"   ✅ Found {len(tools)} tools:")
        for tool in tools:
            logger.info(f"      - {tool.name}: {tool.description}")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Write a test file
    logger.info("\n2️⃣  Testing write_file()...")
    try:
        result = fs.execute_tool("filesystem.write_file", {
            "path": "test_file.txt",
            "content": "This is a test file created by the MCP framework."
        })
        logger.info(f"   ✅ Write successful: {result}")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    # Test 3: Read the file back
    logger.info("\n3️⃣  Testing read_file()...")
    try:
        result = fs.execute_tool("filesystem.read_file", {
            "path": "test_file.txt"
        })
        logger.info(f"   ✅ Read successful: {result}")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    # Test 4: List files in sandbox
    logger.info("\n4️⃣  Testing list_files()...")
    try:
        result = fs.execute_tool("filesystem.list_files", {
            "path": "."
        })
        logger.info(f"   ✅ List successful: {result}")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    logger.info("\n✅ FILESYSTEM SERVER TESTS PASSED\n")
    return True

# ==================== BROWSER TESTS ====================

def test_browser_server():
    """Test Browser MCP Server"""
    logger.info("=" * 60)
    logger.info("🌐 TESTING BROWSER MCP SERVER")
    logger.info("=" * 60)
    
    browser = BrowserMCPServer()
    
    # Test 1: List tools
    logger.info("\n1️⃣  Testing list_tools()...")
    try:
        tools = browser.list_tools()
        logger.info(f"   ✅ Found {len(tools)} tools:")
        for tool in tools:
            logger.info(f"      - {tool.name}: {tool.description}")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Search the web
    logger.info("\n2️⃣  Testing search_web()...")
    try:
        result = browser.execute_tool("browser.search_web", {
            "query": "Python programming tips 2025"
        })
        logger.info(f"   ✅ Search successful")
        logger.info(f"      Results: {json.dumps(result, indent=2)[:200]}...")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    # Test 3: Browse a specific website
    logger.info("\n3️⃣  Testing browse_website()...")
    try:
        result = browser.execute_tool("browser.browse_website", {
            "url": "https://example.com"
        })
        logger.info(f"   ✅ Browse successful")
        logger.info(f"      Content length: {len(result.get('text', '')) if isinstance(result, dict) else len(str(result))} chars")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    logger.info("\n✅ BROWSER SERVER TESTS PASSED\n")
    return True

# ==================== GITHUB TESTS ====================

def test_github_server():
    """Test GitHub MCP Server"""
    logger.info("=" * 60)
    logger.info("🐙 TESTING GITHUB MCP SERVER")
    logger.info("=" * 60)
    
    github = GitHubMCPServer()
    
    # Test 1: List tools
    logger.info("\n1️⃣  Testing list_tools()...")
    try:
        tools = github.list_tools()
        logger.info(f"   ✅ Found {len(tools)} tools:")
        for tool in tools:
            logger.info(f"      - {tool.name}: {tool.description}")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Get authenticated user info
    logger.info("\n2️⃣  Testing get_user_info()...")
    try:
        result = github.execute_tool("github.get_user_info", {})
        logger.info(f"   ✅ User info retrieved: {result}")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    # Test 3: List user repositories
    logger.info("\n3️⃣  Testing list_user_repos()...")
    try:
        result = github.execute_tool("github.list_user_repos", {})
        logger.info(f"   ✅ Repositories retrieved:")
        if isinstance(result, dict) and "repos" in result:
            for repo in result["repos"][:3]:  # Show first 3
                logger.info(f"      - {repo}")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    # Test 4: Get repository info
    logger.info("\n4️⃣  Testing get_repo_info()...")
    try:
        result = github.execute_tool("github.get_repo_info", {
            "repo_full_name": "Om-Shree-0709/Major-Project"
        })
        logger.info(f"   ✅ Repo info retrieved: {json.dumps(result, indent=2)[:300]}...")
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    logger.info("\n✅ GITHUB SERVER TESTS PASSED\n")
    return True

# ==================== MAIN ====================

def main():
    logger.info("\n")
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║" + " " * 10 + "🚀 MCP SERVERS COMPREHENSIVE TEST" + " " * 14 + "║")
    logger.info("╚" + "═" * 58 + "╝")
    
    results = {}
    
    # Run tests
    results["Filesystem"] = test_filesystem_server()
    results["Browser"] = test_browser_server()
    results["GitHub"] = test_github_server()
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    for server, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{server}: {status}")
    
    all_passed = all(results.values())
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED!")
    else:
        logger.info("⚠️  SOME TESTS FAILED - Check the output above")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
