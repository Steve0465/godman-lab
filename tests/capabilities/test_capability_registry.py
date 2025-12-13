from godman_ai.capabilities.registry import CapabilityMetadata, CapabilityRegistry, CapabilityType


def test_registration_and_filtering():
    registry = CapabilityRegistry()
    cap = CapabilityMetadata(
        id="tool.a",
        type=CapabilityType.TOOL,
        name="A",
        description="test tool",
        tags=["finance"],
    )
    registry.register_capability(cap)
    listed = registry.list_capabilities(types=[CapabilityType.TOOL], tags=["finance"])
    assert listed and listed[0].id == "tool.a"


def test_intent_search():
    registry = CapabilityRegistry()
    cap = CapabilityMetadata(
        id="skill.summary",
        type=CapabilityType.SKILL,
        name="Summarize",
        description="Summarize receipts",
        tags=["receipts", "summary"],
    )
    registry.register_capability(cap)
    results = registry.find_capabilities_by_intent("summarize receipts")
    assert cap in results
