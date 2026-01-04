"""Test FastAPI integration with diagnostics"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_diagnostics_can_be_used_in_fastapi():
    """Test that diagnostics can be used in async FastAPI endpoints"""
    from godman_ai.diagnostics import run_llm_health_check

    # Mock the service checks to avoid actual API calls
    with patch(
        "godman_ai.diagnostics.llm_health._check_openai_health", new_callable=AsyncMock
    ) as mock_openai:
        with patch(
            "godman_ai.diagnostics.llm_health._check_google_ai_health", new_callable=AsyncMock
        ) as mock_google:
            mock_openai.return_value = {
                "service": "openai",
                "available": True,
                "response_time_ms": 100,
            }
            mock_google.return_value = {
                "service": "google_ai",
                "available": True,
                "response_time_ms": 150,
            }

            # This simulates calling from an async FastAPI endpoint
            result = await run_llm_health_check()

            assert result["overall_status"] == "healthy"
            assert "services" in result


@pytest.mark.asyncio
async def test_installer_can_be_used_in_fastapi():
    """Test that installer can be used in async FastAPI endpoints"""
    from godman_ai.diagnostics import install_all

    with patch("godman_ai.diagnostics.installer._run_command", new_callable=AsyncMock) as mock_cmd:
        mock_cmd.return_value = {
            "returncode": 0,
            "stdout": "Success",
            "stderr": "",
            "command": "test",
        }

        # This simulates calling from an async FastAPI endpoint
        result = await install_all(pip_packages=["requests"])

        assert result["success"] is True


def test_diagnostics_endpoints_example():
    """Example of how to use diagnostics in FastAPI endpoints"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from unittest.mock import AsyncMock, patch

    app = FastAPI()

    @app.get("/health")
    async def health_endpoint():
        """Health check endpoint using diagnostics"""
        from godman_ai.diagnostics import run_llm_health_check

        # In real usage, this would call the actual health check
        # For this test, we mock it
        with patch(
            "godman_ai.diagnostics.llm_health._check_openai_health", new_callable=AsyncMock
        ) as mock_openai:
            with patch(
                "godman_ai.diagnostics.llm_health._check_google_ai_health", new_callable=AsyncMock
            ) as mock_google:
                mock_openai.return_value = {"service": "openai", "available": True}
                mock_google.return_value = {"service": "google_ai", "available": True}

                result = await run_llm_health_check()
                return result

    # Test the endpoint
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "overall_status" in data
