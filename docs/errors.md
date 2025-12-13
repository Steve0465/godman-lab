# Error Model

Centralized exception types and when they occur.

## ToolExecutionError
- Raised by tools when execution fails or inputs are invalid.
- Surface friendly messages to callers; avoid leaking sensitive data.

## ModelRoutingError
- Raised when model routing inputs are invalid or no model can be selected.
- Ensure callers handle this before issuing LLM calls.

## WorkflowError
- Raised when a workflow step fails.
- Contains the failing step name; `on_error` hook is invoked before propagation.

## ValidationError
- Raised when input validation fails at orchestrator or tool boundaries.
- Prefer explicit validation over silent coercion.
