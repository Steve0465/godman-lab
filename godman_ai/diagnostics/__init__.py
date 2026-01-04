"""
Diagnostics module for GodmanAI.

Provides async diagnostic tools for system health checks and dependency installation.
"""

from godman_ai.diagnostics.installer import install_all
from godman_ai.diagnostics.llm_health import run_llm_health_check

__all__ = ["install_all", "run_llm_health_check"]
