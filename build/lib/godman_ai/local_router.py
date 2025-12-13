"""
Local model router for task-specific model selection.

Selects the best local model for a given task/query using simple heuristics.
"""

from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence

from godman_ai.models.base import BaseModelInterface, LocalModelHandle
from libs.cache import cached_sync


class TaskType(str, Enum):
    """Classification of task types for model routing."""
    REASONING = "reasoning"
    CODE = "code"
    CHAT = "chat"
    ANALYSIS = "analysis"
    EXECUTION = "execution"
    CUSTOM = "custom"


class LocalModelRouter:
    """
    Routes tasks to appropriate local models based on characteristics.
    """

    MODEL_DEEPSEEK = "deepseek-r1:latest"
    MODEL_PHI4 = "phi4-14b:latest"
    MODEL_GODMAN = "godman-raw:latest"

    def __init__(self, default_model: Optional[str] = None, allowed_models: Optional[Sequence[str]] = None):
        self.allowed_models = set(allowed_models) if allowed_models else {
            self.MODEL_DEEPSEEK,
            self.MODEL_PHI4,
            self.MODEL_GODMAN,
        }
        self.default_model = self._validate_model(default_model or self.MODEL_DEEPSEEK)

        self.task_map: Dict[TaskType, str] = {
            TaskType.REASONING: self.MODEL_DEEPSEEK,
            TaskType.CODE: self.MODEL_PHI4,
            TaskType.CHAT: self.MODEL_GODMAN,
            TaskType.ANALYSIS: self.MODEL_DEEPSEEK,
            TaskType.EXECUTION: self.MODEL_PHI4,
            TaskType.CUSTOM: self.MODEL_GODMAN,
        }

        self.routing_keywords: Dict[str, List[str]] = {
            self.MODEL_DEEPSEEK: [
                "reason", "think", "analyze", "plan", "strategy",
                "explain", "why", "calculate", "solve", "logic",
                "compare", "evaluate", "decide"
            ],
            self.MODEL_PHI4: [
                "code", "function", "class", "debug", "implement",
                "script", "program", "syntax", "compile", "execute",
                "refactor", "optimize", "test"
            ],
            self.MODEL_GODMAN: [
                "godman", "personal", "preference", "custom",
                "chat", "conversation", "tell me", "what do you",
                "remember", "context"
            ],
        }

    def _validate_model(self, model: str) -> str:
        if model not in self.allowed_models:
            raise ValueError(f"Model '{model}' is not allowed. Allowed: {sorted(self.allowed_models)}")
        return model

    @cached_sync(ttl=10.0)
    def classify_task(self, query: str) -> TaskType:
        query_lower = query.lower()
        reasoning_indicators = ["why", "how", "explain", "analyze", "reason", "think"]
        if any(word in query_lower for word in reasoning_indicators):
            return TaskType.REASONING
        code_indicators = ["code", "function", "class", "def ", "implement", "script"]
        if any(word in query_lower for word in code_indicators):
            return TaskType.CODE
        analysis_indicators = ["analyze", "compare", "evaluate", "assess", "review"]
        if any(word in query_lower for word in analysis_indicators):
            return TaskType.ANALYSIS
        custom_indicators = ["godman", "personal", "remember", "preference"]
        if any(word in query_lower for word in custom_indicators):
            return TaskType.CUSTOM
        return TaskType.CHAT

    def select_model(
        self,
        task_type: Optional[TaskType] = None,
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        if task_type:
            return self._validate_model(self.task_map.get(task_type, self.default_model))
        if query:
            inferred_type = self.classify_task(query)
            return self._validate_model(self.task_map.get(inferred_type, self.default_model))
        if context:
            if context.get("force_model"):
                return self._validate_model(str(context["force_model"]))
            if context.get("task_type"):
                return self._validate_model(self.task_map.get(context["task_type"], self.default_model))
        return self.default_model

    @cached_sync(ttl=5.0)
    def route(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        task_type = self.classify_task(query)
        model = self.select_model(task_type=task_type, context=context)
        query_lower = query.lower()
        keywords = self.routing_keywords.get(model, [])
        matches = sum(1 for kw in keywords if kw in query_lower)
        confidence = min(matches / 3.0, 1.0) if matches else 0.5
        return {
            "model": model,
            "task_type": task_type.value,
            "confidence": confidence,
            "reasoning": f"Selected {model} for {task_type.value} task (confidence: {confidence:.2f})"
        }

    def get_model_interface(self, model: Optional[str] = None) -> BaseModelInterface:
        target = model or self.default_model
        return LocalModelHandle(self._validate_model(target))


def select_model(
    task_type: Optional[str] = None,
    query: Optional[str] = None,
    **kwargs: Any
) -> str:
    router = LocalModelRouter()
    if task_type and isinstance(task_type, str):
        try:
            task_type = TaskType(task_type)
        except ValueError:
            task_type = None
    return router.select_model(task_type=task_type, query=query, context=kwargs)
