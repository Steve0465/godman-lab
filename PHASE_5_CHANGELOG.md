# Phase 5 Changelog (Release Candidate)

- Finalized public API exports across `godman_ai`, orchestrator, workflows, models, tools, skills, and plugins.
- Added workflow package `__init__.py` and implemented `Orchestrator` facade for stable imports.
- Renamed router metadata class to avoid BaseTool collisions; clarified deprecations.
- Bumped version to `1.0.0rc1` and added minimal `README.md` for packaging.
- Updated documentation (`AUDIT_SUMMARY.md`, `API_REFERENCE.md`) with RC status and deprecated items.
- Expanded CI to lint, build/install wheel, and validate skills/plugins across Python 3.12/3.13.
