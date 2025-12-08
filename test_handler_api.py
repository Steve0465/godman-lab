#!/usr/bin/env python3
"""
Test the Handler API endpoint

Tests the POST /api/handler endpoint with various scenarios including
function execution, validation, error handling, and edge cases.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from libs.tool_runner import tool, runner

# Register sample tools for testing
@tool(
    schema={"name": str, "count": int},
    description="Greet someone multiple times"
)
def greet(name: str, count: int = 1):
    greeting = f"Hello {name}! "
    return {"message": greeting * count, "count": count}


@tool(
    schema={"x": int, "y": int},
    description="Add two numbers"
)
def add(x: int, y: int):
    return {"sum": x + y, "operands": [x, y]}


@tool(
    schema={"x": int, "y": int},
    description="Divide two numbers"
)
def divide(x: int, y: int):
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return {"result": x / y, "operands": [x, y]}


@tool(
    schema={"path": str},
    command="ls -la {path}",
    description="List files in directory"
)
def list_files(path: str):
    pass


# Import app after tools are registered
from godman_ai.server.api import app

client = TestClient(app)


def test_handler_success():
    """Test successful function execution"""
    print("\n1. Testing Successful Execution")
    print("-" * 60)
    
    response = client.post(
        "/api/handler",
        json={"function": "add", "parameters": {"x": 5, "y": 3}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert data["result"]["sum"] == 8
    assert "execution_time" in data
    assert "timestamp" in data
    
    print(f"✓ Status: {response.status_code}")
    print(f"  Result: {data['result']}")
    print(f"  Execution time: {data['execution_time']}s")


def test_handler_with_multiple_params():
    """Test function with multiple parameters"""
    print("\n2. Testing Multiple Parameters")
    print("-" * 60)
    
    response = client.post(
        "/api/handler",
        json={"function": "greet", "parameters": {"name": "Alice", "count": 3}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "Hello Alice!" in data["result"]["message"]
    assert data["result"]["count"] == 3
    
    print(f"✓ Status: {response.status_code}")
    print(f"  Message: {data['result']['message'][:50]}...")


def test_handler_function_not_found():
    """Test error when function doesn't exist"""
    print("\n3. Testing Function Not Found")
    print("-" * 60)
    
    response = client.post(
        "/api/handler",
        json={"function": "nonexistent", "parameters": {}}
    )
    
    assert response.status_code == 400
    data = response.json()
    
    assert "Function not found" in data["detail"]["error"]
    assert "nonexistent" in data["detail"]["function"]
    assert "available_tools" in data["detail"]
    
    print(f"✓ Status: {response.status_code}")
    print(f"  Error: {data['detail']['error']}")
    print(f"  Available tools: {len(data['detail']['available_tools'])}")


def test_handler_parameter_validation_error():
    """Test parameter validation error"""
    print("\n4. Testing Parameter Validation Error")
    print("-" * 60)
    
    response = client.post(
        "/api/handler",
        json={"function": "add", "parameters": {"x": "not_a_number", "y": 3}}
    )
    
    assert response.status_code == 500
    data = response.json()
    
    assert "Execution failed" in data["detail"]["error"]
    assert "error_details" in data["detail"]
    
    print(f"✓ Status: {response.status_code}")
    print(f"  Error: {data['detail']['error']}")


def test_handler_runtime_error():
    """Test runtime error during execution"""
    print("\n5. Testing Runtime Error")
    print("-" * 60)
    
    response = client.post(
        "/api/handler",
        json={"function": "divide", "parameters": {"x": 10, "y": 0}}
    )
    
    assert response.status_code == 500
    data = response.json()
    
    assert "Execution failed" in data["detail"]["error"]
    
    print(f"✓ Status: {response.status_code}")
    print(f"  Error: {data['detail']['error']}")
    print(f"  Details: {data['detail']['error_details']['message']}")


def test_handler_command_execution():
    """Test command-based tool execution"""
    print("\n6. Testing Command Execution")
    print("-" * 60)
    
    response = client.post(
        "/api/handler",
        json={"function": "list_files", "parameters": {"path": "."}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "stdout" in data["result"]
    assert data["result"]["returncode"] == 0
    
    print(f"✓ Status: {response.status_code}")
    print(f"  Return code: {data['result']['returncode']}")
    print(f"  Output lines: {len(data['result']['stdout'].splitlines())}")


def test_handler_empty_parameters():
    """Test function with no parameters"""
    print("\n7. Testing Empty Parameters")
    print("-" * 60)
    
    # Register a parameterless function
    @tool(description="Get current status")
    def get_status():
        return {"status": "operational", "version": "1.0.0"}
    
    response = client.post(
        "/api/handler",
        json={"function": "get_status", "parameters": {}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "status" in data["result"]
    
    print(f"✓ Status: {response.status_code}")
    print(f"  Result: {data['result']}")


def test_handler_missing_function_field():
    """Test missing function field in request"""
    print("\n8. Testing Missing Function Field")
    print("-" * 60)
    
    response = client.post(
        "/api/handler",
        json={"parameters": {"x": 5}}
    )
    
    assert response.status_code == 422  # Validation error
    data = response.json()
    
    print(f"✓ Status: {response.status_code}")
    print(f"  Validation error caught")


def test_list_handler_tools():
    """Test listing available tools"""
    print("\n9. Testing List Handler Tools")
    print("-" * 60)
    
    response = client.get("/api/handler/tools")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "tools" in data
    assert "count" in data
    assert data["count"] > 0
    
    print(f"✓ Status: {response.status_code}")
    print(f"  Tools available: {data['count']}")
    print(f"  Tool names: {', '.join(list(data['tools'].keys())[:5])}...")


def test_handler_response_structure():
    """Test response structure matches schema"""
    print("\n10. Testing Response Structure")
    print("-" * 60)
    
    response = client.post(
        "/api/handler",
        json={"function": "add", "parameters": {"x": 10, "y": 20}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all required fields
    required_fields = ["status", "result", "error", "execution_time", "timestamp"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    # Check field types
    assert isinstance(data["status"], str)
    assert isinstance(data["execution_time"], (int, float))
    assert isinstance(data["timestamp"], str)
    
    print(f"✓ All required fields present")
    print(f"  Fields: {', '.join(required_fields)}")


def run_all_tests():
    """Run all test cases"""
    print("=" * 60)
    print("Handler API Endpoint Tests")
    print("=" * 60)
    
    tests = [
        test_handler_success,
        test_handler_with_multiple_params,
        test_handler_function_not_found,
        test_handler_parameter_validation_error,
        test_handler_runtime_error,
        test_handler_command_execution,
        test_handler_empty_parameters,
        test_handler_missing_function_field,
        test_list_handler_tools,
        test_handler_response_structure
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
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
