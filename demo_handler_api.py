#!/usr/bin/env python3
"""
Demo: Handler API Endpoint

Demonstrates the POST /api/handler endpoint with live examples.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from libs.tool_runner import tool

@tool(schema={"x": int, "y": int}, description="Add two numbers")
def add(x: int, y: int):
    return {"sum": x + y}

@tool(schema={"text": str}, description="Convert to uppercase")
def uppercase(text: str):
    return {"original": text, "uppercase": text.upper()}

@tool(schema={"name": str, "age": int}, description="Create user")
def create_user(name: str, age: int):
    return {"user_id": hash(name) % 10000, "name": name, "age": age}

from fastapi.testclient import TestClient
from godman_ai.server.api import app
import json

client = TestClient(app)

def demo(title, request_data):
    print(f"\n{'='*60}\n{title}\n{'='*60}")
    print(f"Request: {json.dumps(request_data, indent=2)}")
    response = client.post("/api/handler", json=request_data)
    print(f"Response ({response.status_code}): {json.dumps(response.json(), indent=2)}")

print("\n" + "#"*60)
print("Handler API Demo")
print("#"*60)

demo("1. Add Numbers", {"function": "add", "parameters": {"x": 42, "y": 58}})
demo("2. Uppercase Text", {"function": "uppercase", "parameters": {"text": "hello"}})
demo("3. Create User", {"function": "create_user", "parameters": {"name": "Alice", "age": 28}})
demo("4. Function Not Found", {"function": "missing", "parameters": {}})

print(f"\n{'='*60}\nList Tools\n{'='*60}")
response = client.get("/api/handler/tools")
print(f"Available: {response.json()['count']} tools")
for name in response.json()['tools'].keys():
    print(f"  - {name}")

print(f"\n{'='*60}\nDemo Complete!\n{'='*60}\n")
