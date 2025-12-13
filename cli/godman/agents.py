import json
from pathlib import Path
from typing import Optional

import typer

from godman_ai.agents.loop_engine import AgentLoop
from godman_ai.agents.policy_engine import AgentPolicy

app = typer.Typer(help="Agent loop commands")


def _load_policy(path: Optional[str]) -> AgentPolicy:
    if not path:
        return AgentPolicy()
    text = Path(path).read_text()
    try:
        import yaml  # type: ignore
    except ImportError:
        yaml = None
    data = json.loads(text) if path.endswith(".json") or not yaml else yaml.safe_load(text)
    return AgentPolicy.from_dict(data or {})


@app.command("run")
def agent_run(
    workflow_file: str = typer.Argument(..., help="Workflow DSL path"),
    distributed: bool = typer.Option(False, "--distributed", help="Use distributed runner"),
    policy: Optional[str] = typer.Option(None, "--policy", help="Policy file (json/yaml)"),
):
    loop = AgentLoop()
    pol = _load_policy(policy)
    run_id = loop.run_with_self_correction(workflow_file, initial_context={}, policy=pol, distributed=distributed)
    typer.echo(run_id)


@app.command("status")
def agent_status(run_id: str = typer.Argument(..., help="Agent-managed workflow id")):
    loop = AgentLoop()
    run = loop.runner.get_run(run_id)
    typer.echo(json.dumps(run.to_dict(), indent=2, default=str))


@app.command("logs")
def agent_logs(run_id: str = typer.Argument(..., help="Agent-managed workflow id")):
    loop = AgentLoop()
    store = loop.store
    logs = getattr(store, "logs", {})
    typer.echo("\n".join(logs.get(run_id, [])))
