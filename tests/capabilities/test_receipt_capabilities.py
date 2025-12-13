from godman_ai.capabilities.registry import CapabilityRegistry


def test_load_receipt_capabilities():
    registry = CapabilityRegistry()
    registry.load_manifest_dir("godman_ai/capabilities/receipts")
    caps = registry.list_capabilities(tags=["receipts"])
    ids = {c.id for c in caps}
    assert "capability.receipt_ocr" in ids
