import json
from typing import Optional

import typer

from godman_ai.capabilities.registry import CapabilityRegistry, CapabilityType
from godman_ai.capabilities.resolver import CapabilityResolver

app = typer.Typer(help="Capability mesh commands")

_registry = CapabilityRegistry()
_resolver = CapabilityResolver(_registry)


@app.command("list")
def list_capabilities(
    type: Optional[CapabilityType] = typer.Option(None, "--type", help="Filter by type"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
):
    types = [type] if type else None
    tags = [tag] if tag else None
    caps = _registry.list_capabilities(types=types, tags=tags)
    typer.echo(json.dumps([c.__dict__ for c in caps], indent=2, default=str))


@app.command("search")
def search(intent: str, tag: Optional[str] = typer.Option(None, "--tag", help="Tag filter")):
    caps = _resolver.suggest_capabilities_for_intent(intent, tags=[tag] if tag else None)
    typer.echo(json.dumps([c.__dict__ for c in caps], indent=2, default=str))


@app.command("show")
def show(capability_id: str):
    cap = _registry.get_capability(capability_id)
    typer.echo(json.dumps(cap.__dict__ if cap else {}, indent=2, default=str))


@app.command("alternatives")
def alternatives(capability_id: str):
    alts = _resolver.suggest_alternatives_for_tool(capability_id)
    typer.echo(json.dumps([c.__dict__ for c in alts], indent=2, default=str))
