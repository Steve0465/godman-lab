"""Tests for API endpoints"""

import pytest
from unittest.mock import Mock, patch


def test_api_imports():
    """Test that API module imports correctly"""
    try:
        from godman_ai.service.api import app
        assert app is not None
    except ImportError as e:
        pytest.skip(f"FastAPI not installed: {e}")


def test_root_endpoint():
    """Test root endpoint"""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "GodmanAI API Server"
    except ImportError:
        pytest.skip("FastAPI not installed")


def test_dashboard_endpoint():
    """Test dashboard endpoint returns HTML"""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        
        client = TestClient(app)
        response = client.get("/dashboard")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "GodmanAI Dashboard" in response.text
    except ImportError:
        pytest.skip("FastAPI not installed")


def test_tools_endpoint():
    """Test tools listing endpoint"""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        
        client = TestClient(app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)
    except ImportError:
        pytest.skip("FastAPI not installed")
