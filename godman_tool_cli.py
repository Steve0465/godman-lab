#!/usr/bin/env python3
"""
Demo script: Register tools then use CLI to execute them

This demonstrates the proper workflow:
1. Register tools using @tool decorator
2. Import the tools module to make them available
3. Use the CLI to execute registered tools
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Register sample tools using the global runner
from libs.tool_runner import tool, runner

print("Registering sample tools...")

@tool(
    schema={"name": str, "count": int},
    description="Greet someone multiple times"
)
def greet(name: str, count: int = 1):
    """Greet someone with a friendly message"""
    greeting = f"Hello {name}! "
    return {"message": greeting * count, "count": count}


@tool(
    schema={"x": int, "y": int},
    description="Add two numbers together"
)
def add(x: int, y: int):
    """Add two integers and return the sum"""
    return {"sum": x + y, "operands": [x, y]}


@tool(
    schema={"x": int, "y": int},
    description="Multiply two numbers"
)
def multiply(x: int, y: int):
    """Multiply two integers"""
    return {"product": x * y, "operands": [x, y]}


@tool(
    schema={"data": list},
    description="Calculate statistics on a list of numbers"
)
def stats(data: list):
    """Calculate count, sum, average, min, max for a list"""
    return {
        "count": len(data),
        "sum": sum(data),
        "average": sum(data) / len(data) if data else 0,
        "min": min(data) if data else None,
        "max": max(data) if data else None
    }


@tool(
    schema={"text": str},
    description="Convert text to uppercase"
)
def uppercase(text: str):
    """Convert a string to uppercase"""
    return {"original": text, "uppercase": text.upper()}


@tool(
    schema={"path": str},
    command="ls -la {path}",
    description="List files in a directory"
)
def list_files(path: str):
    """List files using ls -la command"""
    pass


@tool(
    schema={"pattern": str, "path": str},
    command="find {path} -name '*{pattern}*' -type f",
    description="Find files by pattern"
)
def find_files(pattern: str, path: str):
    """Find files matching a pattern"""
    pass


print(f"✓ Registered {len(runner.list_tools())} tools\n")

# Now import and run the CLI
from cli.godman.tools import app

if __name__ == "__main__":
    # Run the Typer app
    app()
