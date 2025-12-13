# Drive Automation Pack

This pack adds offline, mocked automation for organizing files in Google Drive-style workflows (no real API calls).

## Capabilities
- `drive_file_classification`, `drive_semantic_foldering`, `drive_tax_year_routing`, `drive_job_routing`, `drive_duplicate_detection`, `drive_filename_normalization`, `drive_metadata_enrichment`, `drive_cleanup_suggestions`, `drive_bulk_ingest`, `drive_crosslink`.

## Skills
- Async skills to inspect, classify, normalize, route, store, and dedupe files (`examples/skills/drive/*`).

## Workflows
- DSLs: `drive_auto_ingest.dsl.yaml`, `drive_cleanup.dsl.yaml`, `drive_crosslink_trello.dsl.yaml` with wrappers in `godman_ai/workflows/drive.py`.

## CLI
- Commands: `godman drive ingest|cleanup|classify|auto|trello-link` (all mocked/offline).

All behavior is optional and does not affect other packs.
