import os
from dotenv import load_dotenv
import requests

load_dotenv()

print("=" * 70)
print("🧪 TESTING ALL FREE LLM API KEYS")
print("=" * 70)

results = []

# ==================== 1. GROQ ====================
print("\n1️⃣  Testing GROQ API...")
groq_key = os.getenv("GROQ_API_KEY")

if not groq_key:
    print("   ❌ GROQ_API_KEY not found in .env")
    results.append(("Groq", False, "No API key"))
else:
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say 'Groq works!'"}],
            max_tokens=20
        )
        
        message = response.choices[0].message.content
        print(f"   ✅ SUCCESS: {message}")
        results.append(("Groq (Llama 3.3 70B)", True, "30 req/min, 14,400/day"))
        
    except ImportError:
        print("   ⚠️  Groq library not installed")
        print("   💡 Install: pip install groq")
        results.append(("Groq", False, "Library not installed"))
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)[:100]}")
        results.append(("Groq", False, str(e)[:50]))

# ==================== 2. GITHUB MODELS ====================
print("\n2️⃣  Testing GITHUB MODELS API...")
github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")

if not github_token:
    print("   ❌ GITHUB_TOKEN not found in .env")
    results.append(("GitHub Models", False, "No API key"))
else:
    try:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Say 'GitHub works!'"}],
                "max_tokens": 20
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content']
            print(f"   ✅ SUCCESS: {message}")
            results.append(("GitHub Models (GPT-4o-mini)", True, "15 req/min"))
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
            print(f"   🔍 Error: {response.text[:100]}")
            results.append(("GitHub Models", False, f"HTTP {response.status_code}"))
            
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)[:100]}")
        results.append(("GitHub Models", False, str(e)[:50]))

# ==================== 3. GEMINI (if still available) ====================
print("\n3️⃣  Testing GEMINI API...")
gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not gemini_key:
    print("   ⚠️  GEMINI_API_KEY not found (expected)")
    results.append(("Gemini", False, "No API key"))
else:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say 'Gemini works!'")
        
        print(f"   ✅ SUCCESS: {response.text}")
        results.append(("Gemini 1.5 Flash", True, "15 req/min (may have limits)"))
        
    except ImportError:
        print("   ⚠️  Gemini library not installed")
        results.append(("Gemini", False, "Library not installed"))
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            print(f"   ⚠️  RATE LIMITED: {error_msg[:100]}")
            results.append(("Gemini", False, "Rate limited"))
        else:
            print(f"   ❌ FAILED: {error_msg[:100]}")
            results.append(("Gemini", False, error_msg[:50]))

# ==================== SUMMARY ====================
print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)

working = [r for r in results if r[1]]
failing = [r for r in results if not r[1]]

print(f"\n✅ WORKING APIs: {len(working)}/{len(results)}")
for name, _, details in working:
    print(f"   • {name} - {details}")

if failing:
    print(f"\n❌ NOT WORKING: {len(failing)}")
    for name, _, reason in failing:
        print(f"   • {name} - {reason}")

print("\n" + "=" * 70)
print("💡 RECOMMENDATION")
print("=" * 70)

if len(working) >= 2:
    print("✅ You have multiple working APIs - PERFECT!")
    print("💡 Use Groq as primary, GitHub Models as backup")
elif len(working) == 1:
    print(f"⚠️  Only {working[0][0]} is working")
    print("💡 Set up more APIs for reliability")
else:
    print("❌ No working APIs found!")
    print("💡 Check your API keys and network connection")

print()
