"""Shell command execution tool with enforced sandboxing."""

import logging
from pathlib import Path
from typing import Optional

from godman_ai.tools.base import BaseTool, ToolExecutionError
from libs.sandbox import SandboxError, SandboxExecutor

audit_logger = logging.getLogger("security.shell_tool")
audit_logger.addHandler(logging.NullHandler())


class ShellCommandTool(BaseTool):
    """Execute shell commands with sandboxing for safety."""

    name = "shell_command"
    description = "Execute shell commands with sandboxing for safety."

    def run(
        self,
        command: str,
        workdir: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> dict:
        if not isinstance(command, str) or not command.strip():
            raise ToolExecutionError("Parameter 'command' must be a non-empty string")
        if kwargs.get("safe_mode") is False:
            raise ToolExecutionError("Unsafe shell execution is disabled; safe_mode must be True.")

        audit_logger.info("Shell command requested: %s", command)
        executor = SandboxExecutor()

        try:
            result = executor.execute_safely(
                command=command,
                workdir=Path(workdir) if workdir else None,
                timeout=timeout
            )
            if not result.get("success", False):
                raise ToolExecutionError(result.get("stderr") or "Shell command failed")
            return result
        except SandboxError as exc:
            raise ToolExecutionError(f"Shell execution blocked: {exc}") from exc
        except Exception as e:
            raise ToolExecutionError(f"Shell execution failed: {e}") from e
