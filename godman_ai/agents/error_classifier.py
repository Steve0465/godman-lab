"""Error classification for self-correcting agents."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional


class ErrorClass(str, Enum):
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    TOOL_CONFIG = "TOOL_CONFIG"
    MODEL_QUALITY = "MODEL_QUALITY"
    REQUIRES_HUMAN = "REQUIRES_HUMAN"


def classify_error(exc: Exception, critic_result: Optional[Any] = None) -> ErrorClass:
    """Map exceptions and critic signals to broad error classes."""
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return ErrorClass.TRANSIENT
    if isinstance(exc, (KeyError, ValueError)):
        return ErrorClass.TOOL_CONFIG
    if critic_result and getattr(critic_result, "score", 1.0) < 0.4:
        return ErrorClass.MODEL_QUALITY
    if isinstance(exc, PermissionError):
        return ErrorClass.REQUIRES_HUMAN
    return ErrorClass.PERMANENT
