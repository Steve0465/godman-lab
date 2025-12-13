import asyncio

from godman_ai.workflows.measurements import (
    run_liner_measurement_review,
    run_safety_cover_review,
)


def test_safety_cover_workflow_runs(tmp_path):
    wf = run_safety_cover_review(str(tmp_path / "file.pdf"))
    ctx = asyncio.run(wf.run())
    assert ctx.get("summary") == "ok"


def test_liner_workflow_runs(tmp_path):
    wf = run_liner_measurement_review(str(tmp_path / "file.pdf"))
    ctx = asyncio.run(wf.run())
    assert ctx.get("summary") == "ok"
