# Workflow Checkpointing

Checkpointing tracks workflow progress and enables resuming after failures.

## Stores
- `InMemoryCheckpointStore`: thread-safe, ideal for tests and local dev.
- `LocalSqliteCheckpointStore`: durable fallback using SQLite (no external services).

## Stored Data
- Workflow id, state, timestamps, metadata.
- Step state (inputs/outputs/errors, retries).
- Optional logs/events.

## States
- `PENDING` → `RUNNING` → `COMPLETED`
- `RUNNING` → `FAILED` (with error)
- `FAILED` → `RETRYING` → `RUNNING`
- `WAITING` for external events, then back to `RUNNING`.

## Resume Flow
1. Query checkpoint store for a workflow id.
2. Identify steps not in `COMPLETED`.
3. Dispatch remaining steps via workers or `DistributedWorkflowRunner`.
