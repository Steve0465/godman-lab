"""Self-healing strategies for agent loop."""

from __future__ import annotations

from typing import Any, Dict, Optional

from godman_ai.local_router import LocalModelRouter
from godman_ai.orchestrator.router_v2 import RouterV2
from godman_ai.capabilities.resolver import CapabilityResolver
from godman_ai.models.registry import ModelRegistry
from godman_ai.models.selector import ModelSelector
from godman_ai.models.performance import InMemoryPerformanceStore
from godman_ai.tools.critics.quality_critic import evaluate_quality


def retry_same_tool(context: Dict[str, Any]) -> Dict[str, Any]:
    return {"action": "retry", "context_updates": context}


def retry_with_alternate_model(
    context: Dict[str, Any],
    allowed_models: Optional[list[str]] = None,
    selector: Optional[ModelSelector] = None,
) -> Dict[str, Any]:
    if selector:
        model = selector.select_model(context.get("task_type", "generic"), None, context)  # type: ignore[arg-type]
    else:
        allowed = allowed_models or None
        default_model = allowed[0] if allowed else None
        router = LocalModelRouter(default_model=default_model, allowed_models=allowed)
        model = router.select_model(query=context.get("last_query", "")) if context else router.default_model
    return {"action": "retry", "context_updates": {"force_model": model}}


def route_to_alternate_tool(query: str, preferred_tools: Optional[list[str]] = None, memory_manager=None) -> Dict[str, Any]:
    resolver = CapabilityResolver()
    alternatives = resolver.find_tools_for_task(query, {}, None)
    tool = alternatives[0].name if alternatives else None
    if not tool:
        router = RouterV2()
        routing = router.route(query)
        tool = routing.get("tool") or (preferred_tools[0] if preferred_tools else None)
    if memory_manager and tool:
        successes = memory_manager.get_successful_patterns_for_workflow(tool)
        if successes:
            tool = tool
    return {"action": "retry", "context_updates": {"tool": tool}}


def run_correction_subworkflow(workflow_def: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    return {"action": "subworkflow", "workflow": workflow_def, "context_updates": context}


def escalate_to_human_flag(reason: str) -> Dict[str, Any]:
    return {"action": "escalate", "reason": reason}


def ensemble_two_models(task: str, models_list: list[str], critic=evaluate_quality, selector: Optional[ModelSelector] = None):
    """Run two models (simulated) and pick best result."""
    outputs = []
    chosen_models = models_list[:2] if models_list else []
    for mid in chosen_models:
        outputs.append((mid, f"[{mid}] {task}"))
    if not outputs:
        return {"action": "none", "result": None}
    scored = []
    for mid, out in outputs:
        score = critic(out).score if critic else 0.0
        scored.append((score, mid, out))
    scored.sort(reverse=True)
    best = scored[0]
    return {"action": "ensemble_select", "model": best[1], "result": best[2], "score": best[0]}
