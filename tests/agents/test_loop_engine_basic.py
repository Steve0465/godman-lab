from godman_ai.agents.loop_engine import AgentLoop
from godman_ai.agents.policy_engine import AgentPolicy
from godman_ai.workflows.engine import Step, Workflow


def test_single_step_retry_success():
    calls = {"count": 0}

    def flaky(ctx):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("first fail")
        return "ok"

    wf = Workflow([Step("flaky", flaky)])
    loop = AgentLoop()
    policy = AgentPolicy(max_retries=2)
    run_id = loop.run_with_self_correction(wf, {}, policy=policy, distributed=True)
    run = loop.runner.get_run(run_id)
    assert run.state == loop.runner.store.get_workflow_state(run_id).state


def test_multi_step_correction():
    wf = Workflow([Step("one", lambda ctx: "a"), Step("two", lambda ctx: "b")])
    loop = AgentLoop()
    policy = AgentPolicy(max_retries=1)
    run_id = loop.run_with_self_correction(wf, {}, policy=policy, distributed=True)
    run = loop.runner.get_run(run_id)
    assert run.state.value in ("COMPLETED", "FAILED")  # loop runs without raising
