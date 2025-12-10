#!/usr/bin/env python3
"""
Test suite for ToolRunner

Tests:
- Function registration
- Parameter validation
- Function execution
- Command execution
- Error handling
- Logging
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from libs.tool_runner import ToolRunner


def test_function_registration():
    """Test @tool decorator registration"""
    print("\n1. Testing Function Registration")
    print("-" * 50)
    
    runner = ToolRunner()
    
    @runner.tool(
        schema={"name": str, "count": int},
        description="Greet someone multiple times"
    )
    def greet(name: str, count: int = 1):
        return {"message": f"Hello {name}! " * count}
    
    tools = runner.list_tools()
    assert "greet" in tools
    assert tools["greet"]["schema"]["name"] == "str"
    assert tools["greet"]["schema"]["count"] == "int"
    print(f"✓ Registered tool: {tools['greet']['name']}")
    print(f"  Schema: {tools['greet']['schema']}")
    print(f"  Description: {tools['greet']['description']}")


def test_function_execution():
    """Test Python function execution"""
    print("\n2. Testing Function Execution")
    print("-" * 50)
    
    runner = ToolRunner()
    
    @runner.tool(schema={"x": int, "y": int})
    def add(x: int, y: int):
        """Add two numbers"""
        return {"sum": x + y}
    
    result = runner.run("add", {"x": 5, "y": 3})
    
    assert result["status"] == "success"
    assert result["result"]["sum"] == 8
    assert "execution_time" in result
    assert "timestamp" in result
    
    print(f"✓ Status: {result['status']}")
    print(f"  Result: {result['result']}")
    print(f"  Execution time: {result['execution_time']}s")


def test_parameter_validation():
    """Test parameter schema validation"""
    print("\n3. Testing Parameter Validation")
    print("-" * 50)
    
    runner = ToolRunner()
    
    @runner.tool(schema={"name": str, "age": int})
    def create_user(name: str, age: int):
        return {"user": name, "age": age}
    
    # Valid parameters
    result = runner.run("create_user", {"name": "Alice", "age": 30})
    assert result["status"] == "success"
    print(f"✓ Valid params: {result['status']}")
    
    # Invalid type
    result = runner.run("create_user", {"name": "Bob", "age": "thirty"})
    assert result["status"] == "error"
    assert "must be int" in result["error"]["message"]
    print(f"✓ Invalid type detected: {result['error']['type']}")


def test_command_execution():
    """Test shell command execution"""
    print("\n4. Testing Command Execution")
    print("-" * 50)
    
    runner = ToolRunner()
    
    @runner.tool(
        schema={"path": str},
        command="ls -la {path}",
        description="List directory contents"
    )
    def list_files(path: str):
        pass
    
    result = runner.run("list_files", {"path": "."})
    
    assert result["status"] == "success"
    assert "stdout" in result["result"]
    assert result["result"]["returncode"] == 0
    
    print(f"✓ Status: {result['status']}")
    print(f"  Return code: {result['result']['returncode']}")
    print(f"  Output lines: {len(result['result']['stdout'].splitlines())}")


def test_command_failure():
    """Test command execution failure handling"""
    print("\n5. Testing Command Failure Handling")
    print("-" * 50)
    
    runner = ToolRunner()
    
    @runner.tool(
        schema={"path": str},
        command="ls {path}",
        description="List non-existent directory"
    )
    def list_bad_path(path: str):
        pass
    
    result = runner.run("list_bad_path", {"path": "/nonexistent/path"})
    
    assert result["status"] == "error"
    print(f"✓ Status: {result['status']}")
    print(f"  Error type: {result['error']['type']}")
    print(f"  Error message: {result['error']['message'][:80]}...")


def test_error_handling():
    """Test exception handling in functions"""
    print("\n6. Testing Error Handling")
    print("-" * 50)
    
    runner = ToolRunner()
    
    @runner.tool(schema={"x": int, "y": int})
    def divide(x: int, y: int):
        """Divide two numbers"""
        return {"result": x / y}
    
    # Division by zero
    result = runner.run("divide", {"x": 10, "y": 0})
    
    assert result["status"] == "error"
    assert result["error"]["type"] == "ZeroDivisionError"
    
    print(f"✓ Caught exception: {result['error']['type']}")
    print(f"  Error message: {result['error']['message']}")


def test_unregistered_function():
    """Test calling unregistered function"""
    print("\n7. Testing Unregistered Function")
    print("-" * 50)
    
    runner = ToolRunner()
    
    result = runner.run("nonexistent_function", {})
    
    assert result["status"] == "error"
    assert "not registered" in result["error"]["message"]
    
    print(f"✓ Status: {result['status']}")
    print(f"  Error: {result['error']['message']}")


def test_get_tool_info():
    """Test retrieving tool information"""
    print("\n8. Testing Tool Info Retrieval")
    print("-" * 50)
    
    runner = ToolRunner()
    
    @runner.tool(
        schema={"text": str, "count": int},
        description="Echo text multiple times"
    )
    def echo(text: str, count: int = 1):
        return {"output": text * count}
    
    info = runner.get_tool_info("echo")
    
    assert info is not None
    assert info["name"] == "echo"
    assert info["description"] == "Echo text multiple times"
    assert "text" in info["schema"]
    
    print(f"✓ Tool name: {info['name']}")
    print(f"  Description: {info['description']}")
    print(f"  Schema: {info['schema']}")


def test_logging():
    """Test that logs are written"""
    print("\n9. Testing Logging")
    print("-" * 50)
    
    log_path = Path.home() / "godman-lab" / "logs" / "tool_runner.log"
    
    # Get initial log size
    initial_size = log_path.stat().st_size if log_path.exists() else 0
    
    runner = ToolRunner()
    
    @runner.tool(schema={"msg": str})
    def log_test(msg: str):
        return {"logged": msg}
    
    runner.run("log_test", {"msg": "test message"})
    
    # Check log file grew
    final_size = log_path.stat().st_size
    assert final_size > initial_size
    
    # Read last few lines
    with open(log_path, 'r') as f:
        lines = f.readlines()
        last_lines = lines[-5:]
    
    print(f"✓ Log file: {log_path}")
    print(f"  Size increase: {final_size - initial_size} bytes")
    print(f"  Last log entries:")
    for line in last_lines:
        print(f"    {line.strip()}")


def test_complex_workflow():
    """Test a complex multi-step workflow"""
    print("\n10. Testing Complex Workflow")
    print("-" * 50)
    
    runner = ToolRunner()
    
    @runner.tool(schema={"text": str})
    def uppercase(text: str):
        """Convert text to uppercase"""
        return {"result": text.upper()}
    
    @runner.tool(schema={"text": str})
    def word_count(text: str):
        """Count words in text"""
        return {"count": len(text.split())}
    
    @runner.tool(schema={"a": int, "b": int, "c": int})
    def sum_three(a: int, b: int, c: int):
        """Sum three numbers"""
        return {"total": a + b + c}
    
    # Execute workflow
    step1 = runner.run("uppercase", {"text": "hello world"})
    step2 = runner.run("word_count", {"text": "hello world from python"})
    step3 = runner.run("sum_three", {"a": 10, "b": 20, "c": 30})
    
    assert step1["status"] == "success"
    assert step1["result"]["result"] == "HELLO WORLD"
    
    assert step2["status"] == "success"
    assert step2["result"]["count"] == 4
    
    assert step3["status"] == "success"
    assert step3["result"]["total"] == 60
    
    print(f"✓ Step 1: {step1['result']}")
    print(f"✓ Step 2: {step2['result']}")
    print(f"✓ Step 3: {step3['result']}")
    
    total_time = (
        step1["execution_time"] + 
        step2["execution_time"] + 
        step3["execution_time"]
    )
    print(f"  Total execution time: {total_time:.3f}s")


def run_all_tests():
    """Run all test suites"""
    print("="*50)
    print("ToolRunner Test Suite")
    print("="*50)
    
    tests = [
        test_function_registration,
        test_function_execution,
        test_parameter_validation,
        test_command_execution,
        test_command_failure,
        test_error_handling,
        test_unregistered_function,
        test_get_tool_info,
        test_logging,
        test_complex_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ FAILED: {test.__name__}")
            print(f"  {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ ERROR: {test.__name__}")
            print(f"  {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
