import json
import typer
from rich.console import Console

from libs.att_scraper import ATTClient


app = typer.Typer(help="AT&T account management and status tools")
console = Console()


@app.command()
def status(
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging")
):
    """Get AT&T network status and outage information."""
    import logging
    
    if debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        with ATTClient(headless=headless) as client:
            data = client.get_status()
            print(json.dumps(data, indent=2))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if debug:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
