# Godman-Lab Platform v1.0.0

## Summary
- Phase 1–5 completed and validated with stable APIs and offline-safe execution paths.
- Async orchestrator + workflow engine (branching, hooks, DSL loader) paired with deterministic routing.
- Sandboxed tooling layer with registry, async runner, and process-safe shell execution.
- Local model router aligned to `BaseModelInterface` with caching and tracing hooks.
- Skill packaging and plugin discovery enabling reusable skills and MCP-style plugins.
- Capability mesh: capability registry/graph/resolver for discoverable tools/skills/plugins and alternatives; CLI (`godman capabilities ...`) and policy-aware routing.

## Phase Rollup (1–5)
- Phase 1: Import/export hardening, subprocess safety, minimal tests, and logging hygiene.
- Phase 2: Tool test scaffolds, type hints, redaction, and error-path tightening.
- Phase 3: Async orchestrator, workflow DSL/engine, docs for workflows/tools/errors.
- Phase 4: Skills/plugins loading, caching decorators, CI/doc refresh, perf hooks.
- Phase 5: Public API surface finalized, packaging tightened (wheel + sdist), RC validation docs.

## Platform Capabilities
- Async workflows: `Workflow`, `ConditionalStep`, `SwitchStep`, hooks, perf tracking, DSL loader.
- Routing: deterministic tool routing (`RouterV2`) + local model selection via `LocalModelRouter`.
- Tools: `BaseTool`, `ToolRunner`, sandboxed `ShellCommandTool`, MCP tool registry stubs.
- Skills & plugins: `load_all_skills`, `load_plugins` with manifest validation and simple registry.
- Caching & safety: sync/async caching decorators; subprocess sandboxing via `libs.security.process_safe`.

## Breaking Changes
- Deprecated `quick_route` in favor of `RouterV2`/`ToolRouter`.
- Unsandboxed shell execution removed; use `ShellCommandTool` or `libs.sandbox`.
- Public imports now flow through `__all__` exports (see `docs/API_REFERENCE.md`).
- Capability subsystem is optional; if unused, legacy tool routing remains unchanged.

## Upgrade Path (RC → Stable)
- Bump dependencies to `godman-ai==1.0.0` (replacing 1.0.0rc1).
- Update imports to public exports (`godman_ai.orchestrator`, `godman_ai.workflows`, `godman_ai.tools`, etc.).
- Align CI to wheel-first install + smoke validation (see `.github/workflows/test.yml`).
- Replace direct subprocess usage with `libs.sandbox` or `ShellCommandTool`.
- Re-run skill/plugin discovery to confirm manifests and entrypoints.
- Optionally register capabilities; otherwise existing workflows continue normally.

## Acknowledgements
Thanks to all contributors across Phases 1–5 for shipping the stable Godman-Lab platform.
