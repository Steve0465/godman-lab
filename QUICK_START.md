# Quick Start Guide

## WebUI Presets

### Python API
```python
from godman_ai.config.presets import get_all_presets, get_preset_by_name

# List all presets
presets = get_all_presets()
# [{"id": "overmind", "name": "Overmind", "model": "deepseek-r1:14b", ...}, ...]

# Get specific preset
overmind = get_preset_by_name("Overmind")
```

### REST API
```bash
# List all presets
curl http://localhost:8000/api/presets

# Get specific preset
curl http://localhost:8000/api/presets/Overmind
```

---

## ToolRunner

### Register a Tool
```python
from libs.tool_runner import tool, runner

# Python function
@tool(schema={"x": int, "y": int}, description="Add two numbers")
def add(x: int, y: int):
    return {"sum": x + y}

# Shell command
@tool(schema={"path": str}, command="ls -la {path}")
def list_files(path: str):
    pass
```

### Execute a Tool
```python
result = runner.run("add", {"x": 5, "y": 3})
# {
#   "status": "success",
#   "result": {"sum": 8},
#   "error": null,
#   "execution_time": 0.001,
#   "timestamp": "2025-12-07T22:41:54"
# }
```

---

## CLI Commands

### List Tools
```bash
godman tool list                  # Table view
godman tool list --verbose        # Detailed view
```

### Get Tool Info
```bash
godman tool info add
```

### Run a Tool
```bash
# Basic
godman tool run --name add --params '{"x": 5, "y": 3}'

# Short flags
godman tool run -n greet -p '{"name": "Alice", "count": 2}'

# Verbose mode
godman tool run -n stats -p '{"data": [1,2,3,4,5]}' --verbose
```

### Show Examples
```bash
godman tool example
```

---

## Demo Script

Run the included demo with pre-registered tools:

```bash
# List available tools
python3 godman_tool_cli.py list

# Run a tool
python3 godman_tool_cli.py run -n add -p '{"x": 10, "y": 20}'

# Get tool info
python3 godman_tool_cli.py info greet

# Show examples
python3 godman_tool_cli.py example
```

---

## Testing

```bash
# Test ToolRunner (10 tests)
python3 test_tool_runner.py

# Test Presets (configuration)
python3 test_presets.py

# Test API (endpoints)
python3 test_api.py

# Run examples
python3 examples_tool_runner.py
```

---

## Log Files

```bash
# View tool execution logs
tail -f ~/godman-lab/logs/tool_runner.log

# View recent entries
tail -20 ~/godman-lab/logs/tool_runner.log
```

---

## Documentation

- **PRESETS_README.md** - WebUI presets documentation
- **TOOL_RUNNER_README.md** - ToolRunner framework guide
- **CLI_TOOLS_README.md** - CLI commands reference
- **FEATURE_SUMMARY.md** - Complete feature overview

---

## Common Workflows

### 1. Create and Execute a Tool

```python
# 1. Register the tool
from libs.tool_runner import tool

@tool(schema={"name": str, "age": int})
def create_user(name: str, age: int):
    return {"user": name, "age": age, "status": "active"}

# 2. List available tools
from libs.tool_runner import runner
print(runner.list_tools())

# 3. Execute from Python
result = runner.run("create_user", {"name": "Alice", "age": 30})
print(result["result"])
```

### 2. Execute from CLI

```bash
# After registering tools in Python:

# List tools
godman tool list

# Get details
godman tool info create_user

# Execute
godman tool run -n create_user -p '{"name": "Bob", "age": 25}'
```

### 3. Use WebUI Presets

```python
from godman_ai.config.presets import get_preset_by_name

# Get Overmind preset for planning
preset = get_preset_by_name("Overmind")
model = preset["model"]      # "deepseek-r1:14b"
prompt = preset["prompt"]    # Strategic reasoning prompt

# Get Forge preset for execution
forge = get_preset_by_name("Forge")
# Use forge["model"] and forge["prompt"] for code generation
```

---

## Exit Codes

All CLI commands return standard exit codes:
- `0` = Success
- `1` = Error

Use in scripts:
```bash
if godman tool run -n validate -p '{"data": "test"}'; then
    echo "Validation passed"
else
    echo "Validation failed"
    exit 1
fi
```

---

## Troubleshooting

### Tools not showing in list
- Ensure tools are registered with `@tool` decorator
- Import the module that registers the tools
- Check you're using the global `runner` instance

### JSON parsing errors
- Quote JSON parameters with single quotes: `'{"x": 5}'`
- Validate JSON syntax before passing
- Use heredoc for complex multi-line JSON

### Execution errors
- Use `--verbose` flag for details
- Check logs: `tail -f ~/godman-lab/logs/tool_runner.log`
- Verify parameter types match schema

---

## Branch Information

**Branch:** feature/webui-presets  
**Status:** ✅ Ready for review  
**Files:** 18 files changed, 2632+ insertions  
**Tests:** All passing
