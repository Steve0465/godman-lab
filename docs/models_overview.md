# Models Overview

The multi-model layer introduces a registry, selector, and performance tracking.

- **ModelRegistry**: stores `ModelConfig` entries with provider/type/tags and cost/latency hints.
- **ModelSelector**: chooses models using policy hints, tags, and enablement; returns fallbacks for resilience.
- **ModelPerformanceStore**: records model successes, latency, and quality scores (in-memory or SQLite).
- **ModelRouterV3**: wraps the legacy router with selector-driven choices and fallbacks.

Use the CLI to inspect models:
```bash
godman models list
godman models stats --model-id deepseek-r1:latest
godman models test deepseek-r1:latest --prompt "hello"
```
