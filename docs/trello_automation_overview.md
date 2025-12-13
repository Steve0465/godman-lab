# Trello Automation Pack

The Trello pack adds capabilities, skills, plugins, workflows, and CLI helpers for job automation based on Trello boards/cards.

- Capabilities: ingest boards, parse cards, classify job type, suggest next actions, infer materials, extract address, estimate duration, and score priority (manifests under `godman_ai/capabilities/trello`).
- Skills: async skills to fetch boards, parse cards, classify jobs, estimate materials/duration (`examples/skills/trello/*`).
- Workflows: daily planner and deep job summarizer DSLs with Python wrappers in `godman_ai/workflows/trello.py`.
- Plugins: material rule overrides, job category rules, priority scoring tweaks (`examples/plugins/trello/*`).
- CLI: `godman trello fetch|summarize|job|workflow` for quick operations (API calls are mocked/offline).

All features remain optional; core orchestrator and other packs continue to work as-is.
