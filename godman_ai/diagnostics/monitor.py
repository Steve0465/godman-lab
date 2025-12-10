"""
Cron-safe LLM health monitor.

Periodically runs health checks and logs results. Can be run as a cron job
or standalone monitoring daemon.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


LOG = Path.home() / "godman-raw" / "monitor" / "llm_health.log"
LOG.parent.mkdir(parents=True, exist_ok=True)


def write_log(msg: str) -> None:
    """Append message to log file."""
    existing = LOG.read_text() if LOG.exists() else ""
    LOG.write_text(existing + msg + "\n")


def monitor_loop() -> dict:
    """
    Run a single health check iteration and log results.
    
    Returns:
        Health check result dictionary
    """
    # Suppress console output for cron mode
    import os
    os.environ['RICH_NO_COLOR'] = '1'
    
    from godman_ai.diagnostics.llm_health import run_llm_health_check
    
    result = run_llm_health_check()
    timestamp = datetime.now().isoformat()
    
    # Log result
    log_entry = f"{timestamp} | {json.dumps(result)}"
    write_log(log_entry)
    
    # Send notification on failure (macOS)
    if not result["all_systems_pass"]:
        try:
            subprocess.run(
                [
                    "osascript", "-e",
                    'display notification "LLM Health FAIL" with title "GodmanAI"'
                ],
                capture_output=True,
                timeout=5
            )
        except Exception:
            pass
    
    return result


if __name__ == "__main__":
    result = monitor_loop()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["all_systems_pass"] else 1)
