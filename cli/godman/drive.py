import json
import asyncio
from pathlib import Path
from typing import Optional

import typer

from godman_ai.skills.drive import (
    drive_copy,
    drive_download,
    drive_move,
    drive_search,
    drive_share,
    drive_upload,
)
from godman_ai.workflows.drive import (
    load_drive_auto_ingest,
    load_drive_cleanup,
    load_drive_crosslink,
)

app = typer.Typer(help="Drive automation commands (mocked)")


@app.command("search")
def search(q: str):
    result = drive_search(q)
    typer.echo(json.dumps(result, default=str))


@app.command("upload")
def upload(path: str, folder_id: Optional[str] = None):
    result = drive_upload(path, folder_id)
    typer.echo(json.dumps(result, default=str))


@app.command("download")
def download(file_id: str, dest: str):
    result = drive_download(file_id, dest)
    typer.echo(json.dumps(result, default=str))


@app.command("share")
def share(file_id: str, email: str, role: str = "reader"):
    result = drive_share(file_id, email, role)
    typer.echo(json.dumps(result, default=str))


@app.command("ingest")
def ingest(file: str):
    wf = load_drive_auto_ingest()
    ctx = asyncio.run(wf.run())
    typer.echo(json.dumps(ctx.data, default=str))


@app.command("cleanup")
def cleanup(folder: str):
    wf = load_drive_cleanup()
    ctx = asyncio.run(wf.run())
    typer.echo(json.dumps(ctx.data, default=str))


@app.command("classify")
def classify(file: str):
    name = Path(file).name.lower()
    cls = "receipt" if "receipt" in name else "general"
    typer.echo(json.dumps({"classification": cls}))


@app.command("auto")
def auto(file: str):
    wf = load_drive_auto_ingest()
    ctx = asyncio.run(wf.run())
    typer.echo(json.dumps(ctx.data, default=str))


@app.command("trello-link")
def trello_link(card_id: str):
    wf = load_drive_crosslink()
    ctx = asyncio.run(wf.run())
    typer.echo(json.dumps({"card": card_id, "link": ctx.get("link")}, default=str))
