from typer.testing import CliRunner

from cli.godman.main import app


runner = CliRunner()


def test_receipts_cli_parse(tmp_path):
    sample = tmp_path / "r.txt"
    sample.write_text("coffee 10", encoding="utf-8")
    result = runner.invoke(app, ["receipts", "parse", str(sample)])
    assert result.exit_code == 0
    assert "mock text" in result.stdout or "coffee" in result.stdout
