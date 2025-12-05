"""Main CLI entry point for godman automation lab."""
import typer
from pathlib import Path
from godman.commands import receipts

app = typer.Typer(
    name="godman",
    help="Godman Automation Lab - Your personal automation toolkit",
    add_completion=False,
)

# Register command modules
app.add_typer(receipts.app, name="receipts", help="Receipt processing commands")


@app.command()
def run(input: str = typer.Argument(..., help="File path or raw string to process")):
    """
    Run orchestrator: accepts a file path or raw string, detects type, and routes through AI system.
    
    Examples:
        godman run scans/receipt.pdf
        godman run data/expenses.csv
        godman run "analyze this text"
    """
    from godman_ai.orchestrator import Orchestrator
    
    typer.echo(f"🎭 Godman Orchestrator v2")
    typer.echo(f"📋 Input: {input}\n")
    
    # Initialize orchestrator
    orchestrator = Orchestrator()
    orchestrator.load_tools_from_package("godman_ai.tools")
    
    typer.echo(f"✅ Loaded {len(orchestrator.tool_classes)} tools")
    typer.echo(f"🚀 Processing...\n")
    
    # Run task
    result = orchestrator.run_task(input)
    
    # Display results
    if result["status"] == "success":
        typer.echo(f"✅ Success!")
        typer.echo(f"📊 Input Type: {result['input_type']}")
        typer.echo(f"🔧 Tool Used: {result['tool']}")
        typer.echo(f"\n📋 Result:")
        typer.echo(result["result"])
    else:
        typer.echo(f"❌ Error: {result['error']}", err=True)
        typer.echo(f"🔍 Error Type: {result.get('error_type', 'Unknown')}", err=True)
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show version information."""
    from godman import __version__
    typer.echo(f"godman version {__version__}")


@app.command()
def status():
    """Show system status and configuration."""
    from godman_ai.orchestrator import Orchestrator
    
    typer.echo("🚀 Godman Automation Lab")
    typer.echo("Status: All systems operational")
    
    # Show orchestrator status
    orchestrator = Orchestrator()
    orchestrator.load_tools_from_package("godman_ai.tools")
    orch_status = orchestrator.status()
    
    typer.echo(f"\n🎭 Orchestrator:")
    typer.echo(f"  • Tools registered: {orch_status['tools_registered']}")
    typer.echo(f"  • Tools available: {', '.join(orch_status['tool_names'])}")
    typer.echo(f"  • Ready: {'✅' if orch_status['ready'] else '❌'}")
    
    typer.echo("\n📦 Available modules:")
    typer.echo("  • receipts - Receipt processing and OCR")
    typer.echo("  • expenses - Expense tracking and summaries")
    typer.echo("\nRun 'godman --help' for more information")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
