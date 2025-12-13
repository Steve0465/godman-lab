from pathlib import Path
from typing import List

import typer
from rich.console import Console
from rich.table import Table

from libs.password_ingest import (
    audit_strength,
    batch_login_test,
    compute_complexity_score,
    compute_strength,
    dedupe,
    export_csv,
    export_full_report,
    export_login_test_report,
    load_multiple_csv,
    load_password_csv,
    normalize_entries,
    summarize_dataset,
    validate_dataset,
)

app = typer.Typer(help="Password ingestion and auditing tools.")
console = Console()


def _enrich(entries: List[dict]) -> List[dict]:
    normalized = normalize_entries(entries)
    deduped = dedupe(normalized)
    enriched: List[dict] = []
    for entry in deduped:
        strength = compute_strength(entry.get("password", ""))
        complexity_score = compute_complexity_score(entry.get("password", ""))
        enriched.append({**entry, "strength": strength, "complexity_score": complexity_score})
    return enriched


@app.command("import-file")
def import_file(
    input_path: Path = typer.Argument(..., help="CSV file containing credentials."),
    output_dir: Path = typer.Option(Path("data/passwords/output"), "--output-dir", "-o", help="Directory for reports."),
):
    """Run full ingestion pipeline for a single CSV and export CSV + JSON reports."""
    entries = load_password_csv(input_path)
    processed = _enrich(entries)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{input_path.stem}_normalized.csv"
    json_path = output_dir / f"{input_path.stem}_report.json"

    export_csv(processed, csv_path)
    export_full_report(processed, json_path)

    console.print(f"[green]Imported[/green] {len(processed)} entries from {input_path}")
    console.print(f"CSV saved to: {csv_path}")
    console.print(f"JSON report saved to: {json_path}")


@app.command("import-multi")
def import_multi(
    input_paths: List[Path] = typer.Argument(..., help="Multiple CSV files to merge and ingest."),
    output_dir: Path = typer.Option(Path("data/passwords/output"), "--output-dir", "-o", help="Directory for reports."),
):
    """Merge multiple CSVs then run the ingestion pipeline."""
    entries = load_multiple_csv(input_paths)
    processed = _enrich(entries)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "merged_normalized.csv"
    json_path = output_dir / "merged_report.json"

    export_csv(processed, csv_path)
    export_full_report(processed, json_path)

    console.print(f"[green]Merged[/green] {len(processed)} entries from {len(input_paths)} files")
    console.print(f"CSV saved to: {csv_path}")
    console.print(f"JSON report saved to: {json_path}")


@app.command("test-credentials")
def test_credentials(
    input_path: Path = typer.Argument(..., help="CSV file containing credentials."),
    output_dir: Path = typer.Option(Path("data/passwords/output"), "--output-dir", "-o", help="Directory for reports."),
):
    """Run simulated login tests and export results."""
    entries = _enrich(load_password_csv(input_path))
    results = batch_login_test(entries)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{input_path.stem}_login_tests.json"
    export_login_test_report(results, report_path)

    success_count = sum(1 for result in results if result["success"])
    console.print(f"Tested {len(results)} credentials")
    console.print(f"[green]Successful:[/green] {success_count} [red]Failed:[/red] {len(results) - success_count}")
    console.print(f"Login test report saved to: {report_path}")


@app.command("summary")
def summary(input_path: Path = typer.Argument(..., help="CSV file containing credentials.")):
    """Summarize password dataset and display validation findings."""
    entries = _enrich(load_password_csv(input_path))
    strengths = audit_strength(entries)
    summary_data = summarize_dataset(entries)
    validation = validate_dataset(entries)

    console.print(f"\n[bold]Dataset Summary for {input_path}[/bold]")
    console.print(f"Total entries: {summary_data['total_entries']}")
    console.print(f"Unique domains: {summary_data['unique_domains']}")
    console.print(
        f"Strength -> weak: {len(strengths['weak'])}, medium: {len(strengths['medium'])}, strong: {len(strengths['strong'])}"
    )
    console.print(f"Average complexity: {summary_data['average_complexity_score']}")

    domain_table = Table(title="Top Domains", show_header=True, header_style="bold magenta")
    domain_table.add_column("Domain")
    domain_table.add_column("Count", justify="right")
    for domain, count in summary_data["domains_most_used"]:
        domain_table.add_row(domain, str(count))
    console.print(domain_table)

    if validation["has_issues"]:
        console.print("\n[red]Validation issues detected:[/red]")
        console.print(f"- Missing URL/username: {len(validation['invalid'])}")
        console.print(f"- Empty passwords: {len(validation['empty_passwords'])}")
    else:
        console.print("\n[green]No validation issues detected.[/green]")
