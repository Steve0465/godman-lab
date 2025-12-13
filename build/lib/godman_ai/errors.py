"""Shared exception types for Godman AI components."""


class ModelRoutingError(Exception):
    """Raised when model routing fails or receives invalid input."""


class WorkflowError(Exception):
    """Raised when a workflow step fails."""


class ValidationError(Exception):
    """Raised when input validation fails."""


__all__ = ["ModelRoutingError", "WorkflowError", "ValidationError"]
