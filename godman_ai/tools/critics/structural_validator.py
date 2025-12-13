"""Structural validator critic."""

from typing import Any, Iterable, List

from godman_ai.tools.critics import CriticResult


def validate_structure(output: Any, required_keys: Iterable[str] | None = None) -> CriticResult:
    required = list(required_keys or [])
    labels: List[str] = []
    missing = []
    if isinstance(output, dict):
        for key in required:
            if key not in output:
                missing.append(key)
        labels.append("dict")
    else:
        labels.append("non-dict")
        missing = required
    score = 1.0 if not missing else max(0.0, 1.0 - len(missing) * 0.25)
    reasons = ["missing: " + ", ".join(missing)] if missing else ["structure ok"]
    return CriticResult(score=score, labels=labels, reasons=reasons)
