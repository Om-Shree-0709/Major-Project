#!/usr/bin/env python3
"""
Debug script to understand the file creation issue
and test direct tool execution
"""
import json
import logging
from filesystem_server import FilesystemMCPServer

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("debug_file_creation")

def test_direct_write():
    """Test writing a file directly without going through the API."""
    print("\n" + "=" * 70)
    print("TEST 1: Direct Filesystem Tool Execution")
    print("=" * 70)
    
    fs = FilesystemMCPServer()
    
    # This should work - explicit path
    print("\n✓ Test 1a: Writing FastAPI.py with explicit path")
    result = fs.execute_tool("filesystem.write_file", {
        "path": "FastAPI.py",
        "content": """from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
"""
    })
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test what happens with missing path
    print("\n✗ Test 1b: Writing file with MISSING path argument")
    result2 = fs.execute_tool("filesystem.write_file", {
        "content": "This should fail"
    })
    print(f"Result: {json.dumps(result2, indent=2)}")
    
    # Test what happens with None path
    print("\n✗ Test 1c: Writing file with None path")
    result3 = fs.execute_tool("filesystem.write_file", {
        "path": None,
        "content": "This should fail"
    })
    print(f"Result: {json.dumps(result3, indent=2)}")
    
    # Test what happens with empty string path
    print("\n✗ Test 1d: Writing file with empty string path")
    result4 = fs.execute_tool("filesystem.write_file", {
        "path": "",
        "content": "This should fail"
    })
    print(f"Result: {json.dumps(result4, indent=2)}")

def test_llm_integration():
    """Test what the LLM generates for a file creation request."""
    print("\n" + "=" * 70)
    print("TEST 2: LLM Integration - What does the LLM generate?")
    print("=" * 70)
    
    # Simulate what the LLM might generate
    print("\nScenario 1: LLM generates correct tool call")
    llm_output_1 = """{
    "action": "tool",
    "server": "filesystem",
    "tool": "write_file",
    "args": {
        "path": "FastAPI.py",
        "content": "from fastapi import FastAPI..."
    }
}"""
    
    decision = json.loads(llm_output_1)
    print(f"LLM Output: {json.dumps(decision, indent=2)}")
    print(f"Path: '{decision['args'].get('path')}'")
    print(f"Content: '{decision['args'].get('content')[:50]}...'")
    
    print("\nScenario 2: LLM generates missing path (THIS IS THE BUG)")
    llm_output_2 = """{
    "action": "tool",
    "server": "filesystem",
    "tool": "write_file",
    "args": {
        "content": "from fastapi import FastAPI..."
    }
}"""
    
    decision2 = json.loads(llm_output_2)
    print(f"LLM Output: {json.dumps(decision2, indent=2)}")
    print(f"Path: '{decision2['args'].get('path')}'  <-- MISSING!")
    
    print("\nScenario 3: LLM generates empty path string")
    llm_output_3 = """{
    "action": "tool",
    "server": "filesystem",
    "tool": "write_file",
    "args": {
        "path": "",
        "content": "from fastapi import FastAPI..."
    }
}"""
    
    decision3 = json.loads(llm_output_3)
    print(f"LLM Output: {json.dumps(decision3, indent=2)}")
    print(f"Path: '{decision3['args'].get('path')}'  <-- EMPTY!")

def test_improved_error_handling():
    """Test how we can handle these edge cases better."""
    print("\n" + "=" * 70)
    print("TEST 3: Proposed Improvements")
    print("=" * 70)
    
    print("\n✓ Improvement 1: Better LLM prompting")
    print("""
The system prompt should emphasize:
- ALWAYS include the 'path' parameter for file operations
- Use descriptive filenames (e.g., "FastAPI.py" not "file")
- Include the complete file content without truncation
    """)
    
    print("\n✓ Improvement 2: Server-side validation")
    print("""
Before executing a tool, validate:
- All required parameters are present
- No parameters have None or empty values
- Return a helpful error message to the LLM
    """)
    
    print("\n✓ Improvement 3: Fallback filename")
    print("""
If path is missing, generate a default:
- For file creation: use a timestamp-based filename
- Inform the LLM of the fallback
- Example: "created_20250120_171520.txt"
    """)

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("🔍 DEBUG: File Creation Issue Analysis")
    logger.info("=" * 70)
    
    test_direct_write()
    test_llm_integration()
    test_improved_error_handling()
    
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("""
The error "Path is required and cannot be empty" occurs because:
1. The LLM is NOT including the 'path' parameter in the tool call
2. The filesystem server correctly rejects requests with missing paths

ROOT CAUSES:
1. The LLM system prompt may not be explicit enough about required parameters
2. The LLM may not be listing the tool parameters clearly
3. The tool schema in the system prompt may not emphasize required fields

SOLUTIONS:
1. ✅ Improve system prompt to show example tool calls with all required params
2. ✅ Add validation in server.py to give the LLM helpful error messages
3. ✅ Test with the detailed test files to ensure Filesystem server works
4. ✅ Run test_filesystem_detailed.py to verify direct tool execution
""")
