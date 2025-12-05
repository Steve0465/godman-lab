"""
CLI command for AI-powered file organization.
"""
import typer
from pathlib import Path
import os

app = typer.Typer()


@app.command()
def files(
    source: str = typer.Argument(..., help="Source directory to organize"),
    dest: str = typer.Argument(..., help="Destination base directory for organized files"),
    ai: bool = typer.Option(True, "--ai/--no-ai", help="Use AI categorization (requires OPENAI_API_KEY)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without moving files"),
    confidence: float = typer.Option(0.5, "--confidence", "-c", min=0.0, max=1.0, help="Minimum confidence threshold"),
):
    """
    Organize files using AI-powered categorization.
    
    Examples:
    
        # Dry run to preview organization
        godman organize files ~/Downloads ~/Documents/Organized --dry-run
        
        # Actually organize files with AI
        godman organize files ~/Downloads ~/Documents/Organized
        
        # Use rule-based only (no AI)
        godman organize files ~/Downloads ~/Documents/Organized --no-ai
        
        # High confidence threshold
        godman organize files ~/Downloads ~/Documents/Organized -c 0.8
    """
    from libs.ai_organizer import organize_files, print_organization_report
    
    # Get OpenAI API key if using AI
    api_key = None
    if ai:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            typer.secho(
                "⚠️  OPENAI_API_KEY not found. Falling back to rule-based categorization.",
                fg=typer.colors.YELLOW
            )
            typer.echo("   Set your API key: export OPENAI_API_KEY='your-key-here'\n")
            ai = False
    
    # Show configuration
    typer.echo(f"\n🔍 Scanning: {source}")
    typer.echo(f"📁 Destination: {dest}")
    typer.echo(f"🤖 AI Mode: {'✅ Enabled' if ai else '❌ Disabled (rule-based)'}")
    typer.echo(f"🎯 Confidence Threshold: {confidence:.0%}")
    typer.echo(f"🧪 Dry Run: {'✅ Preview Only' if dry_run else '❌ Will Move Files'}")
    
    if not dry_run:
        confirm = typer.confirm("\n⚠️  This will move files. Continue?")
        if not confirm:
            typer.echo("Cancelled.")
            raise typer.Exit()
    
    typer.echo("\n⏳ Processing files...\n")
    
    try:
        results = organize_files(
            source_dir=source,
            dest_dir=dest,
            use_ai=ai,
            openai_api_key=api_key,
            dry_run=dry_run,
            min_confidence=confidence
        )
        
        print_organization_report(results, dry_run=dry_run)
        
        if dry_run:
            typer.secho(
                "\n✅ Dry run complete! Run without --dry-run to actually move files.",
                fg=typer.colors.GREEN,
                bold=True
            )
        else:
            typer.secho(
                f"\n✅ Successfully organized {results['organized']} files!",
                fg=typer.colors.GREEN,
                bold=True
            )
    
    except Exception as e:
        typer.secho(f"\n❌ Error: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
