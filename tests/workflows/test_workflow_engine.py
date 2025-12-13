import asyncio

import pytest

from godman_ai.workflows.engine import Context, Step, Workflow, WorkflowError


def test_workflow_runs_steps_and_stores_results():
    step1 = Step("first", lambda ctx: "one")
    step2 = Step("second", lambda ctx: "two")
    wf = Workflow([step1, step2])
    ctx = asyncio.run(wf.run())
    assert ctx.get("first") == "one"
    assert ctx.get("second") == "two"


def test_workflow_handles_errors():
    def fail(ctx):
        raise ValueError("boom")

    wf = Workflow([Step("bad", fail)])
    with pytest.raises(WorkflowError):
        asyncio.run(wf.run(Context()))
