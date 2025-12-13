import asyncio

from godman_ai.models.base import trace_model
from godman_ai.tools.base import BaseTool
from godman_ai.tools.registry import TOOL_REGISTRY, register_tool


def test_trace_model_adds_duration():
    @trace_model
    async def gen():
        return {"text": "ok"}

    result = asyncio.run(gen())
    assert "_duration_ms" in result


def test_trace_tool_wraps_run():
    class SimpleTool(BaseTool):
        name = "simple_tool"
        description = "desc"

        def run(self, **kwargs):
            return {"ok": True}

    register_tool(SimpleTool)
    tool_cls = TOOL_REGISTRY["simple_tool"]
    tool = tool_cls()
    out = tool.run()
    assert out["ok"]
    TOOL_REGISTRY.pop("simple_tool", None)
