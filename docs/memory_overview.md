# Memory Overview

Phase 3 introduces short-term and long-term memory layers so agents and workflows can learn from past runs.

- **ShortTermMemoryStore**: per-process, in-memory, fast queries.
- **LongTermMemoryStore**: durable store (in-memory for tests or SQLite-backed).
- **MemoryRecord**: captures id, timestamp, type, source, payload, tags, and related ids.
- **MemoryManager**: writes to stores and knowledge graph, exposes helpers to record workflow/agent/error events and query histories.

Use cases:
- Avoid retrying failing tools.
- Favor successful tool/model combinations for a workflow.
- Record agent decisions and escalations for auditability.
