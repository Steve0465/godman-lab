"""Receipt processing commands."""
import typer
from pathlib import Path
from typing import Optional
import sys

# Add libs to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "libs"))

app = typer.Typer(help="Receipt processing and OCR")


@app.command()
def process(
    input_dir: Path = typer.Option(
        Path("scans"),
        "--input",
        "-i",
        help="Directory containing receipt images/PDFs",
    ),
    output_dir: Path = typer.Option(
        Path("receipts"),
        "--output",
        "-o",
        help="Directory to store organized receipts",
    ),
    metadata_csv: Path = typer.Option(
        Path("receipts.csv"),
        "--csv",
        "-c",
        help="CSV file to store receipt metadata",
    ),
):
    """Process receipts from input directory using OCR and AI."""
    typer.echo(f"📄 Processing receipts from {input_dir}")
    
    try:
        # Import and call the existing function
        from receipts import process_receipts
        
        # Call the original function (it uses env vars, so set them temporarily)
        import os
        os.environ["INPUT_DIR"] = str(input_dir)
        os.environ["OUTPUT_DIR"] = str(output_dir)
        os.environ["METADATA_CSV"] = str(metadata_csv)
        
        process_receipts()
        
        typer.echo("✅ Receipt processing complete!")
        
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def status():
    """Show receipt processing status and statistics."""
    typer.echo("📊 Receipt Processing Status")
    
    metadata_csv = Path("receipts.csv")
    if metadata_csv.exists():
        import pandas as pd
        df = pd.read_csv(metadata_csv)
        typer.echo(f"\n✓ Total receipts processed: {len(df)}")
        
        if 'total' in df.columns:
            total = df['total'].sum()
            typer.echo(f"✓ Total amount tracked: ${total:,.2f}")
        
        if 'vendor' in df.columns:
            unique_vendors = df['vendor'].nunique()
            typer.echo(f"✓ Unique vendors: {unique_vendors}")
    else:
        typer.echo("\n⚠️  No receipts processed yet")
        typer.echo("Run 'godman receipts process' to start processing")


if __name__ == "__main__":
    app()
