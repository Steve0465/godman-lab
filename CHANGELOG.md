# Changelog

## v1.0.0 (Stable)
- Finalized public API exports across orchestrator, workflows, models, tools, skills, and plugins (Phases 1–5 complete).
- Delivered async-first workflow engine with branching, DSL loader, hooks, perf tracking, and deterministic routing.
- Hardened tool execution with sandboxed shell tool, process safety, async tool runner, and MCP-style registry stubs.
- Added skill packaging + plugin discovery, caching helpers, and local model router alignment to `BaseModelInterface`.
- Docs released for workflows, tools, skills/plugins, model interface, and errors; release notes published.
- CI updated to lint, build/install wheel, run pytest, validate skills/plugins, and upload v1.0.0 artifacts.

## [Unreleased] – Google Drive Automation Pack

### Added
- Full Google Drive Automation Pack:
  - Async Drive capabilities (upload, download, search, move, copy, share)
  - Universal Drive client wrapper
  - Drive workflow suite (OCR → classify → archive; ingest → tag → index)
  - Drive sync agent (event-driven folder monitors)
  - Drive plugins for Codex/Godman AI orchestration
  - Unified exceptions + logging middleware
  - CLI integration: `godman drive *`
  - Test suite: 143 passed, 5 skipped (pydantic warnings inherited from upstream)

### Notes
- All Drive workflows are non-blocking and use async pools.
- Compatible with existing orchestrator planner/executor loops.
- All new skills registered under `godman_ai.skills.drive.*`.
