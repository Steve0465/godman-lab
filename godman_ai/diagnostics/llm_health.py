"""
LLM health check diagnostics with asyncio subprocess support.

This module provides async functions to check the health and availability
of LLM services and APIs.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
import sys

logger = logging.getLogger(__name__)


async def _check_openai_health() -> Dict[str, Any]:
    """
    Check OpenAI API health.

    Returns:
        dict: Health check result with status and response time
    """
    try:
        from openai import OpenAI

        start_time = time.time()

        # Try to create a client and list models
        client = OpenAI()

        # This is a lightweight check - just list models
        # We run this in an executor to avoid blocking
        loop = asyncio.get_event_loop()
        models = await loop.run_in_executor(None, lambda: list(client.models.list()))

        elapsed = time.time() - start_time

        return {
            "service": "openai",
            "available": True,
            "response_time_ms": round(elapsed * 1000, 2),
            "models_count": len(models) if models else 0,
            "error": None,
        }
    except ImportError:
        return {
            "service": "openai",
            "available": False,
            "error": "openai package not installed",
            "response_time_ms": 0,
        }
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        return {"service": "openai", "available": False, "error": str(e), "response_time_ms": 0}


async def _check_google_ai_health() -> Dict[str, Any]:
    """
    Check Google Generative AI health.

    Returns:
        dict: Health check result with status and response time
    """
    try:
        import google.generativeai as genai

        start_time = time.time()

        # Try to list models
        loop = asyncio.get_event_loop()
        models = await loop.run_in_executor(None, lambda: list(genai.list_models()))

        elapsed = time.time() - start_time

        return {
            "service": "google_ai",
            "available": True,
            "response_time_ms": round(elapsed * 1000, 2),
            "models_count": len(models) if models else 0,
            "error": None,
        }
    except ImportError:
        return {
            "service": "google_ai",
            "available": False,
            "error": "google-generativeai package not installed",
            "response_time_ms": 0,
        }
    except Exception as e:
        logger.error(f"Google AI health check failed: {e}")
        return {"service": "google_ai", "available": False, "error": str(e), "response_time_ms": 0}


async def _check_anthropic_health() -> Dict[str, Any]:
    """
    Check Anthropic API health.

    Returns:
        dict: Health check result with status and response time
    """
    try:
        import anthropic

        start_time = time.time()

        # Create a client - this validates the API key if set
        anthropic.Anthropic()

        elapsed = time.time() - start_time

        return {
            "service": "anthropic",
            "available": True,
            "response_time_ms": round(elapsed * 1000, 2),
            "error": None,
        }
    except ImportError:
        return {
            "service": "anthropic",
            "available": False,
            "error": "anthropic package not installed",
            "response_time_ms": 0,
        }
    except Exception as e:
        logger.error(f"Anthropic health check failed: {e}")
        return {"service": "anthropic", "available": False, "error": str(e), "response_time_ms": 0}


async def _check_python_version() -> Dict[str, Any]:
    """
    Check Python version and environment.

    Returns:
        dict: Python version info
    """
    return {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": sys.platform,
    }


async def _run_external_health_check(command: List[str]) -> Dict[str, Any]:
    """
    Run an external health check command asynchronously.

    Args:
        command: Command to run as a list

    Returns:
        dict: Command execution result
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "success": False,
                "error": "Command timed out after 30s",
                "command": " ".join(command),
            }

        return {
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "command": " ".join(command),
        }
    except Exception as e:
        logger.error(f"Error running external health check {' '.join(command)}: {e}")
        return {"success": False, "error": str(e), "command": " ".join(command)}


async def run_llm_health_check(
    check_openai: bool = True,
    check_google: bool = True,
    check_anthropic: bool = False,
    external_commands: Optional[List[List[str]]] = None,
) -> Dict[str, Any]:
    """
    Run comprehensive LLM health checks asynchronously.

    This is the main async function for checking LLM service health.
    It checks multiple services in parallel for efficiency.

    Args:
        check_openai: Whether to check OpenAI API
        check_google: Whether to check Google Generative AI
        check_anthropic: Whether to check Anthropic API
        external_commands: Optional list of external commands to run

    Returns:
        dict: Health check results with status for each service

    Example:
        >>> import asyncio
        >>> result = asyncio.run(run_llm_health_check())
        >>> print(result['overall_status'])
    """
    start_time = time.time()

    results = {
        "timestamp": start_time,
        "overall_status": "healthy",
        "services": {},
        "python_info": {},
        "external_checks": [],
        "summary": {"total_services": 0, "available_services": 0, "unavailable_services": 0},
    }

    # Collect async tasks
    tasks = []
    service_names = []

    # Add Python version check
    tasks.append(_check_python_version())
    service_names.append("python_info")

    # Add LLM service checks
    if check_openai:
        tasks.append(_check_openai_health())
        service_names.append("openai")

    if check_google:
        tasks.append(_check_google_ai_health())
        service_names.append("google_ai")

    if check_anthropic:
        tasks.append(_check_anthropic_health())
        service_names.append("anthropic")

    # Add external command checks
    if external_commands:
        for cmd in external_commands:
            tasks.append(_run_external_health_check(cmd))
            service_names.append(f"external_{' '.join(cmd)}")

    # Run all checks in parallel
    task_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    for service_name, task_result in zip(service_names, task_results):
        if isinstance(task_result, Exception):
            logger.error(f"Health check failed for {service_name}: {task_result}")
            if service_name == "python_info":
                results["python_info"] = {"error": str(task_result)}
            elif service_name.startswith("external_"):
                results["external_checks"].append({"success": False, "error": str(task_result)})
            else:
                results["services"][service_name] = {"available": False, "error": str(task_result)}
        else:
            if service_name == "python_info":
                results["python_info"] = task_result
            elif service_name.startswith("external_"):
                results["external_checks"].append(task_result)
            else:
                results["services"][service_name] = task_result

    # Calculate summary
    services = results["services"]
    results["summary"]["total_services"] = len(services)
    results["summary"]["available_services"] = sum(
        1 for s in services.values() if s.get("available", False)
    )
    results["summary"]["unavailable_services"] = (
        results["summary"]["total_services"] - results["summary"]["available_services"]
    )

    # Determine overall status
    if results["summary"]["available_services"] == 0 and results["summary"]["total_services"] > 0:
        results["overall_status"] = "critical"
    elif results["summary"]["unavailable_services"] > 0:
        results["overall_status"] = "degraded"
    else:
        results["overall_status"] = "healthy"

    # Add execution time
    results["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)

    return results
