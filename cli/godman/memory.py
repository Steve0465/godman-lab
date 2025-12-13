import json
from typing import Optional

import typer

from godman_ai.memory.manager import MemoryManager

app = typer.Typer(help="Memory and knowledge graph commands")


@app.command("recent")
def recent(
    type: Optional[str] = typer.Option(None, "--type", help="Filter by type"),
    limit: int = typer.Option(20, "--limit", "-n", help="Limit results"),
):
    mm = MemoryManager()
    records = mm.long_term.query_records(types=[type] if type else None)
    for rec in records[:limit]:
        typer.echo(json.dumps(rec.__dict__, default=str))


@app.command("workflow-history")
def workflow_history(name: str):
    mm = MemoryManager()
    records = mm.get_successful_patterns_for_workflow(name)
    typer.echo(json.dumps([r.__dict__ for r in records], indent=2, default=str))


@app.command("tool-history")
def tool_history(name: str):
    mm = MemoryManager()
    records = mm.get_recent_failures_for_tool(name, limit=10)
    typer.echo(json.dumps([r.__dict__ for r in records], indent=2, default=str))


@app.command("graph-show")
def graph_show(node_id: str):
    mm = MemoryManager()
    node = mm.graph.nodes.get(node_id)
    typer.echo(json.dumps(node.__dict__ if node else {}, indent=2, default=str))


@app.command("graph-neighbors")
def graph_neighbors(node_id: str, relation: Optional[str] = typer.Option(None, "--relation", help="Filter relation")):
    mm = MemoryManager()
    neighbors = mm.graph.neighbors(node_id, relation)
    typer.echo(json.dumps([n.__dict__ for n in neighbors], indent=2, default=str))
