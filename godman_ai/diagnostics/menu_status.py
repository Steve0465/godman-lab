"""
macOS menu bar status notifier.

Runs in background and displays LLM health status notifications.
Can be used as a menu bar app or background daemon.
"""

import json
import subprocess
import sys
from pathlib import Path
from time import sleep


def menubar_loop() -> None:
    """
    Continuous monitoring loop for menu bar notifications.
    
    Runs health checks every 5 minutes and displays macOS notifications.
    """
    from godman_ai.diagnostics.llm_health import run_llm_health_check
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            print(f"[Iteration {iteration}] Running health check...")
            
            result = run_llm_health_check()
            status = "OK" if result["all_systems_pass"] else "FAIL"
            
            # Build notification message
            models_up = sum(result.get("models_available", {}).values())
            message = f"{status} | Models: {models_up}/4"
            
            # Send macOS notification
            subprocess.run(
                [
                    "osascript", "-e",
                    f'display notification "{message}" with title "LLM Status"'
                ],
                capture_output=True,
                timeout=5
            )
            
            print(f"Status: {status} | Models: {models_up}/4")
            
            # Log to file
            log_dir = Path.home() / "godman-raw" / "monitor"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "menu_status.json"
            
            with open(log_file, "w") as f:
                json.dump(result, f, indent=2)
            
            print(f"Sleeping 5 minutes...\n")
            sleep(300)  # 5 minutes
            
        except KeyboardInterrupt:
            print("\n\nStopping menu bar monitor...")
            break
        except Exception as e:
            print(f"Error: {e}")
            sleep(60)  # Wait 1 minute on error


if __name__ == "__main__":
    print("Starting LLM Menu Bar Monitor...")
    print("Press Ctrl+C to stop\n")
    menubar_loop()
