# Model Routing Policies

Agent policies can influence model selection:
- `preferred_model_tags`: favor models with these tags (e.g., `["high_quality"]`).
- `forbidden_models`: never select these ids.
- `max_latency_hint`: skip models with higher latency hints.
- `allowed_models`: explicit allowlist for retries/fallbacks.
- `use_ensemble_for_critical_tasks`: if true, some strategies can run two models and pick the higher-quality result.

Routing flow:
1) ModelSelector filters enabled models per policy.
2) Preferred tags and latency/cost hints bias the choice.
3) Fallback models are provided; strategies may switch after failures.
4) Performance stats can be used to bias toward historically strong models.
