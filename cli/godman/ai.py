"""
CLI commands for local AI model interaction

Provides Typer commands to interact with local Ollama models.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

ai_app = typer.Typer(help="Interact with local AI models via Ollama")
console = Console()

# Import router from godman-raw
sys.path.insert(0, str(Path.home() / "godman-raw" / "llm"))
try:
    from router.model_router import route, choose_model
    ROUTER_AVAILABLE = True
except ImportError:
    ROUTER_AVAILABLE = False


def _check_ollama_installed() -> bool:
    """Check if ollama is installed and available."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_ollama(prompt: str, system_prompt: Optional[str] = None) -> tuple[bool, str]:
    """
    Run the local Ollama model with the given prompt.
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    if not _check_ollama_installed():
        return False, "Error: ollama is not installed or not in PATH.\nPlease install from: https://ollama.ai"
    
    try:
        # Combine system prompt with user prompt if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        result = subprocess.run(
            ["ollama", "run", "godman-raw"],
            input=full_prompt,
            text=True,
            capture_output=True,
            timeout=120
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error occurred"
            return False, f"Error: {error_msg}"
        
        return True, result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        return False, "Error: Request timed out after 120 seconds"
    except Exception as e:
        return False, f"Error: {str(e)}"


@ai_app.command("local")
def local_prompt(
    prompt: str = typer.Argument(..., help="Prompt to send to the local model")
):
    """
    Run a prompt against the local Ollama model.
    
    Examples:
    
      # Simple prompt
      godman ai local "What is Python?"
    
      # Multi-word prompt
      godman ai local "Explain how decorators work in Python"
    """
    success, output = _run_ollama(prompt)
    
    if success:
        console.print(output)
        sys.exit(0)
    else:
        console.print(f"[red]{output}[/red]")
        sys.exit(1)


@ai_app.command("local-file")
def local_file(
    path: str = typer.Argument(..., help="Path to file to analyze")
):
    """
    Send a file's content to the local Ollama model for analysis.
    
    Examples:
    
      # Analyze a Python file
      godman ai local-file main.py
    
      # Analyze any text file
      godman ai local-file README.md
    """
    file_path = Path(path)
    
    # Check if file exists
    if not file_path.exists():
        console.print(f"[red]Error: File not found: {path}[/red]")
        sys.exit(1)
    
    if not file_path.is_file():
        console.print(f"[red]Error: Path is not a file: {path}[/red]")
        sys.exit(1)
    
    # Read file content
    try:
        content = file_path.read_text()
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        sys.exit(1)
    
    # Prepare prompt with system message
    system_prompt = "You are the local Godman raw model. Analyze the user's file."
    file_prompt = f"File: {file_path.name}\n\n{content}"
    
    success, output = _run_ollama(file_prompt, system_prompt=system_prompt)
    
    if success:
        console.print(output)
        sys.exit(0)
    else:
        console.print(f"[red]{output}[/red]")
        sys.exit(1)


@ai_app.command("shell")
def shell():
    """
    Start an interactive shell session with the local Ollama model.
    
    Examples:
    
      # Start interactive shell
      godman ai shell
    """
    if not _check_ollama_installed():
        console.print("[red]Error: ollama is not installed or not in PATH.[/red]")
        console.print("[red]Please install from: https://ollama.ai[/red]")
        sys.exit(1)
    
    console.print("[bold cyan]Godman AI Shell[/bold cyan]")
    console.print("[dim]Using model: godman-raw[/dim]")
    console.print("[dim]Type 'exit' or 'quit' to end session[/dim]\n")
    
    while True:
        try:
            prompt = console.input("[bold green]> [/bold green]")
            
            if prompt.strip().lower() in ["exit", "quit", "q"]:
                console.print("[dim]Goodbye![/dim]")
                break
            
            if not prompt.strip():
                continue
            
            success, output = _run_ollama(prompt)
            
            if success:
                console.print(f"\n{output}\n")
            else:
                console.print(f"[red]{output}[/red]\n")
                
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]\n")


def print_result(result: dict) -> None:
    """Pretty-print the router result."""
    if result.get("success"):
        console.print()
        console.print(f"[bold cyan]Model:[/bold cyan] {result.get('model', 'unknown')}")
        
        if result.get("category"):
            console.print(f"[bold cyan]Category:[/bold cyan] {result.get('category')}")
        
        console.print(f"[bold cyan]Duration:[/bold cyan] {result.get('duration', 0):.3f}s")
        
        if result.get("tokens_per_second"):
            console.print(f"[bold cyan]Speed:[/bold cyan] {result.get('tokens_per_second')} tok/s")
        
        if result.get("fallback_used"):
            console.print(f"[yellow]⚠️  Fallback used (original: {result.get('original_model')})[/yellow]")
        
        console.print()
        console.print(Panel(result.get("response", ""), title="Response", border_style="green"))
    else:
        console.print()
        console.print(f"[red]❌ Error: {result.get('error', 'Unknown error')}[/red]")
        if result.get("error_details"):
            console.print(f"[red]Details: {result.get('error_details')}[/red]")


@ai_app.command("route")
def ai_route(
    prompt: str = typer.Argument(..., help="Prompt to send to the AI router"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Force a specific model (bypasses routing logic)"),
    raw: bool = typer.Option(False, "--raw", help="Print raw JSON output instead of formatted"),
):
    """
    Route prompt to optimal local LLM using intelligent routing.
    
    Uses the production-grade router to select the best model based on
    prompt analysis (reasoning, math, conversational, or writing tasks).
    
    Examples:
    
      # Auto-route based on content
      godman ai route "Explain the architecture of neural networks"
      
      # Force a specific model
      godman ai route "Hello!" --model llama3.1:8b
      
      # Get raw JSON output
      godman ai route "Calculate 5 + 3" --raw
    """
    if not ROUTER_AVAILABLE:
        console.print("[red]Error: Router module not available.[/red]")
        console.print("[red]Make sure ~/godman-raw/llm/router/model_router.py exists.[/red]")
        sys.exit(1)
    
    try:
        if model:
            # Monkey-patch choose_model to return forced model
            import router.model_router as router_module
            original_choose = router_module.choose_model
            router_module.choose_model = lambda p: model
            
            result = route(prompt)
            
            # Restore original
            router_module.choose_model = original_choose
        else:
            result = route(prompt)
        
        if raw:
            console.print_json(json.dumps(result, indent=2))
        else:
            print_result(result)
        
        sys.exit(0 if result.get("success") else 1)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    ai_app()
