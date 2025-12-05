"""Tests for daemon mode"""

import pytest
from unittest.mock import Mock, patch


def test_daemon_initialization():
    """Test GodmanDaemon can be initialized"""
    from godman_ai.service.daemon import GodmanDaemon
    
    daemon = GodmanDaemon()
    assert daemon.pid_file is not None
    assert daemon.log_dir.exists()


def test_daemon_is_not_running_initially():
    """Test daemon is not running on first check"""
    from godman_ai.service.daemon import GodmanDaemon
    
    daemon = GodmanDaemon()
    
    # Clean up any stale PID file
    if daemon.pid_file.exists():
        daemon.pid_file.unlink()
    
    assert not daemon.is_running()


def test_daemon_status_when_not_running():
    """Test daemon status when not running"""
    from godman_ai.service.daemon import GodmanDaemon
    
    daemon = GodmanDaemon()
    
    # Clean up any stale PID file
    if daemon.pid_file.exists():
        daemon.pid_file.unlink()
    
    status = daemon.status()
    assert status["running"] is False
    assert "message" in status
