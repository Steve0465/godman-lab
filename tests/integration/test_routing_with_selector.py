from godman_ai.agents.policy_engine import AgentPolicy
from godman_ai.models.registry import ModelConfig, ModelRegistry
from godman_ai.models.router_v3 import ModelRouterV3


def test_router_v3_with_fallbacks():
    registry = ModelRegistry()
    registry.register_model(ModelConfig(id="primary", provider="local", type="chat", tags=["fast"]))
    registry.register_model(ModelConfig(id="fallback", provider="local", type="chat", tags=["cheap"]))
    router = ModelRouterV3(registry=registry)
    result = router.route(task_type="chat", query="hi", policy=AgentPolicy())
    assert result["model"] in {"primary", "fallback"}
    assert isinstance(result["fallbacks"], list)
