import asyncio

from godman_ai.workflows.drive import (
    load_drive_auto_ingest,
    load_drive_cleanup,
    load_drive_crosslink,
)


def test_drive_auto_ingest_workflow():
    wf = load_drive_auto_ingest()
    ctx = asyncio.run(wf.run())
    assert ctx.get("stored") == "ok"


def test_drive_cleanup_workflow():
    wf = load_drive_cleanup()
    ctx = asyncio.run(wf.run())
    assert "actions" in ctx.data


def test_drive_crosslink_workflow():
    wf = load_drive_crosslink()
    ctx = asyncio.run(wf.run())
    assert ctx.get("link") == "ok"
