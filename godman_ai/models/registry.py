"""Model registry for multi-model routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class ModelConfig:
    id: str
    provider: str
    type: str
    tags: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    cost_hint: float = 0.0
    latency_hint: float = 0.0
    enabled: bool = True


class ModelRegistry:
    """In-memory model registry with optional config loading."""

    def __init__(self) -> None:
        self._models: Dict[str, ModelConfig] = {}

    def register_model(self, config: ModelConfig) -> None:
        self._models[config.id] = config

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        return self._models.get(model_id)

    def list_models(
        self,
        tags: Optional[Sequence[str]] = None,
        provider: Optional[str] = None,
        type: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> List[ModelConfig]:
        tag_set = set(tags or [])
        results: List[ModelConfig] = []
        for cfg in self._models.values():
            if provider and cfg.provider != provider:
                continue
            if type and cfg.type != type:
                continue
            if enabled is not None and cfg.enabled != enabled:
                continue
            if tag_set and not tag_set.intersection(set(cfg.tags)):
                continue
            results.append(cfg)
        return results

    @classmethod
    def from_file(cls, path: str | Path) -> "ModelRegistry":
        registry = cls()
        data = _load_config(path)
        for item in data:
            registry.register_model(ModelConfig(**item))
        return registry


def _load_config(path: str | Path) -> List[Dict[str, Any]]:
    import json

    p = Path(path)
    text = p.read_text()
    try:
        import yaml  # type: ignore
    except ImportError:
        yaml = None  # type: ignore
    if yaml:
        loaded = yaml.safe_load(text) or []
        return loaded if isinstance(loaded, list) else []
    return json.loads(text)
