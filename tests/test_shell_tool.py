import pytest

from godman_ai.tools.shell import ShellCommandTool
from godman_ai.tools.base import ToolExecutionError


def test_shell_tool_runs_echo():
    tool = ShellCommandTool()
    result = tool.run("echo shelltool")
    assert result["success"]
    assert "shelltool" in result["stdout"]


def test_shell_tool_blocks_unsafe_commands():
    tool = ShellCommandTool()
    with pytest.raises(ToolExecutionError):
        tool.run("echo hi && whoami")


def test_shell_tool_rejects_disabled_safe_mode():
    tool = ShellCommandTool()
    with pytest.raises(ToolExecutionError):
        tool.run("echo hi", safe_mode=False)
