import os
from pathlib import Path

import pytest

from godman_ai.workflows.checkpoint_store import (
    InMemoryCheckpointStore,
    InvalidStateTransition,
    LocalSqliteCheckpointStore,
    WorkflowState,
)
from godman_ai.workflows.distributed_engine import DistributedWorkflowRunner
from godman_ai.workflows.dsl_loader import load_workflow_from_yaml
from godman_ai.workflows.engine import Context, Step, Workflow


def test_local_mode_preserves_behavior():
    step = Step("hello", lambda ctx: "world")
    wf = Workflow([step])
    runner = DistributedWorkflowRunner()
    run_id = runner.submit_workflow(wf, {"foo": "bar"}, distributed=False)
    assert run_id == "local-run"


def test_distributed_run_records_completion(tmp_path):
    step = Step("one", lambda ctx: "done")
    wf = Workflow([step])
    store = InMemoryCheckpointStore()
    runner = DistributedWorkflowRunner(store=store)
    run_id = runner.submit_workflow(wf, {}, distributed=True)
    run = runner.get_run(run_id)
    assert run.state == WorkflowState.COMPLETED
    assert run.steps["one"].state == WorkflowState.COMPLETED
    assert run.steps["one"].output == "done"


def test_state_transition_guard():
    store = InMemoryCheckpointStore()
    wf = Workflow([])
    run_id = store.create_workflow_run({"steps": []}, {}, {})
    store.update_workflow_state(run_id, WorkflowState.RUNNING)
    with pytest.raises(InvalidStateTransition):
        store.update_workflow_state(run_id, WorkflowState.PENDING)


def test_sqlite_store_roundtrip(tmp_path):
    db_path = tmp_path / "checkpoints.db"
    store = LocalSqliteCheckpointStore(path=db_path)
    run_id = store.create_workflow_run({"steps": [{"name": "a"}]}, {}, {})
    store.update_step_state(run_id, "a", WorkflowState.RUNNING)
    store.update_step_state(run_id, "a", WorkflowState.COMPLETED, output={"ok": True})
    run = store.get_workflow_state(run_id)
    assert run.steps["a"].state == WorkflowState.COMPLETED


def test_dsl_load_and_distributed(tmp_path):
    workflow_file = tmp_path / "wf.yml"
    workflow_file.write_text(
        """
steps:
  - name: greet
    action: set:greeted=yes
"""
    )
    workflow = load_workflow_from_yaml(workflow_file)
    runner = DistributedWorkflowRunner()
    run_id = runner.submit_workflow(workflow, {}, distributed=True)
    run = runner.get_run(run_id)
    assert run.state == WorkflowState.COMPLETED
