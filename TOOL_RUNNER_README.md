# ToolRunner

A lightweight function registry and execution framework with decorator-based registration, parameter validation, subprocess execution, and comprehensive logging.

## Features

- **Decorator-based registration** - Simple `@tool` decorator for function registration
- **Parameter validation** - Type-based schema validation
- **Dual execution modes** - Execute Python functions or shell commands
- **Error handling** - Comprehensive exception catching and reporting
- **Structured output** - JSON responses with status, result, error, and timing
- **Logging** - Detailed execution logs with timestamps and performance metrics
- **Standard library only** - No external dependencies except subprocess

## Installation

No installation required - uses only Python standard library:
- `json`
- `logging`
- `subprocess`
- `time`
- `datetime`
- `functools`
- `pathlib`
- `typing`

## Quick Start

```python
from libs.tool_runner import ToolRunner

# Create runner instance
runner = ToolRunner()

# Register a function
@runner.tool(schema={"name": str, "age": int})
def create_user(name: str, age: int):
    return {"user": name, "age": age, "status": "active"}

# Execute the function
result = runner.run("create_user", {"name": "Alice", "age": 30})

if result["status"] == "success":
    print(result["result"])
```

## Usage

### 1. Function Registration

Register Python functions as tools:

```python
runner = ToolRunner()

@runner.tool(
    schema={"x": int, "y": int},
    description="Add two numbers"
)
def add(x: int, y: int):
    return {"sum": x + y}
```

### 2. Command Registration

Register shell commands with parameter substitution:

```python
@runner.tool(
    schema={"path": str},
    command="ls -la {path}",
    description="List directory contents"
)
def list_files(path: str):
    pass  # Function body not executed when command is present
```

### 3. Execution

Execute registered tools by name:

```python
result = runner.run("add", {"x": 5, "y": 3})

# Result structure:
{
    "status": "success",
    "result": {"sum": 8},
    "error": None,
    "execution_time": 0.001,
    "timestamp": "2025-12-07T22:41:54.123456"
}
```

### 4. Error Handling

Errors are captured and returned in a structured format:

```python
result = runner.run("divide", {"x": 10, "y": 0})

# Error result:
{
    "status": "error",
    "result": None,
    "error": {
        "type": "ZeroDivisionError",
        "message": "division by zero",
        "function": "divide",
        "parameters": {"x": 10, "y": 0}
    },
    "execution_time": 0.002,
    "timestamp": "2025-12-07T22:41:54.123456"
}
```

### 5. Tool Discovery

List and inspect registered tools:

```python
# List all tools
tools = runner.list_tools()
for name, info in tools.items():
    print(f"{name}: {info['description']}")

# Get specific tool info
info = runner.get_tool_info("add")
print(info["schema"])  # {"x": "int", "y": "int"}
```

## Global Instance

Use the global runner for simpler imports:

```python
from libs.tool_runner import tool, runner

@tool(schema={"msg": str})
def echo(msg: str):
    return {"echo": msg}

result = runner.run("echo", {"msg": "Hello"})
```

## API Reference

### ToolRunner Class

#### `__init__(log_path: Optional[str] = None)`

Initialize ToolRunner with optional custom log path.

**Default log path:** `~/godman-lab/logs/tool_runner.log`

#### `@tool(name=None, schema=None, description=None, command=None)`

Decorator to register a function or command as a tool.

**Parameters:**
- `name` (str, optional): Tool name. Defaults to function name
- `schema` (dict, optional): Parameter schema `{param_name: type}`
- `description` (str, optional): Tool description
- `command` (str, optional): Shell command template with `{param}` placeholders

**Returns:** Decorated function

#### `run(function_name: str, parameters: dict = None, timeout: int = 30) -> dict`

Execute a registered tool by name.

**Parameters:**
- `function_name` (str): Name of registered tool
- `parameters` (dict, optional): Tool parameters
- `timeout` (int): Execution timeout in seconds

**Returns:** JSON result dictionary

#### `list_tools() -> dict`

List all registered tools with metadata.

**Returns:** Dictionary of tool names and their info

#### `get_tool_info(function_name: str) -> dict | None`

Get detailed information about a specific tool.

**Returns:** Tool metadata or None if not found

## Logging

All tool invocations are logged to `~/godman-lab/logs/tool_runner.log` with:
- Timestamp
- Function name
- Input parameters (JSON)
- Execution time
- Result/Error (truncated to 200 chars)

**Log format:**
```
2025-12-07 22:41:54 - ToolRunner - INFO - Invocation: function=add, parameters={"x": 5, "y": 3}
2025-12-07 22:41:54 - ToolRunner - INFO - Success: function=add, time=0.001s, result={"sum": 8}
```

## Examples

See `examples_tool_runner.py` for comprehensive usage examples including:
1. Basic function registration and execution
2. Shell command execution
3. Python script execution
4. Data processing pipelines
5. Error handling patterns
6. Tool discovery
7. Global runner usage

## Testing

Run the test suite:

```bash
python3 test_tool_runner.py
```

**Tests cover:**
- Function registration
- Parameter validation
- Function execution
- Command execution
- Error handling
- Logging
- Tool discovery
- Complex workflows

## Schema Validation

The schema parameter defines expected types for function parameters:

```python
@runner.tool(schema={
    "name": str,
    "age": int,
    "active": bool,
    "tags": list
})
def example(name, age, active, tags):
    pass
```

Validation errors are caught and returned with helpful messages:
```
Parameter 'age' must be int, got str
```

## Command Execution

Commands support parameter substitution using `{param}` syntax:

```python
@runner.tool(
    schema={"pattern": str, "file": str},
    command="grep '{pattern}' {file}"
)
def search(pattern: str, file: str):
    pass

# Executes: grep 'TODO' myfile.txt
runner.run("search", {"pattern": "TODO", "file": "myfile.txt"})
```

## Output Format

All `run()` calls return a standardized JSON structure:

**Success:**
```json
{
    "status": "success",
    "result": { ... },
    "error": null,
    "execution_time": 0.123,
    "timestamp": "2025-12-07T22:41:54.123456"
}
```

**Error:**
```json
{
    "status": "error",
    "result": null,
    "error": {
        "type": "ValueError",
        "message": "Parameter validation failed",
        "function": "example",
        "parameters": { ... }
    },
    "execution_time": 0.001,
    "timestamp": "2025-12-07T22:41:54.123456"
}
```

## Use Cases

1. **CLI Tool Integration** - Wrap command-line tools with type-safe Python functions
2. **Script Orchestration** - Build pipelines of Python functions and shell commands
3. **API Backends** - Expose registered tools via REST endpoints
4. **Testing Frameworks** - Structured execution with timing and error capture
5. **Automation** - Log-based auditing of tool executions
6. **Function Calling** - Bridge between LLMs and local tools

## License

Part of the godman-lab project.

## Author

Created for the godman-lab WebUI presets feature.
