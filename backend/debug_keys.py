import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 1. Get Key
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
print(f"🔑 API Key Found: {'Yes' if api_key else 'No'}")

if not api_key:
    print("❌ Error: No API Key in .env")
    exit()

# 2. Configure
try:
    genai.configure(api_key=api_key)
    print("✅ Google AI Configured.")
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    exit()

# 3. List Models
print("\n📋 Listing Available Models for your Key:")
try:
    found_any = False
    for m in genai.list_models():
        found_any = True
        print(f"   - Name: {m.name}")
        print(f"     Methods: {m.supported_generation_methods}")
    
    if not found_any:
        print("⚠️ No models found! Check if 'Generative Language API' is enabled in Google Cloud Console.")
except Exception as e:
    print(f"❌ API Connection Error: {e}")