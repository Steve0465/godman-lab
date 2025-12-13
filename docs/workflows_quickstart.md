# Workflows Quickstart

The workflow engine provides an async-first pipeline for chaining steps with shared context, hooks, and clear error propagation.

## Concepts
- **Step**: Encapsulates a unit of work. Each step has a `name`, an `action`, and an optional `timeout`.
- **Context**: Mutable key/value store shared across steps. Use `ctx.get()` and `ctx.set()` to read/write values.
- **Hooks**: Optional `before_all`, `after_all`, and `on_error` callbacks invoked with the current context.
- **Workflow**: Coordinates steps, runs hooks, and surfaces errors as `WorkflowError`.

## Creating Steps
```python
from godman_ai.workflows.engine import Step

step_fetch = Step("fetch_data", lambda ctx: {"items": [1, 2, 3]})

async def enrich(ctx):
    data = ctx.get("fetch_data")
    return {"sum": sum(data["items"])}

step_enrich = Step("enrich", enrich, timeout=5)
```

## Building a Workflow
```python
from godman_ai.workflows.engine import Workflow, Context

wf = Workflow(
    steps=[step_fetch, step_enrich],
    before_all=lambda ctx: ctx.set("started", True),
    after_all=lambda ctx: ctx.set("finished", True),
)

ctx = await wf.run(Context())
print(ctx.get("enrich"))  # {'sum': 6}
```

## Error Propagation & Hooks
- If a step raises, `WorkflowError` is raised with the failing step name.
- `on_error` hook runs after a failure; use it to log or clean up.
- `after_all` only runs if all steps succeed.

```python
from godman_ai.workflows.engine import WorkflowError

def failing_step(ctx):
    raise ValueError("boom")

wf = Workflow([Step("fail", failing_step)], on_error=lambda ctx: ctx.set("failed", True))

try:
    await wf.run()
except WorkflowError:
    ...
```

## Async Execution
- Actions can be sync or async; sync actions are offloaded via `asyncio.to_thread`.
- Step-level timeouts cancel slow actions with `asyncio.wait_for`.
- Workflows are run with `await wf.run(...)` to keep the event loop responsive.
