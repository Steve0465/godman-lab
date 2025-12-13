"""Lightweight sync/async caching utilities with TTL support."""

from __future__ import annotations

import asyncio
import time
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, Hashable, Optional, Tuple, TypeVar, Union

T = TypeVar("T")


class CacheEntry:
    def __init__(self, value: Any, expires_at: Optional[float]) -> None:
        self.value = value
        self.expires_at = expires_at

    def expired(self) -> bool:
        return self.expires_at is not None and time.time() > self.expires_at


class InMemoryCache:
    """Simple in-memory cache with TTL."""

    def __init__(self) -> None:
        self._store: Dict[Hashable, CacheEntry] = {}

    def get(self, key: Hashable) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        if entry.expired():
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: Hashable, value: Any, ttl: Optional[float] = None) -> None:
        expires_at = time.time() + ttl if ttl else None
        self._store[key] = CacheEntry(value, expires_at)

    def invalidate(self, key: Hashable) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


_cache = InMemoryCache()


def _make_key(func: Callable[..., Any], args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Hashable:
    return (func.__module__, func.__qualname__, id(args[0]) if args else None, args[1:], tuple(sorted(kwargs.items())))


def cached_sync(ttl: Optional[float] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for caching sync function results with optional TTL."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            key = _make_key(func, args, kwargs)
            cached = _cache.get(key)
            if cached is not None:
                return cached  # type: ignore[return-value]
            result = func(*args, **kwargs)
            _cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator


def cached_async(ttl: Optional[float] = None) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for caching async function results with optional TTL."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            key = _make_key(func, args, kwargs)
            cached = _cache.get(key)
            if cached is not None:
                return cached  # type: ignore[return-value]
            result = await func(*args, **kwargs)
            _cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator


__all__ = ["cached_sync", "cached_async", "InMemoryCache"]
