from godman_ai.capabilities.registry import CapabilityRegistry


def test_load_trello_capabilities():
    registry = CapabilityRegistry()
    registry.load_manifest_dir("godman_ai/capabilities/trello")
    caps = registry.list_capabilities(tags=["trello"])
    ids = {c.id for c in caps}
    assert "capability.trello_board_ingest" in ids
