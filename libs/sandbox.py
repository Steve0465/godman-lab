"""
Sandboxed command execution with security constraints.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from libs.security.process_safe import ProcessSafetyError, run_safe


class SandboxError(Exception):
    """Raised when sandbox security constraints are violated."""


class SandboxExecutor:
    def __init__(
        self,
        allowed_commands: Optional[List[str]] = None,
        blocked_commands: Optional[List[str]] = None,
        allowed_paths: Optional[List[Path]] = None,
        max_timeout: int = 30
    ):
        self.allowed_commands = allowed_commands
        self.blocked_commands = blocked_commands or []
        self.allowed_paths = allowed_paths
        self.max_timeout = max_timeout

    def _validate_path(self, path: Path) -> None:
        if self.allowed_paths is None:
            return
        path = path.resolve()
        for allowed in self.allowed_paths:
            allowed = allowed.resolve()
            if path == allowed or path.is_relative_to(allowed):
                return
        raise SandboxError(f"Path '{path}' not in allowed paths")

    def execute_safely(
        self,
        command: str,
        workdir: Optional[Union[str, Path]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        if workdir:
            workdir = Path(workdir)
            self._validate_path(workdir)
        else:
            workdir = Path.cwd()

        timeout = min(timeout or self.max_timeout, self.max_timeout)
        try:
            result = run_safe(
                command,
                workdir=workdir,
                timeout=timeout,
                allowed_commands=self.allowed_commands,
                blocked_commands=self.blocked_commands,
            )
            return result
        except ProcessSafetyError as exc:
            raise SandboxError(str(exc)) from exc
        except Exception as exc:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(exc),
                "returncode": -1,
                "error": str(exc),
            }


def execute_safely(
    command: str,
    workdir: Optional[Union[str, Path]] = None,
    timeout: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    executor = SandboxExecutor(**kwargs)
    return executor.execute_safely(command, workdir, timeout)
