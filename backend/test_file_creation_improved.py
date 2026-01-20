#!/usr/bin/env python3
"""
Test the file creation with improved LLM prompts
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_file_creation():
    """Test creating FastAPI.py file with the improved system prompt."""
    print("\n" + "=" * 70)
    print("TEST: Create FastAPI.py File with Improved Prompts")
    print("=" * 70 + "\n")
    
    # Give server a moment to start
    time.sleep(2)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Server Status: {response.status_code}")
    except:
        print("❌ Server is not running!")
        return False
    
    # Test query
    query = "create a file named FastAPI.py with basic connection code with fastapi"
    
    print(f"📝 Query: {query}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json={"user_query": query},
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFinal Answer:")
            print(f"{data.get('final_answer', 'No answer provided')}\n")
            
            # Check if tool was executed
            tool_calls = data.get('tool_calls_executed', [])
            if tool_calls:
                print(f"Tool Calls Executed: {len(tool_calls)}")
                for i, call in enumerate(tool_calls, 1):
                    print(f"\n  Call {i}:")
                    print(f"    Server: {call.get('server')}")
                    print(f"    Tool: {call.get('tool')}")
                    result = call.get('result', {})
                    if result.get('code') == 200:
                        print(f"    Status: ✅ SUCCESS (code {result.get('code')})")
                        if 'path' in result:
                            print(f"    Path: {result.get('path')}")
                        if 'bytes_written' in result:
                            print(f"    Bytes Written: {result.get('bytes_written')}")
                    else:
                        print(f"    Status: ❌ FAILED (code {result.get('code')})")
                        print(f"    Error: {result.get('error')}")
            else:
                print("⚠️  No tools were executed")
            
            # Check if the file was actually created
            print("\n" + "=" * 70)
            print("Verifying File Creation")
            print("=" * 70 + "\n")
            
            verify_query = "list all files in the mcp_sandbox directory"
            verify_response = requests.post(
                f"{BASE_URL}/query",
                json={"user_query": verify_query},
                timeout=30
            )
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                answer = verify_data.get('final_answer', '')
                
                if "FastAPI.py" in answer or "FastAPI" in answer:
                    print("✅ FastAPI.py file was successfully created!")
                    print(f"\nAnswer: {answer}")
                    return True
                else:
                    print("⚠️  FastAPI.py file was not found in the list")
                    print(f"\nAnswer: {answer}")
                    return False
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_file_creation()
    
    print("\n" + "=" * 70)
    print("TEST RESULT")
    print("=" * 70)
    
    if success:
        print("✅ File creation test PASSED")
    else:
        print("❌ File creation test FAILED or inconclusive")
