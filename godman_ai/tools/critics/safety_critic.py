"""Safety critic placeholder."""

from typing import Any

from godman_ai.tools.critics import CriticResult


def check_safety(output: Any) -> CriticResult:
    text = "" if output is None else str(output)
    unsafe_markers = ["rm -rf", "DROP TABLE", "shutdown"]
    if any(marker.lower() in text.lower() for marker in unsafe_markers):
        return CriticResult(score=0.0, labels=["unsafe"], reasons=["unsafe pattern detected"])
    return CriticResult(score=1.0, labels=["safe"], reasons=["no unsafe markers"])
