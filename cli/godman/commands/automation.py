"""
Automation commands for GodmanAI
"""
import typer
from rich.console import Console

app = typer.Typer(help="Automation and monitoring commands")
console = Console()


@app.command()
def watch(
    directory: str = typer.Argument("scans", help="Directory to watch"),
    action: str = typer.Option("process_receipt", help="Action to trigger on new files")
):
    """Start file system watcher"""
    from godman_ai.orchestrator import Orchestrator
    
    console.print(f"[yellow]👀 Watching {directory} for new files...[/yellow]")
    
    orchestrator = Orchestrator()
    orchestrator.load_tools_from_package("godman_ai.tools")
    
    result = orchestrator.run_task({
        "tool": "filesystem_watcher",
        "watch_dir": directory,
        "patterns": {"*.pdf": action, "*.jpg": action, "*.png": action}
    })
    
    console.print(result)


@app.command()
def email():
    """Monitor email for invoices and bills"""
    from godman_ai.orchestrator import Orchestrator
    
    console.print("[yellow]📧 Checking email for new messages...[/yellow]")
    
    orchestrator = Orchestrator()
    orchestrator.load_tools_from_package("godman_ai.tools")
    
    result = orchestrator.run_task({"tool": "email_monitor"})
    console.print(result)


@app.command()
def listen(duration: int = 5):
    """Listen for voice commands"""
    from godman_ai.orchestrator import Orchestrator
    
    console.print(f"[yellow]🎤 Listening for {duration} seconds...[/yellow]")
    
    orchestrator = Orchestrator()
    orchestrator.load_tools_from_package("godman_ai.tools")
    
    result = orchestrator.run_task({
        "tool": "voice",
        "action": "listen",
        "duration": duration
    })
    
    if result.get("text"):
        console.print(f"[green]Heard: {result['text']}[/green]")
    else:
        console.print(f"[red]Error: {result.get('error')}[/red]")


@app.command()
def speak(text: str):
    """Speak text aloud"""
    from godman_ai.orchestrator import Orchestrator
    
    orchestrator = Orchestrator()
    orchestrator.load_tools_from_package("godman_ai.tools")
    
    result = orchestrator.run_task({
        "tool": "voice",
        "action": "speak",
        "text": text
    })
    
    console.print(result)
