import asyncio

import pytest

from godman_ai.tools.base import BaseTool
from godman_ai.tools.registry import TOOL_REGISTRY, register_tool
from godman_ai.orchestrator.executor_v1 import ExecutorAgent


class EchoTool(BaseTool):
    name = "echo_tool"
    description = "Echo text"

    def run(self, text: str):
        return {"text": text}


@pytest.fixture(autouse=True)
def cleanup_registry():
    yield
    TOOL_REGISTRY.pop("echo_tool", None)


def test_act_async_executes_tool():
    register_tool(EchoTool)
    agent = ExecutorAgent()
    async def fake_think(_: str) -> str:
        return "ok"
    agent.think_async = fake_think  # type: ignore[attr-defined]
    result = asyncio.run(agent.act_async("echo this text"))
    assert result["ok"]
    assert result["result"]["ok"]
    assert result["result"]["result"]["text"]
