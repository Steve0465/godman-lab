#!/usr/bin/env python3
"""
Fun Demo: Natural Language to Function Calls
Using your Handler API!
"""

import requests
import json
from time import sleep

API_URL = "http://localhost:8000/api/handler"

def banner(text):
    """Print colorful banner"""
    import subprocess
    subprocess.run(f'figlet "{text}" | lolcat', shell=True)

def call_tool(function_name, parameters):
    """Call a tool via your Handler API"""
    response = requests.post(
        API_URL,
        json={"function": function_name, "parameters": parameters}
    )
    return response.json()

def demo():
    banner("GODMAN AI")
    print("\n🤖 Natural Language Function Calling Demo\n")
    print("━" * 60)
    
    # Demo 1: Math
    print("\n💡 Demo 1: Math Operations")
    print("   Request: 'Add 42 and 58'")
    sleep(1)
    result = call_tool("add", {"x": 42, "y": 58})
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Demo 2: String ops
    print("\n💡 Demo 2: String Operations")
    print("   Request: 'Make HELLO lowercase'")
    sleep(1)
    result = call_tool("lowercase", {"text": "HELLO"})
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Demo 3: Reverse
    print("\n💡 Demo 3: Text Manipulation")
    print("   Request: 'Reverse the text: Godman AI'")
    sleep(1)
    result = call_tool("reverse_text", {"text": "Godman AI"})
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Demo 4: Stats
    print("\n💡 Demo 4: Data Analysis")
    print("   Request: 'Calculate stats for [10, 20, 30, 40, 50]'")
    sleep(1)
    result = call_tool("calculate_stats", {"items": [10, 20, 30, 40, 50]})
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Demo 5: User creation
    print("\n💡 Demo 5: User Management")
    print("   Request: 'Create user Bob who is 35'")
    sleep(1)
    result = call_tool("create_user", {"name": "Bob", "age": 35})
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    print("\n━" * 60)
    print("\n✨ All demos completed!")
    print("🎮 Try it yourself at: http://localhost:8000\n")

if __name__ == "__main__":
    demo()
