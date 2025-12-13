"""Capability graph built on top of the shared knowledge graph."""

from __future__ import annotations

from typing import Any, List, Optional

from godman_ai.capabilities.registry import CapabilityMetadata
from godman_ai.memory.graph import GraphEdge, GraphNode, KnowledgeGraph


class CapabilityGraph:
    def __init__(self, graph: Optional[KnowledgeGraph] = None) -> None:
        self.graph = graph or KnowledgeGraph()

    def add_capability_node(self, capability: CapabilityMetadata) -> None:
        self.graph.add_node(GraphNode(id=capability.id, type=capability.type.value, metadata={"name": capability.name, "tags": capability.tags}))

    def add_relationship(self, src_capability_id: str, dst_capability_id: str, relation_type: str, weight: float = 1.0, metadata: Optional[dict] = None) -> None:
        self.graph.add_edge(GraphEdge(src_id=src_capability_id, dst_id=dst_capability_id, relation_type=relation_type, weight=weight, metadata=metadata or {}))

    def get_related_capabilities(self, capability_id: str, relation_type: Optional[str] = None) -> List[GraphNode]:
        return self.graph.neighbors(capability_id, relation_type)
