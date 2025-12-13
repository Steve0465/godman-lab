"""Model-aware router that consults ModelSelector with fallbacks."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from godman_ai.agents.policy_engine import AgentPolicy
from godman_ai.models.registry import ModelRegistry
from godman_ai.models.selector import ModelSelector


class ModelRouterV3:
    """Wraps LocalModelRouter with registry-based selection and fallbacks."""

    def __init__(self, registry: Optional[ModelRegistry] = None) -> None:
        self.registry = registry or ModelRegistry()
        self.selector = ModelSelector(self.registry)
        self._local_router = None

    def route(self, task_type: Optional[str] = None, query: Optional[str] = None, policy: Optional[AgentPolicy] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self._local_router is None:
            from godman_ai.local_router import LocalModelRouter  # local import to avoid circular import
            self._local_router = LocalModelRouter()
        model = self.selector.select_model(task_type or "generic", policy, context) or self._local_router.select_model(task_type=task_type, query=query, context=context)
        fallbacks: List[str] = self.selector.select_fallback_models(task_type or "generic", policy, context)
        return {
            "model": model,
            "fallbacks": fallbacks,
        }
