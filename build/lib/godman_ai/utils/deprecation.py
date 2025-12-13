"""Deprecation utilities."""

import functools
import warnings
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(reason: str) -> Callable[[F], F]:
    """Decorator to mark functions as deprecated."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            warnings.warn(f"Deprecated: {func.__name__}. {reason}", DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapped  # type: ignore[return-value]

    return decorator
