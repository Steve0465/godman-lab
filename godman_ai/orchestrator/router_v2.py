"""
Router v2: Keyword-scoring tool selector for Godman AI.
"""

import re
from typing import Dict, Optional, Tuple

from godman_ai.local_router import LocalModelRouter
from godman_ai.tools.registry import TOOL_REGISTRY


class RoutedTool:
    """Container for routing result."""

    def __init__(self, name: Optional[str], score: float, reason: str):
        self.name = name
        self.score = score
        self.reason = reason

    def to_dict(self):
        return {
            "tool": self.name,
            "score": self.score,
            "reason": self.reason,
        }


class RouterV2:
    """Deterministic keyword-based router."""

    def __init__(self) -> None:
        self.tools = TOOL_REGISTRY
        self.model_router = LocalModelRouter()

    @staticmethod
    def normalize(text: str) -> str:
        """Lowercase, remove non-alphanumerics except spaces."""
        return re.sub(r"[^a-z0-9 ]+", "", text.lower())

    def score_tool(self, query: str, tool_name: str, description: str) -> Tuple[int, str]:
        q = self.normalize(query)
        n = self.normalize(tool_name)
        d = self.normalize(description)
        score = 0
        reason_parts = []
        for word in q.split():
            if word in n:
                score += 2
                reason_parts.append(f"name:{word}")
            if word in d:
                score += 1
                reason_parts.append(f"desc:{word}")
        reason = ", ".join(reason_parts) if reason_parts else "no matches"
        return score, reason

    def route(self, query: str) -> Dict[str, object]:
        if not self.tools:
            return {"ok": False, "error": "No tools registered"}
        best = RoutedTool(name=None, score=-1, reason="no matches")
        for tool_name, tool_cls in self.tools.items():
            desc = getattr(tool_cls, "description", "") if hasattr(tool_cls, "description") else str(tool_cls)
            score, reason = self.score_tool(query, tool_name, desc)
            if score > best.score:
                best = RoutedTool(tool_name, score, reason)
        return {
            "ok": True,
            "tool": best.name,
            "score": best.score,
            "reason": best.reason,
        }

    def route_with_model(self, query: str, task_type: Optional[str] = None) -> Dict[str, object]:
        selection = self.model_router.route(query)
        return {
            "model": selection["model"],
            "task_type": selection["task_type"],
            "confidence": selection["confidence"],
            "routing": self.route(query),
        }
