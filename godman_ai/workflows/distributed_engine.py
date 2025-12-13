"""Distributed workflow runner built on top of the v1 Workflow engine."""

from __future__ import annotations

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, Optional

from godman_ai.workflows.checkpoint_store import (
    CheckpointStore,
    InMemoryCheckpointStore,
    WorkflowRun,
    WorkflowState,
)
from godman_ai.workflows.engine import Context, Step, Workflow

logger = logging.getLogger("workflows.distributed")
logger.addHandler(logging.NullHandler())


class DistributedWorkflowRunner:
    """Executes workflows locally or via a distributed checkpoint/worker loop."""

    def __init__(
        self,
        store: Optional[CheckpointStore] = None,
        max_parallel: int = 4,
        queue_size: int = 128,
        memory_manager: Optional[Any] = None,
    ) -> None:
        self.store = store or InMemoryCheckpointStore()
        self.max_parallel = max_parallel
        self.queue_size = queue_size
        self._executor = ThreadPoolExecutor(max_workers=max_parallel)
        self.memory_manager = memory_manager

    def submit_workflow(
        self,
        workflow_def: Workflow | Dict[str, Any],
        initial_context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        distributed: bool | None = None,
    ) -> str:
        """
        Submit a workflow for execution.

        If `distributed` is False or options specify local mode, this executes synchronously
        using the v1 Workflow engine. Otherwise it records the workflow in the checkpoint
        store and dispatches step execution with basic concurrency.
        """
        opts = options or {}
        mode_distributed = bool(distributed if distributed is not None else opts.get("distributed", True))
        context_data = initial_context or {}

        workflow = workflow_def if isinstance(workflow_def, Workflow) else _workflow_from_dict(workflow_def)
        if not mode_distributed:
            logger.info("Running workflow locally (compat mode)")
            ctx = asyncio.run(workflow.run(Context(context_data)))
            return ctx.get("workflow_id", "local-run")

        run_id = self.store.create_workflow_run(
            workflow_def=_workflow_to_dict(workflow),
            initial_context=context_data,
            metadata={"options": opts},
        )
        self.store.update_workflow_state(run_id, WorkflowState.RUNNING)
        if self.memory_manager:
            self.memory_manager.record_workflow_event(run_id, "WORKFLOW_START", payload={"options": opts})
        asyncio.run(self._execute_distributed(run_id, workflow, context_data))
        return run_id

    async def _execute_distributed(self, run_id: str, workflow: Workflow, context_data: Dict[str, Any]) -> None:
        context = Context(context_data)
        try:
            # naive parallelism: submit each step to a pool with semaphore
            sem = asyncio.Semaphore(self.max_parallel)
            tasks = []
            for step in workflow.steps:
                tasks.append(self.run_step_distributed(run_id, step, context, sem))
            await asyncio.gather(*tasks)
            self.store.update_workflow_state(run_id, WorkflowState.COMPLETED)
            if self.memory_manager:
                self.memory_manager.record_workflow_event(run_id, "WORKFLOW_COMPLETE", payload={})
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Distributed workflow failed: %s", exc)
            self.store.update_workflow_state(run_id, WorkflowState.FAILED, error=str(exc))
            if self.memory_manager:
                self.memory_manager.record_error_event(run_id, str(exc), metadata={})

    async def run_step_distributed(self, run_id: str, step: Step, context: Context, sem: asyncio.Semaphore) -> None:
        """Execute a workflow step while checkpointing state."""
        async with sem:
            self.store.update_step_state(run_id, step.name, WorkflowState.RUNNING)
            try:
                result = await step.execute(context)
                context.set(step.name, result)
                self.store.update_step_state(run_id, step.name, WorkflowState.COMPLETED, output=result)
                if self.memory_manager:
                    self.memory_manager.record_workflow_event(run_id, "STEP_SUCCESS", payload={"step": step.name})
            except Exception as exc:
                self.store.update_step_state(run_id, step.name, WorkflowState.FAILED, error=str(exc))
                self.store.update_workflow_state(run_id, WorkflowState.FAILED, error=str(exc))
                if self.memory_manager:
                    self.memory_manager.record_error_event(run_id, str(exc), metadata={"step": step.name})
                raise

    def get_run(self, workflow_id: str) -> WorkflowRun:
        return self.store.get_workflow_state(workflow_id)


def _workflow_to_dict(workflow: Workflow) -> Dict[str, Any]:
    steps: Iterable[Step] = workflow.steps
    return {"id": str(uuid.uuid4()), "steps": [{"name": s.name} for s in steps]}


def _workflow_from_dict(data: Dict[str, Any]) -> Workflow:
    steps = [Step(step["name"], lambda ctx, name=step["name"]: ctx.get(name)) for step in data.get("steps", [])]
    return Workflow(steps)
