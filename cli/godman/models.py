import json
from pathlib import Path

import typer

from godman_ai.models.registry import ModelRegistry
from godman_ai.models.performance import InMemoryPerformanceStore, make_perf_record
from godman_ai.models.selector import ModelSelector

app = typer.Typer(help="Model registry and routing commands")


def _registry() -> ModelRegistry:
    config_path = Path("configs/models.yaml")
    if config_path.exists():
        return ModelRegistry.from_file(config_path)
    return ModelRegistry()


@app.command("list")
def list_models():
    reg = _registry()
    models = reg.list_models()
    typer.echo(json.dumps([m.__dict__ for m in models], indent=2))


@app.command("stats")
def stats(model_id: str):
    store = InMemoryPerformanceStore()
    typer.echo(json.dumps(store.get_stats(model_id), indent=2))


@app.command("test")
def test_model(model_id: str, prompt: str = typer.Option("hello", "--prompt", help="Prompt to send")):
    selector = ModelSelector(_registry())
    chosen = selector.select_model("generic", None, {})
    typer.echo(f"Selected model: {chosen or model_id} for prompt: {prompt}")
