import typer

app = typer.Typer()

@app.command()
def health():
    """
    Simple health check for the godman AI framework.
    """
    typer.echo("godman_ai CLI OK")

if __name__ == "__main__":
    app()
