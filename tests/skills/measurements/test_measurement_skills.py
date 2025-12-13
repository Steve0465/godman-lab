import asyncio

from examples.skills.measurements.skill_ab_plot_parse import main as ab_parse_main
from examples.skills.measurements.skill_breakline_validator import main as breakline_main
from examples.skills.measurements.skill_manufacturing_risk_assessor import main as risk_main
from examples.skills.measurements.skill_measurement_ocr import main as ocr_main
from examples.skills.measurements.skill_pool_shape_analyzer import main as shape_main


def test_measurement_skill_flow(tmp_path):
    sample = tmp_path / "ab.txt"
    sample.write_text("A 10 10\nB 12 11", encoding="utf-8")
    ocr = asyncio.run(ocr_main.run(str(sample)))
    ab = asyncio.run(ab_parse_main.run(ocr["text"]))
    shape = asyncio.run(shape_main.run(ab["ab_data"], {}))
    issues = asyncio.run(breakline_main.run(ab["ab_data"], shape["shape"]))
    risk = asyncio.run(risk_main.run(ab["ab_data"], shape["shape"], issues["issues"]))
    assert "ab_data" in ab
    assert isinstance(shape["shape"], str)
    assert isinstance(issues["issues"], list)
    assert risk["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
