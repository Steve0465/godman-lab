from godman_ai.workflows.receipts import load_receipt_full, load_receipt_monthly
import asyncio


def test_receipt_workflow_full_runs():
    wf = load_receipt_full()
    ctx = asyncio.run(wf.run())
    assert ctx.get("category") == "Meals"


def test_receipt_workflow_monthly_runs():
    wf = load_receipt_monthly()
    ctx = asyncio.run(wf.run())
    assert ctx.get("statement") == "ready"
