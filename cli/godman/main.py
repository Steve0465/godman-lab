"""Main CLI entry point for godman automation lab."""
import typer
from godman.commands import receipts

app = typer.Typer(
    name="godman",
    help="Godman Automation Lab - Your personal automation toolkit",
    add_completion=False,
)

# Register command modules
app.add_typer(receipts.app, name="receipts", help="Receipt processing commands")


@app.command()
def version():
    """Show version information."""
    from godman import __version__
    typer.echo(f"godman version {__version__}")


@app.command()
def status():
    """Show system status and configuration."""
    typer.echo("🚀 Godman Automation Lab")
    typer.echo("Status: All systems operational")
    typer.echo("\nAvailable modules:")
    typer.echo("  • receipts - Receipt processing and OCR")
    typer.echo("  • expenses - Expense tracking and summaries")
    typer.echo("\nRun 'godman --help' for more information")


if __name__ == "__main__":
    app()
