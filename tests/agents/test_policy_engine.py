from godman_ai.agents.error_classifier import ErrorClass
from godman_ai.agents.policy_engine import AgentPolicy, PolicyEngine


def test_policy_serialization():
    data = {"max_retries": 2, "critics_to_run": ["quality"]}
    policy = AgentPolicy.from_dict(data)
    assert policy.max_retries == 2
    assert policy.to_dict()["critics_to_run"] == ["quality"]


def test_strategy_selection():
    engine = PolicyEngine(AgentPolicy())
    assert engine.choose_strategy(ErrorClass.TRANSIENT, None) == "retry_same_tool"
    assert engine.choose_strategy(ErrorClass.TOOL_CONFIG, None) == "route_to_alternate_tool"
