import pytest

from libs.sandbox import SandboxError, SandboxExecutor
from libs.security import ProcessSafetyError, run_safe


def test_run_safe_blocks_shell_operators():
    with pytest.raises(ProcessSafetyError):
        run_safe("echo hello && whoami")


def test_sandbox_blocks_dangerous_command():
    executor = SandboxExecutor()
    with pytest.raises(SandboxError):
        executor.execute_safely("rm -rf /")


def test_sandbox_respects_allowed_paths(tmp_path):
    executor = SandboxExecutor(allowed_paths=[tmp_path])
    ok_result = executor.execute_safely("echo safe", workdir=tmp_path)
    assert ok_result["success"]

    with pytest.raises(SandboxError):
        executor.execute_safely("echo blocked", workdir=tmp_path.parent)


def test_sandbox_runs_basic_command():
    executor = SandboxExecutor()
    result = executor.execute_safely("echo hello")
    assert result["success"]
    assert "hello" in result["stdout"]
