"""Lightweight interface for invoking configured LLMs."""

import asyncio
from typing import Optional

from godman_ai.llm.registry import MODEL_REGISTRY


async def llm_call_async(model_name: str, prompt: str, temperature: float = 0.1) -> str:
    config = MODEL_REGISTRY.get(model_name)
    if not config:
        raise ValueError(f"Unknown model '{model_name}'")
    await asyncio.sleep(0)  # yield control
    return f"[{model_name}] {prompt}"


def llm_call(model_name: str, prompt: str, temperature: float = 0.1) -> str:
    return asyncio.run(llm_call_async(model_name, prompt, temperature=temperature))
