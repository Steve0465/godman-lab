import json
from pathlib import Path
from typing import Optional

import typer

from godman_ai.distributed.job_server import JobServer, run_server
from godman_ai.distributed.worker import Worker
from godman_ai.workflows.distributed_engine import DistributedWorkflowRunner
from godman_ai.workflows.dsl_loader import load_workflow_from_yaml

app = typer.Typer(help="Distributed workflow commands")


@app.command("start")
def start_workflow(
    workflow_file: str = typer.Argument(..., help="Workflow DSL file"),
    distributed: bool = typer.Option(False, "--distributed", help="Run in distributed mode"),
    context: Optional[str] = typer.Option(None, "--context", help="JSON context"),
):
    ctx = json.loads(context) if context else {}
    runner = DistributedWorkflowRunner()
    workflow = load_workflow_from_yaml(workflow_file)
    run_id = runner.submit_workflow(workflow, ctx, distributed=distributed)
    typer.echo(run_id)


@app.command("status")
def status(workflow_id: str = typer.Argument(..., help="Workflow run id")):
    runner = DistributedWorkflowRunner()
    run = runner.get_run(workflow_id)
    typer.echo(json.dumps(run.to_dict(), indent=2, default=str))


@app.command("worker")
def worker_start(
    poll_interval: float = typer.Option(0.1, "--poll-interval", help="Poll interval seconds"),
):
    worker = Worker(DistributedWorkflowRunner(), poll_interval=poll_interval)
    typer.echo("Worker started. Press Ctrl+C to stop.")
    try:
        worker.run_forever()
    except KeyboardInterrupt:
        worker.stop()


@app.command("job-server")
def job_server(port: int = typer.Option(8080, "--port", help="Port to bind")):
    run_server(port=port)
