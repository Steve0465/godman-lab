from godman_ai.memory.stores import ShortTermMemoryStore, make_record


def test_add_and_query_records():
    store = ShortTermMemoryStore()
    rec1 = make_record("SUCCESS", "test", payload={}, tags=["foo"])
    rec2 = make_record("ERROR", "test", payload={}, tags=["bar"])
    store.add_record(rec1)
    store.add_record(rec2)
    results = store.query_records(types=["ERROR"])
    assert len(results) == 1
    assert results[0].id == rec2.id


def test_link_records():
    store = ShortTermMemoryStore()
    rec1 = make_record("A", "test")
    rec2 = make_record("B", "test")
    store.add_record(rec1)
    store.add_record(rec2)
    store.link_records(rec1.id, rec2.id, "related")
    assert store.links[0][0] == rec1.id
