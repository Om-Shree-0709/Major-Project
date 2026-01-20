#!/usr/bin/env python3
"""
Example Usage Script for the Unified MCP Framework with Swarm Intelligence

This script demonstrates how to use the backend API for various query types.
Run the backend first: python server.py
"""
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

# ==================== HELPER FUNCTIONS ====================

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def submit_query(query: str, session_id: str = "demo") -> Dict[str, Any]:
    """
    Submit a query to the backend and get the response.
    
    Args:
        query: The user query
        session_id: Optional session identifier
    
    Returns:
        The API response as a dictionary
    """
    url = f"{BASE_URL}/query"
    payload = {
        "user_query": query,
        "session_id": session_id
    }
    
    print(f"📤 Submitting query: {query}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=300)  # 5 min timeout
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to backend at", BASE_URL)
        print("   Make sure to run: python server.py")
        return None
    except requests.exceptions.Timeout:
        print("⏱️  ERROR: Request timed out (API call took too long)")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

def display_response(response: Dict[str, Any]):
    """Display the API response in a readable format."""
    if not response:
        return
    
    print("📋 RESPONSE:")
    print("-" * 70)
    
    # Display final answer
    final_answer = response.get("final_answer", "No answer provided")
    print(f"\n🎯 FINAL ANSWER:\n{final_answer}\n")
    
    # Display tool calls
    tool_calls = response.get("tool_calls_executed", [])
    if tool_calls:
        print(f"🛠️  TOOLS EXECUTED ({len(tool_calls)}):")
        for i, call in enumerate(tool_calls, 1):
            print(f"\n   {i}. {call['server']}.{call['tool']}")
            if 'result' in call:
                result_str = json.dumps(call['result'], indent=6)[:300]
                print(f"      Result: {result_str}...")
    else:
        print("🛠️  No tools were needed for this query")

def check_health():
    """Check if the backend is healthy."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

# ==================== DEMO QUERIES ====================

def demo_simple_query():
    """Simple query that uses basic reasoning."""
    print_header("1️⃣  SIMPLE QUERY - Basic Reasoning")
    
    query = "What are the top 3 benefits of using Python for web development?"
    response = submit_query(query)
    display_response(response)
    time.sleep(2)

def demo_research_query():
    """Query that requires research using Browser MCP Server."""
    print_header("2️⃣  RESEARCH QUERY - Using Browser MCP Server")
    
    query = "Search for the latest trends in Python web frameworks in 2025 and provide a brief summary"
    response = submit_query(query)
    display_response(response)
    time.sleep(2)

def demo_code_query():
    """Query that requires code implementation using Filesystem MCP Server."""
    print_header("3️⃣  CODE IMPLEMENTATION QUERY - Using Filesystem MCP Server")
    
    query = """Create a Python script in the sandbox that:
    1. Defines a function to calculate fibonacci numbers
    2. Tests it with input 10
    3. Saves the output to a file called 'fibonacci_result.txt'
    """
    response = submit_query(query)
    display_response(response)
    time.sleep(2)

def demo_complex_query():
    """Complex query requiring multiple personas and all 3 MCP servers."""
    print_header("4️⃣  COMPLEX QUERY - Multi-Persona Coordination")
    
    query = """Complete this full workflow:
    1. Research: Find information about common Python asyncio pitfalls in 2025
    2. Implement: Create a well-documented async Python example that avoids these pitfalls
    3. Save: Write the code to sandbox/async_best_practices.py
    """
    response = submit_query(query)
    display_response(response)
    time.sleep(2)

def demo_github_query():
    """Query that uses GitHub MCP Server for repository operations."""
    print_header("5️⃣  GITHUB OPERATIONS QUERY - Using GitHub MCP Server")
    
    query = """List my recent repositories and provide:
    1. Repository names
    2. Brief descriptions
    3. Programming languages used
    """
    response = submit_query(query)
    display_response(response)
    time.sleep(2)

# ==================== CUSTOM QUERY ====================

def demo_custom_query():
    """Allow user to input a custom query."""
    print_header("🎯 CUSTOM QUERY")
    
    print("Enter your query (or 'skip' to skip):")
    print("Examples:")
    print("  - 'Search for Python async best practices'")
    print("  - 'Create a Python file with a class to calculate prime numbers'")
    print("  - 'Research FastAPI and create example code'")
    print()
    
    query = input("Your query: ").strip()
    
    if query.lower() != "skip" and query:
        response = submit_query(query)
        display_response(response)
    else:
        print("Skipped custom query")

# ==================== MAIN ====================

def main():
    """Run the demo."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 10 + "🚀 UNIFIED MCP FRAMEWORK - EXAMPLE USAGE" + " " * 17 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # Check health
    print("\n⏳ Checking backend health...", end=" ")
    if not check_health():
        print("\n❌ Backend is not running!")
        print("   Please run: python server.py")
        return
    print("✅ Backend is running!\n")
    
    # Run demos
    print("This script demonstrates 5 example queries:")
    print("  1️⃣  Simple Query - Basic reasoning")
    print("  2️⃣  Research Query - Uses Browser MCP Server")
    print("  3️⃣  Code Implementation - Uses Filesystem MCP Server")
    print("  4️⃣  Complex Multi-Persona - Uses multiple servers")
    print("  5️⃣  GitHub Operations - Uses GitHub MCP Server")
    print("  🎯 Custom Query - Enter your own\n")
    
    try:
        # Demo 1: Simple
        demo_simple_query()
        
        # Demo 2: Research
        demo_research_query()
        
        # Demo 3: Code
        demo_code_query()
        
        # Demo 4: Complex
        demo_complex_query()
        
        # Demo 5: GitHub
        demo_github_query()
        
        # Custom
        demo_custom_query()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    
    print("\n" + "=" * 70)
    print("✅ Demo completed!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
