import os
from dotenv import load_dotenv
import time

load_dotenv()

print("=" * 60)
print("⏰ RATE LIMIT STATUS CHECK")
print("=" * 60)

# Check Groq
try:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print("✅ GROQ: Ready to use")
except Exception as e:
    if "429" in str(e):
        print("⏰ GROQ: Rate limited - wait 60 seconds")
    else:
        print(f"❌ GROQ: {str(e)[:50]}")

# Wait a moment
time.sleep(1)

# Check GitHub Models
try:
    import requests
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://models.inference.ai.azure.com/chat/completions",
        headers=headers,
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5
        },
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ GITHUB MODELS: Ready to use")
    elif response.status_code == 429:
        print("⏰ GITHUB MODELS: Rate limited - wait 60 seconds")
    else:
        print(f"❌ GITHUB MODELS: HTTP {response.status_code}")
except Exception as e:
    print(f"❌ GITHUB MODELS: {str(e)[:50]}")

print("\n" + "=" * 60)
print("💡 RECOMMENDATION:")
print("   Wait 1 minute, then both should work again")
print("=" * 60)
