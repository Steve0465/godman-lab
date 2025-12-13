from godman_ai.capabilities.registry import CapabilityRegistry


def test_drive_capabilities_load():
    registry = CapabilityRegistry()
    registry.load_manifest_dir("godman_ai/capabilities/drive")
    ids = {c.id for c in registry.list_capabilities(tags=["drive"])}
    assert "capability.drive_file_classification" in ids
    assert "capability.drive_crosslink" in ids
