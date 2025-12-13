import asyncio
import time

import pytest

from godman_ai.tools.base import BaseTool
from godman_ai.tools.registry import TOOL_REGISTRY, register_tool
from godman_ai.tools.runner import ToolRunner


class EchoTool(BaseTool):
    name = "echo_tool"
    description = "Echo text"

    def run(self, text: str):
        return {"text": text}


class SlowTool(BaseTool):
    name = "slow_tool"
    description = "Sleeps briefly"

    def run(self):
        time.sleep(0.2)
        return {"done": True}


@pytest.fixture(autouse=True)
def cleanup_registry():
    yield
    TOOL_REGISTRY.pop("echo_tool", None)
    TOOL_REGISTRY.pop("slow_tool", None)

def test_run_async_executes_and_returns_result():
    register_tool(EchoTool)
    runner = ToolRunner()
    res = asyncio.run(runner.run_async("echo_tool", text="hi"))
    assert res["ok"]
    assert res["result"]["text"] == "hi"


def test_run_async_honors_timeout():
    register_tool(SlowTool)
    runner = ToolRunner(timeout=0.05)
    res = asyncio.run(runner.run_async("slow_tool"))
    assert not res["ok"]
    assert res["trace"] == "TimeoutError"
