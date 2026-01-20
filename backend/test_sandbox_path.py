#!/usr/bin/env python3
"""
Test: Verify file creation in correct sandbox directory
"""

from pathlib import Path
from filesystem_server import FilesystemMCPServer

def test_file_creation():
    """Test that files are created in backend/mcp_sandbox"""
    
    fs = FilesystemMCPServer()
    
    # Test writing a file
    result = fs.execute_tool("filesystem.write_file", {
        "path": "test_file.txt",
        "content": "This is a test file created on " + str(Path.cwd())
    })
    
    print("✅ Write File Result:")
    print(result)
    print()
    
    # List the files
    list_result = fs.execute_tool("filesystem.list_dir", {
        "path": ""
    })
    
    print("✅ Files in sandbox:")
    print(list_result)
    print()
    
    # Read the file back
    read_result = fs.execute_tool("filesystem.read_file", {
        "path": "test_file.txt"
    })
    
    print("✅ Read File Result:")
    print(read_result)

if __name__ == "__main__":
    test_file_creation()
