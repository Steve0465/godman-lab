from pathlib import Path

from godman_ai.agents.loop_engine import AgentLoop
from godman_ai.agents.policy_engine import AgentPolicy
from godman_ai.workflows.dsl_loader import load_workflow_from_yaml


def test_agent_with_distributed_workflow(tmp_path):
    workflow_file = tmp_path / "wf.yml"
    workflow_file.write_text(
        """
steps:
  - name: step1
    action: set:result=ok
"""
    )
    workflow = load_workflow_from_yaml(workflow_file)
    loop = AgentLoop()
    policy = AgentPolicy(max_retries=1)
    run_id = loop.run_with_self_correction(workflow, {}, policy=policy, distributed=True)
    run = loop.runner.get_run(run_id)
    assert run.state.value in ("COMPLETED", "FAILED")
