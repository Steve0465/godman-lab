#!/usr/bin/env python3
"""
Direct chat interface to your LOCAL uncensored model.
No GitHub. No restrictions. Just you and the model.
"""
import requests
import json

MODEL = "dolphin-llama3:8b"  # Uncensored Dolphin-Llama3 - Smart & Unrestricted!
OLLAMA_URL = "http://localhost:11434/api/generate"

def chat():
    print(f"🐬 Connected to LOCAL MODEL: {MODEL}")
    print("=" * 60)
    print("You are now talking to YOUR uncensored local AI.")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            break
            
        try:
            response = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "prompt": user_input,
                "stream": False
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n🤖 Local AI: {result['response']}\n")
            else:
                print(f"Error: {response.status_code}")
                
        except Exception as e:
            print(f"Connection error: {e}")
            print("Make sure Ollama is running: ollama serve")

if __name__ == "__main__":
    chat()
