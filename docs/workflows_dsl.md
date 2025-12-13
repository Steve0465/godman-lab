# Workflows DSL

Minimal YAML/JSON DSL for constructing workflows.

## Structure
```yaml
steps:
  - name: set_flag
    action: "set:flag=true"
  - name: choose
    switch: flag
    cases:
      true: "set:result=yes"
      false: "set:result=no"
```

## Fields
- `name`: step name (required)
- `action`: string or callable reference; built-ins:
  - `set:key=value` sets context and returns value
  - `noop` does nothing
- `when`: context key that must be truthy to run (creates ConditionalStep)
- `switch`: context key used to select a case (creates SwitchStep)
- `cases`: mapping of value -> action

## Loading
```python
from godman_ai.workflows.dsl_loader import load_workflow_from_yaml

wf = load_workflow_from_yaml("path/to/workflow.yaml")
ctx = await wf.run()
```
