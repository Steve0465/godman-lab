import json
import typer
from rich.console import Console

from libs.att_scraper import ATTClient


app = typer.Typer(help="AT&T account management and status tools")
console = Console()


@app.command()
def status():
    """Get AT&T network status and outage information."""
    try:
        with ATTClient() as client:
            data = client.get_status()
            print(json.dumps(data, indent=2))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
