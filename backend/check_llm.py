"""Quick script to verify the Gemini chat integration."""

print("🚀 Script started!")

import os
import sys

print("✅ Imports successful")

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env loaded")
except Exception as e:
    print(f"❌ Error loading .env: {e}")
    sys.exit(1)

# Check API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    print("\nYour .env should contain:")
    print("GEMINI_API_KEY=your-key-here")
    sys.exit(1)

print(f"✅ API Key found: {api_key[:20]}...")

# List models if requested
if len(sys.argv) > 1 and sys.argv[1] == "--list-models":
    try:
        print("\n🔍 Connecting to Google AI...")
        from google import genai
        
        client = genai.Client(api_key=api_key)
        print("✅ Client created")
        
        print("\n📋 Listing models...")
        models = list(client.models.list())
        
        print(f"\nFound {len(models)} models:")
        for model in models:
            print(f"   ✓ {model.name}")
        
        print("\n💡 Recommended: gemini-2.5-flash")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0)

# Test chat
print("\n🤖 Testing chat...\n")

try:
    from services.llm_service import generate_chat_response
    print("✅ llm_service imported")
    
    messages = [{"role": "user", "content": "Say hello in one sentence"}]
    print("✅ Messages created")
    
    print("🔄 Calling Gemini API...")
    reply = generate_chat_response(messages)
    
    print(f"\n📨 Reply: {reply}\n")
    
    if "Sorry" in reply or "unable" in reply:
        print("❌ Test FAILED")
    else:
        print("✅ Test SUCCESSFUL!")
        
except Exception as e:
    print(f"\n❌ Error during chat test: {e}")
    import traceback
    traceback.print_exc()