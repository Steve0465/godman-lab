"""Agent loop for self-correcting workflows."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from godman_ai.agents.error_classifier import ErrorClass, classify_error
from godman_ai.agents.policy_engine import AgentPolicy, PolicyEngine
from godman_ai.agents import strategies
from godman_ai.tools.critics import CriticResult
from godman_ai.tools.critics.factuality_critic import evaluate_factuality
from godman_ai.tools.critics.quality_critic import evaluate_quality
from godman_ai.tools.critics.safety_critic import check_safety
from godman_ai.tools.critics.structural_validator import validate_structure
from godman_ai.models.selector import ModelSelector
from godman_ai.models.registry import ModelRegistry
from godman_ai.models.performance import InMemoryPerformanceStore
from godman_ai.memory.manager import MemoryManager
from godman_ai.workflows.checkpoint_store import CheckpointStore, InMemoryCheckpointStore, WorkflowState
from godman_ai.workflows.distributed_engine import DistributedWorkflowRunner
from godman_ai.workflows.dsl_loader import load_workflow_from_yaml
from godman_ai.workflows.engine import Workflow

logger = logging.getLogger("agents.loop")
logger.addHandler(logging.NullHandler())


CRITIC_MAP = {
    "quality": evaluate_quality,
    "structure": validate_structure,
    "safety": check_safety,
    "factuality": evaluate_factuality,
}


@dataclass
class LoopContext:
    workflow_id: str
    attempts: int = 0
    last_result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentLoop:
    """Orchestrates evaluation → correction → retry cycles."""

    def __init__(
        self,
        store: Optional[CheckpointStore] = None,
        runner: Optional[DistributedWorkflowRunner] = None,
        policy: Optional[AgentPolicy] = None,
        memory_manager: Optional[MemoryManager] = None,
    ) -> None:
        self.store = store or InMemoryCheckpointStore()
        self.memory = memory_manager
        self.runner = runner or DistributedWorkflowRunner(store=self.store, memory_manager=self.memory)
        self.policy = policy or AgentPolicy()
        self.policy_engine = PolicyEngine(self.policy, memory_manager=self.memory)
        self.agent_runs: Dict[str, LoopContext] = {}
        self.model_selector = ModelSelector(ModelRegistry.from_file(Path("configs/models.yaml")) if Path("configs/models.yaml").exists() else ModelRegistry(), InMemoryPerformanceStore())

    def run_with_self_correction(
        self,
        workflow_def: Workflow | str | Dict[str, Any],
        initial_context: Optional[Dict[str, Any]] = None,
        policy: Optional[AgentPolicy] = None,
        distributed: bool = True,
    ) -> str:
        policy_obj = policy or self.policy
        if isinstance(workflow_def, str):
            workflow = load_workflow_from_yaml(workflow_def)
        elif isinstance(workflow_def, Workflow):
            workflow = workflow_def
        else:
            workflow = Workflow([])
        run_id = self.runner.submit_workflow(workflow, initial_context or {}, distributed=distributed)
        ctx = LoopContext(workflow_id=run_id, attempts=0, metadata={"distributed": distributed})
        self.agent_runs[run_id] = ctx
        self.store.append_log(run_id, f"agent_started: distributed={distributed}")
        if self.memory:
            self.memory.record_agent_decision(run_id, "start", {"distributed": distributed})

        result = self.runner.get_run(run_id)
        if result.state != WorkflowState.COMPLETED:
            self._attempt_corrections(workflow, ctx, policy_obj, initial_context or {})
        return run_id

    def _attempt_corrections(
        self,
        workflow: Workflow,
        loop_ctx: LoopContext,
        policy: AgentPolicy,
        base_context: Dict[str, Any],
    ) -> None:
        while loop_ctx.attempts < policy.max_retries:
            loop_ctx.attempts += 1
            self.store.append_log(loop_ctx.workflow_id, f"retry_attempt:{loop_ctx.attempts}")
            try:
                new_run_id = self.runner.submit_workflow(workflow, base_context, distributed=True)
                loop_ctx.workflow_id = new_run_id
                run = self.runner.get_run(new_run_id)
                loop_ctx.last_result = run
                if run.state == WorkflowState.COMPLETED:
                    if self.memory:
                        self.memory.record_workflow_event(run.id, "WORKFLOW_COMPLETE", payload={"attempt": loop_ctx.attempts})
                    return
            except Exception as exc:  # pragma: no cover - safety
                error_class = classify_error(exc)
                self.store.append_log(loop_ctx.workflow_id, f"error:{error_class}")
                if self.memory:
                    self.memory.record_error_event(loop_ctx.workflow_id, str(exc), metadata={"error_class": error_class.value})
                if error_class == ErrorClass.PERMANENT:
                    break

    def handle_step_result(self, result: Any) -> CriticResult:
        critics = self.policy_engine.choose_critics_for_step(None, None)
        outcomes = []
        for critic_name in critics:
            critic_fn = CRITIC_MAP.get(critic_name)
            if critic_fn:
                outcomes.append(critic_fn(result))
        if not outcomes:
            return CriticResult(score=1.0, labels=["pass"], reasons=["no critics configured"])
        avg = sum(c.score for c in outcomes) / len(outcomes)
        labels = [lbl for c in outcomes for lbl in c.labels]
        reasons = [reason for c in outcomes for reason in c.reasons]
        return CriticResult(score=avg, labels=labels, reasons=reasons)

    def apply_strategy(self, error_class: ErrorClass, loop_ctx: LoopContext) -> Dict[str, Any]:
        name = self.policy_engine.choose_strategy(error_class, loop_ctx)
        if name == "retry_same_tool":
            return strategies.retry_same_tool(loop_ctx.metadata)
        if name == "retry_with_alternate_model":
            return strategies.retry_with_alternate_model(
                loop_ctx.metadata,
                self.policy.allowed_models,
                selector=self.model_selector,
            )
        if name == "route_to_alternate_tool":
            return strategies.route_to_alternate_tool(loop_ctx.metadata.get("last_query", ""), self.policy.preferred_tools)
        if name == "escalate_to_human_flag":
            if self.memory:
                self.memory.record_error_event(loop_ctx.workflow_id, "escalated", metadata={})
            return strategies.escalate_to_human_flag("policy escalation")
        if name == "ensemble" and self.policy.use_ensemble_for_critical_tasks:
            models = self.model_selector.select_fallback_models(loop_ctx.metadata.get("task_type", "generic")) or []
            return strategies.ensemble_two_models(loop_ctx.metadata.get("last_query", ""), models, critic=evaluate_quality, selector=self.model_selector)
        return strategies.run_correction_subworkflow({}, loop_ctx.metadata)
