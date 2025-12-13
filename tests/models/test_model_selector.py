from godman_ai.agents.policy_engine import AgentPolicy
from godman_ai.models.registry import ModelConfig, ModelRegistry
from godman_ai.models.selector import ModelSelector


def test_selector_respects_tags_and_enabled():
    registry = ModelRegistry()
    registry.register_model(ModelConfig(id="fast", provider="local", type="chat", tags=["fast"], latency_hint=0.5))
    registry.register_model(ModelConfig(id="slow", provider="local", type="chat", tags=["slow"], latency_hint=5.0, enabled=False))
    policy = AgentPolicy(preferred_model_tags=["fast"])
    selector = ModelSelector(registry)
    chosen = selector.select_model("chat", policy, {})
    assert chosen == "fast"
    fallbacks = selector.select_fallback_models("chat", policy, {})
    assert "slow" not in fallbacks
