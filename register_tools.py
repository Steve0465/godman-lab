#!/usr/bin/env python3
"""
Register sample tools for the API server
Run this to make tools available for the Handler endpoint
"""

from libs.tool_runner import tool

# Math operations
@tool(schema={"x": int, "y": int}, description="Add two numbers")
def add(x: int, y: int):
    return {"sum": x + y, "operands": [x, y]}

@tool(schema={"x": int, "y": int}, description="Subtract two numbers")
def subtract(x: int, y: int):
    return {"difference": x - y, "operands": [x, y]}

@tool(schema={"x": int, "y": int}, description="Multiply two numbers")
def multiply(x: int, y: int):
    return {"product": x * y, "operands": [x, y]}

# String operations
@tool(schema={"text": str}, description="Convert text to uppercase")
def uppercase(text: str):
    return {"original": text, "uppercase": text.upper()}

@tool(schema={"text": str}, description="Convert text to lowercase")
def lowercase(text: str):
    return {"original": text, "lowercase": text.lower()}

@tool(schema={"text": str}, description="Reverse text")
def reverse_text(text: str):
    return {"original": text, "reversed": text[::-1]}

# Data operations
@tool(schema={"items": list}, description="Calculate list statistics")
def calculate_stats(items: list):
    if not items:
        return {"count": 0, "sum": 0, "average": 0, "min": None, "max": None}
    return {
        "count": len(items),
        "sum": sum(items),
        "average": sum(items) / len(items),
        "min": min(items),
        "max": max(items)
    }

@tool(schema={"text": str}, description="Count words in text")
def word_count(text: str):
    words = text.split()
    return {"text": text, "word_count": len(words), "char_count": len(text)}

# User management
@tool(schema={"name": str, "age": int}, description="Create user profile")
def create_user(name: str, age: int):
    import time
    return {
        "user_id": abs(hash(name)) % 10000,
        "name": name,
        "age": age,
        "status": "active",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# System operations (command-based)
@tool(schema={"path": str}, command="ls -la {path}", description="List files in directory")
def list_files(path: str):
    pass

@tool(schema={"text": str}, command='echo "{text}"', description="Echo text to stdout")
def echo(text: str):
    pass

print("✓ Registered 11 tools for Handler API:")
print("  Math: add, subtract, multiply")
print("  String: uppercase, lowercase, reverse_text")
print("  Data: calculate_stats, word_count")
print("  User: create_user")
print("  System: list_files, echo")
