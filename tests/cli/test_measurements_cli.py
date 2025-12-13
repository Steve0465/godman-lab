from typer.testing import CliRunner

from cli.godman.main import app


runner = CliRunner()


def test_measurements_cli_cover(tmp_path):
    sample = tmp_path / "m.txt"
    sample.write_text("A 1 1", encoding="utf-8")
    result = runner.invoke(app, ["measures", "cover", str(sample)])
    assert result.exit_code == 0
    assert "risk" in result.stdout


def test_measurements_cli_liner(tmp_path):
    sample = tmp_path / "m2.txt"
    sample.write_text("B 2 2", encoding="utf-8")
    result = runner.invoke(app, ["measures", "liner", str(sample)])
    assert result.exit_code == 0
