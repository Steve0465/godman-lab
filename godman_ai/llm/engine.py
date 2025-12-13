"""LLM engine providing simple interface over registry."""

from godman_ai.llm.interface import llm_call, llm_call_async
from godman_ai.llm.registry import MODEL_REGISTRY, available_models


class LLMEngine:
    def __init__(self, default_model: str = "godman-raw:latest") -> None:
        self.set_default(default_model)

    def call(self, prompt: str, model: str | None = None, temperature: float = 0.1) -> str:
        target_model = model or self.default_model
        if target_model not in MODEL_REGISTRY:
            raise ValueError(f"Model '{target_model}' is not registered")
        return llm_call(target_model, prompt, temperature=temperature)

    async def call_async(self, prompt: str, model: str | None = None, temperature: float = 0.1) -> str:
        target_model = model or self.default_model
        if target_model not in MODEL_REGISTRY:
            raise ValueError(f"Model '{target_model}' is not registered")
        return await llm_call_async(target_model, prompt, temperature=temperature)

    def list_registered(self) -> list[str]:
        return list(MODEL_REGISTRY.keys())

    def list_available(self) -> list[str]:
        return available_models()

    def set_default(self, model: str) -> None:
        if model not in MODEL_REGISTRY:
            raise ValueError(f"Model '{model}' is not registered")
        self.default_model = model
