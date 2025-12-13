"""Policy definitions for self-correcting agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from godman_ai.agents.error_classifier import ErrorClass


@dataclass
class AgentPolicy:
    max_retries: int = 1
    max_corrections: int = 1
    allowed_models: List[str] = field(default_factory=list)
    preferred_model_tags: List[str] = field(default_factory=list)
    forbidden_models: List[str] = field(default_factory=list)
    max_latency_hint: Optional[float] = None
    use_ensemble_for_critical_tasks: bool = False
    preferred_capability_tags: List[str] = field(default_factory=list)
    preferred_tools: List[str] = field(default_factory=list)
    escalation_thresholds: Dict[str, int] = field(default_factory=dict)
    critics_to_run: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentPolicy":
        return cls(
            max_retries=int(data.get("max_retries", 1)),
            max_corrections=int(data.get("max_corrections", 1)),
            allowed_models=list(data.get("allowed_models", [])),
            preferred_model_tags=list(data.get("preferred_model_tags", [])),
            forbidden_models=list(data.get("forbidden_models", [])),
            max_latency_hint=data.get("max_latency_hint"),
            use_ensemble_for_critical_tasks=bool(data.get("use_ensemble_for_critical_tasks", False)),
            preferred_capability_tags=list(data.get("preferred_capability_tags", [])),
            preferred_tools=list(data.get("preferred_tools", [])),
            escalation_thresholds=dict(data.get("escalation_thresholds", {})),
            critics_to_run=list(data.get("critics_to_run", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_retries": self.max_retries,
            "max_corrections": self.max_corrections,
            "allowed_models": self.allowed_models,
            "preferred_model_tags": self.preferred_model_tags,
            "forbidden_models": self.forbidden_models,
            "max_latency_hint": self.max_latency_hint,
            "use_ensemble_for_critical_tasks": self.use_ensemble_for_critical_tasks,
            "preferred_tools": self.preferred_tools,
            "escalation_thresholds": self.escalation_thresholds,
            "critics_to_run": self.critics_to_run,
        }


class PolicyEngine:
    """Lightweight policy selection helpers."""

    def __init__(self, policy: AgentPolicy, memory_manager=None):
        self.policy = policy
        self.memory = memory_manager

    def choose_critics_for_step(self, step, context) -> List[str]:
        return self.policy.critics_to_run

    def choose_strategy(self, error_class: ErrorClass, loop_context) -> str:
        if self.memory and error_class == ErrorClass.TOOL_CONFIG:
            failures = self.memory.get_recent_failures_for_tool(
                loop_context.metadata.get("tool", ""),
                limit=self.policy.escalation_thresholds.get("tool_failures", 3),
            )
            if len(failures) >= self.policy.escalation_thresholds.get("tool_failures", 3):
                return "retry_with_alternate_model"
        if error_class == ErrorClass.TRANSIENT:
            return "retry_same_tool"
        if error_class == ErrorClass.MODEL_QUALITY:
            return "retry_with_alternate_model"
        if error_class == ErrorClass.TOOL_CONFIG:
            return "route_to_alternate_tool"
        if error_class == ErrorClass.REQUIRES_HUMAN:
            return "escalate_to_human_flag"
        return "run_correction_subworkflow"

    def should_escalate(self, loop_context, critic_result) -> bool:
        max_corr = self.policy.max_corrections
        return loop_context.attempts >= max_corr
