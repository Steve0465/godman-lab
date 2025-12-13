"""Tax archive management CLI commands."""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from libs.tax.tax_validator import TaxValidator
from libs.tax.tax_sync import TaxSync
from libs.tax.tax_classifier import TaxClassifier
from libs.tax.tax_inbox_watcher import TaxInboxWatcher

app = typer.Typer(help="Tax archive management tools")
console = Console()


@app.command()
def validate(
    archive_path: str = typer.Argument(..., help="Path to TAX_MASTER_ARCHIVE root"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
):
    """
    Validate tax archive structure, detect duplicates, and find misplaced files.
    """
    root = Path(archive_path).expanduser().resolve()
    
    if not root.exists():
        console.print(f"[red]Error: Path does not exist: {root}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Validating tax archive:[/cyan] {root}")
    console.print()
    
    validator = TaxValidator(root)
    
    with console.status("[bold green]Scanning files..."):
        records = validator.scan()
    
    console.print(f"[green]✓[/green] Scanned {len(records)} files")
    console.print()
    
    with console.status("[bold green]Running validation..."):
        report = validator.validate()
    
    # Display summary
    console.print(report.summary())
    
    # Show detailed issues if verbose
    if verbose and report.issues:
        console.print("\n[bold]Detailed Issues:[/bold]")
        for issue in report.issues[:50]:  # Limit to first 50
            color = "yellow" if issue.level == "warning" else "red"
            console.print(f"  [{color}]{issue.level.upper()}[/{color}]: {issue.message}")
            console.print(f"    Path: {issue.path}")
    
    # Exit with error code if validation failed
    if not report.valid:
        raise typer.Exit(1)


@app.command()
def sync(
    archive_path: str = typer.Argument(..., help="Path to TAX_MASTER_ARCHIVE root"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview changes without applying"),
    safe_delete: bool = typer.Option(False, "--safe-delete", help="Enable deletion of duplicates")
):
    """
    Sync and organize files into canonical year/category structure.
    """
    root = Path(archive_path).expanduser().resolve()
    
    if not root.exists():
        console.print(f"[red]Error: Path does not exist: {root}[/red]")
        raise typer.Exit(1)
    
    mode = "DRY RUN" if dry_run else "APPLY"
    console.print(f"[cyan]Tax Archive Sync ({mode}):[/cyan] {root}")
    console.print()
    
    syncer = TaxSync(root)
    
    with console.status("[bold green]Analyzing files..."):
        plan = syncer.plan()
    
    # Display plan summary
    console.print(Panel.fit(
        f"[bold]Sync Plan Summary[/bold]\n\n"
        f"  Duplicates to move: {len(plan.duplicate_moves)}\n"
        f"  Files to copy:      {len(plan.to_copy)}\n"
        f"  Files to update:    {len(plan.to_update)}\n"
        f"  Files to delete:    {len(plan.to_delete)}\n"
        f"  Total changes:      {len(plan.duplicate_moves) + len(plan.to_copy) + len(plan.to_update) + len(plan.to_delete)}",
        title="📋 Plan",
        border_style="cyan"
    ))
    
    if plan.duplicate_moves or plan.to_copy or plan.to_update or plan.to_delete:
        # Show sample operations
        if plan.duplicate_moves:
            console.print("\n[bold]Sample Duplicate Move Operations (automatic):[/bold]")
            for op in plan.duplicate_moves[:5]:
                console.print(f"  [magenta]⇄[/magenta] {op.source} → {op.destination}")
        
        if plan.to_copy:
            console.print("\n[bold]Sample Copy Operations:[/bold]")
            for op in plan.to_copy[:5]:
                console.print(f"  [green]→[/green] {op.source} → {op.destination}")
        
        if plan.to_update:
            console.print("\n[bold]Sample Update Operations:[/bold]")
            for op in plan.to_update[:5]:
                console.print(f"  [yellow]↻[/yellow] {op.source} → {op.destination}")
        
        if plan.to_delete:
            console.print("\n[bold]Sample Delete Operations:[/bold]")
            for op in plan.to_delete[:5]:
                console.print(f"  [red]✕[/red] {op.source}")
    
    if dry_run:
        console.print("\n[yellow]This was a dry run. Use --apply to execute changes.[/yellow]")
        return
    
    # Apply changes
    console.print()
    confirm = typer.confirm("Apply these changes?")
    if not confirm:
        console.print("[yellow]Sync cancelled.[/yellow]")
        return
    
    with console.status("[bold green]Applying changes..."):
        result = syncer.apply(plan, dry_run=False)
    
    # Display results
    console.print(Panel.fit(
        f"[bold]Sync Results[/bold]\n\n"
        f"  Duplicates moved: {result.duplicates_moved}\n"
        f"  Copied:           {result.copied}\n"
        f"  Updated:          {result.updated}\n"
        f"  Deleted:          {result.deleted}\n"
        f"  Successful:       {result.successful}\n"
        f"  Failed:           {result.failed}\n"
        f"  Total:            {result.successful + result.failed}",
        title="✓ Complete" if result.failed == 0 else "⚠ Complete with Errors",
        border_style="green" if result.failed == 0 else "yellow"
    ))
    
    if result.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result.errors[:10]:
            console.print(f"  [red]✕[/red] {error}")


@app.command()
def classify(
    file_path: str = typer.Argument(..., help="Path to file to classify"),
    use_ocr: bool = typer.Option(False, "--ocr", help="Enable OCR for scanned documents")
):
    """
    Classify a document to infer year and category.
    """
    path = Path(file_path).expanduser().resolve()
    
    if not path.exists():
        console.print(f"[red]Error: File does not exist: {path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Classifying:[/cyan] {path.name}")
    console.print()
    
    classifier = TaxClassifier()
    
    with console.status("[bold green]Analyzing document..."):
        result = classifier.classify(path)
    
    # Display results
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Year", str(result.inferred_year) if result.inferred_year else "[dim]Unknown[/dim]")
    table.add_row("Category", result.inferred_category or "[dim]Unknown[/dim]")
    table.add_row("Confidence", f"{result.confidence:.1%}")
    
    console.print(table)
    
    if result.evidence:
        console.print("\n[bold]Evidence:[/bold]")
        for evidence in result.evidence:
            console.print(f"  • {evidence}")


@app.command()
def watch(
    archive_path: str = typer.Argument(..., help="Path to TAX_MASTER_ARCHIVE root"),
    debounce: int = typer.Option(30, "--debounce", help="Seconds to wait after last file before processing")
):
    """
    Watch the _inbox directory and automatically process new files.
    
    Files are classified and routed to the appropriate year/category folders.
    High-confidence classifications are auto-applied. Low-confidence files
    are moved to _metadata/review for manual inspection.
    """
    root = Path(archive_path).expanduser().resolve()
    
    if not root.exists():
        console.print(f"[red]Error: Path does not exist: {root}[/red]")
        raise typer.Exit(1)
    
    inbox = root / "_inbox"
    console.print(f"[cyan]Starting inbox watcher[/cyan]")
    console.print(f"  Archive: {root}")
    console.print(f"  Inbox:   {inbox}")
    console.print(f"  Debounce: {debounce}s")
    console.print()
    console.print("[green]Watching for new files... (Press Ctrl+C to stop)[/green]")
    console.print()
    
    watcher = TaxInboxWatcher(root, debounce_seconds=debounce)
    
    try:
        watcher.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping watcher...[/yellow]")


if __name__ == "__main__":
    app()
