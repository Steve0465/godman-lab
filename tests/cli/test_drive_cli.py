from typer.testing import CliRunner

from cli.godman.main import app


runner = CliRunner()


def test_drive_cli_ingest(tmp_path):
    sample = tmp_path / "doc.txt"
    sample.write_text("data", encoding="utf-8")
    result = runner.invoke(app, ["drive", "ingest", str(sample)])
    assert result.exit_code == 0


def test_drive_cli_classify(tmp_path):
    sample = tmp_path / "receipt.pdf"
    sample.write_text("data", encoding="utf-8")
    result = runner.invoke(app, ["drive", "classify", str(sample)])
    assert result.exit_code == 0
