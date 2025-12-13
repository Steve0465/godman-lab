from godman_ai.memory.stores import SqliteLongTermStore, make_record


def test_persistence_roundtrip(tmp_path):
    db_path = tmp_path / "mem.db"
    store1 = SqliteLongTermStore(path=db_path)
    rec = make_record("SUCCESS", "unit", payload={"x": 1}, tags=["foo"])
    store1.add_record(rec)

    store2 = SqliteLongTermStore(path=db_path)
    results = store2.query_records(types=["SUCCESS"])
    assert len(results) == 1
    assert results[0].payload["x"] == 1
