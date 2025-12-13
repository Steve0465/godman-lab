"""Heuristic factuality critic."""

from typing import Any

from godman_ai.tools.critics import CriticResult


def evaluate_factuality(output: Any) -> CriticResult:
    text = "" if output is None else str(output)
    contradictions = ["not not", "cannot cannot"]
    if any(token in text for token in contradictions):
        return CriticResult(score=0.2, labels=["contradiction"], reasons=["self-contradiction detected"])
    if text:
        return CriticResult(score=0.8, labels=["plausible"], reasons=["basic plausibility (heuristic)"])
    return CriticResult(score=0.0, labels=["missing"], reasons=["no content"])
