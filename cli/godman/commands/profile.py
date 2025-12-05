"""
Profile management commands for building personalized AI.
"""

import typer
from pathlib import Path
from rich import print
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()


@app.command()
def analyze(
    full: bool = typer.Option(False, "--full", help="Run full system analysis"),
    filesystem: bool = typer.Option(False, "--filesystem", help="Analyze filesystem only"),
    documents: bool = typer.Option(False, "--documents", help="Analyze documents only"),
):
    """
    Analyze your system to build a personal AI profile.
    This learns about YOU so the AI can be more helpful.
    """
    from godman_ai.profiler import PersonalDataCollector
    
    collector = PersonalDataCollector()
    
    console.print("[bold cyan]🧠 Analyzing your system to build personal AI profile...[/bold cyan]")
    console.print()
    
    if full or filesystem:
        console.print("[yellow]📁 Analyzing filesystem...[/yellow]")
        fs_analysis = collector.analyze_filesystem()
        collector.profile["filesystem_analysis"] = fs_analysis
        console.print(f"  ✓ Found {len(fs_analysis['projects'])} projects")
        console.print(f"  ✓ Identified {len(fs_analysis['file_types'])} file types")
        console.print()
    
    if full or documents:
        console.print("[yellow]📄 Analyzing documents...[/yellow]")
        doc_analysis = collector.analyze_documents()
        collector.profile["document_analysis"] = doc_analysis
        console.print(f"  ✓ Found {len(doc_analysis['business_docs'])} business documents")
        console.print(f"  ✓ Found {len(doc_analysis['personal_docs'])} personal documents")
        console.print()
    
    collector.save_profile()
    
    # Show report
    console.print(collector.full_analysis_report())


@app.command()
def questions():
    """
    Get questions the AI needs answered to know you better.
    """
    from godman_ai.profiler import PersonalDataCollector
    
    collector = PersonalDataCollector()
    questions = collector.generate_questions()
    
    console.print("[bold cyan]❓ Answer these to help me understand you better:[/bold cyan]")
    console.print()
    
    for i, q in enumerate(questions, 1):
        console.print(f"[yellow]{i}.[/yellow] {q}")
    
    console.print()
    console.print("[dim]Answer with: godman profile answer[/dim]")


@app.command()
def answer():
    """
    Interactive Q&A to update your profile.
    """
    from godman_ai.profiler import PersonalDataCollector
    
    collector = PersonalDataCollector()
    questions = collector.generate_questions()
    
    console.print("[bold cyan]🤝 Let's get to know each other![/bold cyan]")
    console.print("[dim]Press Enter to skip any question[/dim]")
    console.print()
    
    answers = {}
    for i, question in enumerate(questions, 1):
        response = typer.prompt(f"\n{i}. {question}", default="")
        if response.strip():
            answers[f"q{i}"] = response
    
    if answers:
        collector.update_from_answers(answers)
        console.print()
        console.print("[bold green]✓ Profile updated![/bold green]")
    else:
        console.print()
        console.print("[yellow]No answers provided.[/yellow]")


@app.command()
def show():
    """
    Display your current AI profile.
    """
    from godman_ai.profiler import PersonalDataCollector
    import json
    
    collector = PersonalDataCollector()
    
    console.print("[bold cyan]📋 Your Personal AI Profile:[/bold cyan]")
    console.print()
    console.print(json.dumps(collector.profile, indent=2))


@app.command()
def export(output: Path = typer.Argument(..., help="Output file path")):
    """
    Export your profile for training a custom model.
    """
    from godman_ai.profiler import PersonalDataCollector
    import json
    
    collector = PersonalDataCollector()
    
    with open(output, 'w') as f:
        json.dump(collector.profile, f, indent=2)
    
    console.print(f"[bold green]✓ Profile exported to {output}[/bold green]")
    console.print("[dim]Use this file to fine-tune a local model[/dim]")


@app.command()
def reset():
    """
    Reset your profile (start over).
    """
    from godman_ai.profiler import PersonalDataCollector
    
    confirm = typer.confirm("Are you sure you want to reset your profile?")
    if not confirm:
        console.print("[yellow]Cancelled.[/yellow]")
        return
    
    collector = PersonalDataCollector()
    collector.profile_path.unlink(missing_ok=True)
    
    console.print("[bold green]✓ Profile reset![/bold green]")
