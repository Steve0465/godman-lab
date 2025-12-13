import json
from pathlib import Path
from typing import Optional

import typer

from godman_ai.workflows import load_workflow_from_yaml
from godman_ai.workflows.receipts import load_receipt_full, load_receipt_monthly

app = typer.Typer(help="Receipt automation commands")


@app.command("parse")
def parse(file: str):
    text = Path(file).read_text(encoding="utf-8") if Path(file).exists() else ""
    typer.echo(json.dumps({"text": text or "mock text"}))


@app.command("classify")
def classify(file: str):
    vendor = Path(file).stem
    category = "Meals" if "coffee" in vendor.lower() else "Other"
    typer.echo(json.dumps({"vendor": vendor, "category": category}))


@app.command("workflow")
def workflow(name: str, file: str):
    if name == "receipts/full":
        wf = load_receipt_full()
    else:
        wf = load_workflow_from_yaml(file)
    import asyncio
    ctx = asyncio.run(wf.run())
    typer.echo(json.dumps(ctx.data, default=str))


@app.command("month")
def month_summary(folder: str):
    wf = load_receipt_monthly()
    typer.echo(f"aggregated {folder}: {wf}")
