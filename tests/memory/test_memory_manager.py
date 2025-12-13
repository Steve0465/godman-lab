from godman_ai.memory.manager import MemoryManager


def test_record_workflow_and_error():
    mm = MemoryManager()
    wf_record = mm.record_workflow_event("wf1", "WORKFLOW_START", payload={"name": "wf1"})
    err_record = mm.record_error_event("wf1", "boom", metadata={"step": "one"})
    assert wf_record
    assert err_record
    failures = mm.get_recent_failures_for_tool("nonexistent", limit=5)
    assert isinstance(failures, list)


def test_success_patterns():
    mm = MemoryManager()
    from godman_ai.memory.stores import make_record

    rec = make_record("SUCCESS", "workflow", payload={}, tags=["workflow:test"])
    mm.long_term.add_record(rec)
    patterns = mm.get_successful_patterns_for_workflow("test")
    assert isinstance(patterns, list)
