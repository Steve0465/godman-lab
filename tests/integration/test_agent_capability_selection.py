from godman_ai.agents.loop_engine import AgentLoop
from godman_ai.agents.policy_engine import AgentPolicy
from godman_ai.capabilities.registry import CapabilityMetadata, CapabilityRegistry, CapabilityType, register_tool_capability
from godman_ai.capabilities.resolver import CapabilityResolver
from godman_ai.workflows.engine import Step, Workflow


def test_agent_uses_capability_resolver(monkeypatch):
    registry = CapabilityRegistry()
    register_tool_capability(registry, type("Tool", (), {"name": "cap_tool", "description": "does task"}))
    resolver = CapabilityResolver(registry=registry)

    def fake_find(query, ctx, pol):
        return registry.list_capabilities()

    monkeypatch.setattr(resolver, "find_tools_for_task", fake_find)
    loop = AgentLoop()
    policy = AgentPolicy(max_retries=1, preferred_capability_tags=["test"])
    wf = Workflow([Step("noop", lambda ctx: "ok")])
    run_id = loop.run_with_self_correction(wf, {}, policy=policy, distributed=True)
    assert isinstance(run_id, str)
