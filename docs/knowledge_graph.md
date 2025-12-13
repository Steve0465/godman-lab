# Knowledge Graph

The knowledge graph stores relationships between workflows, steps, tools, agents, errors, and models.

## Nodes
- Types: `WORKFLOW`, `STEP`, `TOOL`, `SKILL`, `AGENT_RUN`, `ERROR`, `MODEL`, `POLICY`.
- Each node has an id and metadata.

## Edges
- Directed edges with `relation_type` (e.g., `HAS_STEP`, `USES_TOOL`, `ERROR`, `DECISION`) and optional weight/metadata.

## Operations
- `add_node`, `add_edge`
- `neighbors(node_id, relation_type=None)`
- `find_paths(source_id, target_id, max_depth=3)` for short path discovery.

Persistence is optional; when a SQLite path is provided, nodes/edges are stored in local tables.
Model-aware workflows can also write performance or routing metadata into the graph when enabled via MemoryManager. CapabilityGraph layers capability nodes/edges (e.g., ALTERNATIVE_FOR, USES) on top of the same storage.
