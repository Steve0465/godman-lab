# Receipts Automation Pack

The receipt pack provides capabilities, skills, plugins, and workflows for common receipt flows.

- Capabilities: OCR, vendor detection, category mapping, date inference, amount extraction, filename normalization, tax routing, duplicate detection, statement aggregation.
- Skills: async skills for OCR, parsing, classification, normalization under `examples/skills/receipts/*`.
- Plugins: vendor rules, category overrides, smart retry under `examples/plugins/*`.
- Workflows: `workflow_receipt_full.dsl.yaml`, `workflow_receipt_monthly_aggregate.dsl.yaml` with Python wrappers in `godman_ai.workflows.receipts`.
- CLI: `godman receipts parse|classify|workflow|month` for quick operations.

All features are optional; if unused, the platform behaves as before.
