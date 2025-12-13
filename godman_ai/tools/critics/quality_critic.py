"""Simple quality critic."""

from typing import Any, Dict

from godman_ai.tools.critics import CriticResult


def evaluate_quality(output: Any) -> CriticResult:
    text = "" if output is None else str(output)
    score = 1.0 if text else 0.0
    labels = ["complete"] if text else ["missing"]
    reasons = ["output present"] if text else ["no output produced"]
    return CriticResult(score=score, labels=labels, reasons=reasons)
