# Phase 2 Changelog

## Summary
- Integrated LocalModelRouter across orchestrators and tool routers with stronger typing and validation.
- Hardened logging to redact sensitive values and aligned utilities with GODMAN_LOG_DIR.
- Added test scaffolding for MCP tools, routing, logging security, and import boundaries.
- Fixed audit findings: removed bare `except` in receipts, added type hints to tool registry.

## Details
- `godman_ai/local_router.py`: Refactored router with allowed model validation, richer metadata, and type hints.
- `godman_ai/orchestrator/*`: Attached LocalModelRouter to RouterV2, ToolRouter, and new Orchestrator wrapper.
- `godman_ai/tools/registry.py`: Fully typed registry helpers.
- `godman_ai/tools/receipts.py`: Replaced bare exception with targeted handling and logging.
- `godman_ai/utils/logging_config.py`: Added redaction for password/api_key/token/secret patterns and redacting formatter.
- `libs/tool_runner.py`: Ensured log flushing and append audit line for executions.
- Tests: Added routing/import/log-security coverage plus scaffolds for future MCP tool tests.
- Docs: Updated `AUDIT_SUMMARY.md` to mark Phase 2 completion.

## Testing
- `pytest -q`
