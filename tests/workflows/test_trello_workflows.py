import asyncio

from godman_ai.workflows.trello import load_trello_daily, load_trello_job_summary


def test_trello_daily_workflow_runs():
    wf = load_trello_daily()
    ctx = asyncio.run(wf.run())
    assert ctx.get("summary") == "ok"


def test_trello_job_workflow_runs():
    wf = load_trello_job_summary()
    ctx = asyncio.run(wf.run())
    assert ctx.get("materials") == "list"
