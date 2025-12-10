# CLI Tool Commands

CLI extension for executing ToolRunner registered tools from the command line with rich formatted output.

## Commands

### `godman tool run`

Execute a registered tool by name with JSON parameters.

**Usage:**
```bash
godman tool run --name <tool_name> --params <json_string> [--verbose]
```

**Options:**
- `--name`, `-n`: Name of the registered tool to execute (required)
- `--params`, `-p`: Tool parameters as JSON string (default: `{}`)
- `--verbose`, `-v`: Show detailed execution info
- `--runner`: Path to custom runner module (optional)

**Examples:**
```bash
# Run a simple tool
godman tool run --name greet --params '{"name": "Alice", "count": 2}'

# Run with short flags
godman tool run -n add -p '{"x": 5, "y": 3}'

# Run command-based tool
godman tool run -n list_files -p '{"path": "."}'

# Verbose output with timing
godman tool run -n calculate -p '{"value": 42}' --verbose

# Complex parameters
godman tool run -n stats -p '{"data": [1, 5, 3, 9, 2, 7]}'
```

### `godman tool list`

List all registered tools.

**Usage:**
```bash
godman tool list [--verbose]
```

**Options:**
- `--verbose`, `-v`: Show detailed tool information including schemas

**Output:**
- Default: Table view with tool names, descriptions, parameters, and type (PY/CMD)
- Verbose: Detailed list with full schemas and descriptions

**Examples:**
```bash
# Table view
godman tool list

# Detailed view
godman tool list --verbose
```

### `godman tool info`

Get detailed information about a specific tool.

**Usage:**
```bash
godman tool info <tool_name>
```

**Shows:**
- Tool name
- Description
- Parameter schema with types
- Command template (if command-based)
- Tool type (Python function or Command-based)

**Examples:**
```bash
# Get info for a tool
godman tool info greet

# Get info for command tool
godman tool info list_files
```

### `godman tool example`

Show comprehensive examples of tool command usage.

**Usage:**
```bash
godman tool example
```

**Displays:**
- Tool registration examples
- CLI execution examples
- Complex parameter examples
- Debugging tips

## Output Format

### Success Output

```
✓ SUCCESS
╭─────────────────────── Result ───────────────────────╮
│ {                                                    │
│   "sum": 8,                                          │
│   "operands": [5, 3]                                 │
│ }                                                    │
╰──────────────────────────────────────────────────────╯

[verbose mode adds:]
Execution time: 0.001s
Timestamp: 2025-12-07T22:50:51.488509
```

### Error Output

```
✗ ERROR
╭─────────────────────── Error ────────────────────────╮
│ {                                                    │
│   "type": "ValueError",                              │
│   "message": "Parameter 'x' must be int, got str",  │
│   "function": "add",                                 │
│   "parameters": {"x": "5", "y": 3}                  │
│ }                                                    │
╰──────────────────────────────────────────────────────╯

Execution time: 0.0s
Timestamp: 2025-12-07T22:50:51.488509
```

## Features

### Pretty JSON Output

- Syntax highlighted JSON results
- Color-coded success/error badges
- Formatted panels with borders
- Line numbers disabled for cleaner output

### Rich Tables

The `list` command displays tools in a formatted table:

```
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━┓
┃ Tool Name  ┃ Description             ┃ Parameters    ┃ Type ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━┩
│ greet      │ Greet someone           │ name, count   │  PY  │
│ add        │ Add two numbers         │ x, y          │  PY  │
│ list_files │ List directory contents │ path          │ CMD  │
└────────────┴─────────────────────────┴───────────────┴──────┘
```

### Verbose Mode

When using `--verbose`:
- Shows execution parameters before running
- Displays execution time in seconds
- Shows ISO 8601 timestamp
- Useful for debugging and performance monitoring

## Integration with Main CLI

The tool commands are integrated into the main `godman` CLI:

```bash
godman tool list
godman tool run -n my_tool -p '{"param": "value"}'
godman tool info my_tool
```

## Tool Registration

Tools must be registered before they can be executed via CLI:

```python
from libs.tool_runner import tool

@tool(
    schema={"name": str, "age": int},
    description="Create a user profile"
)
def create_user(name: str, age: int):
    return {"user": name, "age": age, "status": "active"}
```

Then use from CLI:
```bash
godman tool run -n create_user -p '{"name": "Alice", "age": 30}'
```

## Example Workflow

```bash
# 1. Register tools in your Python code
# (see examples in godman_tool_cli.py)

# 2. List available tools
godman tool list

# 3. Get details about a tool
godman tool info add

# 4. Run the tool
godman tool run -n add -p '{"x": 10, "y": 20}'

# 5. Check logs
tail -f ~/godman-lab/logs/tool_runner.log
```

## JSON Parameter Tips

1. **Quote JSON with single quotes:**
   ```bash
   godman tool run -n add -p '{"x": 5, "y": 3}'
   ```

2. **Escape internal quotes if using double quotes:**
   ```bash
   godman tool run -n greet -p "{\"name\": \"Alice\", \"count\": 2}"
   ```

3. **Multi-line JSON (use heredoc):**
   ```bash
   godman tool run -n complex -p "$(cat <<EOF
   {
     "data": [1, 2, 3, 4, 5],
     "operation": "sum",
     "filter": true
   }
   EOF
   )"
   ```

4. **Read from file:**
   ```bash
   godman tool run -n process -p "$(cat params.json)"
   ```

## Exit Codes

- `0`: Success
- `1`: Error (tool execution failed, validation error, tool not found, etc.)

Use in scripts:
```bash
if godman tool run -n validate -p '{"data": "test"}'; then
    echo "Validation passed"
else
    echo "Validation failed"
fi
```

## Dependencies

- `typer`: CLI framework
- `rich`: Beautiful terminal output
  - Console for printing
  - Syntax highlighting for JSON
  - Panels and tables
- `libs.tool_runner`: ToolRunner backend

## Files

- `cli/godman/tools.py`: Tool CLI commands implementation
- `cli/godman/main.py`: Main CLI app (mounts tool commands)
- `godman_tool_cli.py`: Standalone demo with sample tools

## Demo Script

A complete demo script is provided at `godman_tool_cli.py` that:
1. Registers 7 sample tools
2. Exposes all tool commands
3. Can be used for testing

**Usage:**
```bash
# List tools
python3 godman_tool_cli.py list

# Run a tool
python3 godman_tool_cli.py run -n add -p '{"x": 5, "y": 3}'

# Get help
python3 godman_tool_cli.py --help
```

## Troubleshooting

**No tools registered:**
- Make sure tools are registered using `@tool` decorator
- Import the module that registers tools before running CLI
- Check that you're using the global runner instance

**JSON parsing errors:**
- Ensure JSON is properly quoted
- Validate JSON syntax with `jq` or online validator
- Check for special characters that need escaping

**Tool not found:**
- List available tools with `godman tool list`
- Check tool name spelling (case-sensitive)
- Ensure tool registration code has been executed

**Execution errors:**
- Use `--verbose` flag for more details
- Check logs at `~/godman-lab/logs/tool_runner.log`
- Verify parameter types match schema
