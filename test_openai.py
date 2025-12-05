#!/usr/bin/env python3
"""Quick test of OpenAI API integration."""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

print("=" * 60)
print("OpenAI Configuration Test")
print("=" * 60)

if not api_key or api_key == 'your_openai_api_key_here':
    print("✗ API key not configured")
    exit(1)

print(f"✓ API key loaded: {api_key[:20]}...")
print(f"✓ Model: {model}")
print()

# Test API connection
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    print("Testing API connection...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Reply with just the word 'SUCCESS' if you receive this."}
        ],
        max_tokens=10
    )
    
    result = response.choices[0].message.content.strip()
    print(f"✓ API Response: {result}")
    print()
    print("=" * 60)
    print("✅ OpenAI API is working correctly!")
    print("=" * 60)
    print()
    print("You're ready to process receipts with AI-powered extraction.")
    print("Cost: ~$0.01-0.05 per receipt with gpt-4o-mini")
    
except ImportError:
    print("✗ OpenAI library not installed")
    print("Run: pip install openai")
    exit(1)
except Exception as e:
    print(f"✗ API Error: {e}")
    print()
    print("Troubleshooting:")
    print("1. Verify API key at: https://platform.openai.com/api-keys")
    print("2. Check you have credits: https://platform.openai.com/usage")
    print("3. Make sure key starts with 'sk-' or 'sk-proj-'")
    exit(1)
