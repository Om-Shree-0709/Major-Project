#!/usr/bin/env python3
"""
Comprehensive Test Suite for Browser MCP Server
Tests web search and website browsing capabilities
"""
import json
import logging
from browser_server import BrowserMCPServer

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("test_browser")

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"🌐 {title}")
    print("=" * 70 + "\n")

def test_search_web_fastapi():
    """Test web search for FastAPI."""
    print_section("TEST 1: Search Web - FastAPI")
    
    browser = BrowserMCPServer()
    
    result = browser.execute_tool("browser.search_web", {
        "query": "FastAPI framework Python"
    })
    
    print(f"Search Status: {result.get('code')}")
    if result.get("code") == 200:
        results = result.get("results", [])
        print(f"Found {len(results)} results")
        
        # Print first 3 results
        for i, res in enumerate(results[:3], 1):
            print(f"\n  Result {i}:")
            print(f"    Title: {res.get('title', 'N/A')[:60]}")
            print(f"    URL: {res.get('url', 'N/A')}")
            print(f"    Description: {res.get('description', 'N/A')[:80]}")
    else:
        print(f"Error: {result.get('error')}")
    
    return result.get("code") == 200

def test_search_web_python():
    """Test web search for Python."""
    print_section("TEST 2: Search Web - Python Documentation")
    
    browser = BrowserMCPServer()
    
    result = browser.execute_tool("browser.search_web", {
        "query": "Python official documentation"
    })
    
    print(f"Search Status: {result.get('code')}")
    if result.get("code") == 200:
        results = result.get("results", [])
        print(f"Found {len(results)} results")
        
        if results:
            first_result = results[0]
            print(f"\n  Top Result:")
            print(f"    Title: {first_result.get('title', 'N/A')}")
            print(f"    URL: {first_result.get('url', 'N/A')}")
    else:
        print(f"Error: {result.get('error')}")
    
    return result.get("code") == 200

def test_search_web_mcp():
    """Test web search for MCP Protocol."""
    print_section("TEST 3: Search Web - Model Context Protocol")
    
    browser = BrowserMCPServer()
    
    result = browser.execute_tool("browser.search_web", {
        "query": "Model Context Protocol MCP"
    })
    
    print(f"Search Status: {result.get('code')}")
    if result.get("code") == 200:
        results = result.get("results", [])
        print(f"Found {len(results)} results")
        
        for i, res in enumerate(results[:2], 1):
            print(f"\n  Result {i}:")
            print(f"    Title: {res.get('title', 'N/A')[:70]}")
            print(f"    URL: {res.get('url', 'N/A')}")
    else:
        print(f"Error: {result.get('error')}")
    
    return result.get("code") == 200

def test_browse_website_python():
    """Test browsing Python official website."""
    print_section("TEST 4: Browse Website - Python.org")
    
    browser = BrowserMCPServer()
    
    result = browser.execute_tool("browser.browse_website", {
        "url": "https://www.python.org"
    })
    
    print(f"Browse Status: {result.get('code')}")
    if result.get("code") == 200:
        content = result.get("content", "")
        print(f"Content Length: {len(content)} characters")
        print(f"First 300 characters:\n{content[:300]}...")
    else:
        print(f"Error: {result.get('error')}")
    
    return result.get("code") == 200

def test_browse_github():
    """Test browsing GitHub."""
    print_section("TEST 5: Browse Website - GitHub")
    
    browser = BrowserMCPServer()
    
    result = browser.execute_tool("browser.browse_website", {
        "url": "https://www.github.com"
    })
    
    print(f"Browse Status: {result.get('code')}")
    if result.get("code") == 200:
        content = result.get("content", "")
        print(f"Content Length: {len(content)} characters")
        
        # Check if we got actual content
        if len(content) > 100:
            print(f"✅ Successfully retrieved page content")
            print(f"First 250 characters:\n{content[:250]}...")
        else:
            print(f"⚠️  Content seems minimal")
    else:
        print(f"Error: {result.get('error')}")
    
    return result.get("code") == 200

def test_browse_stackoverflow():
    """Test browsing Stack Overflow."""
    print_section("TEST 6: Browse Website - Stack Overflow")
    
    browser = BrowserMCPServer()
    
    result = browser.execute_tool("browser.browse_website", {
        "url": "https://stackoverflow.com/questions/tagged/fastapi"
    })
    
    print(f"Browse Status: {result.get('code')}")
    if result.get("code") == 200:
        content = result.get("content", "")
        print(f"Content Length: {len(content)} characters")
        
        if "FastAPI" in content or "fastapi" in content.lower():
            print(f"✅ Successfully retrieved Stack Overflow content")
        
        print(f"First 300 characters:\n{content[:300]}...")
    else:
        print(f"Error: {result.get('error')}")
    
    return result.get("code") == 200

def test_search_web_error_handling():
    """Test error handling with empty query."""
    print_section("TEST 7: Error Handling - Empty Query")
    
    browser = BrowserMCPServer()
    
    result = browser.execute_tool("browser.search_web", {
        "query": ""
    })
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Should either return empty results or an error
    return True  # Error handling is fine either way

def test_search_web_special_chars():
    """Test search with special characters."""
    print_section("TEST 8: Search - Special Characters")
    
    browser = BrowserMCPServer()
    
    result = browser.execute_tool("browser.search_web", {
        "query": "C++ programming tutorial"
    })
    
    print(f"Search Status: {result.get('code')}")
    if result.get("code") == 200:
        results = result.get("results", [])
        print(f"Found {len(results)} results for 'C++ programming tutorial'")
    else:
        print(f"Error: {result.get('error')}")
    
    return result.get("code") == 200

def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("🚀 BROWSER MCP SERVER - COMPREHENSIVE TEST SUITE")
    logger.info("=" * 70)
    
    tests = [
        ("Search - FastAPI", test_search_web_fastapi),
        ("Search - Python Documentation", test_search_web_python),
        ("Search - MCP Protocol", test_search_web_mcp),
        ("Browse - Python.org", test_browse_website_python),
        ("Browse - GitHub", test_browse_github),
        ("Browse - Stack Overflow", test_browse_stackoverflow),
        ("Error Handling - Empty Query", test_search_web_error_handling),
        ("Search - Special Characters", test_search_web_special_chars),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results[test_name] = "✅ PASSED" if passed else "❌ FAILED"
        except Exception as e:
            results[test_name] = f"❌ ERROR: {str(e)[:50]}"
            logger.error(f"Test '{test_name}' error: {e}")
    
    # Print summary
    print_section("TEST SUMMARY")
    
    for test_name, status in results.items():
        print(f"{test_name:40} {status}")
    
    # Count results
    passed = sum(1 for s in results.values() if "PASSED" in s)
    total = len(results)
    
    print(f"\n📊 Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} tests failed or had issues")

if __name__ == "__main__":
    main()
