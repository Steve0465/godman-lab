from godman_ai.capabilities.registry import CapabilityRegistry


def test_measurement_pack_capabilities_load():
    registry = CapabilityRegistry()
    registry.load_manifest_dir("godman_ai/capabilities/measurements")
    ids = {c.id for c in registry.list_capabilities(tags=["measurements"])}
    assert "capability.measurement_table_parse" in ids
    assert "capability.fitment_check" in ids
