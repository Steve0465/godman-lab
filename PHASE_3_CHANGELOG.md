# Phase 3 Changelog

## Overview
Phase 3 introduced async-first orchestration, workflow primitives, and supporting utilities. This changelog summarizes core changes delivered in Phase 3 and follow-on polish.

## Changes
- Added async pathways across tool execution and orchestrator flows while preserving sync compatibility.
- Introduced workflow engine with steps, context, hooks, and robust error propagation.
- Added caching utilities for lightweight sync/async memoization with TTL support.
- Hardened logging redaction and error documentation.
- Expanded tests for async executors, workflow engine, caching, routing, and redaction.

## Key Files
- `godman_ai/tools/base.py`, `godman_ai/tools/runner.py`: async-friendly tool interfaces and runner with timeouts/concurrency.
- `godman_ai/orchestrator/executor_v1.py`, `godman_ai/orchestrator/orchestrator.py`: async execution entry points.
- `godman_ai/workflows/engine.py`: workflow steps/context/hooks.
- `libs/cache.py`: sync/async caching decorators with TTL.
- Tests in `tests/orchestrator/`, `tests/workflows/`, `tests/test_async_tool_runner.py`, `tests/test_cache.py`, `tests/test_redaction.py`.

## Testing
- `pytest -q`
