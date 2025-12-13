from godman_ai.agents import strategies


def test_retry_same_tool():
    result = strategies.retry_same_tool({"foo": "bar"})
    assert result["action"] == "retry"


def test_retry_with_alternate_model():
    result = strategies.retry_with_alternate_model({"last_query": "code"}, allowed_models=["phi4-14b:latest"])
    assert result["action"] == "retry"
    assert "force_model" in result["context_updates"]


def test_route_to_alternate_tool():
    result = strategies.route_to_alternate_tool("analyze data", preferred_tools=["a"])
    assert result["action"] == "retry"


def test_escalate():
    result = strategies.escalate_to_human_flag("needs review")
    assert result["action"] == "escalate"
