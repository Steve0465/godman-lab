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


def test_error_handling_no_information_disclosure():
    """Test that internal error details are not exposed to clients"""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        
        client = TestClient(app)
        
        # Test an endpoint that will trigger an internal error
        # Use mock to simulate internal exception
        with patch("godman_ai.orchestrator.Orchestrator") as mock_orchestrator_cls:
            # Simulate an internal error with detailed message
            mock_instance = Mock()
            mock_orchestrator_cls.return_value = mock_instance
            mock_instance.load_tools_from_package = Mock()
            
            # Simulate AttributeError when accessing tools attribute
            type(mock_instance).tools = Mock(side_effect=AttributeError(
                "'Orchestrator' object has no attribute 'tools'"
            ))
            
            response = client.get("/tools")
            
            # Should return 500 status
            assert response.status_code == 500
            
            # Response should NOT contain internal error details
            error_detail = response.json()["detail"]
            
            # Should be a generic error message
            assert "Internal Server Error" in error_detail
            
            # Should NOT contain the actual exception message
            assert "AttributeError" not in error_detail
            assert "has no attribute" not in error_detail
            assert "'tools'" not in error_detail
    except ImportError:
        pytest.skip("FastAPI not installed")


def test_error_handling_with_orchestrator_failure():
    """Test error handling when orchestrator run fails"""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        
        client = TestClient(app)
        
        # Mock orchestrator to raise an exception
        with patch("godman_ai.orchestrator.Orchestrator") as mock_orchestrator_cls:
            mock_instance = Mock()
            mock_orchestrator_cls.return_value = mock_instance
            mock_instance.load_tools_from_package = Mock()
            mock_instance.run_task.side_effect = ValueError(
                "Internal database connection failed at line 42 in module xyz"
            )
            
            response = client.post(
                "/run",
                json={"input": "test task"}
            )
            
            # Should return 500 status
            assert response.status_code == 500
            
            # Response should NOT contain internal error details
            error_detail = response.json()["detail"]
            
            # Should be a generic error message
            assert "Internal Server Error" in error_detail
            
            # Should NOT contain the actual exception message
            assert "database connection" not in error_detail
            assert "line 42" not in error_detail
            assert "module xyz" not in error_detail
    except ImportError:
        pytest.skip("FastAPI not installed")
