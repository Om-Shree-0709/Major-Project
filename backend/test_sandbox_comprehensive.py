#!/usr/bin/env python3
"""
Comprehensive Test: File Creation and Retrieval in Sandbox
Verifies that files are correctly created in backend/mcp_sandbox/
"""

import sys
from pathlib import Path
from filesystem_server import FilesystemMCPServer

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_sandbox_path():
    """Test 1: Verify sandbox path is correct"""
    print_section("TEST 1: Sandbox Path Configuration")
    
    from filesystem_server import SANDBOX_DIR
    print(f"✅ Sandbox Directory: {SANDBOX_DIR}")
    print(f"✅ Exists: {SANDBOX_DIR.exists()}")
    print(f"✅ Is Directory: {SANDBOX_DIR.is_dir()}")
    print(f"✅ Path Type: {type(SANDBOX_DIR)}")

def test_file_write():
    """Test 2: Write a file"""
    print_section("TEST 2: File Write Operation")
    
    fs = FilesystemMCPServer()
    
    test_content = """# Test News File

## Bollywood Latest
- News Item 1
- News Item 2

## Tech News
- Breaking news from TechCrunch
- AI developments
"""
    
    result = fs.execute_tool("filesystem.write_file", {
        "path": "news_test.txt",
        "content": test_content
    })
    
    print(f"Write Result: {result}")
    
    if result.get("code") == 200:
        print(f"✅ File created successfully: {result['path']}")
        print(f"✅ Bytes written: {result['bytes_written']}")
        return True
    else:
        print(f"❌ Write failed: {result.get('error')}")
        return False

def test_file_read():
    """Test 3: Read the file back"""
    print_section("TEST 3: File Read Operation")
    
    fs = FilesystemMCPServer()
    
    result = fs.execute_tool("filesystem.read_file", {
        "path": "news_test.txt"
    })
    
    if result.get("code") == 200:
        print(f"✅ File read successfully")
        print(f"✅ Path: {result['path']}")
        print(f"✅ Content Preview (first 200 chars):\n")
        print(result['content'][:200])
        return True
    else:
        print(f"❌ Read failed: {result.get('error')}")
        return False

def test_file_existence():
    """Test 4: Verify file exists on disk"""
    print_section("TEST 4: Disk File Verification")
    
    from filesystem_server import SANDBOX_DIR
    
    file_path = SANDBOX_DIR / "news_test.txt"
    
    print(f"Full path: {file_path}")
    print(f"✅ File exists on disk: {file_path.exists()}")
    
    if file_path.exists():
        print(f"✅ File size: {file_path.stat().st_size} bytes")
        print(f"✅ Can read from disk: {file_path.is_file()}")
        return True
    else:
        print(f"❌ File not found at {file_path}")
        return False

def main():
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  SANDBOX FILE CREATION TEST SUITE".center(58) + "║")
    print("║" + "  Verifying backend/mcp_sandbox/ configuration".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    try:
        test_sandbox_path()
        
        if test_file_write() and test_file_read() and test_file_existence():
            print_section("✅ ALL TESTS PASSED")
            print("Files are being created correctly in backend/mcp_sandbox/")
            print("The fix is working as expected!")
            return 0
        else:
            print_section("❌ SOME TESTS FAILED")
            return 1
            
    except Exception as e:
        print_section("❌ ERROR DURING TESTS")
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
