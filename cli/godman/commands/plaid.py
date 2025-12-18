import typer

app = typer.Typer(help="Plaid banking integration")


@app.command("list-tokens")
def list_tokens():
    typer.echo("✅ Plaid command is wired correctly (no tokens yet).")

