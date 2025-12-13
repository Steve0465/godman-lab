"""Capability resolver that consults registry and graph."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from godman_ai.capabilities.graph import CapabilityGraph
from godman_ai.capabilities.registry import CapabilityMetadata, CapabilityRegistry, CapabilityType


class CapabilityResolver:
    def __init__(self, registry: Optional[CapabilityRegistry] = None, graph: Optional[CapabilityGraph] = None) -> None:
        self.registry = registry or CapabilityRegistry()
        self.graph = graph or CapabilityGraph()

    def find_tools_for_task(self, task_type: str, context: Dict[str, Any], policy: Any) -> List[CapabilityMetadata]:
        tags = getattr(policy, "preferred_capability_tags", []) if policy else []
        results = self.registry.find_capabilities_by_intent(task_type, tags=tags)
        return [cap for cap in results if cap.type == CapabilityType.TOOL]

    def suggest_alternatives_for_tool(self, tool_id: str, context: Optional[Dict[str, Any]] = None) -> List[CapabilityMetadata]:
        related_nodes = self.graph.get_related_capabilities(tool_id, relation_type="ALTERNATIVE_FOR")
        alts = []
        for node in related_nodes:
            cap = self.registry.get_capability(node.id)
            if cap:
                alts.append(cap)
        return alts

    def suggest_capabilities_for_intent(self, intent_text: str, tags: Optional[List[str]] = None) -> List[CapabilityMetadata]:
        return self.registry.find_capabilities_by_intent(intent_text, tags=tags)
