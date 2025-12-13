from godman_ai.models.registry import ModelConfig, ModelRegistry


def test_register_and_list():
    registry = ModelRegistry()
    registry.register_model(ModelConfig(id="m1", provider="local", type="chat", tags=["fast"]))
    registry.register_model(ModelConfig(id="m2", provider="local", type="code", tags=["high_quality"], enabled=False))
    enabled = registry.list_models(enabled=True)
    assert any(m.id == "m1" for m in enabled)
    assert all(m.enabled for m in enabled)
