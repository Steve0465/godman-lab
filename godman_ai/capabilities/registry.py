"""Capability metadata registry and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence


class CapabilityType(str, Enum):
    TOOL = "TOOL"
    SKILL = "SKILL"
    PLUGIN = "PLUGIN"
    WORKFLOW_TEMPLATE = "WORKFLOW_TEMPLATE"


@dataclass
class CapabilityMetadata:
    id: str
    type: CapabilityType
    name: str
    description: str
    input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    permissions: str = "low"
    risk_level: str = "low"
    related_model_tags: List[str] = field(default_factory=list)


class CapabilityRegistry:
    """In-memory capability registry with intent search."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, CapabilityMetadata] = {}

    def register_capability(self, metadata: CapabilityMetadata) -> None:
        self._capabilities[metadata.id] = metadata

    def get_capability(self, cap_id: str) -> Optional[CapabilityMetadata]:
        return self._capabilities.get(cap_id)

    def list_capabilities(
        self,
        types: Optional[Sequence[CapabilityType]] = None,
        tags: Optional[Iterable[str]] = None,
        risk_level: Optional[str] = None,
    ) -> List[CapabilityMetadata]:
        tag_set = set(tags or [])
        results: List[CapabilityMetadata] = []
        for cap in self._capabilities.values():
            if types and cap.type not in types:
                continue
            if risk_level and cap.risk_level != risk_level:
                continue
            if tag_set and not tag_set.intersection(set(cap.tags)):
                continue
            results.append(cap)
        return results

    def find_capabilities_by_intent(
        self,
        intent_text: str,
        tags: Optional[Iterable[str]] = None,
        io_types: Optional[Iterable[str]] = None,
    ) -> List[CapabilityMetadata]:
        intent_lower = intent_text.lower()
        tag_set = set(tags or [])
        io_set = set(io_types or [])
        results = []
        for cap in self._capabilities.values():
            text_match = cap.name.lower() in intent_lower or any(tok in cap.description.lower() for tok in intent_lower.split())
            tag_match = not tag_set or tag_set.intersection(set(cap.tags))
            io_match = not io_set or io_set.intersection(set(cap.output_types + cap.input_types))
            if text_match or tag_match or io_match:
                results.append(cap)
        return results

    def load_manifest_dir(self, directory: str) -> None:
        """Load capability manifests (yaml/json) from a directory."""
        from pathlib import Path
        import json
        try:
            import yaml  # type: ignore
        except ImportError:
            yaml = None  # type: ignore

        base = Path(directory)
        if not base.exists():
            return
        for path in base.glob("*.yaml"):
            data = yaml.safe_load(path.read_text()) if yaml else json.loads(path.read_text())
            if not isinstance(data, dict):
                continue
            cap_type = CapabilityType(data.get("type", "TOOL"))
            meta = CapabilityMetadata(
                id=data["id"],
                type=cap_type,
                name=data.get("name", data["id"]),
                description=data.get("description", ""),
                input_types=data.get("input_types", []) or [],
                output_types=data.get("output_types", []) or [],
                tags=data.get("tags", []) or [],
                permissions=data.get("permissions", "low"),
                risk_level=data.get("risk_level", "low"),
                related_model_tags=data.get("related_model_tags", []) or [],
            )
            self.register_capability(meta)


def register_tool_capability(registry: CapabilityRegistry, tool_cls: Any, **overrides: Any) -> str:
    cap_id = overrides.get("id") or getattr(tool_cls, "name", tool_cls.__name__)
    metadata = CapabilityMetadata(
        id=cap_id,
        type=CapabilityType.TOOL,
        name=getattr(tool_cls, "name", cap_id),
        description=getattr(tool_cls, "description", "") or overrides.get("description", ""),
        input_types=overrides.get("input_types", []),
        output_types=overrides.get("output_types", []),
        tags=overrides.get("tags", []),
        permissions=overrides.get("permissions", "low"),
        risk_level=overrides.get("risk_level", "low"),
        related_model_tags=overrides.get("related_model_tags", []),
    )
    registry.register_capability(metadata)
    return cap_id


def register_skill_capability(registry: CapabilityRegistry, skill_id: str, description: str, **overrides: Any) -> str:
    metadata = CapabilityMetadata(
        id=skill_id,
        type=CapabilityType.SKILL,
        name=skill_id,
        description=description,
        input_types=overrides.get("input_types", []),
        output_types=overrides.get("output_types", []),
        tags=overrides.get("tags", []),
        permissions=overrides.get("permissions", "low"),
        risk_level=overrides.get("risk_level", "low"),
        related_model_tags=overrides.get("related_model_tags", []),
    )
    registry.register_capability(metadata)
    return skill_id


def register_plugin_capability(registry: CapabilityRegistry, plugin_id: str, description: str, **overrides: Any) -> str:
    metadata = CapabilityMetadata(
        id=plugin_id,
        type=CapabilityType.PLUGIN,
        name=plugin_id,
        description=description,
        input_types=overrides.get("input_types", []),
        output_types=overrides.get("output_types", []),
        tags=overrides.get("tags", []),
        permissions=overrides.get("permissions", "medium"),
        risk_level=overrides.get("risk_level", "medium"),
        related_model_tags=overrides.get("related_model_tags", []),
    )
    registry.register_capability(metadata)
    return plugin_id
