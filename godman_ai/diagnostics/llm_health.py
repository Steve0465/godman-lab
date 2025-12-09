"""
LLM Health Check Diagnostics

Provides comprehensive health check for the local Ollama LLM infrastructure.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from rich.console import Console
from rich.table import Table

console = Console()

OLLAMA_HOST = "http://127.0.0.1:11434"
REQUIRED_MODELS = [
    "deepseek-r1:14b",
    "phi4:14b",
    "llama3.1:8b",
    "qwen2.5:7b"
]


def _safe_request(method: str, path: str, payload: Optional[Dict] = None, timeout: int = 10) -> Optional[Dict]:
    """Make HTTP request with error handling."""
    try:
        data = None if payload is None else json.dumps(payload).encode()
        req = Request(OLLAMA_HOST + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read())
    except Exception:
        return None


def _kill_ollama_processes() -> bool:
    """Kill all existing ollama processes safely."""
    try:
        # Find ollama processes
        result = subprocess.run(
            ["pgrep", "-f", "ollama"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except (ProcessLookupError, ValueError):
                    pass
            
            # Wait for processes to terminate
            time.sleep(2)
            return True
        
        return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not kill ollama processes: {e}[/yellow]")
        return False


def _start_ollama_serve() -> bool:
    """Start ollama serve as background process."""
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait for server to be ready (max 30 seconds)
        for _ in range(30):
            time.sleep(1)
            result = _safe_request("GET", "/api/tags", timeout=2)
            if result is not None:
                return True
        
        return False
    except Exception as e:
        console.print(f"[red]Failed to start ollama: {e}[/red]")
        return False


def _check_models_installed() -> Dict[str, bool]:
    """Check which required models are installed."""
    result = _safe_request("GET", "/api/tags")
    if not result:
        return {model: False for model in REQUIRED_MODELS}
    
    installed_models = [m.get("name") for m in result.get("models", [])]
    return {model: model in installed_models for model in REQUIRED_MODELS}


def _test_model_speed(model: str) -> Optional[float]:
    """Test model generation speed with a tiny prompt."""
    payload = {
        "model": model,
        "prompt": "Say OK.",
        "stream": False,
        "options": {
            "num_predict": 5,
            "temperature": 0.0
        }
    }
    
    result = _safe_request("POST", "/api/generate", payload, timeout=30)
    
    if result and "eval_count" in result and "eval_duration" in result:
        eval_count = result.get("eval_count", 0)
        eval_duration_ns = result.get("eval_duration", 1)
        tokens_per_sec = eval_count / (eval_duration_ns / 1e9) if eval_duration_ns > 0 else 0
        return round(tokens_per_sec, 2)
    
    return None


def _test_router() -> Optional[str]:
    """Test the tool router."""
    try:
        sys.path.insert(0, str(Path.home() / "godman-raw" / "llm"))
        from router.model_router import route
        
        result = route("health check routing test")
        
        if isinstance(result, dict) and "model" in result:
            return result["model"]
        return None
    except Exception:
        return None


def run_llm_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for Ollama LLM infrastructure.
    
    Returns:
        Dictionary with health check results including:
        - ollama_online: bool
        - models_available: dict of model availability
        - model_speeds: dict of tokens/sec for each model
        - router_selected: str or None
        - all_systems_pass: bool
    """
    console.print("[bold cyan]Starting LLM Health Check...[/bold cyan]\n")
    
    health_status = {
        "ollama_online": False,
        "models_available": {},
        "model_speeds": {},
        "router_selected": None,
        "all_systems_pass": False
    }
    
    try:
        # Step 1: Kill existing ollama processes
        console.print("→ Stopping existing Ollama processes...")
        _kill_ollama_processes()
        console.print("[green]✓[/green] Stopped\n")
        
        # Step 2: Start ollama serve
        console.print("→ Starting Ollama server...")
        if not _start_ollama_serve():
            console.print("[red]✗ Failed to start Ollama server[/red]")
            return health_status
        
        health_status["ollama_online"] = True
        console.print(f"[green]✓[/green] Server online at {OLLAMA_HOST}\n")
        
        # Step 3: Check installed models
        console.print("→ Checking installed models...")
        models_available = _check_models_installed()
        health_status["models_available"] = models_available
        
        installed_count = sum(models_available.values())
        console.print(f"[green]✓[/green] {installed_count}/{len(REQUIRED_MODELS)} models installed\n")
        
        # Step 4: Test model speeds
        console.print("→ Testing model performance...")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Model", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Speed (tok/s)", justify="right")
        
        for model in REQUIRED_MODELS:
            if models_available.get(model):
                speed = _test_model_speed(model)
                health_status["model_speeds"][model] = speed
                
                if speed:
                    table.add_row(model, "[green]✓[/green]", f"[green]{speed}[/green]")
                else:
                    table.add_row(model, "[red]✗[/red]", "[red]Failed[/red]")
            else:
                health_status["model_speeds"][model] = None
                table.add_row(model, "[yellow]⊘[/yellow]", "[dim]Not installed[/dim]")
        
        console.print(table)
        console.print()
        
        # Step 5: Test router
        console.print("→ Testing tool router...")
        router_result = _test_router()
        health_status["router_selected"] = router_result
        
        if router_result:
            console.print(f"[green]✓[/green] Router returned: [cyan]{router_result}[/cyan]\n")
        else:
            console.print("[red]✗[/red] Router test failed\n")
        
        # Final assessment
        all_models_work = all(
            health_status["model_speeds"].get(model) is not None 
            for model in REQUIRED_MODELS 
            if models_available.get(model)
        )
        
        health_status["all_systems_pass"] = (
            health_status["ollama_online"] and
            installed_count >= 3 and
            all_models_work
        )
        
        if health_status["all_systems_pass"]:
            console.print("[bold green]✓ All systems operational[/bold green]")
        else:
            console.print("[bold yellow]⚠ Some systems failed[/bold yellow]")
        
        return health_status
        
    except Exception as e:
        console.print(f"[bold red]✗ Health check failed: {e}[/bold red]")
        health_status["error"] = str(e)
        return health_status


if __name__ == "__main__":
    result = run_llm_health_check()
    console.print(f"\n[dim]Result: {json.dumps(result, indent=2)}[/dim]")
