import asyncio

from godman_ai.local_router import LocalModelRouter


def test_route_cached_and_async_safe():
    router = LocalModelRouter()
    first = router.route("please write some code")
    second = router.route("please write some code")
    assert first == second  # cached_sync should return same content

    async def run_route():
        return await asyncio.to_thread(router.route, "let's reason this out")

    async_result = asyncio.run(run_route())
    assert "model" in async_result
    assert "confidence" in async_result
