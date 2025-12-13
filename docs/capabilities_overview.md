# Capabilities Overview (Release)

Capabilities form a discoverable mesh of tools, skills, plugins, and workflow templates.

- Registry: `CapabilityRegistry` holds `CapabilityMetadata` (id, type, io hints, tags, permissions/risk, related model tags).
- Graph: `CapabilityGraph` layers relationships (USES, DEPENDS_ON, COMPOSES, ALTERNATIVE_FOR, IMPROVES) on the shared knowledge graph.
- Resolver: `CapabilityResolver` searches by intent/tags and suggests alternatives using registry + graph.
- CLI: `godman capabilities list/search/show/alternatives`.
- Receipt Pack: capability manifests under `godman_ai/capabilities/receipts` for OCR, vendor detection, category mapping, date inference, amount extraction, aggregation, normalization, tax routing, and duplicate detection.
- Trello Pack: capability manifests under `godman_ai/capabilities/trello` for board ingest, card parsing, job classification, next actions, materials inference, address extraction, duration estimation, and priority scoring.
- Measurements Pack: capability manifests under `godman_ai/capabilities/measurements` for measurement OCR, AB parsing, shape classification, gap detection, breakline validation, depth analysis, risk assessment, cover layout planning, and liner cut estimation.
- Drive Pack: capability manifests under `godman_ai/capabilities/drive` for file classification, semantic foldering, tax/job routing, duplicate detection, filename normalization, metadata enrichment, cleanup suggestions, bulk ingest, and crosslinking.

Behavior is optional and backward-compatible: if no capabilities are registered, existing tool/skill workflows continue unchanged.
