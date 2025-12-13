import json
import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from godman_ai.workflows.trello import load_trello_daily, load_trello_job_summary
from libs.trello import TrelloClient, TrelloAuthError, TrelloAPIError
from libs.trello.attachment_extractor import extract_safety_cover_attachments

app = typer.Typer(help="Trello automation commands")
console = Console()


@app.command("export-board")
def export_board(
    board_id: str,
    out: str = typer.Option(
        None,
        "--out",
        help="Output file path (default: exports/trello_board_<board_id>.json)"
    )
):
    """
    Export a Trello board with all lists, cards, and metadata.
    
    Fetches complete board data including:
    - Board metadata
    - All lists
    - All cards (with descriptions, labels, due dates, attachments, comments)
    
    Example:
        godman trello export-board abc123
        godman trello export-board abc123 --out my_board.json
    """
    try:
        # Initialize Trello client
        console.print("[cyan]Connecting to Trello...[/cyan]")
        client = TrelloClient()
        
        # Set default output path if not provided
        if not out:
            out = f"exports/trello_board_{board_id}.json"
        
        output_path = Path(out)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Fetch board metadata
        console.print(f"[cyan]Fetching board {board_id}...[/cyan]")
        board = client.get_board(board_id)
        
        # Fetch all lists
        console.print("[cyan]Fetching lists...[/cyan]")
        lists = client.get_board_lists(board_id)
        
        # Fetch all cards with full details
        console.print("[cyan]Fetching cards (with attachments, comments, labels)...[/cyan]")
        cards = client.get_board_cards(
            board_id,
            attachments="true",
            checklists="all",
            members="true"
        )
        
        # Fetch comments for each card
        console.print("[cyan]Fetching card comments...[/cyan]")
        for card in cards:
            try:
                # Get comments (actions of type commentCard)
                response = client._request(
                    'GET',
                    f'/cards/{card["id"]}/actions',
                    params={'filter': 'commentCard'}
                )
                card['comments'] = response
            except Exception as e:
                console.print(f"[yellow]Warning: Could not fetch comments for card {card['id']}: {e}[/yellow]")
                card['comments'] = []
        
        # Structure output
        export_data = {
            "board": board,
            "lists": lists,
            "cards": cards
        }
        
        # Write to file
        console.print(f"[cyan]Writing to {output_path}...[/cyan]")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Print success summary
        console.print("\n[green]✓ Export successful![/green]\n")
        console.print(f"[bold]Board:[/bold] {board['name']}")
        console.print(f"[bold]URL:[/bold] {board['url']}")
        console.print(f"[bold]Lists:[/bold] {len(lists)}")
        console.print(f"[bold]Cards:[/bold] {len(cards)}")
        
        # Card breakdown by list
        cards_by_list = {}
        for card in cards:
            list_id = card.get('idList')
            cards_by_list[list_id] = cards_by_list.get(list_id, 0) + 1
        
        console.print("\n[bold]Cards per list:[/bold]")
        for lst in lists:
            count = cards_by_list.get(lst['id'], 0)
            if count > 0:
                console.print(f"  • {lst['name']:40s} {count:3d} cards")
        
        console.print(f"\n[bold]Output:[/bold] {output_path.absolute()}")
        
    except TrelloAuthError as e:
        console.print(f"[red]✗ Authentication Error:[/red] {e}", err=True)
        console.print("\n[yellow]Set environment variables:[/yellow]")
        console.print("  export TRELLO_API_KEY='your_key'")
        console.print("  export TRELLO_TOKEN='your_token'")
        console.print("\nGet credentials from: https://trello.com/power-ups/admin")
        raise typer.Exit(code=1)
        
    except TrelloAPIError as e:
        console.print(f"[red]✗ Trello API Error:[/red] {e}", err=True)
        raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}", err=True)
        raise typer.Exit(code=1)


@app.command("fetch")
def fetch(board_id: str):
    typer.echo(json.dumps({"board_id": board_id, "status": "fetched"}))


@app.command("summarize")
def summarize(board_id: str):
    typer.echo(json.dumps({"board_id": board_id, "summary": "ok"}))


@app.command("job")
def job(card_id: str):
    typer.echo(json.dumps({"card_id": card_id, "job_type": "General"}))


@app.command("export-cover-attachments")
def export_cover_attachments(
    export_file: str = typer.Argument(..., help="Path to Trello export JSON file"),
    out: str = typer.Option(
        "exports/cover_attachments",
        "--out",
        help="Output directory for downloaded attachments"
    )
):
    """
    Extract and download all attachments from safety cover cards.
    
    Scans the Trello export for cards in lists containing "safety cover",
    downloads all attachments, and saves them with normalized filenames.
    
    Example:
        godman trello export-cover-attachments exports/memphis_pool_board.json
        godman trello export-cover-attachments exports/board.json --out my_attachments/
    """
    try:
        console.print(f"[cyan]Loading export from {export_file}...[/cyan]")
        
        # Extract attachments
        file_paths = extract_safety_cover_attachments(export_file, out)
        
        # Print results
        if file_paths:
            console.print(f"\n[green]✓ Downloaded {len(file_paths)} attachments[/green]\n")
            console.print("[bold]Files:[/bold]")
            for path in file_paths:
                console.print(f"  • {path}")
            console.print(f"\n[bold]Output directory:[/bold] {Path(out).absolute()}")
        else:
            console.print("[yellow]No attachments found in safety cover cards.[/yellow]")
    
    except FileNotFoundError as e:
        console.print(f"[red]✗ File not found:[/red] {e}", err=True)
        raise typer.Exit(code=1)
    
    except TrelloAuthError as e:
        console.print(f"[red]✗ Authentication Error:[/red] {e}", err=True)
        console.print("\n[yellow]Set environment variables:[/yellow]")
        console.print("  export TRELLO_API_KEY='your_key'")
        console.print("  export TRELLO_TOKEN='your_token'")
        raise typer.Exit(code=1)
    
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}", err=True)
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(code=1)


@app.command("workflow")
def workflow(mode: str, resource_id: str):
    if mode == "daily":
        wf = load_trello_daily()
    else:
        wf = load_trello_job_summary()
    ctx = asyncio.run(wf.run())
    typer.echo(json.dumps(ctx.data, default=str))
