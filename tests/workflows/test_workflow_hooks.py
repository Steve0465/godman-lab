import asyncio

import pytest

from godman_ai.workflows.engine import Context, Step, Workflow, WorkflowError


def test_workflow_before_after_hooks_and_early_exit():
    order = []

    def before(ctx):
        order.append("before")

    def after(ctx):
        order.append("after")

    def first(ctx):
        order.append("first")
        ctx.set("stop", True)
        return "done"

    def second(ctx):
        order.append("second")
        if ctx.get("stop"):
            return "skipped"
        return "ran"

    wf = Workflow([Step("first", first), Step("second", second)], before_all=before, after_all=after)
    ctx = asyncio.run(wf.run(Context()))
    assert ctx.get("first") == "done"
    assert ctx.get("second") == "skipped"
    assert order == ["before", "first", "second", "after"]


def test_workflow_on_error_invoked():
    flags = {"error": False}

    def failing(ctx):
        raise ValueError("boom")

    def on_error(ctx):
        flags["error"] = True

    wf = Workflow([Step("fail", failing)], on_error=on_error)
    with pytest.raises(WorkflowError):
        asyncio.run(wf.run(Context()))
    assert flags["error"]
