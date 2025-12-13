"""Minimal YAML/JSON workflow DSL loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from godman_ai.workflows.engine import ConditionalStep, Context, Step, SwitchStep, Workflow


def _parse(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError:
        yaml = None  # type: ignore

    if yaml:
        return yaml.safe_load(text) or {}
    try:
        return json.loads(text)
    except Exception:
        # Minimal fallback parser for simple workflows
        data: Dict[str, Any] = {"steps": []}
        lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
        steps: List[Dict[str, Any]] = []
        current: Dict[str, Any] = {}
        in_cases = False
        for line in lines:
            if line.startswith("steps"):
                continue
            if line.lstrip().startswith("- "):
                if current:
                    steps.append(current)
                current = {}
                line = line.lstrip("- ").strip()
                if line:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        current[k.strip()] = v.strip().strip('"')
                in_cases = False
                continue
            stripped = line.strip()
            if stripped.startswith("cases:"):
                in_cases = True
                current["cases"] = {}
                continue
            if ":" in stripped:
                k, v = stripped.split(":", 1)
                if in_cases:
                    current.setdefault("cases", {})[k.strip()] = v.strip().strip('"')
                else:
                    current[k.strip()] = v.strip().strip('"')
        if current:
            steps.append(current)
        data["steps"] = steps
        return data


def _build_action(action_spec: Any):
    if isinstance(action_spec, str):
        if action_spec.startswith("set:"):
            key, _, value = action_spec.partition(":")[2].partition("=")
            def _action(ctx):
                ctx.set(key, value)
                return value
            return _action
        if action_spec == "noop":
            return lambda ctx: None
    if callable(action_spec):
        return action_spec
    raise ValueError(f"Unsupported action spec: {action_spec}")


def load_workflow_from_yaml(path: str | Path) -> Workflow:
    data = _parse(Path(path))
    steps_cfg: List[Dict[str, Any]] = data.get("steps", [])
    steps = []

    for step_cfg in steps_cfg:
        name = step_cfg["name"]
        when = step_cfg.get("when")
        switch = step_cfg.get("switch")
        action_spec = step_cfg.get("action", "noop")
        action = _build_action(action_spec)

        if when is not None:
            predicate = lambda ctx, key=when: bool(ctx.get(key))
            steps.append(ConditionalStep(name, action, predicate))
        elif switch:
            def switch_fn(ctx, key=switch):
                return ctx.get(key, "")
            cases_spec = step_cfg.get("cases", {})
            cases = {str(case_key).lower(): _build_action(case_action) for case_key, case_action in cases_spec.items()}
            steps.append(SwitchStep(name, switch_fn, cases))
        else:
            steps.append(Step(name, action))

    return Workflow(steps)
