"""Model performance tracking."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ModelPerformanceRecord:
    model_id: str
    timestamp: float
    success: bool
    latency_ms: float
    quality_score: float = 0.0
    tags: List[str] = field(default_factory=list)


class ModelPerformanceStore:
    """Interface for performance storage."""

    def record_result(self, record: ModelPerformanceRecord) -> None:
        raise NotImplementedError

    def get_stats(self, model_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_top_models(self, criterion: str = "quality_score", limit: int = 3) -> List[str]:
        raise NotImplementedError


class InMemoryPerformanceStore(ModelPerformanceStore):
    def __init__(self) -> None:
        self.records: List[ModelPerformanceRecord] = []

    def record_result(self, record: ModelPerformanceRecord) -> None:
        self.records.append(record)

    def get_stats(self, model_id: str) -> Dict[str, Any]:
        recs = [r for r in self.records if r.model_id == model_id]
        if not recs:
            return {"count": 0, "success_rate": 0.0, "avg_latency": 0.0, "avg_quality": 0.0}
        success_rate = sum(1 for r in recs if r.success) / len(recs)
        avg_latency = sum(r.latency_ms for r in recs) / len(recs)
        avg_quality = sum(r.quality_score for r in recs) / len(recs)
        return {"count": len(recs), "success_rate": success_rate, "avg_latency": avg_latency, "avg_quality": avg_quality}

    def get_top_models(self, criterion: str = "quality_score", limit: int = 3) -> List[str]:
        scored: Dict[str, float] = {}
        for rec in self.records:
            scored.setdefault(rec.model_id, 0.0)
            scored[rec.model_id] += getattr(rec, criterion, 0.0)
        ranked = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
        return [m for m, _ in ranked[:limit]]


class SqlitePerformanceStore(ModelPerformanceStore):
    def __init__(self, path: str | Path = "model_performance.db") -> None:
        self.path = Path(path)
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS perf (
                    model_id TEXT,
                    ts REAL,
                    success INTEGER,
                    latency REAL,
                    quality REAL,
                    tags TEXT
                )
                """
            )
            conn.commit()

    def record_result(self, record: ModelPerformanceRecord) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO perf (model_id, ts, success, latency, quality, tags) VALUES (?,?,?,?,?,?)",
                (record.model_id, record.timestamp, int(record.success), record.latency_ms, record.quality_score, ",".join(record.tags)),
            )
            conn.commit()

    def get_stats(self, model_id: str) -> Dict[str, Any]:
        with self._conn() as conn:
            rows = conn.execute("SELECT success, latency, quality FROM perf WHERE model_id=?", (model_id,)).fetchall()
        if not rows:
            return {"count": 0, "success_rate": 0.0, "avg_latency": 0.0, "avg_quality": 0.0}
        count = len(rows)
        success_rate = sum(row[0] for row in rows) / count
        avg_latency = sum(row[1] for row in rows) / count
        avg_quality = sum(row[2] for row in rows) / count
        return {"count": count, "success_rate": success_rate, "avg_latency": avg_latency, "avg_quality": avg_quality}

    def get_top_models(self, criterion: str = "quality", limit: int = 3) -> List[str]:
        with self._conn() as conn:
            rows = conn.execute(f"SELECT model_id, AVG({criterion}) as score FROM perf GROUP BY model_id ORDER BY score DESC").fetchall()
        return [row[0] for row in rows[:limit]]


def make_perf_record(model_id: str, success: bool, latency_ms: float, quality_score: float = 0.0, tags: Optional[List[str]] = None) -> ModelPerformanceRecord:
    return ModelPerformanceRecord(
        model_id=model_id,
        timestamp=time.time(),
        success=success,
        latency_ms=latency_ms,
        quality_score=quality_score,
        tags=tags or [],
    )
