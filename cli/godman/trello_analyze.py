"""
Trello Board Analysis CLI

Provides commands to analyze exported Trello board data:
- List cards by list name
- Filter safety cover jobs
- Filter measure jobs
- Filter liner installation jobs
"""

from pathlib import Path
from typing import Optional
import json
import typer
from rich.console import Console
from rich.table import Table

from libs.trello_normalizer import normalize_trello_export
from libs.trello.attachment_extractor import extract_safety_cover_attachments

app = typer.Typer(help="Analyze exported Trello board data")
console = Console()


def load_and_normalize(export_file: Path) -> dict:
    """Load and normalize a Trello export JSON file."""
    if not export_file.exists():
        console.print(f"[red]Error: File not found: {export_file}[/red]")
        raise typer.Exit(1)
    
    with open(export_file) as f:
        data = json.load(f)
    
    return normalize_trello_export(data)


def print_cards_table(cards: list, title: str):
    """Print a formatted table of cards."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Card Name", style="cyan", no_wrap=False)
    table.add_column("URL", style="blue")
    table.add_column("Attachments", justify="right", style="green")
    table.add_column("Comments", justify="right", style="yellow")
    
    for card in cards:
        table.add_row(
            card["name"],
            card.get("shortUrl", "N/A"),
            str(card.get("attachment_count", 0)),
            str(card.get("comment_count", 0))
        )
    
    console.print(table)
    console.print(f"\n[bold]Total cards: {len(cards)}[/bold]\n")


@app.command()
def list_by_list_name(
    export_file: Path = typer.Argument(..., help="Path to exported Trello JSON file"),
    list_name: str = typer.Option(..., "--list", "-l", help="List name to filter by"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", help="Use case-sensitive matching")
):
    """
    List all cards from a specific list by name.
    
    Example:
        godman trello-analyze list-by-list-name exports/board.json --list "Completed"
    """
    normalized = load_and_normalize(export_file)
    
    # Find matching list
    if case_sensitive:
        cards = normalized["cards_by_list_name"].get(list_name, [])
    else:
        # Case-insensitive search
        list_name_lower = list_name.lower()
        cards = []
        for ln, card_list in normalized["cards_by_list_name"].items():
            if ln.lower() == list_name_lower:
                cards = card_list
                break
    
    if not cards:
        console.print(f"[yellow]No cards found in list: {list_name}[/yellow]")
        return
    
    print_cards_table(cards, f"Cards in List: {list_name}")


@app.command()
def safety_covers(
    export_file: Path = typer.Argument(..., help="Path to exported Trello JSON file")
):
    """
    List all safety cover jobs (list name contains 'SAFETY COVER').
    
    Example:
        godman trello-analyze safety-covers exports/board.json
    """
    normalized = load_and_normalize(export_file)
    
    # Find lists containing "SAFETY COVER"
    safety_cover_cards = []
    for list_name, cards in normalized["cards_by_list_name"].items():
        if "safety cover" in list_name.lower():
            safety_cover_cards.extend(cards)
    
    if not safety_cover_cards:
        console.print("[yellow]No safety cover jobs found[/yellow]")
        return
    
    print_cards_table(safety_cover_cards, "Safety Cover Jobs")


@app.command()
def measures(
    export_file: Path = typer.Argument(..., help="Path to exported Trello JSON file")
):
    """
    List all measure jobs (list name contains 'MEASURE').
    
    Example:
        godman trello-analyze measures exports/board.json
    """
    normalized = load_and_normalize(export_file)
    
    # Find lists containing "MEASURE"
    measure_cards = []
    for list_name, cards in normalized["cards_by_list_name"].items():
        if "measure" in list_name.lower():
            measure_cards.extend(cards)
    
    if not measure_cards:
        console.print("[yellow]No measure jobs found[/yellow]")
        return
    
    print_cards_table(measure_cards, "Measure Jobs")


@app.command()
def liner_installs(
    export_file: Path = typer.Argument(..., help="Path to exported Trello JSON file")
):
    """
    List all liner installation jobs (list name contains 'LINER').
    
    Example:
        godman trello-analyze liner-installs exports/board.json
    """
    normalized = load_and_normalize(export_file)
    
    # Find lists containing "LINER"
    liner_cards = []
    for list_name, cards in normalized["cards_by_list_name"].items():
        if "liner" in list_name.lower():
            liner_cards.extend(cards)
    
    if not liner_cards:
        console.print("[yellow]No liner installation jobs found[/yellow]")
        return
    
    print_cards_table(liner_cards, "Liner Installation Jobs")


@app.command()
def summary(
    export_file: Path = typer.Argument(..., help="Path to exported Trello JSON file")
):
    """
    Show a summary of all lists and card counts.
    
    Example:
        godman trello-analyze summary exports/board.json
    """
    normalized = load_and_normalize(export_file)
    
    table = Table(title="Board Summary", show_header=True, header_style="bold magenta")
    table.add_column("List Name", style="cyan", no_wrap=False)
    table.add_column("Card Count", justify="right", style="green")
    table.add_column("Total Attachments", justify="right", style="yellow")
    table.add_column("Total Comments", justify="right", style="blue")
    
    total_cards = 0
    total_attachments = 0
    total_comments = 0
    
    for list_name, cards in sorted(normalized["cards_by_list_name"].items()):
        card_count = len(cards)
        attachments = sum(card.get("attachment_count", 0) for card in cards)
        comments = sum(card.get("comment_count", 0) for card in cards)
        
        table.add_row(
            list_name,
            str(card_count),
            str(attachments),
            str(comments)
        )
        
        total_cards += card_count
        total_attachments += attachments
        total_comments += comments
    
    console.print(table)
    console.print(f"\n[bold]Total Lists: {len(normalized['lists_by_name'])}[/bold]")
    console.print(f"[bold]Total Cards: {total_cards}[/bold]")
    console.print(f"[bold]Total Attachments: {total_attachments}[/bold]")
    console.print(f"[bold]Total Comments: {total_comments}[/bold]\n")


@app.command()
def export_cover_attachments(
    export_file: Path = typer.Argument(..., help="Path to exported Trello JSON file"),
    out_dir: Path = typer.Option(
        Path("exports/cover_attachments"),
        "--out",
        "-o",
        help="Output directory for downloaded attachments"
    )
):
    """
    Download all attachments from safety cover job cards.
    
    Example:
        godman trello-analyze export-cover-attachments exports/board.json --out exports/cover_attachments/
    """
    if not export_file.exists():
        console.print(f"[red]Error: Export file not found: {export_file}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Extracting safety cover attachments from {export_file}...[/cyan]")
    console.print(f"[cyan]Output directory: {out_dir}[/cyan]\n")
    
    try:
        downloaded_files = extract_safety_cover_attachments(str(export_file), str(out_dir))
        
        console.print(f"\n[green]✓ Successfully downloaded {len(downloaded_files)} attachment(s)[/green]")
        console.print(f"[green]✓ Files saved to: {out_dir}[/green]\n")
        
        if downloaded_files:
            console.print("[bold]Downloaded files:[/bold]")
            for file_path in downloaded_files:
                console.print(f"  • {Path(file_path).name}")
        else:
            console.print("[yellow]No attachments found in safety cover cards[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
