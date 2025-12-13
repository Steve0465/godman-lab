"""High-level orchestrator facade."""

from __future__ import annotations

from typing import Any, Dict, Optional

from godman_ai.orchestrator.executor_v1 import ExecutorAgent
from godman_ai.orchestrator.router_v2 import RouterV2


class Orchestrator:
    """Simple facade that wires routing and execution paths."""

    def __init__(self, executor: Optional[ExecutorAgent] = None) -> None:
        self.executor = executor or ExecutorAgent()
        self.router = RouterV2()

    def route(self, query: str) -> Dict[str, Any]:
        """Return tool and model routing suggestion for a query."""
        return self.router.route_with_model(query)

    def run(self, query: str) -> Dict[str, Any]:
        """Execute a query synchronously using routing + executor."""
        return self.executor.act(query)

    async def run_async(self, query: str) -> Dict[str, Any]:
        """Execute a query asynchronously using routing + executor."""
        return await self.executor.act_async(query)
