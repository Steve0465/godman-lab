import typer

# Import the sync subcommands
from cli.godman import sync as sync_cli
from cli.godman import tools as tools_cli

app = typer.Typer(help="Godman Automation Lab CLI.")

# Mount the sync Typer app under: godman sync ...
app.add_typer(sync_cli.app, name="sync")

# Mount the tools Typer app under: godman tool ...
app.add_typer(tools_cli.app, name="tool")


@app.command()
def health():
    """
    Simple health check for the godman AI framework.
    """
    typer.echo("godman_ai CLI OK")


if __name__ == "__main__":
    app()
