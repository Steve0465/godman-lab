"""
Dependency installer with asyncio subprocess support.

This module provides async functions to install system dependencies
using package managers like pip, npm, etc.
"""

import asyncio
import logging
import sys
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


async def _run_command(cmd: List[str], timeout: Optional[int] = 300) -> Dict[str, Any]:
    """
    Run a command asynchronously using asyncio subprocess.

    Args:
        cmd: Command and arguments as list
        timeout: Command timeout in seconds (default: 300)

    Returns:
        dict: Result with returncode, stdout, stderr
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Command timed out after {timeout}s: {' '.join(cmd)}")

        return {
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "command": " ".join(cmd),
        }
    except Exception as e:
        logger.error(f"Error running command {' '.join(cmd)}: {e}")
        raise


async def _install_pip_packages(packages: List[str]) -> Dict[str, Any]:
    """
    Install Python packages using pip.

    Args:
        packages: List of package names to install

    Returns:
        dict: Installation result
    """
    if not packages:
        return {"success": True, "message": "No packages to install", "installed": []}

    logger.info(f"Installing pip packages: {', '.join(packages)}")

    cmd = [sys.executable, "-m", "pip", "install"] + packages
    result = await _run_command(cmd)

    success = result["returncode"] == 0

    return {
        "success": success,
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "installed": packages if success else [],
        "failed": [] if success else packages,
    }


async def _install_npm_packages(
    packages: List[str], global_install: bool = False
) -> Dict[str, Any]:
    """
    Install Node.js packages using npm.

    Args:
        packages: List of package names to install
        global_install: Whether to install globally

    Returns:
        dict: Installation result
    """
    if not packages:
        return {"success": True, "message": "No packages to install", "installed": []}

    logger.info(f"Installing npm packages: {', '.join(packages)}")

    cmd = ["npm", "install"]
    if global_install:
        cmd.append("-g")
    cmd.extend(packages)

    result = await _run_command(cmd)

    success = result["returncode"] == 0

    return {
        "success": success,
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "installed": packages if success else [],
        "failed": [] if success else packages,
    }


async def _check_command_available(command: str) -> bool:
    """
    Check if a command is available in PATH.

    Args:
        command: Command name to check

    Returns:
        bool: True if command is available
    """
    try:
        if sys.platform == "win32":
            cmd = ["where", command]
        else:
            cmd = ["which", command]

        result = await _run_command(cmd, timeout=10)
        return result["returncode"] == 0
    except Exception as e:
        logger.debug(f"Error checking command {command}: {e}")
        return False


async def install_all(
    pip_packages: Optional[List[str]] = None,
    npm_packages: Optional[List[str]] = None,
    npm_global: bool = False,
) -> Dict[str, Any]:
    """
    Install all specified dependencies asynchronously.

    This is the main async function for installing dependencies.
    It can install pip and npm packages in parallel.

    Args:
        pip_packages: List of Python packages to install via pip
        npm_packages: List of Node.js packages to install via npm
        npm_global: Whether to install npm packages globally

    Returns:
        dict: Installation results with success status and details

    Example:
        >>> import asyncio
        >>> result = asyncio.run(install_all(
        ...     pip_packages=['requests', 'beautifulsoup4'],
        ...     npm_packages=['typescript']
        ... ))
    """
    results = {"success": True, "pip": {}, "npm": {}, "errors": []}

    tasks = []

    # Prepare pip installation task
    if pip_packages:
        tasks.append(("pip", _install_pip_packages(pip_packages)))

    # Prepare npm installation task
    if npm_packages:
        # First check if npm is available
        npm_available = await _check_command_available("npm")
        if npm_available:
            tasks.append(("npm", _install_npm_packages(npm_packages, npm_global)))
        else:
            logger.warning("npm not found, skipping npm package installation")
            results["npm"] = {"success": False, "error": "npm command not found"}
            results["errors"].append("npm not available")
            results["success"] = False

    # Run installations in parallel
    if tasks:
        task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

        for (name, _), task_result in zip(tasks, task_results):
            if isinstance(task_result, Exception):
                logger.error(f"Error during {name} installation: {task_result}")
                results[name] = {"success": False, "error": str(task_result)}
                results["errors"].append(f"{name}: {task_result}")
                results["success"] = False
            else:
                results[name] = task_result
                if not task_result.get("success", False):
                    results["success"] = False

    return results
