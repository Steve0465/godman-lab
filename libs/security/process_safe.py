"""Safe process execution helpers."""

from __future__ import annotations

import logging
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Union

logger = logging.getLogger("security.process_safe")
logger.addHandler(logging.NullHandler())

DEFAULT_BLOCKED_COMMANDS = {
    "rm",
    "rmdir",
    "dd",
    "mkfs",
    "format",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "chmod",
    "chown",
    "passwd",
    "su",
    "sudo",
    "curl",
    "wget",
    ">",
    ">>",
}

FORBIDDEN_TOKENS = ["|", ";", "&&", "||", "`", "$(", ">", "<"]


class ProcessSafetyError(Exception):
    """Raised when a command violates safety constraints."""


def _normalize_command(command: Union[str, Sequence[str]]) -> List[str]:
    """Turn a command into a safe argv list and block shell operators."""
    if isinstance(command, str):
        try:
            parts = shlex.split(command)
        except ValueError as exc:
            raise ProcessSafetyError(f"Invalid command syntax: {exc}") from exc
    else:
        parts = [str(part) for part in command]

    if not parts:
        raise ProcessSafetyError("Command cannot be empty")

    for token in parts:
        for pattern in FORBIDDEN_TOKENS:
            if pattern in token:
                raise ProcessSafetyError(
                    f"Disallowed shell operator '{pattern}' in command"
                )

    return parts


def _validate_command_name(
    command_parts: Sequence[str],
    allowed_commands: Optional[Iterable[str]],
    blocked_commands: Optional[Iterable[str]],
) -> None:
    """Validate the base command against allowed/blocked lists."""
    base_cmd = Path(command_parts[0]).name

    blocked = set(DEFAULT_BLOCKED_COMMANDS)
    if blocked_commands:
        blocked.update(blocked_commands)

    if base_cmd in blocked:
        raise ProcessSafetyError(f"Command '{base_cmd}' is blocked")

    if allowed_commands is not None and base_cmd not in set(allowed_commands):
        raise ProcessSafetyError(f"Command '{base_cmd}' is not allowed")


def run_safe(
    command: Union[str, Sequence[str]],
    workdir: Optional[Union[str, Path]] = None,
    timeout: Optional[int] = None,
    allowed_commands: Optional[Iterable[str]] = None,
    blocked_commands: Optional[Iterable[str]] = None,
    input_data: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, object]:
    """
    Execute a command without invoking a shell and with basic safety checks.

    Args:
        command: Command string or sequence of arguments.
        workdir: Working directory to run the command in.
        timeout: Timeout in seconds (default: 30).
        allowed_commands: Optional whitelist of allowed base commands.
        blocked_commands: Optional additional blocked base commands.
        input_data: Optional stdin content passed to the process.
        env: Optional environment variables to use during execution.

    Returns:
        A dictionary containing stdout, stderr, returncode, success, and error (if any).
    """
    cmd_parts = _normalize_command(command)
    _validate_command_name(cmd_parts, allowed_commands, blocked_commands)

    cwd = Path(workdir).resolve() if workdir else Path.cwd()
    if not cwd.exists() or not cwd.is_dir():
        raise ProcessSafetyError(f"Invalid working directory: {cwd}")

    timeout_val = timeout or 30
    logger.info("Executing safe command: %s", " ".join(cmd_parts))

    try:
        result = subprocess.run(
            cmd_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_val,
            check=False,
            input=input_data,
            env=env,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "command": cmd_parts,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout_val} seconds",
            "returncode": -1,
            "command": cmd_parts,
            "error": "timeout",
        }
    except Exception as exc:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(exc),
            "returncode": -1,
            "command": cmd_parts,
            "error": str(exc),
        }
