# API Reference (Summary)

Public entry points are exported via `__all__` in each package:

- `godman_ai`: `__version__`, `ModelRoutingError`, `ValidationError`, `WorkflowError`, `LocalModelRouter`, `TaskType`, `select_model`
- `godman_ai.orchestrator`: `Orchestrator`, `ExecutorAgent`, `RouterV2`, `ToolRouter`, `quick_route`
- `godman_ai.models`: `BaseModelInterface`, `LocalModelHandle`, `trace_model`, `Preset`
- `godman_ai.workflows`: `Workflow`, `Step`, `ConditionalStep`, `SwitchStep`, `Context`, `WorkflowError`, `load_workflow_from_yaml`, `DistributedWorkflowRunner`, `CheckpointStore`, `InMemoryCheckpointStore`, `LocalSqliteCheckpointStore`, `WorkflowRun`, `WorkflowState`
- `godman_ai.tools`: `ToolRunner`, `BaseTool`, `ShellCommandTool`, `ToolExecutionError`, `register_tool`, `register_function_tool`, `list_tools`, `get_tool`, `initialize_mcp_tools`, receipt helpers under `godman_ai.tools.receipts`
- `godman_ai.skills`: `load_skill`, `load_all_skills`, `SkillLoadError`
- `godman_ai.plugins`: `register_plugin`, `list_plugins`, `load_plugins`
- `godman_ai.capabilities`: `CapabilityRegistry`, `CapabilityMetadata`, `CapabilityGraph`, `CapabilityResolver`, `CapabilityType`, `register_tool_capability`, `register_skill_capability`, `register_plugin_capability`
- `godman_ai.workflows.measurements`: helpers for cover/liner measurement reviews; DSL loaders for measurement workflows.

See individual module docstrings for detailed method signatures.
