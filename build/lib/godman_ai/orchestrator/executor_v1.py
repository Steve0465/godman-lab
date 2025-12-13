import asyncio
from typing import Any, Dict

from godman_ai.llm.engine import LLMEngine
from godman_ai.local_router import LocalModelRouter
from godman_ai.orchestrator.router_v2 import RouterV2
from godman_ai.tools.runner import ToolRunner


class ExecutorAgent:
    """
    ExecutorAgent v1 with async support.
    """

    def __init__(self, default_model: str = LocalModelRouter.MODEL_DEEPSEEK, timeout: float | None = None):
        self.model_router = LocalModelRouter(default_model=default_model)
        self.engine = LLMEngine(default_model)
        self.router = RouterV2()
        self.runner = ToolRunner(timeout=timeout)
        self.timeout = timeout

    def think(self, query: str) -> str:
        model = self.model_router.select_model(query=query)
        prompt = (
            "You are the reasoning module of Godman Agent.\n"
            "User query: " + query + "\n"
            "Provide a short reasoning summary (1-2 sentences)."
        )
        return self.engine.call(prompt, model=model)

    async def think_async(self, query: str) -> str:
        model = self.model_router.select_model(query=query)
        prompt = (
            "You are the reasoning module of Godman Agent.\n"
            "User query: " + query + "\n"
            "Provide a short reasoning summary (1-2 sentences)."
        )
        return await self.engine.call_async(prompt, model=model)

    def act(self, query: str) -> dict:
        model_selection = self.model_router.route(query)
        selected_model = model_selection["model"]
        routing = self.router.route(query)
        reasoning = self.think(query)
        if routing.get("score", 0) <= 0 or not routing.get("tool"):
            llm_output = self.engine.call(
                "User query: " + query + "\n"
                "Answer directly.",
                model=selected_model
            )
            return {
                "ok": True,
                "mode": "llm_only",
                "model": selected_model,
                "model_selection": model_selection,
                "reasoning": reasoning,
                "tool": None,
                "result": llm_output,
            }
        tool_name = routing["tool"]
        result = self.runner.run(tool_name, text=query)
        return {
            "ok": True,
            "mode": "tool_execution",
            "model": selected_model,
            "model_selection": model_selection,
            "reasoning": reasoning,
            "routing": routing,
            "result": result,
        }

    async def act_async(self, query: str) -> Dict[str, Any]:
        model_selection = self.model_router.route(query)
        selected_model = model_selection["model"]
        routing = self.router.route(query)
        reasoning = await self.think_async(query)
        if routing.get("score", 0) <= 0 or not routing.get("tool"):
            llm_output = await self.engine.call_async(
                "User query: " + query + "\n"
                "Answer directly.",
                model=selected_model
            )
            return {
                "ok": True,
                "mode": "llm_only",
                "model": selected_model,
                "model_selection": model_selection,
                "reasoning": reasoning,
                "tool": None,
                "result": llm_output,
            }
        tool_name = routing["tool"]
        tool_run = self.runner.run_async(tool_name, text=query)
        try:
            result = await tool_run if not self.timeout else await asyncio.wait_for(tool_run, timeout=self.timeout)
        except asyncio.TimeoutError:
            return {
                "ok": False,
                "mode": "tool_execution",
                "model": selected_model,
                "model_selection": model_selection,
                "reasoning": reasoning,
                "routing": routing,
                "result": {"ok": False, "error": "Timeout"},
            }
        return {
            "ok": True,
            "mode": "tool_execution",
            "model": selected_model,
            "model_selection": model_selection,
            "reasoning": reasoning,
            "routing": routing,
            "result": result,
        }
