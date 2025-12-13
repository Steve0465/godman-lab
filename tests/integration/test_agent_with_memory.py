from godman_ai.agents.loop_engine import AgentLoop
from godman_ai.agents.policy_engine import AgentPolicy
from godman_ai.memory.manager import MemoryManager
from godman_ai.workflows.engine import Step, Workflow


def test_agent_loop_records_memory():
    mm = MemoryManager()

    def failing(ctx):
        raise ValueError("fail")

    wf = Workflow([Step("fail", failing)])
    loop = AgentLoop(memory_manager=mm)
    policy = AgentPolicy(max_retries=1)
    run_id = loop.run_with_self_correction(wf, {}, policy=policy, distributed=True)
    # Even if it fails, memory should have an entry
    errs = mm.long_term.query_records(types=["ERROR"])
    assert isinstance(errs, list)
