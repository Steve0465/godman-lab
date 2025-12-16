"""
CLI commands for Gemini PromptLab. 
"""
import typer
from pathlib import Path
import logging

from libs.gemini_promptlab import (
    load_prompt_config,
    run_test_cases,
    write_report_md
)

app = typer.Typer(help="Gemini PromptLab commands")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.command()
def run(
    config:  str = typer.Option(..., "--config", help="Path to prompt config JSON"),
    out: str = typer.Option("reports/", "--out", help="Output directory for reports"),
    api_key: str = typer.Option(None, "--api-key", help="Gemini API key (or use GEMINI_API_KEY env var)")
):
    """
    Run PromptLab tests with a config file.
    
    Example: 
        godman gemini promptlab run --config configs/gemini/prompts/receipt_parser.json
    """
    try:
        # Load config
        typer.echo(f"Loading config:  {config}")
        prompt_config = load_prompt_config(config)
        
        # Run tests
        typer.echo(f"Running {len(prompt_config.get('test_cases', []))} test cases...")
        results = run_test_cases(prompt_config, dry_run=False, api_key=api_key)
        
        # Write report
        output_dir = Path(out)
        report_name = f"{prompt_config['name']}_{typer.get_app_dir('godman')}.md"
        report_path = output_dir / report_name
        
        write_report_md(prompt_config, results, str(report_path))
        
        # Summary
        passed = sum(1 for r in results if r.get('status') == 'pass')
        failed = sum(1 for r in results if r.get('status') == 'fail')
        
        typer.echo(f"\n✅ Tests complete:  {passed} passed, {failed} failed")
        typer.echo(f"📄 Report: {report_path}")
        
    except Exception as e:
        logger.error(f"Error running PromptLab: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def dry_run(
    config: str = typer.Option(..., "--config", help="Path to prompt config JSON")
):
    """
    Dry run - render prompts without calling Gemini API.
    
    Example:
        godman gemini promptlab dry-run --config configs/gemini/prompts/receipt_parser.json
    """
    try: 
        # Load config
        typer.echo(f"Loading config: {config}")
        prompt_config = load_prompt_config(config)
        
        # Dry run
        typer.echo(f"Rendering {len(prompt_config.get('test_cases', []))} test cases...")
        results = run_test_cases(prompt_config, dry_run=True)
        
        # Show rendered prompts
        typer.echo("\n" + "="*60)
        for result in results:
            typer.echo(f"\n📝 Test Case {result['test_case']}")
            typer.echo("-" * 60)
            typer.echo(result.get('rendered_prompt', ''))
            typer.echo("-" * 60)
        
        typer.echo(f"\n✅ Dry run complete - {len(results)} prompts rendered")
        
    except Exception as e:
        logger.error(f"Error in dry run: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__": 
    app()