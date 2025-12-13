from pathlib import Path

from godman_ai.distributed.job_server import JobServer
from godman_ai.distributed.worker import Worker
from godman_ai.workflows.checkpoint_store import InMemoryCheckpointStore, WorkflowState
from godman_ai.workflows.distributed_engine import DistributedWorkflowRunner
from godman_ai.workflows.engine import Step, Workflow


def test_worker_processes_pending_step():
    store = InMemoryCheckpointStore()
    runner = DistributedWorkflowRunner(store=store)
    # create a pending workflow run directly in the store
    run_id = store.create_workflow_run({"steps": [{"name": "first"}]}, {}, {})
    worker = Worker(runner=runner, poll_interval=0.0)
    processed = worker.run_once()
    assert processed is True
    run = store.get_workflow_state(run_id)
    assert run.steps["first"].state == WorkflowState.COMPLETED
    assert run.state == WorkflowState.COMPLETED


def test_job_server_submit_and_status(tmp_path):
    workflow_file = tmp_path / "wf.yml"
    workflow_file.write_text(
        """
steps:
  - name: ping
    action: set:result=pong
"""
    )
    runner = DistributedWorkflowRunner()
    server = JobServer(runner)
    run_id = server.submit(str(workflow_file), context={"x": 1})
    status = server.status(run_id)
    assert status.state == WorkflowState.COMPLETED
    logs = server.logs(run_id)
    assert "logs" in logs
