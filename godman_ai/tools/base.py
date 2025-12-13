"""Base definitions for tools."""

import asyncio
import time
from typing import Any, Dict


class ToolExecutionError(Exception):
    """Raised when a tool fails to execute properly."""


class BaseTool:
    """
    Base interface for tools.

    Attributes:
        name: Human-readable tool name.
        description: Short description of tool behavior.
    """

    name: str
    description: str

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute the tool.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            A dictionary with tool results.

        Raises:
            ToolExecutionError: When execution fails.
            NotImplementedError: If not implemented by subclasses.
        """
        raise NotImplementedError("Tool must implement run()")

    async def run_async(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute the tool asynchronously.

        By default, this offloads the synchronous `run` method to a thread to
        preserve backward compatibility. Tools may override with a native async
        implementation.
        """
        return await asyncio.to_thread(self.run, **kwargs)


def trace_tool(func):
    """Decorator to capture tool execution timing."""

    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration_ms = int((time.time() - start) * 1000)
        if isinstance(result, dict):
            result = {**result, "_duration_ms": duration_ms}
        return result

    return wrapper
