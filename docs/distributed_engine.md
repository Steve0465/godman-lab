# Distributed Engine (v2 Phase 1)

The distributed workflow runner wraps the existing async workflow engine with checkpointing and worker coordination.

## Components
- `DistributedWorkflowRunner`: submits workflows in local or distributed mode, checkpoints step state, and coordinates concurrency.
- `CheckpointStore`: persistence API with in-memory and SQLite implementations.
- `JobServer`: lightweight HTTP server for submitting workflows and checking status.
- `Worker`: polling worker that processes pending steps.
- `AgentLoop` integration: when `--distributed` is used in `godman agent run`, the AgentLoop uses the distributed runner and checkpoint store to track retries and self-corrections.
- Memory integration: DistributedWorkflowRunner can log workflow start/stop and step outcomes via MemoryManager for later analysis.

## Usage
```bash
godman workflow start examples/workflows/sample.yml --distributed
godman workflow status <workflow_id>
godman worker start
godman job-server start
```

## Execution Modes
- **Local**: compatible with v1.x `Workflow.run` (default).
- **Distributed**: steps are checkpointed, executed concurrently, and can be resumed.
- **Agent-managed**: AgentLoop wraps distributed runs with critics/strategies for self-correction.

## Architecture (text)
- Client submits workflow DSL → JobServer → CheckpointStore.
- Worker polls CheckpointStore for pending steps, executes, and updates state.
- Runner tracks workflow state machine and records outputs/errors.
