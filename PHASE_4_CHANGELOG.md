# Phase 4 Changelog

## Overview
Phase 4 introduces skill packaging, plugin discovery, model abstraction, workflow branching/DSL, caching, and instrumentation polish.

## Changes
- Added skill packaging system with manifest validation and examples under `examples/skills/`.
- Introduced plugin registry with discovery hooks.
- Added `BaseModelInterface`, tracing decorator, and LocalModelHandle adapter.
- Extended workflow engine with conditional/switch steps and DSL loader.
- Added caching utilities, documentation, and CI enhancements.

## Testing
- `pytest -q`
