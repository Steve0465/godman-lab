#!/usr/bin/env python3
"""
ToolRunner Usage Examples

Demonstrates various usage patterns for the ToolRunner class.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from libs.tool_runner import ToolRunner


def example_basic_usage():
    """Basic function registration and execution"""
    print("\n" + "="*60)
    print("Example 1: Basic Usage")
    print("="*60)
    
    runner = ToolRunner()
    
    # Register a simple function
    @runner.tool(
        schema={"name": str, "age": int},
        description="Create a user profile"
    )
    def create_profile(name: str, age: int):
        return {
            "profile": {
                "name": name,
                "age": age,
                "status": "active"
            }
        }
    
    # Execute the function
    result = runner.run("create_profile", {"name": "Alice", "age": 30})
    
    print(f"Status: {result['status']}")
    print(f"Result: {result['result']}")
    print(f"Execution time: {result['execution_time']}s")


def example_command_execution():
    """Execute shell commands"""
    print("\n" + "="*60)
    print("Example 2: Command Execution")
    print("="*60)
    
    runner = ToolRunner()
    
    # Register a command
    @runner.tool(
        schema={"pattern": str, "path": str},
        command="grep -r '{pattern}' {path}",
        description="Search for pattern in files"
    )
    def search_files(pattern: str, path: str):
        pass
    
    # Execute command
    result = runner.run("search_files", {
        "pattern": "def",
        "path": "libs/"
    })
    
    if result["status"] == "success":
        print(f"Found matches:")
        print(result["result"]["stdout"][:500])
    else:
        print(f"Error: {result['error']}")


def example_python_script_execution():
    """Execute Python scripts as tools"""
    print("\n" + "="*60)
    print("Example 3: Python Script Execution")
    print("="*60)
    
    runner = ToolRunner()
    
    @runner.tool(
        schema={"script": str},
        command='python3 -c "{script}"',
        description="Execute Python code"
    )
    def run_python(script: str):
        pass
    
    result = runner.run("run_python", {
        "script": "print('Hello from inline Python!')"
    })
    
    print(f"Output: {result['result']['stdout'].strip()}")


def example_data_processing():
    """Chain multiple tools for data processing"""
    print("\n" + "="*60)
    print("Example 4: Data Processing Pipeline")
    print("="*60)
    
    runner = ToolRunner()
    
    @runner.tool(schema={"data": list})
    def filter_positive(data: list):
        """Filter positive numbers"""
        return {"filtered": [x for x in data if x > 0]}
    
    @runner.tool(schema={"data": list})
    def calculate_sum(data: list):
        """Calculate sum"""
        return {"sum": sum(data)}
    
    @runner.tool(schema={"data": list})
    def calculate_average(data: list):
        """Calculate average"""
        return {"average": sum(data) / len(data) if data else 0}
    
    # Process data through pipeline
    numbers = [-5, 10, -3, 20, 15, -1, 8]
    print(f"Original data: {numbers}")
    
    step1 = runner.run("filter_positive", {"data": numbers})
    filtered = step1["result"]["filtered"]
    print(f"After filter: {filtered}")
    
    step2 = runner.run("calculate_sum", {"data": filtered})
    print(f"Sum: {step2['result']['sum']}")
    
    step3 = runner.run("calculate_average", {"data": filtered})
    print(f"Average: {step3['result']['average']:.2f}")


def example_error_handling():
    """Demonstrate error handling"""
    print("\n" + "="*60)
    print("Example 5: Error Handling")
    print("="*60)
    
    runner = ToolRunner()
    
    @runner.tool(schema={"path": str})
    def read_file(path: str):
        """Read file contents"""
        with open(path, 'r') as f:
            return {"contents": f.read()}
    
    # Try reading non-existent file
    result = runner.run("read_file", {"path": "/nonexistent/file.txt"})
    
    if result["status"] == "error":
        print(f"Error type: {result['error']['type']}")
        print(f"Error message: {result['error']['message']}")
    
    # Try with wrong parameter type
    result = runner.run("read_file", {"path": 123})
    
    if result["status"] == "error":
        print(f"Validation error: {result['error']['message']}")


def example_list_tools():
    """List all registered tools"""
    print("\n" + "="*60)
    print("Example 6: List and Inspect Tools")
    print("="*60)
    
    runner = ToolRunner()
    
    @runner.tool(schema={"x": int}, description="Square a number")
    def square(x: int):
        return {"result": x ** 2}
    
    @runner.tool(schema={"text": str}, description="Count characters")
    def char_count(text: str):
        return {"count": len(text)}
    
    @runner.tool(
        schema={"dir": str},
        command="du -sh {dir}",
        description="Get directory size"
    )
    def dir_size(dir: str):
        pass
    
    # List all tools
    tools = runner.list_tools()
    print(f"Registered tools: {len(tools)}")
    
    for name, info in tools.items():
        print(f"\n  {name}:")
        print(f"    Description: {info['description']}")
        print(f"    Schema: {info['schema']}")
        print(f"    Command: {info['has_command']}")
    
    # Get detailed info
    print("\nDetailed info for 'square':")
    info = runner.get_tool_info("square")
    for key, value in info.items():
        print(f"  {key}: {value}")


def example_global_runner():
    """Use the global runner instance"""
    print("\n" + "="*60)
    print("Example 7: Global Runner Instance")
    print("="*60)
    
    from libs.tool_runner import tool, runner
    
    # Use global decorator
    @tool(schema={"msg": str}, description="Echo a message")
    def echo(msg: str):
        return {"echo": msg}
    
    # Use global runner
    result = runner.run("echo", {"msg": "Hello, World!"})
    print(f"Echo result: {result['result']}")


def main():
    """Run all examples"""
    print("\n" + "#"*60)
    print("# ToolRunner Usage Examples")
    print("#"*60)
    
    examples = [
        example_basic_usage,
        example_command_execution,
        example_python_script_execution,
        example_data_processing,
        example_error_handling,
        example_list_tools,
        example_global_runner
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nExample failed: {e}")
    
    print("\n" + "#"*60)
    print("# Examples completed")
    print("#"*60 + "\n")


if __name__ == "__main__":
    main()
