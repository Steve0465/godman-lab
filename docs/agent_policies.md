# Agent Policies

Policies tune how agents run self-correction.

## AgentPolicy fields
- `max_retries`: total retry attempts.
- `max_corrections`: maximum correction passes before escalation.
- `allowed_models`: list of alternative models.
- `preferred_model_tags`: model preference tags (e.g., high_quality, fast).
- `max_latency_hint`: skip models with higher latency hints.
- `preferred_tools`: fallback tools to try.
- `preferred_capability_tags`: bias capability discovery toward domains/tools with matching tags.
- `escalation_thresholds`: optional per-error thresholds.
- `critics_to_run`: critics to run per step.
- Memory-aware heuristics: policies can use MemoryManager to avoid tools with repeated failures and to favor successful tools/models.

## PolicyEngine behavior
- `choose_critics_for_step`: returns configured critics.
- `choose_strategy`: maps error classes to strategy names.
- `should_escalate`: checks correction/attempt limits.

Policies are serializable (dict/json/yaml) for future DSL integration.
