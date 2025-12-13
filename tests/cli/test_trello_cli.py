from typer.testing import CliRunner

from cli.godman.main import app


runner = CliRunner()


def test_trello_cli_fetch():
    result = runner.invoke(app, ["trello", "fetch", "board1"])
    assert result.exit_code == 0
    assert "fetched" in result.stdout


def test_trello_cli_workflow():
    result = runner.invoke(app, ["trello", "workflow", "daily", "board1"])
    assert result.exit_code == 0
