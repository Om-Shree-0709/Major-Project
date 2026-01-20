import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

print("=" * 60)
print("🧪 TESTING GITHUB MODELS API")
print("=" * 60)

# 1. Get Key
api_key = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
print(f"\n🔑 API Key Found: {'✅ Yes' if api_key else '❌ No'}")

if not api_key:
    print("❌ Error: No API Key in .env")
    print("💡 Add GITHUB_TOKEN=your_token to backend/.env")
    exit(1)

print(f"🔑 Key Preview: {api_key[:10]}...{api_key[-4:]}")

# 2. Prepare request
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

test_payload = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'GitHub Models is working!' and nothing else."}
    ],
    "temperature": 0.7,
    "max_tokens": 50
}

print(f"\n📡 Endpoint: https://models.inference.ai.azure.com/chat/completions")
print(f"🤖 Model: gpt-4o-mini")
print(f"\n⏳ Sending request...\n")

# 3. Make request
try:
    response = requests.post(
        "https://models.inference.ai.azure.com/chat/completions",
        headers=headers,
        json=test_payload,
        timeout=30
    )
    
    print(f"📊 Status Code: {response.status_code}")
    
    # Check if successful
    if response.status_code == 200:
        print("✅ SUCCESS! GitHub Models is working!\n")
        
        data = response.json()
        
        # Extract response
        if 'choices' in data and len(data['choices']) > 0:
            message = data['choices'][0]['message']['content']
            print("🤖 AI Response:")
            print(f"   {message}")
            print()
            
            # Show usage stats
            if 'usage' in data:
                usage = data['usage']
                print("📊 Token Usage:")
                print(f"   Input: {usage.get('prompt_tokens', 'N/A')}")
                print(f"   Output: {usage.get('completion_tokens', 'N/A')}")
                print(f"   Total: {usage.get('total_tokens', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("✅ GITHUB MODELS API: WORKING PERFECTLY")
        print("=" * 60)
        
    elif response.status_code == 401:
        print("❌ AUTHENTICATION FAILED")
        print("💡 Your GitHub token might be invalid or expired")
        print("📝 Generate new token at: https://github.com/settings/tokens")
        print(f"\n🔍 Error Details: {response.text}")
        
    elif response.status_code == 403:
        print("❌ ACCESS FORBIDDEN")
        print("💡 GitHub Models might not be enabled for your account")
        print("📝 Try accessing: https://github.com/marketplace/models")
        print(f"\n🔍 Error Details: {response.text}")
        
    elif response.status_code == 429:
        print("⏰ RATE LIMIT EXCEEDED")
        print("💡 Wait a few moments and try again")
        print(f"\n🔍 Error Details: {response.text}")
        
    else:
        print(f"⚠️  UNEXPECTED STATUS: {response.status_code}")
        print(f"\n🔍 Response Body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)

except requests.exceptions.Timeout:
    print("❌ REQUEST TIMEOUT")
    print("💡 The API took too long to respond. Try again.")
    
except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR")
    print("💡 Check your internet connection")
    
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {type(e).__name__}")
    print(f"💡 Details: {str(e)}")

print()
