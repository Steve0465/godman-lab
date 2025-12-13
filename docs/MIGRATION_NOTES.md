# Migration Notes (pre-v1 to v1.0.0-RC)

## Breaking / Structural Changes
- Tools: standardized around `BaseTool`, `ToolRunner`, and registry exports under `godman_ai.tools`.
- Models: introduced `BaseModelInterface` and `LocalModelHandle`; model access now via `godman_ai.models`.
- Routing: `LocalModelRouter` moved to root package with caching; orchestrators expose `RouterV2` and `ExecutorAgent`.
- Workflows: async-first engine with branching, DSL loader, and structured hooks.
- Skills/Plugins: packaged skills with `skill.yaml` and plugin discovery via `godman_ai.plugins`.

## Deprecations
- `godman_ai.orchestrator.tool_router.quick_route` is deprecated; use `RouterV2` or `ToolRouter`.
- Legacy shell execution without sandboxing is removed.

## Migration Tips
- Update imports to use package exports listed in `docs/API_REFERENCE.md`.
- Replace direct subprocess shell calls with `ToolRunner` or sandboxed `ShellCommandTool`.
- For workflows, wrap synchronous actions or use the DSL loader for simple flows.

## Versioning
- Version is tracked in `godman_ai/version.py` (`1.0.0`).
- Capabilities: optional capability registry/graph/resolver added. If unused, prior tool/skill behavior remains. You can register capabilities via `CapabilityRegistry` or CLI and use `CapabilityResolver` for intent-based selection. Workflows/agents can still reference tools directly.
- Examples:
  - `godman capabilities list`
  - `godman capabilities search --intent "summarize receipts"`
  - programmatic: `from godman_ai.capabilities import CapabilityRegistry, CapabilityResolver`
