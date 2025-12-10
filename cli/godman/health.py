"""
Health check CLI commands for LLM diagnostics.
"""

import sys
import typer
from rich.console import Console

from godman_ai.diagnostics.llm_health import run_llm_health_check

app = typer.Typer(help="LLM health check and diagnostics")
console = Console()


@app.command("check")
def health_check():
    """
    Run comprehensive LLM infrastructure health check.
    
    Checks:
    - Ollama server status
    - Model availability
    - Model performance
    - Router functionality
    """
    result = run_llm_health_check()
    
    sys.exit(0 if result.get("all_systems_pass") else 1)


@app.command("monitor")
def monitor(
    every: int = typer.Option(5, help="Minutes between checks"),
    install_cron: bool = typer.Option(False, "--install", help="Install as cron job")
):
    """
    Install cron job to run LLM health monitor periodically.
    
    Examples:
    
      # Check every 5 minutes (default)
      godman health monitor
      
      # Check every 3 minutes
      godman health monitor --every 3
      
      # Install as cron job
      godman health monitor --every 5 --install
    """
    import getpass
    import subprocess
    from pathlib import Path
    
    user = getpass.getuser()
    monitor_script = Path(__file__).parent.parent / "diagnostics" / "monitor.py"
    cron_line = f"*/{every} * * * * {sys.executable} {monitor_script}"
    
    if install_cron:
        # Get existing crontab
        p = subprocess.Popen(
            ["crontab", "-l"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        existing, _ = p.communicate()
        existing = existing or ""
        
        # Check if already installed
        if cron_line in existing:
            console.print(f"[yellow]Cron job already installed[/yellow]")
            return
        
        # Add new cron line
        new_crontab = existing.strip() + "\n" + cron_line + "\n"
        
        # Install new crontab
        subprocess.run(
            ["crontab", "-"],
            input=new_crontab,
            text=True,
            check=True
        )
        
        console.print(f"[green]✓ Cron monitor installed (every {every} minutes)[/green]")
        console.print(f"[dim]Command: {cron_line}[/dim]")
    else:
        console.print(f"[cyan]Would install cron job:[/cyan]")
        console.print(f"[dim]{cron_line}[/dim]")
        console.print(f"\n[yellow]Add --install flag to actually install[/yellow]")


if __name__ == "__main__":
    app()
