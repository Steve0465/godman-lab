"""Memory stores for agent/workflow history."""

from __future__ import annotations

import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


def _ts() -> float:
    return time.time()


@dataclass
class MemoryRecord:
    id: str
    timestamp: float
    type: str
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    related_ids: List[str] = field(default_factory=list)


class ShortTermMemoryStore:
    """Ephemeral in-memory store for a single process."""

    def __init__(self) -> None:
        self.records: List[MemoryRecord] = []
        self.links: List[tuple[str, str, str]] = []

    def add_record(self, record: MemoryRecord) -> str:
        self.records.append(record)
        return record.id

    def query_records(
        self,
        types: Optional[Sequence[str]] = None,
        tags: Optional[Iterable[str]] = None,
        source: Optional[str] = None,
        since: Optional[float] = None,
    ) -> List[MemoryRecord]:
        tag_set = set(tags or [])
        results = []
        for rec in self.records:
            if types and rec.type not in types:
                continue
            if source and rec.source != source:
                continue
            if since and rec.timestamp < since:
                continue
            if tag_set and not tag_set.intersection(set(rec.tags)):
                continue
            results.append(rec)
        return results

    def link_records(self, primary_id: str, related_id: str, relation_type: str) -> None:
        self.links.append((primary_id, related_id, relation_type))


class LongTermMemoryStore:
    """Interface for durable memory stores."""

    def add_record(self, record: MemoryRecord) -> str:
        raise NotImplementedError

    def query_records(
        self,
        types: Optional[Sequence[str]] = None,
        tags: Optional[Iterable[str]] = None,
        source: Optional[str] = None,
        since: Optional[float] = None,
    ) -> List[MemoryRecord]:
        raise NotImplementedError

    def link_records(self, primary_id: str, related_id: str, relation_type: str) -> None:
        raise NotImplementedError


class InMemoryLongTermStore(LongTermMemoryStore):
    """Durable-like in-memory store for tests/dev."""

    def __init__(self) -> None:
        self._store = ShortTermMemoryStore()

    def add_record(self, record: MemoryRecord) -> str:
        return self._store.add_record(record)

    def query_records(
        self,
        types: Optional[Sequence[str]] = None,
        tags: Optional[Iterable[str]] = None,
        source: Optional[str] = None,
        since: Optional[float] = None,
    ) -> List[MemoryRecord]:
        return self._store.query_records(types, tags, source, since)

    def link_records(self, primary_id: str, related_id: str, relation_type: str) -> None:
        self._store.link_records(primary_id, related_id, relation_type)


class SqliteLongTermStore(LongTermMemoryStore):
    """SQLite-backed memory store."""

    def __init__(self, path: str | Path = "memory_store.db") -> None:
        self.path = Path(path)
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS records (
                    id TEXT PRIMARY KEY,
                    ts REAL,
                    type TEXT,
                    source TEXT,
                    payload TEXT,
                    tags TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS links (
                    primary_id TEXT,
                    related_id TEXT,
                    relation_type TEXT
                )
                """
            )
            conn.commit()

    def add_record(self, record: MemoryRecord) -> str:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO records (id, ts, type, source, payload, tags) VALUES (?,?,?,?,?,?)",
                (
                    record.id,
                    record.timestamp,
                    record.type,
                    record.source,
                    json_dumps(record.payload),
                    ",".join(record.tags),
                ),
            )
            for rid in record.related_ids:
                conn.execute(
                    "INSERT INTO links (primary_id, related_id, relation_type) VALUES (?,?,?)",
                    (record.id, rid, "related"),
                )
            conn.commit()
        return record.id

    def query_records(
        self,
        types: Optional[Sequence[str]] = None,
        tags: Optional[Iterable[str]] = None,
        source: Optional[str] = None,
        since: Optional[float] = None,
    ) -> List[MemoryRecord]:
        clauses = []
        params: List[Any] = []
        if types:
            clauses.append("type IN (%s)" % ",".join("?" * len(types)))
            params.extend(types)
        if source:
            clauses.append("source=?")
            params.append(source)
        if since:
            clauses.append("ts>=?")
            params.append(since)
        sql = "SELECT id, ts, type, source, payload, tags FROM records"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        tag_filter = set(tags or [])
        results: List[MemoryRecord] = []
        for row in rows:
            rec_tags = row[5].split(",") if row[5] else []
            if tag_filter and not tag_filter.intersection(set(rec_tags)):
                continue
            results.append(
                MemoryRecord(
                    id=row[0],
                    timestamp=row[1],
                    type=row[2],
                    source=row[3],
                    payload=json_loads(row[4]),
                    tags=rec_tags,
                    related_ids=[],
                )
            )
        return results

    def link_records(self, primary_id: str, related_id: str, relation_type: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO links (primary_id, related_id, relation_type) VALUES (?,?,?)",
                (primary_id, related_id, relation_type),
            )
            conn.commit()


def make_record(
    type: str,
    source: str,
    payload: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    related_ids: Optional[List[str]] = None,
) -> MemoryRecord:
    return MemoryRecord(
        id=str(uuid.uuid4()),
        timestamp=_ts(),
        type=type,
        source=source,
        payload=payload or {},
        tags=tags or [],
        related_ids=related_ids or [],
    )


def json_dumps(data: Any) -> str:
    import json
    return json.dumps(data)


def json_loads(data: str) -> Any:
    import json
    return json.loads(data or "{}")
