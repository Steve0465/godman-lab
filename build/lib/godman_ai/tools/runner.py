"""Tool runner that discovers and executes registered tools."""

import asyncio
import time
from typing import Any, Dict, Optional

from .base import ToolExecutionError
from .loader import discover_tools
from .registry import get_tool


class ToolRunner:
    """
    Discovers tools and provides a simple interface to execute them.
    """

    def __init__(self, concurrency_limit: Optional[int] = None, timeout: Optional[float] = None) -> None:
        """
        Initialize the runner.

        Args:
            concurrency_limit: Optional max concurrent async executions.
            timeout: Optional default timeout (seconds) for async runs.
        """
        discover_tools()
        self._sem = asyncio.Semaphore(concurrency_limit) if concurrency_limit else None
        self.timeout = timeout

    def _get_tool(self, tool_name: str):
        tool_cls = get_tool(tool_name)
        if not tool_cls:
            raise ToolExecutionError(f"Unknown tool: {tool_name}")
        if isinstance(tool_cls, dict) and callable(tool_cls.get("function")):
            def func_wrapper(**kwargs):
                return tool_cls["function"](**kwargs)
            return type("FunctionTool", (), {"run": staticmethod(func_wrapper)})()
        return tool_cls() if isinstance(tool_cls, type) else tool_cls

    def run(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute a tool by name with provided parameters synchronously.
        """
        tool = self._get_tool(tool_name)
        start = time.time()
        try:
            if hasattr(tool, "run"):
                result = tool.run(**kwargs)
            else:
                result = tool(**kwargs)
        except Exception as e:
            return {
                "ok": False,
                "tool": tool_name,
                "error": str(e),
                "trace": type(e).__name__,
            }
        end = time.time()
        return {
            "ok": True,
            "tool": tool_name,
            "duration_ms": int((end - start) * 1000),
            "result": result,
        }

    async def run_async(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute a tool by name asynchronously with optional timeout and concurrency limits.
        """
        tool = self._get_tool(tool_name)

        async def _execute():
            if hasattr(tool, "run_async"):
                return await tool.run_async(**kwargs)
            return await asyncio.to_thread(tool.run, **kwargs)

        async def _with_timeout():
            coro = _execute()
            if self.timeout:
                return await asyncio.wait_for(coro, timeout=self.timeout)
            return await coro

        start = time.time()
        try:
            if self._sem:
                async with self._sem:
                    result = await _with_timeout()
            else:
                result = await _with_timeout()
        except asyncio.TimeoutError:
            return {
                "ok": False,
                "tool": tool_name,
                "error": f"Timeout after {self.timeout} seconds" if self.timeout else "Timeout",
                "trace": "TimeoutError",
            }
        except asyncio.CancelledError:
            return {
                "ok": False,
                "tool": tool_name,
                "error": "Cancelled",
                "trace": "CancelledError",
            }
        except Exception as e:
            return {
                "ok": False,
                "tool": tool_name,
                "error": str(e),
                "trace": type(e).__name__,
            }
        end = time.time()
        return {
            "ok": True,
            "tool": tool_name,
            "duration_ms": int((end - start) * 1000),
            "result": result,
        }
