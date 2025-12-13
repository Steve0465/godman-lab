from godman_ai.models.performance import InMemoryPerformanceStore, make_perf_record


def test_record_and_stats():
    store = InMemoryPerformanceStore()
    store.record_result(make_perf_record("m1", True, latency_ms=100, quality_score=0.8))
    store.record_result(make_perf_record("m1", False, latency_ms=200, quality_score=0.2))
    stats = store.get_stats("m1")
    assert stats["count"] == 2
    assert stats["success_rate"] < 1.0


def test_top_models():
    store = InMemoryPerformanceStore()
    store.record_result(make_perf_record("a", True, 10, quality_score=0.9))
    store.record_result(make_perf_record("b", True, 10, quality_score=0.1))
    top = store.get_top_models()
    assert top[0] == "a"
