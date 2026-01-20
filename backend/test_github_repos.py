#!/usr/bin/env python3
"""Quick test script for the GitHub repos query."""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_github_repos_query():
    """Test listing GitHub repositories."""
    
    print("\n" + "=" * 70)
    print("🧪 Testing GitHub Repos Query")
    print("=" * 70 + "\n")
    
    query = {
        "user_query": "List all my github repositories",
        "session_id": "test_session"
    }
    
    print(f"📤 Sending query: {query['user_query']}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json=query,
            timeout=60
        )
        
        print(f"✅ Response Status: {response.status_code}\n")
        
        result = response.json()
        
        print("📋 FINAL ANSWER:")
        print("-" * 70)
        print(result.get("final_answer", "No answer"))
        print("-" * 70)
        
        tool_calls = result.get("tool_calls_executed", [])
        if tool_calls:
            print(f"\n🛠️  Tools Executed ({len(tool_calls)}):")
            for i, call in enumerate(tool_calls, 1):
                print(f"\n   {i}. {call['server']}.{call['tool']}")
                if 'result' in call:
                    res_str = json.dumps(call['result'], indent=6)
                    if len(res_str) > 300:
                        print(f"      {res_str[:300]}...")
                    else:
                        print(f"      {res_str}")
        
        print("\n" + "=" * 70)
        print("✅ Test completed successfully!")
        print("=" * 70 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to backend")
        print("   Make sure to run: python server.py")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_github_repos_query()
