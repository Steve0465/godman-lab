"""Knowledge graph primitives."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GraphNode:
    id: str
    type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    src_id: str
    dst_id: str
    relation_type: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """In-memory knowledge graph with optional SQLite persistence."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        if self.path:
            self._init_db()
            self._load_from_db()

    def _conn(self):
        if not self.path:
            raise RuntimeError("Persistence disabled")
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        if not self.path:
            return
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    metadata TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS edges (
                    src_id TEXT,
                    dst_id TEXT,
                    relation_type TEXT,
                    weight REAL,
                    metadata TEXT
                )
                """
            )
            conn.commit()

    def _load_from_db(self) -> None:
        if not self.path:
            return
        import json
        with self._conn() as conn:
            for row in conn.execute("SELECT id, type, metadata FROM nodes"):
                self.nodes[row[0]] = GraphNode(id=row[0], type=row[1], metadata=json.loads(row[2] or "{}"))
            for row in conn.execute("SELECT src_id, dst_id, relation_type, weight, metadata FROM edges"):
                self.edges.append(
                    GraphEdge(
                        src_id=row[0],
                        dst_id=row[1],
                        relation_type=row[2],
                        weight=row[3],
                        metadata=json.loads(row[4] or "{}"),
                    )
                )

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node
        if self.path:
            import json
            with self._conn() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO nodes (id, type, metadata) VALUES (?,?,?)",
                    (node.id, node.type, json.dumps(node.metadata)),
                )
                conn.commit()

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)
        if self.path:
            import json
            with self._conn() as conn:
                conn.execute(
                    "INSERT INTO edges (src_id, dst_id, relation_type, weight, metadata) VALUES (?,?,?,?,?)",
                    (
                        edge.src_id,
                        edge.dst_id,
                        edge.relation_type,
                        edge.weight,
                        json.dumps(edge.metadata),
                    ),
                )
                conn.commit()

    def neighbors(self, node_id: str, relation_type: Optional[str] = None) -> List[GraphNode]:
        neighbor_ids = [
            edge.dst_id for edge in self.edges if edge.src_id == node_id and (relation_type is None or edge.relation_type == relation_type)
        ]
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]

    def find_paths(self, source_id: str, target_id: str, max_depth: int = 3) -> List[List[str]]:
        paths: List[List[str]] = []

        def _dfs(current: str, target: str, depth: int, path: List[str]) -> None:
            if depth > max_depth:
                return
            if current == target:
                paths.append(list(path))
                return
            for edge in self.edges:
                if edge.src_id == current and edge.dst_id not in path:
                    path.append(edge.dst_id)
                    _dfs(edge.dst_id, target, depth + 1, path)
                    path.pop()

        _dfs(source_id, target_id, 0, [source_id])
        return paths
