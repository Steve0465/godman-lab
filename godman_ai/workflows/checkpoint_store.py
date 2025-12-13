"""Checkpoint store interfaces for distributed workflows."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class WorkflowState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"


def _timestamp() -> float:
    return time.time()


@dataclass
class StepRecord:
    name: str
    state: WorkflowState = WorkflowState.PENDING
    input: Dict[str, Any] | None = None
    output: Any | None = None
    error: str | None = None
    started_at: float | None = None
    finished_at: float | None = None
    retries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "input": self.input,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "retries": self.retries,
        }


@dataclass
class WorkflowRun:
    id: str
    definition: Dict[str, Any]
    context: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: WorkflowState = WorkflowState.PENDING
    steps: Dict[str, StepRecord] = field(default_factory=dict)
    created_at: float = field(default_factory=_timestamp)
    updated_at: float = field(default_factory=_timestamp)
    error: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "definition": self.definition,
            "context": self.context,
            "metadata": self.metadata,
            "state": self.state.value,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }


class InvalidStateTransition(Exception):
    """Raised when an invalid state transition is requested."""


class CheckpointStore:
    """Abstract store for workflow checkpoints."""

    def create_workflow_run(
        self, workflow_def: Dict[str, Any], initial_context: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        raise NotImplementedError

    def update_workflow_state(self, workflow_id: str, state: WorkflowState, error: Optional[str] = None) -> None:
        raise NotImplementedError

    def update_step_state(
        self,
        workflow_id: str,
        step_name: str,
        state: WorkflowState,
        output: Any | None = None,
        error: str | None = None,
    ) -> None:
        raise NotImplementedError

    def get_workflow_state(self, workflow_id: str) -> WorkflowRun:
        raise NotImplementedError

    def list_active_workflows(self) -> List[WorkflowRun]:
        raise NotImplementedError

    def append_log(self, workflow_id: str, message: str) -> None:
        """Optional: stores log/event lines."""
        return None


class InMemoryCheckpointStore(CheckpointStore):
    """Thread-safe in-memory store for tests and local runs."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: Dict[str, WorkflowRun] = {}
        self.logs: Dict[str, List[str]] = {}

    def create_workflow_run(
        self, workflow_def: Dict[str, Any], initial_context: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        run_id = str(uuid.uuid4())
        steps = {step["name"]: StepRecord(step["name"]) for step in workflow_def.get("steps", [])}
        run = WorkflowRun(
            id=run_id,
            definition=workflow_def,
            context=dict(initial_context or {}),
            metadata=metadata or {},
            steps=steps,
        )
        with self._lock:
            self._runs[run_id] = run
        return run_id

    def update_workflow_state(self, workflow_id: str, state: WorkflowState, error: Optional[str] = None) -> None:
        with self._lock:
            run = self._runs[workflow_id]
            _validate_transition(run.state, state)
            run.state = state
            run.error = error
            run.updated_at = _timestamp()

    def update_step_state(
        self,
        workflow_id: str,
        step_name: str,
        state: WorkflowState,
        output: Any | None = None,
        error: str | None = None,
    ) -> None:
        with self._lock:
            run = self._runs[workflow_id]
            step = run.steps[step_name]
            _validate_transition(step.state, state)
            if state == WorkflowState.RUNNING:
                step.started_at = _timestamp()
            if state in (WorkflowState.COMPLETED, WorkflowState.FAILED):
                step.finished_at = _timestamp()
            step.state = state
            step.output = output
            step.error = error
            run.updated_at = _timestamp()
            self._runs[workflow_id] = run

    def get_workflow_state(self, workflow_id: str) -> WorkflowRun:
        with self._lock:
            return self._runs[workflow_id]

    def list_active_workflows(self) -> List[WorkflowRun]:
        with self._lock:
            return [run for run in self._runs.values() if run.state in {WorkflowState.PENDING, WorkflowState.RUNNING, WorkflowState.RETRYING, WorkflowState.WAITING}]

    def append_log(self, workflow_id: str, message: str) -> None:
        with self._lock:
            self.logs.setdefault(workflow_id, []).append(message)


class LocalSqliteCheckpointStore(CheckpointStore):
    """SQLite-backed store for simple durability."""

    def __init__(self, path: str | Path = "workflow_checkpoints.db") -> None:
        self.path = Path(path)
        self._init_db()
        self._lock = threading.Lock()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                state TEXT,
                definition TEXT,
                context TEXT,
                metadata TEXT,
                created_at REAL,
                updated_at REAL,
                error TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS steps (
                workflow_id TEXT,
                name TEXT,
                state TEXT,
                input TEXT,
                output TEXT,
                error TEXT,
                started_at REAL,
                finished_at REAL,
                retries INTEGER,
                PRIMARY KEY(workflow_id, name)
            )
            """
        )
        conn.commit()
        conn.close()

    def _conn(self):
        return sqlite3.connect(self.path)

    def create_workflow_run(
        self, workflow_def: Dict[str, Any], initial_context: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        run_id = str(uuid.uuid4())
        now = _timestamp()
        steps = workflow_def.get("steps", [])
        with self._lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO workflows (id, state, definition, context, metadata, created_at, updated_at, error) VALUES (?,?,?,?,?,?,?,?)",
                (
                    run_id,
                    WorkflowState.PENDING.value,
                    json.dumps(workflow_def),
                    json.dumps(initial_context or {}),
                    json.dumps(metadata or {}),
                    now,
                    now,
                    None,
                ),
            )
            for step in steps:
                conn.execute(
                    "INSERT INTO steps (workflow_id, name, state, input, output, error, started_at, finished_at, retries) VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        run_id,
                        step["name"],
                        WorkflowState.PENDING.value,
                        None,
                        None,
                        None,
                        None,
                        None,
                        0,
                    ),
                )
            conn.commit()
        return run_id

    def update_workflow_state(self, workflow_id: str, state: WorkflowState, error: Optional[str] = None) -> None:
        with self._lock, self._conn() as conn:
            current_state = self.get_workflow_state(workflow_id).state
            _validate_transition(current_state, state)
            conn.execute(
                "UPDATE workflows SET state=?, updated_at=?, error=? WHERE id=?",
                (state.value, _timestamp(), error, workflow_id),
            )
            conn.commit()

    def update_step_state(
        self,
        workflow_id: str,
        step_name: str,
        state: WorkflowState,
        output: Any | None = None,
        error: str | None = None,
    ) -> None:
        with self._lock, self._conn() as conn:
            current = self.get_workflow_state(workflow_id)
            step = current.steps[step_name]
            _validate_transition(step.state, state)
            timestamps: Tuple[float | None, float | None] = (step.started_at, step.finished_at)
            if state == WorkflowState.RUNNING:
                timestamps = (_timestamp(), step.finished_at)
            if state in (WorkflowState.COMPLETED, WorkflowState.FAILED):
                timestamps = (step.started_at or _timestamp(), _timestamp())
            conn.execute(
                "UPDATE steps SET state=?, output=?, error=?, started_at=?, finished_at=? WHERE workflow_id=? AND name=?",
                (
                    state.value,
                    json.dumps(output),
                    error,
                    timestamps[0],
                    timestamps[1],
                    workflow_id,
                    step_name,
                ),
            )
            conn.execute(
                "UPDATE workflows SET updated_at=? WHERE id=?",
                (_timestamp(), workflow_id),
            )
            conn.commit()

    def get_workflow_state(self, workflow_id: str) -> WorkflowRun:
        with self._conn() as conn:
            cur = conn.cursor()
            wf_row = cur.execute(
                "SELECT id, state, definition, context, metadata, created_at, updated_at, error FROM workflows WHERE id=?",
                (workflow_id,),
            ).fetchone()
            if not wf_row:
                raise KeyError(f"Workflow {workflow_id} not found")
            steps_rows = cur.execute(
                "SELECT name, state, input, output, error, started_at, finished_at, retries FROM steps WHERE workflow_id=?",
                (workflow_id,),
            ).fetchall()
        steps = {
            row[0]: StepRecord(
                name=row[0],
                state=WorkflowState(row[1]),
                input=json.loads(row[2]) if row[2] else None,
                output=json.loads(row[3]) if row[3] else None,
                error=row[4],
                started_at=row[5],
                finished_at=row[6],
                retries=row[7] or 0,
            )
            for row in steps_rows
        }
        return WorkflowRun(
            id=wf_row[0],
            state=WorkflowState(wf_row[1]),
            definition=json.loads(wf_row[2]),
            context=json.loads(wf_row[3]),
            metadata=json.loads(wf_row[4]),
            created_at=wf_row[5],
            updated_at=wf_row[6],
            steps=steps,
            error=wf_row[7],
        )

    def list_active_workflows(self) -> List[WorkflowRun]:
        with self._conn() as conn:
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT id FROM workflows WHERE state IN (?, ?, ?, ?)",
                (
                    WorkflowState.PENDING.value,
                    WorkflowState.RUNNING.value,
                    WorkflowState.RETRYING.value,
                    WorkflowState.WAITING.value,
                ),
            ).fetchall()
        return [self.get_workflow_state(row[0]) for row in rows]

    def append_log(self, workflow_id: str, message: str) -> None:
        # Logs can be expanded; no-op for now to keep sqlite schema simple.
        return None


def _validate_transition(current: WorkflowState, new: WorkflowState) -> None:
    allowed = {
        WorkflowState.PENDING: {WorkflowState.RUNNING, WorkflowState.FAILED, WorkflowState.RETRYING},
        WorkflowState.RUNNING: {WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.WAITING, WorkflowState.RETRYING},
        WorkflowState.WAITING: {WorkflowState.RUNNING, WorkflowState.FAILED},
        WorkflowState.RETRYING: {WorkflowState.RUNNING, WorkflowState.FAILED},
        WorkflowState.FAILED: {WorkflowState.RETRYING, WorkflowState.FAILED},
        WorkflowState.COMPLETED: {WorkflowState.COMPLETED},
    }
    if new not in allowed.get(current, set()):
        raise InvalidStateTransition(f"Cannot transition from {current} to {new}")
