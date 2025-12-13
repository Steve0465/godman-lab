import asyncio

from godman_ai.workflows.measurements import (
    load_measurement_full,
    load_trello_measurement_auto,
    load_cover_fit_estimator,
)


def test_measurement_full_workflow():
    wf = load_measurement_full()
    ctx = asyncio.run(wf.run())
    assert ctx.get("summary") == "ok"


def test_trello_measurement_auto():
    wf = load_trello_measurement_auto()
    ctx = asyncio.run(wf.run())
    assert ctx.get("summary") == "ok"


def test_cover_fit_workflow():
    wf = load_cover_fit_estimator()
    ctx = asyncio.run(wf.run())
    assert ctx.get("fitment") == "READY"
