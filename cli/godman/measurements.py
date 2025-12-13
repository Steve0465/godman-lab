import json
import asyncio
from pathlib import Path
from typing import Optional

import typer

from godman_ai.workflows.measurements import (
    run_liner_measurement_review,
    run_safety_cover_review,
    load_measurement_full,
    load_trello_measurement_auto,
    load_cover_fit_estimator,
)

app = typer.Typer(help="Safety cover and liner measurement commands")


def _load_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _run_workflow(wf):
    return asyncio.run(wf.run())


@app.command("cover")
def cover_review(file_or_folder: str, report: Optional[str] = typer.Option(None, "--out", help="Write report to path")):
    wf = run_safety_cover_review(file_or_folder)
    ctx = _run_workflow(wf)
    summary = {"shape": ctx.get("shape"), "risk": ctx.get("risk_level"), "issues": ctx.get("issues")}
    typer.echo(json.dumps(summary, default=str))
    if report:
        Path(report).write_text(f"# Cover Review\n\n{json.dumps(summary, indent=2)}", encoding="utf-8")


@app.command("liner")
def liner_review(file_or_folder: str, report: Optional[str] = typer.Option(None, "--out", help="Write report to path")):
    wf = run_liner_measurement_review(file_or_folder)
    ctx = _run_workflow(wf)
    summary = {"shape": ctx.get("shape"), "risk": ctx.get("risk_level"), "issues": ctx.get("issues")}
    typer.echo(json.dumps(summary, default=str))
    if report:
        Path(report).write_text(f"# Liner Review\n\n{json.dumps(summary, indent=2)}", encoding="utf-8")


@app.command("analyze")
def analyze(file: str):
    wf = load_measurement_full()
    ctx = _run_workflow(wf)
    typer.echo(json.dumps(ctx.data, default=str))


@app.command("fitment")
def fitment(file: str):
    wf = load_cover_fit_estimator()
    ctx = _run_workflow(wf)
    typer.echo(json.dumps({"fitment": ctx.get("fitment")}, default=str))


@app.command("workflow")
def workflow(mode: str, resource: str):
    if mode == "full":
        wf = load_measurement_full()
    elif mode == "trello":
        wf = load_trello_measurement_auto()
    else:
        wf = load_measurement_full()
    ctx = _run_workflow(wf)
    typer.echo(json.dumps(ctx.data, default=str))
