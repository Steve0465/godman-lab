"""High-level memory manager combining stores and graph."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from godman_ai.memory.graph import GraphEdge, GraphNode, KnowledgeGraph
from godman_ai.memory.stores import (
    InMemoryLongTermStore,
    LongTermMemoryStore,
    MemoryRecord,
    ShortTermMemoryStore,
    SqliteLongTermStore,
    make_record,
)


class MemoryManager:
    """Orchestrates memory store writes and graph updates."""

    def __init__(
        self,
        short_term: Optional[ShortTermMemoryStore] = None,
        long_term: Optional[LongTermMemoryStore] = None,
        graph: Optional[KnowledgeGraph] = None,
    ) -> None:
        self.short_term = short_term or ShortTermMemoryStore()
        self.long_term = long_term or InMemoryLongTermStore()
        self.graph = graph or KnowledgeGraph()

    def record_workflow_event(self, workflow_id: str, event_type: str, payload: Optional[Dict[str, Any]] = None) -> str:
        record = make_record(type=event_type, source="workflow", payload=payload or {"workflow_id": workflow_id}, tags=["workflow"])
        self.short_term.add_record(record)
        self.long_term.add_record(record)
        self.graph.add_node(GraphNode(id=workflow_id, type="WORKFLOW", metadata=payload or {}))
        return record.id

    def record_agent_decision(self, agent_id: str, decision: str, payload: Optional[Dict[str, Any]] = None) -> str:
        record = make_record(type="AGENT_DECISION", source="agent", payload={"decision": decision, **(payload or {})}, tags=["agent"])
        self.short_term.add_record(record)
        self.long_term.add_record(record)
        self.graph.add_node(GraphNode(id=agent_id, type="AGENT_RUN", metadata=payload or {}))
        self.graph.add_edge(GraphEdge(src_id=agent_id, dst_id=record.id, relation_type="DECISION"))
        return record.id

    def record_error_event(self, source_id: str, error_msg: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        record = make_record(type="ERROR", source="agent", payload={"error": error_msg, **(metadata or {})}, tags=["error"])
        self.short_term.add_record(record)
        self.long_term.add_record(record)
        self.graph.add_node(GraphNode(id=record.id, type="ERROR", metadata=record.payload))
        self.graph.add_edge(GraphEdge(src_id=source_id, dst_id=record.id, relation_type="ERROR"))
        return record.id

    def get_recent_failures_for_tool(self, tool_name: str, limit: int = 5) -> List[MemoryRecord]:
        records = self.long_term.query_records(types=["ERROR"], tags=["tool:" + tool_name])
        return sorted(records, key=lambda r: r.timestamp, reverse=True)[:limit]

    def get_successful_patterns_for_workflow(self, workflow_name: str) -> List[MemoryRecord]:
        return self.long_term.query_records(types=["SUCCESS"], tags=["workflow:" + workflow_name])

    def link_records(self, primary_id: str, related_id: str, relation_type: str) -> None:
        self.short_term.link_records(primary_id, related_id, relation_type)
        self.long_term.link_records(primary_id, related_id, relation_type)
        self.graph.add_edge(GraphEdge(src_id=primary_id, dst_id=related_id, relation_type=relation_type))

    def use_sqlite(self, path: str) -> None:
        """Switch long-term store to SQLite persistence."""
        self.long_term = SqliteLongTermStore(path)
