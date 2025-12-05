"""Main CLI entry point for godman automation lab."""
import typer
from pathlib import Path
from godman.commands import receipts

app = typer.Typer(
    name="godman",
    help="Godman Automation Lab - Your personal automation toolkit",
    add_completion=False,
)

# Register command modules
app.add_typer(receipts.app, name="receipts", help="Receipt processing commands")


@app.command()
def run(input: str = typer.Argument(..., help="File path or raw string to process")):
    """
    Run orchestrator: accepts a file path or raw string, detects type, and routes through AI system.
    
    Examples:
        godman run scans/receipt.pdf
        godman run data/expenses.csv
        godman run "analyze this text"
    """
    from godman_ai.orchestrator import Orchestrator
    
    typer.echo(f"🎭 Godman Orchestrator v2")
    typer.echo(f"📋 Input: {input}\n")
    
    # Initialize orchestrator
    orchestrator = Orchestrator()
    orchestrator.load_tools_from_package("godman_ai.tools")
    
    typer.echo(f"✅ Loaded {len(orchestrator.tool_classes)} tools")
    typer.echo(f"🚀 Processing...\n")
    
    # Run task
    result = orchestrator.run_task(input)
    
    # Display results
    if result["status"] == "success":
        typer.echo(f"✅ Success!")
        typer.echo(f"📊 Input Type: {result['input_type']}")
        typer.echo(f"🔧 Tool Used: {result['tool']}")
        typer.echo(f"\n📋 Result:")
        typer.echo(result["result"])
    else:
        typer.echo(f"❌ Error: {result['error']}", err=True)
        typer.echo(f"🔍 Error Type: {result.get('error_type', 'Unknown')}", err=True)
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show version information."""
    from godman import __version__
    typer.echo(f"godman version {__version__}")


@app.command()
def agent(input: str = typer.Argument(..., help="File path or raw text for agent processing")):
    """
    Run the full AgentLoop on the provided input (file or raw text).
    
    The agent system will:
    1. Generate an execution plan
    2. Execute each step using appropriate tools
    3. Review outputs and replan if needed
    
    Examples:
        godman agent scans/receipt.pdf
        godman agent "Process all receipts from last month"
    """
    from godman_ai.agents.agent_loop import AgentLoop
    import os
    
    typer.echo(f"🤖 Godman Agent System v1")
    typer.echo(f"📋 Input: {input}\n")
    
    # Check if input is a file
    input_data = input
    if os.path.isfile(input):
        typer.echo(f"📁 Detected file input")
        # For now, pass the file path; agents will handle reading
        input_data = input
    else:
        typer.echo(f"📝 Detected text input")
    
    # Initialize agent loop
    typer.echo(f"🔧 Initializing agent loop...")
    agent_loop = AgentLoop(max_retries=3, review_strictness="medium")
    
    typer.echo(f"🚀 Starting agent execution...\n")
    typer.echo("=" * 60)
    
    # Run agent loop
    result = agent_loop.run(input_data)
    
    # Display results
    typer.echo("\n" + "=" * 60)
    typer.echo("📊 AGENT EXECUTION SUMMARY")
    typer.echo("=" * 60)
    
    if result.get('success', False):
        typer.echo(f"✅ Overall Status: SUCCESS")
    else:
        typer.echo(f"❌ Overall Status: FAILED")
        if 'error' in result:
            typer.echo(f"   Error: {result['error']}")
    
    # Show plan summary
    raw_plan = result.get('raw_plan', [])
    typer.echo(f"\n📋 Plan: {len(raw_plan)} steps generated")
    for i, step in enumerate(raw_plan, 1):
        typer.echo(f"   {i}. {step.get('action_type', 'unknown')} - {step.get('expected_output', 'N/A')}")
    
    # Show execution summary
    steps = result.get('steps', [])
    typer.echo(f"\n⚡ Execution: {len(steps)} steps completed")
    for step_result in steps:
        step_id = step_result['step']['id']
        success = step_result['execution'].get('success', False)
        approved = step_result['review'].get('approved', False)
        status_icon = "✅" if success and approved else "❌"
        typer.echo(f"   {status_icon} {step_id}: {'SUCCESS' if success else 'FAILED'} / {'APPROVED' if approved else 'REJECTED'}")
    
    # Show final output
    final_output = result.get('final_output')
    if final_output:
        typer.echo(f"\n📤 Final Output:")
        if isinstance(final_output, dict):
            import json
            typer.echo(json.dumps(final_output, indent=2))
        else:
            typer.echo(str(final_output))
    
    typer.echo("\n" + "=" * 60)
    
    if not result.get('success', False):
        raise typer.Exit(code=1)


@app.command()
def status():
    """Show system status and configuration."""
    from godman_ai.orchestrator import Orchestrator
    
    typer.echo("🚀 Godman Automation Lab")
    typer.echo("Status: All systems operational")
    
    # Show orchestrator status
    orchestrator = Orchestrator()
    orchestrator.load_tools_from_package("godman_ai.tools")
    orch_status = orchestrator.status()
    
    typer.echo(f"\n🎭 Orchestrator:")
    typer.echo(f"  • Tools registered: {orch_status['tools_registered']}")
    typer.echo(f"  • Tools available: {', '.join(orch_status['tool_names'])}")
    typer.echo(f"  • Ready: {'✅' if orch_status['ready'] else '❌'}")
    
    typer.echo("\n🤖 Agent System:")
    typer.echo("  • Planner: ✅ Available")
    typer.echo("  • Executor: ✅ Available")
    typer.echo("  • Reviewer: ✅ Available")
    typer.echo("  • AgentLoop: ✅ Available")
    
    typer.echo("\n📦 Available modules:")
    typer.echo("  • receipts - Receipt processing and OCR")
    typer.echo("  • expenses - Expense tracking and summaries")
    typer.echo("\nRun 'godman --help' for more information")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
