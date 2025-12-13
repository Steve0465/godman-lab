# Agents Overview

Phase 2 introduces a self-correcting AgentLoop that evaluates outputs, classifies errors, and retries with alternative strategies.

## Components
- `AgentLoop`: orchestrates evaluation → correction → retry.
- `AgentPolicy`: controls retries, critics, preferred tools/models, and escalation thresholds.
- Critics: quality, structure, safety, factuality.
- Strategies: retry same tool, switch model, route to another tool, run correction subworkflow, escalate.
- Error classifier: maps exceptions to broad error classes.
- Memory-aware decisions: AgentLoop can log successes/failures via MemoryManager and policies can reference past outcomes.
- Model strategies: policies can prefer tagged models, switch to fallbacks, and optionally run ensembles for critical tasks.
- Capability-aware routing: agents can select tools/skills/plugins via CapabilityResolver and suggest alternatives when failures occur.

## Running
```bash
godman agent run examples/workflows/sample.yml --distributed
godman agent status <workflow_id>
godman agent logs <workflow_id>
```
