"""Async-first workflow engine."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from godman_ai.errors import WorkflowError

Action = Callable[..., Union[Any, Awaitable[Any]]]
Hook = Callable[["Context"], Union[None, Awaitable[None]]]


@dataclass
class Context:
    """Mutable workflow context."""

    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value


@dataclass
class Step:
    """Single workflow step."""

    name: str
    action: Action
    timeout: Optional[float] = None

    async def execute(self, context: Context) -> Any:
        result = self.action(context)
        if asyncio.iscoroutine(result):
            coro = result
        else:
            coro = asyncio.to_thread(lambda: result)

        if self.timeout:
            return await asyncio.wait_for(coro, timeout=self.timeout)
        return await coro


class Workflow:
    """Async workflow runner with hooks and error propagation."""

    def __init__(
        self,
        steps: List[Step],
        before_all: Optional[Hook] = None,
        after_all: Optional[Hook] = None,
        on_error: Optional[Hook] = None,
    ) -> None:
        self.steps = steps
        self.before_all = before_all
        self.after_all = after_all
        self.on_error = on_error
        self.before_workflow: Optional[Hook] = None
        self.after_workflow: Optional[Hook] = None

    async def run(self, context: Optional[Context] = None) -> Context:
        ctx = context or Context()

        async def _maybe_call(hook: Optional[Hook]) -> None:
            if not hook:
                return
            res = hook(ctx)
            if asyncio.iscoroutine(res):
                await res

        await _maybe_call(self.before_all)
        await _maybe_call(self.before_workflow)

        for step in self.steps:
            try:
                start = asyncio.get_event_loop().time()
                result = await step.execute(ctx)
                duration = int((asyncio.get_event_loop().time() - start) * 1000)
                perf = ctx.get("_perf", {})
                perf[step.name] = {"duration_ms": duration}
                ctx.set("_perf", perf)
                ctx.set(step.name, result)
            except asyncio.CancelledError:
                await _maybe_call(self.on_error)
                raise
            except Exception as exc:
                ctx.set("error", {"step": step.name, "error": str(exc)})
                await _maybe_call(self.on_error)
                raise WorkflowError(f"Step '{step.name}' failed: {exc}") from exc

        await _maybe_call(self.after_all)
        await _maybe_call(self.after_workflow)
        return ctx


class ConditionalStep(Step):
    """Step that executes only when predicate(context) is True."""

    def __init__(self, name: str, action: Action, predicate: Callable[[Context], bool], timeout: Optional[float] = None):
        super().__init__(name, action, timeout)
        self.predicate = predicate

    async def execute(self, context: Context) -> Any:
        if not self.predicate(context):
            return None
        return await super().execute(context)


class SwitchStep(Step):
    """Step that selects an action based on a switch function."""

    def __init__(
        self,
        name: str,
        switch: Callable[[Context], str],
        cases: Dict[str, Action],
        timeout: Optional[float] = None,
    ):
        self.switch = switch
        self.cases = {str(k).lower(): v for k, v in cases.items()}
        super().__init__(name, lambda ctx: self._dispatch(ctx), timeout)

    def _dispatch(self, context: Context) -> Any:
        key = str(self.switch(context)).lower()
        action = self.cases.get(key)
        if not action:
            raise WorkflowError(f"No case for key '{key}'")
        result = action(context)
        return result
