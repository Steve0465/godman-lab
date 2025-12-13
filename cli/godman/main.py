import sys
import typer
from rich.console import Console

# Import the sync subcommands
from cli.godman import sync as sync_cli
from cli.godman import tools as tools_cli
from cli.godman import ai as ai_cli
from cli.godman import health as health_cli
from cli.godman import att as att_cli
from cli.godman import workflows as workflows_cli
from cli.godman import agents as agents_cli
from cli.godman import memory as memory_cli
from cli.godman import models as models_cli
from cli.godman import capabilities as capabilities_cli
from cli.godman import receipts as receipts_cli
from cli.godman import trello as trello_cli
from cli.godman import trello_analyze as trello_analyze_cli
from cli.godman import measurements as measurements_cli
from cli.godman import passwords as passwords_cli
from cli.godman import drive as drive_cli
from cli.godman import tax as tax_cli

app = typer.Typer(help="Godman Automation Lab CLI.")
console = Console()

# Mount the sync Typer app under: godman sync ...
app.add_typer(sync_cli.app, name="sync")

# Mount the tools Typer app under: godman tool ...
app.add_typer(tools_cli.app, name="tool")

# Mount the AI Typer app under: godman ai ...
app.add_typer(ai_cli.ai_app, name="ai")

# Mount the health Typer app under: godman health ...
app.add_typer(health_cli.app, name="health")

# Mount the att Typer app under: godman att ...
app.add_typer(att_cli.app, name="att")
# Distributed workflows
app.add_typer(workflows_cli.app, name="workflow")
# Agents
app.add_typer(agents_cli.app, name="agent")
# Memory
app.add_typer(memory_cli.app, name="memory")
# Models
app.add_typer(models_cli.app, name="models")
# Capabilities
app.add_typer(capabilities_cli.app, name="capabilities")
# Receipts
app.add_typer(receipts_cli.app, name="receipts")
# Trello
app.add_typer(trello_cli.app, name="trello")
# Trello Analysis
trello_cli.app.add_typer(trello_analyze_cli.app, name="analyze")
# Measurements
app.add_typer(measurements_cli.app, name="measures")
# Drive
app.add_typer(drive_cli.app, name="drive")
# Password ingestion
app.add_typer(passwords_cli.app, name="passwords")
# Tax archive management
app.add_typer(tax_cli.app, name="tax")


@app.command()
def status():
    """
    Simple health check for the godman AI framework.
    """
    typer.echo("godman_ai CLI OK")


@app.command()
def install():
    """
    Auto-install all required LLMs and perform full system health check.
    
    This will:
    - Check for installed models
    - Pull any missing models (deepseek-r1:14b, phi4:14b, llama3.1:8b, qwen2.5:7b)
    - Run comprehensive health check
    - Display results
    """
    from godman_ai.diagnostics.installer import install_all
    
    console.print("\n[bold cyan]Starting Godman AI Installation...[/bold cyan]\n")
    
    try:
        result = install_all()
        
        console.print("\n[bold]Installation Summary:[/bold]")
        console.print(f"  Ollama online: {result['ollama_online']}")
        console.print(f"  Models installed: {sum(result['models_available'].values())}/4")
        console.print(f"  All systems pass: {result['all_systems_pass']}")
        
        sys.exit(0 if result["all_systems_pass"] else 1)
    except Exception as e:
        console.print(f"[red]Installation failed: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    app()
