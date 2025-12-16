"""Shield Pro Media Box commands."""
import typer
import json
import sys
from pathlib import Path

# Add libs to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "libs"))

from libs.triton import (
    TritonConfig,
    parse_metrics,
    format_gpu_utilization,
    format_throughput_latency,
)

app = typer.Typer(help="Shield Pro Media Box commands")

# Triton subcommand group
triton_app = typer.Typer(help="Triton Inference Server integration")
app.add_typer(triton_app, name="triton")


@triton_app.command()
def plan():
    """Generate Triton inference integration plan documentation.
    
    Creates docs/shield/triton_inference_plan.md with comprehensive
    deployment and integration strategy.
    
    Example:
        godman shield triton plan
    """
    # Get the project root (4 levels up from this file)
    project_root = Path(__file__).parent.parent.parent.parent
    docs_dir = project_root / "docs" / "shield"
    plan_file = docs_dir / "triton_inference_plan.md"
    
    # Check if file already exists
    if plan_file.exists():
        typer.echo(f"✅ Plan already exists: {plan_file}")
        typer.echo("\n📄 File location:")
        typer.echo(f"   {plan_file.absolute()}")
        typer.echo("\n💡 The plan document is ready for review.")
        return
    
    # This shouldn't happen since we created it, but just in case
    typer.echo("❌ Error: Plan template not found", err=True)
    typer.echo("\n💡 The plan document should exist at:")
    typer.echo(f"   {plan_file.absolute()}")
    raise typer.Exit(code=1)


@triton_app.command()
def metrics(
    file_path: Path = typer.Argument(
        ...,
        help="Path to metrics file (Prometheus text or JSON format)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    )
):
    """Format and display Triton metrics from a file.
    
    Reads metrics from a file (Prometheus text or JSON format) and
    displays formatted output including GPU utilization, throughput,
    and latency statistics.
    
    Example:
        godman shield triton metrics sample_metrics.txt
        godman shield triton metrics metrics.json
    """
    try:
        # Read metrics file
        raw_metrics = file_path.read_text()
        
        # Parse metrics
        typer.echo(f"📊 Parsing metrics from: {file_path.name}\n")
        parsed = parse_metrics(raw_metrics)
        
        if not parsed:
            typer.echo("⚠️  No metrics found in file", err=True)
            typer.echo("\n💡 Expected format:")
            typer.echo("   - Prometheus text format (nv_* metrics)")
            typer.echo("   - JSON format with metric keys")
            raise typer.Exit(code=1)
        
        # Display formatted output
        typer.echo("=" * 60)
        typer.echo("  TRITON INFERENCE SERVER METRICS")
        typer.echo("=" * 60)
        typer.echo()
        
        # GPU utilization
        gpu_output = format_gpu_utilization(parsed)
        typer.echo(f"🎮 {gpu_output}")
        typer.echo()
        
        # Throughput and latency
        perf_output = format_throughput_latency(parsed)
        typer.echo("⚡ Performance Metrics:")
        typer.echo("─" * 60)
        for line in perf_output.split('\n'):
            if line.strip():
                typer.echo(f"   {line}")
        
        typer.echo()
        typer.echo("=" * 60)
        typer.echo(f"✅ Metrics parsed successfully from {file_path.name}")
        
    except Exception as e:
        typer.echo(f"❌ Error reading metrics file: {e}", err=True)
        raise typer.Exit(code=1)


@triton_app.command()
def config():
    """Initialize Triton configuration file with default values.
    
    Creates data/shield/triton_config.json with placeholder configuration
    for connecting to a Triton Inference Server.
    
    Example:
        godman shield triton config
    """
    # Get the project root
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data" / "shield"
    config_file = data_dir / "triton_config.json"
    
    # Check if config already exists
    if config_file.exists():
        typer.echo(f"⚠️  Config file already exists: {config_file}")
        
        # Ask user if they want to overwrite
        overwrite = typer.confirm("Do you want to overwrite it?", default=False)
        if not overwrite:
            typer.echo("❌ Cancelled. Existing config file preserved.")
            raise typer.Exit(code=0)
    
    # Create parent directories if needed
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except NotADirectoryError:
        # Handle case where 'data' is a file instead of directory
        typer.echo("❌ Error: 'data' exists as a file, not a directory", err=True)
        typer.echo("\n💡 Please rename or remove the 'data' file to create config.", err=True)
        raise typer.Exit(code=1)
    
    # Create default config
    default_config = TritonConfig(
        endpoint_url="http://nas.local:8000",
        protocol="http",
        model_name="object_detection",
        timeout_seconds=30,
        verify_ssl=True,
    )
    
    # Write config to file
    try:
        with open(config_file, 'w') as f:
            json.dump(default_config.model_dump(), f, indent=2)
        
        typer.echo(f"✅ Config file created: {config_file}")
        typer.echo("\n📄 Configuration:")
        typer.echo("─" * 60)
        typer.echo(json.dumps(default_config.model_dump(), indent=2))
        typer.echo("─" * 60)
        typer.echo("\n💡 Next steps:")
        typer.echo("   1. Edit the config file to match your Triton server")
        typer.echo("   2. Update endpoint_url to your server address")
        typer.echo("   3. Set model_name to your default model")
        
    except Exception as e:
        typer.echo(f"❌ Error creating config file: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
