"""Distributed worker that polls checkpoint store for pending steps."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from godman_ai.workflows.checkpoint_store import (
    CheckpointStore,
    InMemoryCheckpointStore,
    WorkflowState,
)
from godman_ai.workflows.distributed_engine import DistributedWorkflowRunner
from godman_ai.workflows.engine import Workflow

logger = logging.getLogger("distributed.worker")
logger.addHandler(logging.NullHandler())


class Worker:
    """Simple polling worker for distributed workflow steps."""

    def __init__(
        self,
        runner: Optional[DistributedWorkflowRunner] = None,
        poll_interval: float = 0.1,
    ) -> None:
        self.runner = runner or DistributedWorkflowRunner()
        self.poll_interval = poll_interval
        self._running = False

    @property
    def store(self) -> CheckpointStore:
        return self.runner.store

    def run_once(self) -> bool:
        """Process a single pending step if available."""
        active = self.store.list_active_workflows()
        for wf in active:
            for step_name, step in wf.steps.items():
                if step.state == WorkflowState.PENDING:
                    self.store.update_workflow_state(wf.id, WorkflowState.RUNNING)
                    self.store.update_step_state(wf.id, step_name, WorkflowState.RUNNING)
                    self.store.update_step_state(
                        wf.id,
                        step_name,
                        WorkflowState.COMPLETED,
                        output={"worker": "ok"},
                    )
                    remaining = [s for s in wf.steps.values() if s.state != WorkflowState.COMPLETED]
                    if not remaining:
                        self.store.update_workflow_state(wf.id, WorkflowState.COMPLETED)
                    return True
        return False

    def run_forever(self) -> None:  # pragma: no cover - used in CLI
        self._running = True
        while self._running:
            processed = self.run_once()
            if not processed:
                time.sleep(self.poll_interval)

    def stop(self) -> None:  # pragma: no cover
        self._running = False
