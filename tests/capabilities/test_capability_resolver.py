from godman_ai.capabilities.registry import CapabilityMetadata, CapabilityRegistry, CapabilityType
from godman_ai.capabilities.resolver import CapabilityResolver


def test_resolver_intent_and_alternatives():
    registry = CapabilityRegistry()
    cap = CapabilityMetadata(id="t1", type=CapabilityType.TOOL, name="Extract", description="extract data", tags=["data"])
    registry.register_capability(cap)
    resolver = CapabilityResolver(registry=registry)
    results = resolver.find_tools_for_task("extract data", {}, None)
    assert results and results[0].id == "t1"
    alts = resolver.suggest_alternatives_for_tool("t1")
    assert isinstance(alts, list)
