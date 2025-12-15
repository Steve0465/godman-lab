"""Trello board sync, analysis, and audit commands."""
import typer
from pathlib import Path
from typing import Optional
import os
import sys
import json

# Add libs to path so we can import analysis/sync helpers
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "libs"))

app = typer.Typer(help="Trello board sync and analytics")


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise typer.BadParameter(f"Missing required environment variable: {name}")
    return val


@app.command()
def sync(
    board_id: Optional[str] = typer.Option(None, "--board", "-b", help="Trello board ID"),
    out_dir: Path = typer.Option(Path("data/trello"), "--out", "-o", help="Output directory"),
    since_days: int = typer.Option(180, help="How many days of actions to fetch"),
):
    """Fetch and store board snapshot + actions locally."""
    from trello_sync import sync_board

    _require_env("TRELLO_API_KEY")
    _require_env("TRELLO_TOKEN")
    if not board_id:
        board_id = os.getenv("TRELLO_BOARD_ID")
    if not board_id:
        raise typer.BadParameter("Provide --board or set TRELLO_BOARD_ID")

    res = sync_board(board_id=board_id, out_dir=str(out_dir), since_days=since_days)
    typer.echo(json.dumps({
        "snapshot": res.snapshot_path,
        "actions": res.actions_path,
        "counts": res.counts,
        "latest": res.latest_pointer,
    }, indent=2))


@app.command()
def analyze(
    snapshot_path: Path = typer.Argument(..., help="Path to snapshot JSON"),
    actions_path: Path = typer.Argument(..., help="Path to actions JSON"),
    mapping: Optional[Path] = typer.Option(None, "--map", "-m", help="Path to list-role map (yml/json)"),
    out_md: Path = typer.Option(Path("reports/trello_audit.md"), "--out", "-o", help="Output markdown report"),
):
    """Analyze a snapshot + actions and generate a markdown audit report."""
    from trello_analyze import infer_list_roles, compute_metrics, generate_audit_report

    snapshot = json.loads(Path(snapshot_path).read_text())
    actions = json.loads(Path(actions_path).read_text())

    list_names = [l.get("name") for l in snapshot.get("lists", [])]
    list_role_map = infer_list_roles(list_names, str(mapping) if mapping else None)

    metrics = compute_metrics(snapshot, actions, list_role_map)
    # Pass snapshot meta subset for report presentation
    snapshot_meta = {
        "lists": snapshot.get("lists", []),
        "labels": snapshot.get("labels", []),
        "members": snapshot.get("members", []),
    }
    generate_audit_report(metrics, snapshot_meta, str(out_md))
    typer.echo(f"✅ Wrote audit report to {out_md}")


@app.command()
def audit(
    board_id: Optional[str] = typer.Option(None, "--board", "-b", help="Trello board ID"),
    mapping: Optional[Path] = typer.Option(None, "--map", "-m", help="List-role mapping file (yml/json)"),
    out_dir: Path = typer.Option(Path("data/trello"), "--out", "-o", help="Output directory"),
    report: Path = typer.Option(Path("reports/trello_audit.md"), "--report", help="Report output path"),
    since_days: int = typer.Option(180, help="How many days of actions to fetch"),
):
    """Run sync then analysis in one go."""
    from trello_sync import sync_board
    from trello_analyze import infer_list_roles, compute_metrics, generate_audit_report

    _require_env("TRELLO_API_KEY")
    _require_env("TRELLO_TOKEN")
    if not board_id:
        board_id = os.getenv("TRELLO_BOARD_ID")
    if not board_id:
        raise typer.BadParameter("Provide --board or set TRELLO_BOARD_ID")

    res = sync_board(board_id=board_id, out_dir=str(out_dir), since_days=since_days)
    snapshot = json.loads(Path(res.snapshot_path).read_text())
    actions = json.loads(Path(res.actions_path).read_text())

    list_names = [l.get("name") for l in snapshot.get("lists", [])]
    list_role_map = infer_list_roles(list_names, str(mapping) if mapping else None)
    metrics = compute_metrics(snapshot, actions, list_role_map)
    snapshot_meta = {
        "lists": snapshot.get("lists", []),
        "labels": snapshot.get("labels", []),
        "members": snapshot.get("members", []),
    }
    generate_audit_report(metrics, snapshot_meta, str(report))
    typer.echo(json.dumps({
        "snapshot": res.snapshot_path,
        "actions": res.actions_path,
        "report": str(report),
        "counts": res.counts,
    }, indent=2))


if __name__ == "__main__":
    app()
