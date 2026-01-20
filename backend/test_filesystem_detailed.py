#!/usr/bin/env python3
"""
Comprehensive Test Suite for Filesystem MCP Server
Tests file creation, writing, reading, and manipulation
"""
import json
import logging
from filesystem_server import FilesystemMCPServer

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("test_filesystem")

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"🔧 {title}")
    print("=" * 70 + "\n")

def test_write_file():
    """Test writing a new file."""
    print_section("TEST 1: Write File")
    
    fs = FilesystemMCPServer()
    
    result = fs.execute_tool("filesystem.write_file", {
        "path": "FastAPI.py",
        "content": """from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
"""
    })
    
    print(f"Result: {json.dumps(result, indent=2)}")
    return result.get("code") == 200

def test_read_file():
    """Test reading the file we just created."""
    print_section("TEST 2: Read File")
    
    fs = FilesystemMCPServer()
    
    result = fs.execute_tool("filesystem.read_file", {
        "path": "FastAPI.py"
    })
    
    print(f"Read Result Status: {result.get('code')}")
    if result.get("code") == 200:
        content = result.get("content", "")
        print(f"File Content Length: {len(content)} characters")
        print(f"First 200 chars:\n{content[:200]}...")
    else:
        print(f"Error: {result.get('error')}")
    
    return result.get("code") == 200

def test_write_python_script():
    """Test writing a Python script."""
    print_section("TEST 3: Write Python Script")
    
    fs = FilesystemMCPServer()
    
    result = fs.execute_tool("filesystem.write_file", {
        "path": "hello_world.py",
        "content": """#!/usr/bin/env python3
'''
Hello World Script
A simple script to print hello world
'''

def main():
    print("Hello, World!")
    print("This is a test script created by the MCP Filesystem Server")

if __name__ == "__main__":
    main()
"""
    })
    
    print(f"Result: {json.dumps(result, indent=2)}")
    return result.get("code") == 200

def test_write_config_file():
    """Test writing a configuration file."""
    print_section("TEST 4: Write Config File (JSON)")
    
    fs = FilesystemMCPServer()
    
    config_content = {
        "app": "MyApp",
        "version": "1.0.0",
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "mydb"
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    result = fs.execute_tool("filesystem.write_file", {
        "path": "config.json",
        "content": json.dumps(config_content, indent=2)
    })
    
    print(f"Result: {json.dumps(result, indent=2)}")
    return result.get("code") == 200

def test_append_file():
    """Test appending to a file."""
    print_section("TEST 5: Append to File")
    
    fs = FilesystemMCPServer()
    
    # First create a file
    fs.execute_tool("filesystem.write_file", {
        "path": "notes.txt",
        "content": "Initial notes\n"
    })
    
    # Then append to it
    result = fs.execute_tool("filesystem.append_file", {
        "path": "notes.txt",
        "content": "- Added note 1\n- Added note 2\n- Added note 3\n"
    })
    
    print(f"Append Result: {json.dumps(result, indent=2)}")
    
    # Read it back
    read_result = fs.execute_tool("filesystem.read_file", {
        "path": "notes.txt"
    })
    
    print(f"\nFile Content After Append:\n{read_result.get('content', '')}")
    return result.get("code") == 200

def test_list_files():
    """Test listing files in the sandbox."""
    print_section("TEST 6: List Files in Sandbox")
    
    fs = FilesystemMCPServer()
    
    result = fs.execute_tool("filesystem.list_dir", {
        "path": "."
    })
    
    print(f"List Result: {json.dumps(result, indent=2)}")
    return result.get("code") == 200

def test_create_directory():
    """Test creating a directory."""
    print_section("TEST 7: Create Directory")
    
    fs = FilesystemMCPServer()
    
    result = fs.execute_tool("filesystem.make_directory", {
        "path": "test_project"
    })
    
    print(f"Create Directory Result: {json.dumps(result, indent=2)}")
    return result.get("code") == 200

def test_file_exists():
    """Test checking if a file exists."""
    print_section("TEST 8: Check File Exists")
    
    fs = FilesystemMCPServer()
    
    # Check a file that should exist
    result1 = fs.execute_tool("filesystem.file_exists", {
        "path": "FastAPI.py"
    })
    
    print(f"FastAPI.py exists: {json.dumps(result1, indent=2)}")
    
    # Check a file that shouldn't exist
    result2 = fs.execute_tool("filesystem.file_exists", {
        "path": "nonexistent.py"
    })
    
    print(f"nonexistent.py exists: {json.dumps(result2, indent=2)}")
    
    return result1.get("code") == 200

def test_file_metadata():
    """Test getting file metadata."""
    print_section("TEST 9: Get File Metadata")
    
    fs = FilesystemMCPServer()
    
    result = fs.execute_tool("filesystem.get_metadata", {
        "path": "FastAPI.py"
    })
    
    print(f"File Metadata: {json.dumps(result, indent=2)}")
    return result.get("code") == 200

def test_search_files():
    """Test searching for files."""
    print_section("TEST 10: Search Files")
    
    fs = FilesystemMCPServer()
    
    result = fs.execute_tool("filesystem.search_files", {
        "path": ".",
        "pattern": "*.py"
    })
    
    print(f"Search Results: {json.dumps(result, indent=2)}")
    return result.get("code") == 200

def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("🚀 FILESYSTEM MCP SERVER - COMPREHENSIVE TEST SUITE")
    logger.info("=" * 70)
    
    tests = [
        ("Write File", test_write_file),
        ("Read File", test_read_file),
        ("Write Python Script", test_write_python_script),
        ("Write Config File", test_write_config_file),
        ("Append to File", test_append_file),
        ("List Files", test_list_files),
        ("Create Directory", test_create_directory),
        ("File Exists Check", test_file_exists),
        ("Get File Metadata", test_file_metadata),
        ("Search Files", test_search_files),
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
        print(f"\n⚠️  {total - passed} tests failed")

if __name__ == "__main__":
    main()
