"""Base model abstraction layer."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Protocol


class BaseModelInterface(Protocol):
    """Standardized model interface for generation."""

    name: str

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        ...


def trace_model(func):
    """Decorator to capture simple timing metadata."""

    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration_ms = int((time.time() - start) * 1000)
        if isinstance(result, dict):
            result = {**result, "_duration_ms": duration_ms}
        return result

    return wrapper


class LocalModelHandle:
    """Lightweight adapter exposing BaseModelInterface for local model names."""

    def __init__(self, name: str):
        self.name = name

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        # Placeholder: delegate to existing LLM engine if available
        from godman_ai.llm.engine import LLMEngine

        engine = LLMEngine(default_model=self.name)
        return await engine.call_async(prompt, model=self.name)

    def generate_sync(self, prompt: str, **kwargs: Any) -> str:
        return asyncio.run(self.generate(prompt, **kwargs))
