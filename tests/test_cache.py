import asyncio
import time

from libs.cache import InMemoryCache, cached_async, cached_sync


def test_cached_sync_returns_cached_value():
    calls = {"count": 0}

    @cached_sync(ttl=1)
    def add(a, b):
        calls["count"] += 1
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert calls["count"] == 1


def test_cached_sync_ttl_expires():
    calls = {"count": 0}

    @cached_sync(ttl=0.01)
    def ping():
        calls["count"] += 1
        return calls["count"]

    first = ping()
    time.sleep(0.02)
    second = ping()
    assert second > first


def test_cached_async_caches_results():
    calls = {"count": 0}

    @cached_async(ttl=1)
    async def echo(val):
        calls["count"] += 1
        return val

    result1 = asyncio.run(echo("x"))
    result2 = asyncio.run(echo("x"))
    assert result1 == result2
    assert calls["count"] == 1


def test_inmemory_cache_invalidate_and_clear():
    cache = InMemoryCache()
    cache.set("k", "v")
    assert cache.get("k") == "v"
    cache.invalidate("k")
    assert cache.get("k") is None
    cache.set("k2", "v2")
    cache.clear()
    assert cache.get("k2") is None
