# Capability Graph

Capabilities are represented as nodes in the knowledge graph with typed edges.

## Relations
- `USES`: capability uses another capability.
- `DEPENDS_ON`: hard dependency.
- `COMPOSES`: combines multiple capabilities into a workflow template.
- `ALTERNATIVE_FOR`: interchangeable capabilities; used for fallback/ substitution.
- `IMPROVES`: capability enhances another (e.g., higher quality model/tool).

CapabilityGraph is backed by the shared KnowledgeGraph and persists nodes/edges (SQLite optional). Relation queries support alternative lookups and neighborhood discovery.
