import asyncio

from examples.skills.measurements.skill_measurement_ocr import main as ocr_main
from examples.skills.measurements.skill_measurement_parse import main as parse_main
from examples.skills.measurements.skill_measurement_boundary import main as boundary_main
from examples.skills.measurements.skill_breakline_validate import main as breakline_main
from examples.skills.measurements.skill_measurement_normalize import main as normalize_main
from examples.skills.measurements.skill_measurement_fitment import main as fitment_main


def test_measurement_pack_flow(tmp_path):
    sample = tmp_path / "measure.txt"
    sample.write_text("A 1 1\nB 2 2", encoding="utf-8")
    ocr = asyncio.run(ocr_main.run(str(sample)))
    table = asyncio.run(parse_main.run(ocr["text"]))
    ab_points = [{"label": row[0], "distance_a": float(row[1]), "distance_b": float(row[2])} for row in table["table"]]
    boundaries = asyncio.run(boundary_main.run(ab_points))
    issues = asyncio.run(breakline_main.run(boundaries["boundaries"]))
    normalized = asyncio.run(normalize_main.run(ab_points))
    fitment = asyncio.run(fitment_main.run(normalized["normalized"], boundaries["boundaries"]))
    assert fitment["fitment"] in {"READY", "UNKNOWN"}
