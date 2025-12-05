#!/usr/bin/env python3
"""Test script for local model integration"""

from godman_ai.models import LocalModelClient, HybridModelRouter

def main():
    print("🧪 Testing GodmanAI Local Model Integration\n")
    
    # Test 1: Check Ollama availability
    print("1️⃣ Checking Ollama availability...")
    client = LocalModelClient()
    if client.is_available():
        print("   ✅ Ollama is running!")
        
        # Test 2: List models
        print("\n2️⃣ Available models:")
        models = client.list_models()
        for model in models:
            print(f"   - {model}")
        
        # Test 3: Generate with uncensored model
        print("\n3️⃣ Testing uncensored model generation...")
        prompt = "List 3 creative automation ideas for a home lab system."
        print(f"   Prompt: {prompt}")
        print("   Generating...")
        
        response = client.generate(
            prompt=prompt,
            model="dolphin-llama3:8b",
            temperature=0.8
        )
        print(f"\n   Response:\n{response}\n")
        
        # Test 4: Hybrid router
        print("4️⃣ Testing hybrid router (prefer local)...")
        router = HybridModelRouter(prefer_local=True)
        response = router.route(
            task_type="chat",
            prompt="Say 'Local model working!' in a fun way"
        )
        print(f"   {response}\n")
        
        print("✅ All tests passed! Your local uncensored AI is ready.")
        
    else:
        print("   ❌ Ollama is not running")
        print("   Start it with: brew services start ollama")
        print("   Then pull a model: ollama pull dolphin-llama3:8b")

if __name__ == "__main__":
    main()
