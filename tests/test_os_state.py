"""Tests for OS Core state manager."""

import pytest
from pathlib import Path
from godman_ai.os_core.state_manager import GlobalState, get_global_state


def test_global_state_initialization():
    """Test that GlobalState initializes correctly."""
    state = GlobalState()
    
    assert state.runtime_stats is not None
    assert "total_tasks_executed" in state.runtime_stats
    assert "total_failures" in state.runtime_stats
    assert "tool_usage_frequencies" in state.runtime_stats


def test_snapshot():
    """Test state snapshot generation."""
    state = GlobalState()
    snapshot = state.snapshot()
    
    assert "uptime_seconds" in snapshot
    assert "runtime_stats" in snapshot
    assert "active_models" in snapshot


def test_update_tool_usage():
    """Test tool usage tracking."""
    state = GlobalState()
    
    state.update_tool_usage("test_tool")
    state.update_tool_usage("test_tool")
    state.update_tool_usage("another_tool")
    
    freq = state.runtime_stats["tool_usage_frequencies"]
    assert freq["test_tool"] == 2
    assert freq["another_tool"] == 1


def test_record_task_execution():
    """Test task execution recording."""
    state = GlobalState()
    
    # Record successful task
    state.record_task_execution(success=True, execution_time=1.5)
    
    assert state.runtime_stats["total_tasks_executed"] == 1
    assert state.runtime_stats["total_failures"] == 0
    assert state.runtime_stats["average_execution_time"] > 0
    
    # Record failed task
    state.record_task_execution(success=False, execution_time=0.5)
    
    assert state.runtime_stats["total_tasks_executed"] == 2
    assert state.runtime_stats["total_failures"] == 1


def test_register_model():
    """Test model registration."""
    state = GlobalState()
    
    state.register_model("gpt-4o")
    state.register_model("gpt-3.5-turbo")
    
    assert "gpt-4o" in state.active_models
    assert "gpt-3.5-turbo" in state.active_models
    
    # Duplicate registration should not add twice
    state.register_model("gpt-4o")
    assert state.active_models.count("gpt-4o") == 1


def test_singleton_global_state():
    """Test that get_global_state returns singleton."""
    state1 = get_global_state()
    state2 = get_global_state()
    
    assert state1 is state2
