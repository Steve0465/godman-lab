"""Critic utilities for evaluating outputs."""

from dataclasses import dataclass
from typing import List


@dataclass
class CriticResult:
    score: float
    labels: List[str]
    reasons: List[str]
