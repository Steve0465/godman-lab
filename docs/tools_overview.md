# Tools Overview

Godman tools now share a standardized interface with async support and a centralized runner.

## BaseTool
- Inherit from `godman_ai.tools.base.BaseTool`.
- Implement `run(self, **kwargs) -> dict`.
- Optionally override `run_async(self, **kwargs) -> dict` for native async; otherwise sync `run` is offloaded to a thread.
- Raise `ToolExecutionError` for user-facing failures.

## Runner
- `ToolRunner.run(name, **kwargs)`: synchronous execution with timing and error capture.
- `ToolRunner.run_async(name, **kwargs)`: async execution with optional timeout and concurrency limits.
- Tools are discovered via `discover_tools()` and registered in `TOOL_REGISTRY`.

## Registry
- Register classes with `register_tool(MyTool)`.
- Register functions with `register_function_tool(name, func, description="")`.
- Retrieve with `get_tool(name)`; list via `list_tools()`.

## Safety & Logging
- No `shell=True` usage; shell commands are sandboxed separately.
- Logging is redacted for sensitive key/value patterns.

## Example
```python
from godman_ai.tools.base import BaseTool
from godman_ai.tools.registry import register_tool

class EchoTool(BaseTool):
    name = "echo"
    description = "Echo text"

    def run(self, text: str):
        return {"text": text}

register_tool(EchoTool)
```

Use with the runner:
```python
from godman_ai.tools.runner import ToolRunner

runner = ToolRunner(timeout=5)
runner.run("echo", text="hi")
```
