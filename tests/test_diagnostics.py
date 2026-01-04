"""Tests for diagnostics module"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_install_all_with_pip_packages():
    """Test install_all with pip packages"""
    from godman_ai.diagnostics import install_all

    with patch("godman_ai.diagnostics.installer._run_command", new_callable=AsyncMock) as mock_cmd:
        mock_cmd.return_value = {
            "returncode": 0,
            "stdout": "Successfully installed test-package",
            "stderr": "",
            "command": "pip install test-package",
        }

        result = await install_all(pip_packages=["test-package"])

        assert result["success"] is True
        assert "pip" in result
        assert result["pip"]["success"] is True
        assert "test-package" in result["pip"]["installed"]


@pytest.mark.asyncio
async def test_install_all_with_npm_packages():
    """Test install_all with npm packages"""
    from godman_ai.diagnostics import install_all

    with patch(
        "godman_ai.diagnostics.installer._check_command_available", new_callable=AsyncMock
    ) as mock_check:
        with patch(
            "godman_ai.diagnostics.installer._run_command", new_callable=AsyncMock
        ) as mock_cmd:
            mock_check.return_value = True
            mock_cmd.return_value = {
                "returncode": 0,
                "stdout": "Successfully installed typescript",
                "stderr": "",
                "command": "npm install typescript",
            }

            result = await install_all(npm_packages=["typescript"])

            assert result["success"] is True
            assert "npm" in result
            assert result["npm"]["success"] is True
            assert "typescript" in result["npm"]["installed"]


@pytest.mark.asyncio
async def test_install_all_npm_not_available():
    """Test install_all when npm is not available"""
    from godman_ai.diagnostics import install_all

    with patch(
        "godman_ai.diagnostics.installer._check_command_available", new_callable=AsyncMock
    ) as mock_check:
        mock_check.return_value = False

        result = await install_all(npm_packages=["typescript"])

        assert result["success"] is False
        assert "npm" in result
        assert result["npm"]["success"] is False
        assert "npm not available" in result["errors"]


@pytest.mark.asyncio
async def test_install_all_parallel_installation():
    """Test that pip and npm installations run in parallel"""
    from godman_ai.diagnostics import install_all

    with patch(
        "godman_ai.diagnostics.installer._check_command_available", new_callable=AsyncMock
    ) as mock_check:
        with patch(
            "godman_ai.diagnostics.installer._run_command", new_callable=AsyncMock
        ) as mock_cmd:
            mock_check.return_value = True
            mock_cmd.return_value = {
                "returncode": 0,
                "stdout": "Success",
                "stderr": "",
                "command": "test",
            }

            result = await install_all(pip_packages=["requests"], npm_packages=["typescript"])

            assert result["success"] is True
            assert "pip" in result
            assert "npm" in result


@pytest.mark.asyncio
async def test_run_llm_health_check_basic():
    """Test basic LLM health check"""
    from godman_ai.diagnostics import run_llm_health_check

    # Mock all service checks to avoid actual API calls
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
                "error": None,
            }
            mock_google.return_value = {
                "service": "google_ai",
                "available": True,
                "response_time_ms": 150,
                "error": None,
            }

            result = await run_llm_health_check()

            assert "overall_status" in result
            assert "services" in result
            assert "summary" in result
            assert result["summary"]["total_services"] > 0


@pytest.mark.asyncio
async def test_run_llm_health_check_all_unavailable():
    """Test health check when all services are unavailable"""
    from godman_ai.diagnostics import run_llm_health_check

    with patch(
        "godman_ai.diagnostics.llm_health._check_openai_health", new_callable=AsyncMock
    ) as mock_openai:
        with patch(
            "godman_ai.diagnostics.llm_health._check_google_ai_health", new_callable=AsyncMock
        ) as mock_google:
            mock_openai.return_value = {
                "service": "openai",
                "available": False,
                "error": "API key not set",
            }
            mock_google.return_value = {
                "service": "google_ai",
                "available": False,
                "error": "Not installed",
            }

            result = await run_llm_health_check()

            assert result["overall_status"] == "critical"
            assert result["summary"]["available_services"] == 0


@pytest.mark.asyncio
async def test_run_llm_health_check_degraded():
    """Test health check in degraded state"""
    from godman_ai.diagnostics import run_llm_health_check

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
                "available": False,
                "error": "Not installed",
            }

            result = await run_llm_health_check()

            assert result["overall_status"] == "degraded"
            assert result["summary"]["available_services"] > 0
            assert result["summary"]["unavailable_services"] > 0


@pytest.mark.asyncio
async def test_run_llm_health_check_with_external_commands():
    """Test health check with external commands"""
    from godman_ai.diagnostics import run_llm_health_check

    with patch(
        "godman_ai.diagnostics.llm_health._check_openai_health", new_callable=AsyncMock
    ) as mock_openai:
        with patch(
            "godman_ai.diagnostics.llm_health._check_google_ai_health", new_callable=AsyncMock
        ) as mock_google:
            with patch(
                "godman_ai.diagnostics.llm_health._run_external_health_check",
                new_callable=AsyncMock,
            ) as mock_external:
                mock_openai.return_value = {"service": "openai", "available": True}
                mock_google.return_value = {"service": "google_ai", "available": True}
                mock_external.return_value = {"success": True, "returncode": 0, "stdout": "OK"}

                result = await run_llm_health_check(external_commands=[["echo", "test"]])

                assert len(result["external_checks"]) > 0


def test_install_all_sync_wrapper():
    """Test that install_all can be called from sync code"""
    from godman_ai.diagnostics import install_all

    with patch("godman_ai.diagnostics.installer._run_command", new_callable=AsyncMock) as mock_cmd:
        mock_cmd.return_value = {
            "returncode": 0,
            "stdout": "Success",
            "stderr": "",
            "command": "test",
        }

        # This should work from sync code using asyncio.run()
        result = asyncio.run(install_all(pip_packages=["test"]))
        assert result is not None


def test_run_llm_health_check_sync_wrapper():
    """Test that run_llm_health_check can be called from sync code"""
    from godman_ai.diagnostics import run_llm_health_check

    with patch(
        "godman_ai.diagnostics.llm_health._check_openai_health", new_callable=AsyncMock
    ) as mock_openai:
        with patch(
            "godman_ai.diagnostics.llm_health._check_google_ai_health", new_callable=AsyncMock
        ) as mock_google:
            mock_openai.return_value = {"service": "openai", "available": True}
            mock_google.return_value = {"service": "google_ai", "available": True}

            # This should work from sync code using asyncio.run()
            result = asyncio.run(run_llm_health_check())
            assert result is not None
            assert "overall_status" in result
