"""
Auto-installer for required LLM models.

Automatically pulls and installs all required models for the Godman AI system,
then runs a comprehensive health check.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def install_all() -> Dict[str, Any]:
    """
    Auto-install all required LLM models and run health check.
    
    Returns:
        Health check result dictionary
    """
    console.print("\n[bold cyan]Godman AI — Auto Installer[/bold cyan]")
    console.print("-" * 50 + "\n")

    models = [
        "deepseek-r1:14b",
        "phi4:14b",
        "llama3.1:8b",
        "qwen2.5:7b",
    ]

    for model in models:
        console.print(f"[yellow]→ Checking {model}...[/yellow]")
        
        # Check if model exists
        check_result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if model not in check_result.stdout:
            console.print(f"[blue]  Pulling {model}...[/blue]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Downloading {model}...", total=None)
                
                pull_result = subprocess.run(
                    ["ollama", "pull", model],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if pull_result.returncode == 0:
                    console.print(f"[green]  ✓ {model} installed successfully[/green]")
                else:
                    console.print(f"[red]  ✗ Failed to install {model}[/red]")
                    console.print(f"[red]  Error: {pull_result.stderr}[/red]")
        else:
            console.print(f"[green]  ✓ {model} already installed[/green]")
        
        console.print()

    console.print("[green]Model installation complete.[/green]\n")
    console.print("[cyan]Running health check...[/cyan]\n")
    
    # Import and run health check
    from godman_ai.diagnostics.llm_health import run_llm_health_check
    result = run_llm_health_check()

    console.print()
    if result["all_systems_pass"]:
        console.print(Panel(
            "[bold green]✓ Installation OK — all systems ready[/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[bold red]✗ Installation completed but health check FAILED[/bold red]\n\n"
            f"Details:\n"
            f"  Ollama online: {result['ollama_online']}\n"
            f"  Models available: {sum(result['models_available'].values())}/4\n"
            f"  All systems pass: {result['all_systems_pass']}",
            border_style="red"
        ))

    return result


if __name__ == "__main__":
    result = install_all()
    sys.exit(0 if result["all_systems_pass"] else 1)
