"""Tests for server module"""

import pytest
from unittest.mock import Mock, patch


def test_find_available_port():
    """Test port finding logic"""
    from godman_ai.service.server import _find_available_port
    
    port = _find_available_port(start_port=9000)
    assert isinstance(port, int)
    assert port >= 9000


def test_server_initialization():
    """Test server can be initialized"""
    try:
        from godman_ai.service.server import run_server
        assert callable(run_server)
    except ImportError as e:
        pytest.skip(f"Uvicorn not installed: {e}")
