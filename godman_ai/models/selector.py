"""Model selector driven by registry and policy hints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from godman_ai.agents.policy_engine import AgentPolicy
from godman_ai.models.registry import ModelConfig, ModelRegistry
from godman_ai.models.performance import ModelPerformanceStore


class ModelSelector:
    """Select models based on tags, cost, latency, and policy hints."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        performance_store: Optional[ModelPerformanceStore] = None,
    ) -> None:
        self.registry = registry or ModelRegistry()
        self.performance_store = performance_store

    def select_model(self, task_type: str, policy: Optional[AgentPolicy] = None, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        candidates = self._filter_by_policy(policy)
        if not candidates:
            return None
        # Simple heuristic: prefer tags first, then cost/latency hints
        preferred_tags = set(policy.preferred_model_tags) if policy else set()
        if preferred_tags:
            tagged = [c for c in candidates if preferred_tags.intersection(set(c.tags))]
            if tagged:
                candidates = tagged
        candidates = sorted(
            candidates,
            key=lambda c: (c.cost_hint, c.latency_hint),
        )
        return candidates[0].id if candidates else None

    def select_fallback_models(self, task_type: str, policy: Optional[AgentPolicy] = None, context: Optional[Dict[str, Any]] = None) -> List[str]:
        primary = self.select_model(task_type, policy, context)
        candidates = self._filter_by_policy(policy)
        fallback = [c.id for c in candidates if c.id != primary]
        return fallback[:2]

    def _filter_by_policy(self, policy: Optional[AgentPolicy]) -> List[ModelConfig]:
        models = self.registry.list_models(enabled=True)
        if not policy:
            return models
        forbidden = set(policy.forbidden_models)
        filtered = [m for m in models if m.id not in forbidden]
        if policy.max_latency_hint is not None:
            filtered = [m for m in filtered if m.latency_hint <= policy.max_latency_hint]
        return filtered
