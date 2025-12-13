"""Tax archive management CLI commands."""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import json
import shutil
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional

from libs.tax.tax_validator import TaxValidator
from libs.tax.tax_sync import TaxSync
from libs.tax.tax_classifier import TaxClassifier
from libs.tax.tax_inbox_watcher import TaxInboxWatcher
from libs.tax.att_bill_importer import import_att_bills
from libs.tax.filename_schema import (
    TaxFilenameParts, OwnerTag, IntentTag, StatusTag, 
    build_tax_filename, parse_tax_filename, sanitize_token
)
from libs.tax.allocations import suggest_allocation

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


@app.command("import-att")
def import_att(
    inbox_dir: str = typer.Option("data/tax/inbox/att", "--inbox-dir", help="Target inbox directory for imported bills")
):
    """
    Import AT&T bills from billing API into tax inbox directory.
    
    Downloads bill PDFs from AT&T billing API and copies them to the
    tax inbox directory for processing. Requires authenticated session
    from att_scraper.
    """
    console.print(f"[cyan]Importing AT&T bills to:[/cyan] {inbox_dir}")
    console.print()
    
    try:
        with console.status("[bold green]Fetching bills from AT&T API..."):
            summary = import_att_bills(inbox_dir=inbox_dir)
        
        # Display summary
        console.print(Panel.fit(
            f"[bold]Import Summary[/bold]\n\n"
            f"  Bills imported:  {summary['count']}\n"
            f"  Total amount:    ${summary['total_amount']:.2f}\n"
            f"  Inbox directory: {summary['inbox_dir']}",
            title="✓ Import Complete",
            border_style="green"
        ))
        
        # Display bill details
        if summary['bills']:
            console.print("\n[bold]Bills:[/bold]")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Bill ID", style="cyan")
            table.add_column("Date", style="yellow")
            table.add_column("Amount", style="green", justify="right")
            table.add_column("Status", style="magenta")
            
            for bill in summary['bills']:
                status_icon = "✓" if bill["status"] in ["imported", "already_exists"] else "✗"
                status_text = f"{status_icon} {bill['status']}"
                status_color = "green" if bill["status"] == "imported" else "yellow" if bill["status"] == "already_exists" else "red"
                
                table.add_row(
                    bill["bill_id"],
                    bill["date"],
                    f"${bill['amount']:.2f}",
                    f"[{status_color}]{status_text}[/{status_color}]"
                )
            
            console.print(table)
        
        console.print(f"\n[green]✓[/green] Successfully imported {summary['count']} bills")
    
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[yellow]Please run the AT&T scraper first to authenticate:[/yellow]")
        console.print("  python -c 'from libs.att_scraper import ATTClient; client = ATTClient(headless=False); client.login()'")
        raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]Error importing AT&T bills:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@app.command("init-year")
def init_year(
    archive_path: str = typer.Argument(..., help="Path to TAX_MASTER_ARCHIVE root"),
    year: int = typer.Option(..., "--year", help="Tax year to initialize")
):
    """
    Initialize the folder structure for a specific tax year.
    """
    root = Path(archive_path).expanduser().resolve()
    year_dir = root / str(year)
    
    folders = [
        "00_INCOME",
        "01_EXPENSES",
        "02_HEALTHCARE",
        "03_TAX_FORMS",
        "04_BANK_CREDIT",
        "05_CHARITY",
        "06_ASSETS_PROPERTY",
        "07_RETIREMENT_HSA",
        "99_SUPPORTING_MISC",
        "_SUMMARY"
    ]
    
    console.print(f"[cyan]Initializing tax year {year} in:[/cyan] {year_dir}")
    
    for folder in folders:
        (year_dir / folder).mkdir(parents=True, exist_ok=True)
        console.print(f"  [green]✓[/green] Created {folder}")
        
    # Ensure rules exist
    rules_dir = root / "_RULES"
    rules_dir.mkdir(exist_ok=True)
    rules_file = rules_dir / "TAX_DEDUCTION_RULES.md"
    if not rules_file.exists():
        rules_file.write_text("# Tax Deduction Rules\n\nAdd your rules here.")
        console.print(f"  [green]✓[/green] Created _RULES/TAX_DEDUCTION_RULES.md")
        
    # Ensure summary files exist
    summary_dir = year_dir / "_SUMMARY"
    (summary_dir / f"{year}__ALLOCATION_NOTES.md").touch()
    (summary_dir / f"{year}__YEAR_END_ASSERTIONS.md").touch()
    console.print(f"  [green]✓[/green] Created summary files")


def _refresh_review_queue(year_dir: Path):
    review_files = []
    for f in year_dir.rglob("*"):
        if f.is_file() and "__REVIEW" in f.name:
            review_files.append(f)
            
    queue_file = year_dir / "_SUMMARY" / "review_queue.md"
    with open(queue_file, "w") as f:
        f.write("# Review Queue\n\n")
        for rf in sorted(review_files):
            f.write(f"- {rf.relative_to(year_dir)}\n")
    console.print(f"[green]Updated review queue with {len(review_files)} items.[/green]")


@app.command("intake-scan")
def intake_scan(
    archive_path: str = typer.Argument(..., help="Path to TAX_MASTER_ARCHIVE root"),
    year: int = typer.Option(..., "--year", help="Tax year"),
    inbox: Optional[str] = typer.Option(None, "--inbox", help="Path to inbox directory")
):
    """
    Scan inbox, parse/prompt for metadata, rename, and route files.
    """
    root = Path(archive_path).expanduser().resolve()
    year_dir = root / str(year)
    
    if not year_dir.exists():
        console.print(f"[red]Error: Year directory {year_dir} does not exist. Run init-year first.[/red]")
        raise typer.Exit(1)
        
    # Determine inbox
    if inbox:
        inbox_path = Path(inbox).expanduser().resolve()
    else:
        inbox_path = root / "data/tax/inbox"
        if not inbox_path.exists():
            inbox_path = root / "_inbox"
            
    if not inbox_path.exists():
        console.print(f"[red]Error: Inbox not found at {inbox_path}[/red]")
        raise typer.Exit(1)
        
    console.print(f"[cyan]Scanning inbox:[/cyan] {inbox_path}")
    
    # Setup logging
    summary_dir = year_dir / "_SUMMARY"
    summary_dir.mkdir(exist_ok=True)
    log_file = summary_dir / f"intake_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    files = list(inbox_path.glob("*"))
    files = [f for f in files if f.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']]
    
    if not files:
        console.print("[yellow]No files found in inbox.[/yellow]")
        return

    for file_path in files:
        console.print(f"\n[bold]Processing:[/bold] {file_path.name}")
        
        # 1. Try to parse existing filename
        parts = parse_tax_filename(file_path.name)
        
        if not parts:
            # 2. Prompt user
            console.print("[yellow]Filename does not match schema v2. Please provide details.[/yellow]")
            
            # Date
            default_date = date.fromtimestamp(file_path.stat().st_mtime)
            date_str = typer.prompt("Date (YYYY-MM-DD)", default=default_date.strftime("%Y-%m-%d"))
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                console.print("[red]Invalid date format.[/red]")
                continue
                
            # Owner
            owner_str = typer.prompt("Owner", default="STEVE", show_choices=True)
            owner = OwnerTag(owner_str.upper())
            
            # Intent
            intent_str = typer.prompt("Intent", default="BIZ", show_choices=True)
            intent = IntentTag(intent_str.upper())
            
            # Category
            category = typer.prompt("Category (INCOME, EXPENSE, HEALTHCARE, TAXFORM, BANK, CHARITY, ASSET, RETIREMENT_HSA, MISC)", default="EXPENSE")
            
            # Source
            source = typer.prompt("Source (e.g. ATT, AMAZON)")
            
            # Amount
            amount_str = typer.prompt("Amount (optional)", default="")
            amount = Decimal(amount_str) if amount_str else None
            
            # Description
            description = typer.prompt("Description")
            
            # Status
            status_str = typer.prompt("Status (OK, REVIEW)", default="REVIEW")
            status = StatusTag(status_str.upper())
            
            parts = TaxFilenameParts(
                date=file_date,
                owner=owner,
                intent=intent,
                category=category,
                source=source,
                description=description,
                ext=file_path.suffix.lstrip('.'),
                amount=amount,
                status=status
            )
            
        # 3. Rename and Route
        new_filename = build_tax_filename(parts)
        
        # Determine target folder
        category_map = {
            "INCOME": "00_INCOME",
            "EXPENSE": "01_EXPENSES",
            "HEALTHCARE": "02_HEALTHCARE",
            "TAXFORM": "03_TAX_FORMS",
            "BANK": "04_BANK_CREDIT",
            "CHARITY": "05_CHARITY",
            "ASSET": "06_ASSETS_PROPERTY",
            "RETIREMENT_HSA": "07_RETIREMENT_HSA",
            "MISC": "99_SUPPORTING_MISC"
        }
        
        target_folder_name = category_map.get(sanitize_token(parts.category), "99_SUPPORTING_MISC")
        target_dir = year_dir / target_folder_name
        target_dir.mkdir(exist_ok=True)
        
        target_path = target_dir / new_filename
        
        # Handle collisions
        counter = 1
        while target_path.exists():
            stem = Path(new_filename).stem
            # If status is present, insert DUP before it
            if parts.status:
                status_suffix = f"__{parts.status.value}"
                base = stem[:-len(status_suffix)]
                new_name = f"{base}__DUP{counter}{status_suffix}.{parts.ext}"
            else:
                new_name = f"{stem}__DUP{counter}.{parts.ext}"
            target_path = target_dir / new_name
            counter += 1
            
        try:
            shutil.move(str(file_path), str(target_path))
            console.print(f"  [green]Moved to:[/green] {target_path.relative_to(root)}")
            
            # Log
            log_entry = {
                "original_path": str(file_path),
                "new_path": str(target_path),
                "parts": {
                    "date": parts.date.isoformat(),
                    "owner": parts.owner.value,
                    "intent": parts.intent.value,
                    "category": parts.category,
                    "source": parts.source,
                    "description": parts.description,
                    "amount": str(parts.amount) if parts.amount else None,
                    "status": parts.status.value if parts.status else None
                },
                "action": "move",
                "timestamp": datetime.now().isoformat()
            }
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            console.print(f"[red]Error moving file: {e}[/red]")
            error_dir = summary_dir / "_intake_errors"
            error_dir.mkdir(exist_ok=True)
            shutil.move(str(file_path), str(error_dir / file_path.name))

    # Refresh review queue
    _refresh_review_queue(year_dir)


@app.command("healthcare-report")
def healthcare_report(
    archive_path: str = typer.Argument(..., help="Path to TAX_MASTER_ARCHIVE root"),
    year: int = typer.Option(..., "--year", help="Tax year")
):
    """
    Generate healthcare readiness report.
    """
    root = Path(archive_path).expanduser().resolve()
    year_dir = root / str(year)
    healthcare_dir = year_dir / "02_HEALTHCARE"
    
    if not healthcare_dir.exists():
        console.print(f"[red]Healthcare directory not found: {healthcare_dir}[/red]")
        return

    files = list(healthcare_dir.glob("*"))
    
    # Heuristics
    has_1095a = any("1095" in f.name.upper() for f in files)
    has_policy = any(x in f.name.upper() for x in ["POLICY", "PLAN", "SUMMARY"] for f in files)
    premium_proofs = [f for f in files if any(x in f.name.upper() for x in ["PREMIUM", "INVOICE", "PAYMENT"])]
    reconciliations = [f for f in files if any(x in f.name.upper() for x in ["RECONCILE", "RECONCILIATION", "LETTER"])]
    
    report_path = year_dir / "_SUMMARY" / f"{year}__HEALTHCARE_READINESS.md"
    
    with open(report_path, "w") as f:
        f.write(f"# Healthcare Readiness Report {year}\n\n")
        
        f.write("## Next Actions\n")
        if not has_1095a:
            f.write("- [ ] Download 1095-A from Marketplace\n")
        if len(premium_proofs) < 12:
            f.write("- [ ] Capture remaining monthly premium proofs (aim for 12)\n")
        if not has_policy:
            f.write("- [ ] Add plan/policy summary\n")
        f.write("- [ ] Ensure reconciliation letters are filed if applicable\n\n")
        
        f.write("## Evidence Status\n")
        f.write(f"- **1095-A**: {'✅ Found' if has_1095a else '❌ Missing'}\n")
        f.write(f"- **Policy Summary**: {'✅ Found' if has_policy else '❌ Missing'}\n")
        f.write(f"- **Premium Proofs**: {len(premium_proofs)} found\n")
        f.write(f"- **Reconciliations**: {len(reconciliations)} found\n\n")
        
        f.write("## Files\n")
        for file in sorted(files):
            f.write(f"- {file.name}\n")
            
    console.print(f"[green]Report generated at:[/green] {report_path}")


@app.command("allocations")
def allocations(
    archive_path: str = typer.Argument(..., help="Path to TAX_MASTER_ARCHIVE root"),
    year: int = typer.Option(..., "--year", help="Tax year")
):
    """
    Generate joint allocations suggestion report.
    """
    root = Path(archive_path).expanduser().resolve()
    year_dir = root / str(year)
    
    report_path = year_dir / "_SUMMARY" / f"{year}__JOINT_ALLOCATIONS.md"
    
    joint_mixed_files = []
    
    # Scan all folders
    for f in year_dir.rglob("*"):
        if f.is_file():
            parts = parse_tax_filename(f.name)
            if parts and parts.owner == OwnerTag.JOINT and parts.intent == IntentTag.MIXED:
                joint_mixed_files.append((f, parts))
                
    with open(report_path, "w") as f:
        f.write(f"# Joint Allocations Report {year}\n\n")
        
        f.write("## Suggested Allocations\n")
        f.write("| File | Source | Amount | Suggestion |\n")
        f.write("|---|---|---|---|\n")
        
        unmatched = []
        
        for file_path, parts in sorted(joint_mixed_files, key=lambda x: x[1].date):
            suggestion = suggest_allocation(parts)
            if suggestion:
                split_str = ", ".join([f"{k.value}: {v}%" for k, v in suggestion.items()])
                amount_str = f"${parts.amount:.2f}" if parts.amount else "-"
                f.write(f"| {file_path.name} | {parts.source} | {amount_str} | {split_str} |\n")
            else:
                unmatched.append((file_path, parts))
                
        f.write("\n## Needs Decision\n")
        for file_path, parts in unmatched:
            amount_str = f"${parts.amount:.2f}" if parts.amount else "-"
            f.write(f"- {file_path.name} (Source: {parts.source}, Amount: {amount_str})\n")
            
    console.print(f"[green]Report generated at:[/green] {report_path}")


if __name__ == "__main__":
    app()
