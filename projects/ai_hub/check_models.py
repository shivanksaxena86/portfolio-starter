import os

import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load your API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env file.")
else:
    print(f"✅ Found API Key: {api_key[:10]}...")

    # 2. Configure Google AI
    genai.configure(api_key=api_key)

    print("\n🔍 Fetching available models from Google...")
    try:
        # 3. List models
        for m in genai.list_models():
            # We only care about models that can 'generateContent' (Chat models)
            if "generateContent" in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"❌ Error fetching models: {e}")
