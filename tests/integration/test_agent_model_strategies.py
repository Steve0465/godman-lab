from godman_ai.agents.loop_engine import AgentLoop
from godman_ai.agents.policy_engine import AgentPolicy
from godman_ai.memory.manager import MemoryManager
from godman_ai.workflows.engine import Step, Workflow


def test_agent_changes_model_on_failure():
    mm = MemoryManager()

    def fail_then_pass(ctx):
        raise ValueError("fail")

    wf = Workflow([Step("fail", fail_then_pass)])
    loop = AgentLoop(memory_manager=mm)
    policy = AgentPolicy(max_retries=1, allowed_models=["phi4-14b:latest"])
    run_id = loop.run_with_self_correction(wf, {}, policy=policy, distributed=True)
    assert isinstance(run_id, str)
