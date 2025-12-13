from godman_ai.capabilities.registry import CapabilityRegistry


def test_load_measurement_capabilities():
    registry = CapabilityRegistry()
    registry.load_manifest_dir("godman_ai/capabilities/measurements")
    caps = registry.list_capabilities(tags=["measurements"])
    ids = {c.id for c in caps}
    assert "capability.measurement_ocr" in ids
