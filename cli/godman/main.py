"""Main CLI entry point for godman automation lab."""

import typer
import sys
from pathlib import Path

# Add cli directory to path for imports
_cli_dir = Path(__file__).parent.parent
if str(_cli_dir) not in sys.path:
    sys.path.insert(0, str(_cli_dir))

from godman.commands import receipts, shield

app = typer.Typer(
    name="godman",
    help="Godman Automation Lab - Your personal automation toolkit",
    add_completion=False,
)

# Register command modules
app.add_typer(receipts.app, name="receipts", help="Receipt processing commands")
app.add_typer(shield.app, name="shield", help="Shield Pro Media Box commands")


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

    if result.get("success", False):
        typer.echo(f"✅ Overall Status: SUCCESS")
    else:
        typer.echo(f"❌ Overall Status: FAILED")
        if "error" in result:
            typer.echo(f"   Error: {result['error']}")

    # Show plan summary
    raw_plan = result.get("raw_plan", [])
    typer.echo(f"\n📋 Plan: {len(raw_plan)} steps generated")
    for i, step in enumerate(raw_plan, 1):
        typer.echo(
            f"   {i}. {step.get('action_type', 'unknown')} - {step.get('expected_output', 'N/A')}"
        )

    # Show execution summary
    steps = result.get("steps", [])
    typer.echo(f"\n⚡ Execution: {len(steps)} steps completed")
    for step_result in steps:
        step_id = step_result["step"]["id"]
        success = step_result["execution"].get("success", False)
        approved = step_result["review"].get("approved", False)
        status_icon = "✅" if success and approved else "❌"
        typer.echo(
            f"   {status_icon} {step_id}: {'SUCCESS' if success else 'FAILED'} / {'APPROVED' if approved else 'REJECTED'}"
        )

    # Show final output
    final_output = result.get("final_output")
    if final_output:
        typer.echo(f"\n📤 Final Output:")
        if isinstance(final_output, dict):
            import json

            typer.echo(json.dumps(final_output, indent=2))
        else:
            typer.echo(str(final_output))

    typer.echo("\n" + "=" * 60)

    if not result.get("success", False):
        raise typer.Exit(code=1)


@app.command()
def queue_enqueue(
    input: str = typer.Argument(..., help="Task input to enqueue"),
    priority: int = typer.Option(1, help="Job priority"),
):
    """Enqueue a task for background processing."""
    from godman_ai.queue import JobQueue

    queue = JobQueue()
    job_id = queue.enqueue(input, priority=priority)

    typer.echo(f"✅ Job enqueued: ID={job_id}, Priority={priority}")
    typer.echo(f"📊 Queue size: {queue.size()} pending jobs")


@app.command()
def queue_worker(poll_interval: float = typer.Option(2.0, help="Polling interval in seconds")):
    """Run the job worker to process queued tasks."""
    from godman_ai.queue import JobWorker

    typer.echo(f"🔄 Starting job worker (poll interval: {poll_interval}s)")
    typer.echo("Press Ctrl+C to stop\n")

    worker = JobWorker()

    try:
        worker.run_forever(poll_interval=poll_interval)
    except KeyboardInterrupt:
        typer.echo("\n👋 Worker stopped")


@app.command()
def queue_status():
    """Show job queue status."""
    from godman_ai.queue import JobQueue

    queue = JobQueue()
    status = queue.get_status()

    typer.echo("📊 Job Queue Status")
    typer.echo("=" * 40)

    for state, count in status.items():
        typer.echo(f"  {state.capitalize()}: {count}")

    total = sum(status.values())
    typer.echo(f"  Total: {total}")


@app.command()
def schedule_add(
    cron: str = typer.Argument(..., help="Cron expression"),
    command: str = typer.Argument(..., help="Command to run"),
):
    """Add a scheduled task."""
    from godman_ai.scheduler import Scheduler

    scheduler = Scheduler()

    try:
        schedule_id = scheduler.add_schedule(cron, command)
        typer.echo(f"✅ Schedule added: ID={schedule_id}")
        typer.echo(f"   Cron: {cron}")
        typer.echo(f"   Command: {command}")
    except ValueError as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def schedule_list():
    """List all scheduled tasks."""
    from godman_ai.scheduler import Scheduler

    scheduler = Scheduler()
    schedules = scheduler.get_schedules()

    typer.echo("📅 Scheduled Tasks")
    typer.echo("=" * 60)

    if not schedules:
        typer.echo("  No schedules found")
        return

    for schedule in schedules:
        status = "✅" if schedule.enabled else "❌"
        typer.echo(f"\n  {status} ID {schedule.id}: {schedule.cron}")
        typer.echo(f"     Command: {schedule.command}")
        if schedule.next_run:
            typer.echo(f"     Next run: {schedule.next_run}")
        if schedule.last_run:
            typer.echo(f"     Last run: {schedule.last_run}")


@app.command()
def schedule_run():
    """Check and run pending scheduled tasks."""
    from godman_ai.scheduler import Scheduler

    scheduler = Scheduler()

    typer.echo("⏰ Checking for pending scheduled tasks...")
    scheduler.run_pending()
    typer.echo("✅ Done")


@app.command()
def status():
    """Show system status and configuration."""
    from godman_ai.orchestrator import Orchestrator
    from godman_ai.queue import JobQueue
    from godman_ai.scheduler import Scheduler

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

    # Show queue status
    queue = JobQueue()
    queue_status = queue.get_status()
    typer.echo("\n📊 Job Queue:")
    for state, count in queue_status.items():
        typer.echo(f"  • {state.capitalize()}: {count}")

    # Show scheduler status
    scheduler = Scheduler()
    schedules = scheduler.get_schedules()
    enabled_count = sum(1 for s in schedules if s.enabled)
    typer.echo(f"\n📅 Scheduler:")
    typer.echo(f"  • Total schedules: {len(schedules)}")
    typer.echo(f"  • Enabled: {enabled_count}")

    typer.echo("\n📦 Available modules:")
    typer.echo("  • receipts - Receipt processing and OCR")
    typer.echo("  • expenses - Expense tracking and summaries")
    typer.echo("\nRun 'godman --help' for more information")


@app.command()
def os_state():
    """Show OS Core global state snapshot."""
    from godman_ai.os_core import GlobalState
    import json

    typer.echo("🖥️  GodmanAI OS Core - Global State")
    typer.echo("=" * 60)

    state = GlobalState()
    state.initialize()
    snapshot = state.snapshot()

    typer.echo(json.dumps(snapshot, indent=2))


@app.command()
def os_health():
    """Show system health metrics."""
    from godman_ai.os_core import system_health, tool_stats, model_stats
    import json

    typer.echo("🏥 GodmanAI OS Core - Health Check")
    typer.echo("=" * 60)

    health = system_health()

    # Show overall status
    status_icon = (
        "✅" if health["status"] == "healthy" else "⚠️" if health["status"] == "warning" else "❌"
    )
    typer.echo(f"\n{status_icon} Overall Status: {health['status'].upper()}")

    # Show warnings if any
    if "warnings" in health:
        typer.echo("\n⚠️  Warnings:")
        for warning in health["warnings"]:
            typer.echo(f"  • {warning}")

    # Show checks
    typer.echo("\n📊 System Checks:")
    for check, value in health["checks"].items():
        check_icon = "✅" if value else "❌"
        typer.echo(f"  {check_icon} {check}: {value}")

    # Show tool stats
    typer.echo("\n🔧 Tool Statistics:")
    t_stats = tool_stats()
    typer.echo(f"  • Total tools used: {t_stats.get('total_tools_used', 0)}")
    typer.echo(f"  • Total invocations: {t_stats.get('total_invocations', 0)}")

    if t_stats.get("top_tools"):
        typer.echo("\n  Top Tools:")
        for tool, count in list(t_stats["top_tools"].items())[:5]:
            typer.echo(f"    • {tool}: {count}")

    # Show model stats
    typer.echo("\n🤖 Model Statistics:")
    m_stats = model_stats()
    typer.echo(f"  • Available models: {m_stats.get('total_available', 0)}")
    if m_stats.get("active_models"):
        typer.echo(f"  • Active models: {', '.join(m_stats['active_models'])}")


@app.command()
def os_plugins():
    """Show loaded plugins and available tools."""
    from godman_ai.os_core import PluginManager
    import json

    typer.echo("🔌 GodmanAI OS Core - Plugin Manager")
    typer.echo("=" * 60)

    pm = PluginManager()
    pm.load_plugins()

    info = pm.get_plugin_info()

    typer.echo(f"\n📦 Loaded Plugins: {len(info['loaded_plugins'])}")
    for plugin in info["loaded_plugins"]:
        typer.echo(f"  • {plugin}")

    typer.echo(f"\n🔧 Plugin Tools: {info['total_tools']}")
    for tool in info["tools"]:
        typer.echo(f"  • {tool}")

    typer.echo(f"\n🤖 Plugin Agents: {info['total_agents']}")
    for agent in info["agents"]:
        typer.echo(f"  • {agent}")

    if not info["loaded_plugins"]:
        typer.echo("\n💡 Tip: Add plugins to godman_ai/plugins/ directory")
        typer.echo("   Run 'godman os-plugins-example' to create a sample plugin")


@app.command()
def server(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    auto_port: bool = typer.Option(True, help="Auto-find available port"),
):
    """Start the GodmanAI API server."""
    from godman_ai.service import run_server

    try:
        run_server(host=host, port=port, auto_port=auto_port)
    except KeyboardInterrupt:
        typer.echo("\n👋 Server stopped")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def tunnel(url: str = typer.Option("http://127.0.0.1:8000", help="Local server URL to tunnel")):
    """
    Start a Cloudflare tunnel to expose the local server publicly.
    Requires cloudflared to be installed.

    Install cloudflared:
      macOS: brew install cloudflare/cloudflare/cloudflared
      Linux: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
    """
    import shutil
    import subprocess

    # Check if cloudflared is installed
    if not shutil.which("cloudflared"):
        typer.echo("❌ cloudflared not found", err=True)
        typer.echo("\n📦 Installation instructions:")
        typer.echo("  macOS:   brew install cloudflare/cloudflare/cloudflared")
        typer.echo(
            "  Linux:   https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        )
        typer.echo(
            "  Windows: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        )
        raise typer.Exit(code=1)

    typer.echo(f"🌐 Starting Cloudflare tunnel to {url}")
    typer.echo("Press Ctrl+C to stop\n")

    try:
        # Run cloudflared tunnel
        subprocess.run(["cloudflared", "tunnel", "--url", url])
    except KeyboardInterrupt:
        typer.echo("\n👋 Tunnel stopped")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def daemon_start():
    """Start the GodmanAI daemon (scheduler + worker)."""
    from godman_ai.service import GodmanDaemon

    daemon = GodmanDaemon()

    try:
        daemon.start()
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def daemon_stop():
    """Stop the GodmanAI daemon."""
    from godman_ai.service import GodmanDaemon

    daemon = GodmanDaemon()

    if not daemon.stop():
        raise typer.Exit(code=1)


@app.command()
def daemon_status():
    """Show daemon status."""
    from godman_ai.service import GodmanDaemon
    import json

    daemon = GodmanDaemon()
    status = daemon.status()

    typer.echo("🔄 GodmanAI Daemon Status")
    typer.echo("=" * 60)
    typer.echo(json.dumps(status, indent=2))


@app.command()
def skills_list():
    """List available skills in the skill store."""
    from godman_ai.service import SkillStore

    store = SkillStore()
    skills = store.list_available()

    typer.echo("🏪 GodmanAI Skill Store")
    typer.echo("=" * 60)
    typer.echo("\n📦 Available Skills:\n")

    for skill in skills:
        typer.echo(f"  • {skill['name']}")
        typer.echo(f"    {skill['description']}")
        typer.echo(f"    Type: {skill.get('type', 'unknown')}\n")

    # Show installed skills
    installed = store.list_installed()
    if installed:
        typer.echo("\n✅ Installed Skills:")
        for skill_name in installed:
            typer.echo(f"  • {skill_name}")


@app.command()
def skills_install(name: str = typer.Argument(..., help="Skill name to install")):
    """Install a skill from the skill store."""
    from godman_ai.service import SkillStore

    store = SkillStore()

    typer.echo(f"📥 Installing skill: {name}")

    if store.install(name):
        typer.echo(f"✅ Skill '{name}' installed successfully")
    else:
        typer.echo(f"❌ Failed to install skill '{name}'", err=True)
        raise typer.Exit(code=1)


@app.command()
def skills_uninstall(name: str = typer.Argument(..., help="Skill name to uninstall")):
    """Uninstall a skill."""
    from godman_ai.service import SkillStore

    store = SkillStore()

    typer.echo(f"🗑️  Uninstalling skill: {name}")

    if store.uninstall(name):
        typer.echo(f"✅ Skill '{name}' uninstalled successfully")
    else:
        typer.echo(f"❌ Failed to uninstall skill '{name}'", err=True)
        raise typer.Exit(code=1)


@app.command()
def skill_new(
    name: str = typer.Argument(..., help="Skill name (hyphenated, e.g., my-custom-tool)"),
    dest: str = typer.Option(".", help="Destination directory"),
    author: str = typer.Option("unknown", help="Author name"),
):
    """
    Create a new skill from template.

    This scaffolds a new skill directory with tool.py, agent.py, and manifest.yaml
    ready for customization.

    Example:
        godman skill new my-ocr-tool --author "Your Name"
    """
    from godman_ai.sdk import SkillBuilder
    from pathlib import Path

    builder = SkillBuilder()
    dest_path = Path(dest)

    try:
        skill_path = builder.create_skill(name, dest_path, author=author)
        typer.echo(f"✅ Skill created: {skill_path}")
        typer.echo(f"\n📁 Structure:")
        typer.echo(f"  {skill_path}/")
        typer.echo(f"  ├── manifest.yaml")
        typer.echo(f"  ├── tool.py")
        typer.echo(f"  ├── agent.py")
        typer.echo(f"  └── __init__.py")
        typer.echo(f"\n💡 Next steps:")
        typer.echo(f"  1. Edit {skill_path}/tool.py to implement your tool")
        typer.echo(f"  2. Update {skill_path}/manifest.yaml with proper metadata")
        typer.echo(f"  3. Run: godman skill validate {skill_path}")
        typer.echo(f"  4. Run: godman skill package {skill_path}")
    except ValueError as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def skill_package(
    path: str = typer.Argument(..., help="Path to skill directory"),
    output: str = typer.Option(None, help="Output directory for .godmanskill file"),
):
    """
    Package a skill into a .godmanskill archive.

    Creates a distributable .godmanskill file that can be installed
    using the skill store or shared with others.

    Example:
        godman skill package ./my-custom-tool
    """
    from godman_ai.sdk import SkillBuilder
    from pathlib import Path

    builder = SkillBuilder()
    skill_path = Path(path)
    output_dir = Path(output) if output else None

    try:
        archive_path = builder.package_skill(skill_path, output_dir)
        typer.echo(f"✅ Skill packaged: {archive_path}")
        typer.echo(f"\n📦 Archive created successfully")
        typer.echo(f"   Size: {archive_path.stat().st_size} bytes")
        typer.echo(f"\n💡 To install this skill:")
        typer.echo(f"   godman skills install {archive_path}")
    except ValueError as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def skill_validate(
    path: str = typer.Argument(..., help="Path to skill directory or .godmanskill file")
):
    """
    Validate a skill's structure and manifest.

    Checks that:
    - manifest.yaml exists and is valid
    - All required fields are present
    - Entrypoint class exists and is importable
    - Tool classes have required methods

    Example:
        godman skill validate ./my-custom-tool
    """
    from godman_ai.sdk import validate_skill
    from pathlib import Path

    skill_path = Path(path)

    typer.echo(f"🔍 Validating skill: {skill_path}")
    typer.echo("=" * 60)

    errors = validate_skill(skill_path)

    if not errors:
        typer.echo("\n✅ Skill is valid!")
        typer.echo("   All checks passed")
        typer.echo("\n💡 Ready to package:")
        typer.echo(f"   godman skill package {skill_path}")
    else:
        typer.echo(f"\n❌ Validation failed with {len(errors)} error(s):\n")
        for i, error in enumerate(errors, 1):
            typer.echo(f"  {i}. {error}")
        typer.echo("\n💡 Fix the errors above and try again")
        raise typer.Exit(code=1)


@app.command()
def store_list():
    """List all skills available in the App Store."""
    from godman_ai.appstore import SkillRegistry

    registry = SkillRegistry()
    skills = registry.list()

    typer.echo("🏪 GodmanAI App Store")
    typer.echo("=" * 60)

    if not skills:
        typer.echo("\n📦 No skills available")
        typer.echo("\n💡 Check back later or add custom registry at ~/.godman/registry/skills.json")
        return

    typer.echo(f"\n📦 Available Skills ({len(skills)}):\n")

    for skill in skills:
        typer.echo(f"  📌 {skill['name']} (v{skill['version']})")
        typer.echo(f"     {skill['description']}")
        tags = skill.get("tags", [])
        if tags:
            typer.echo(f"     Tags: {', '.join(tags)}")
        typer.echo()


@app.command()
def store_search(query: str = typer.Argument(..., help="Search query (name, description, or tag)")):
    """Search for skills in the App Store."""
    from godman_ai.appstore import SkillRegistry

    registry = SkillRegistry()
    results = registry.search(query)

    typer.echo(f"🔍 Search results for '{query}'")
    typer.echo("=" * 60)

    if not results:
        typer.echo("\n❌ No skills found matching your query")
        typer.echo("\n💡 Try a different search term or browse all skills:")
        typer.echo("   godman store list")
        return

    typer.echo(f"\n✅ Found {len(results)} skill(s):\n")

    for skill in results:
        typer.echo(f"  📌 {skill['name']} (v{skill['version']})")
        typer.echo(f"     {skill['description']}")
        tags = skill.get("tags", [])
        if tags:
            typer.echo(f"     Tags: {', '.join(tags)}")
        typer.echo()


@app.command()
def store_install(name: str = typer.Argument(..., help="Skill name to install")):
    """Install a skill from the App Store."""
    from godman_ai.appstore import SkillRegistry, SkillFetcher

    registry = SkillRegistry()
    skill = registry.get(name)

    if not skill:
        typer.echo(f"❌ Skill '{name}' not found in registry", err=True)
        typer.echo("\n💡 Search for available skills:")
        typer.echo("   godman store list")
        typer.echo("   godman store search <query>")
        raise typer.Exit(code=1)

    typer.echo(f"📥 Installing skill: {skill['name']} (v{skill['version']})")
    typer.echo(f"   {skill['description']}")

    # Download the skill
    fetcher = SkillFetcher()

    try:
        url = skill.get("url")
        if not url:
            typer.echo("❌ Skill has no download URL", err=True)
            raise typer.Exit(code=1)

        typer.echo(f"\n⬇️  Downloading from {url}...")
        archive_path = fetcher.download(url, skill.get("sha256"))

        typer.echo(f"✅ Downloaded: {archive_path}")

        # TODO: Install the skill using SkillStore
        # For now, just notify user
        typer.echo("\n⚠️  Note: Automatic installation not yet implemented")
        typer.echo(f"   Archive saved to: {archive_path}")
        typer.echo(f"   Manual installation required")

    except ValueError as e:
        typer.echo(f"❌ Installation failed: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def diagnostics_install(
    pip: str = typer.Option(None, help="Comma-separated pip packages to install"),
    npm: str = typer.Option(None, help="Comma-separated npm packages to install"),
    npm_global: bool = typer.Option(False, help="Install npm packages globally"),
):
    """
    Install dependencies using async subprocess.

    Examples:
        godman diagnostics install --pip "requests,beautifulsoup4"
        godman diagnostics install --npm "typescript" --npm-global
    """
    import asyncio
    from godman_ai.diagnostics import install_all

    pip_packages = [p.strip() for p in pip.split(",")] if pip else None
    npm_packages = [p.strip() for p in npm.split(",")] if npm else None

    if not pip_packages and not npm_packages:
        typer.echo("❌ No packages specified. Use --pip or --npm options", err=True)
        raise typer.Exit(code=1)

    typer.echo("🔧 GodmanAI Dependency Installer")
    typer.echo("=" * 60)

    if pip_packages:
        typer.echo(f"\n📦 Pip packages: {', '.join(pip_packages)}")
    if npm_packages:
        npm_type = "global" if npm_global else "local"
        typer.echo(f"📦 NPM packages ({npm_type}): {', '.join(npm_packages)}")

    typer.echo("\n⏳ Installing packages...\n")

    # Run async function
    result = asyncio.run(
        install_all(pip_packages=pip_packages, npm_packages=npm_packages, npm_global=npm_global)
    )

    # Display results
    typer.echo("\n📊 Installation Results")
    typer.echo("=" * 60)

    if result.get("pip"):
        pip_result = result["pip"]
        if pip_result.get("success"):
            typer.echo(
                f"\n✅ Pip: Successfully installed {len(pip_result.get('installed', []))} packages"
            )
        else:
            typer.echo(f"\n❌ Pip: Installation failed")
            if pip_result.get("stderr"):
                typer.echo(f"   Error: {pip_result['stderr']}")

    if result.get("npm"):
        npm_result = result["npm"]
        if npm_result.get("success"):
            typer.echo(
                f"\n✅ NPM: Successfully installed {len(npm_result.get('installed', []))} packages"
            )
        else:
            typer.echo(f"\n❌ NPM: Installation failed")
            if npm_result.get("error"):
                typer.echo(f"   Error: {npm_result['error']}")

    if result.get("errors"):
        typer.echo(f"\n⚠️  Errors encountered:")
        for error in result["errors"]:
            typer.echo(f"   • {error}")

    if not result.get("success"):
        raise typer.Exit(code=1)


@app.command()
def diagnostics_health(
    openai: bool = typer.Option(True, help="Check OpenAI API"),
    google: bool = typer.Option(True, help="Check Google Generative AI"),
    anthropic: bool = typer.Option(False, help="Check Anthropic API"),
):
    """
    Run LLM health checks using async subprocess.

    Examples:
        godman diagnostics health
        godman diagnostics health --no-openai --anthropic
    """
    import asyncio
    from godman_ai.diagnostics import run_llm_health_check
    import json

    typer.echo("🏥 GodmanAI LLM Health Check")
    typer.echo("=" * 60)
    typer.echo("\n⏳ Running health checks...\n")

    # Run async health check
    result = asyncio.run(
        run_llm_health_check(check_openai=openai, check_google=google, check_anthropic=anthropic)
    )

    # Display results
    typer.echo("📊 Health Check Results")
    typer.echo("=" * 60)

    # Overall status
    status_icon = (
        "✅"
        if result["overall_status"] == "healthy"
        else "⚠️" if result["overall_status"] == "degraded" else "❌"
    )
    typer.echo(f"\n{status_icon} Overall Status: {result['overall_status'].upper()}")
    typer.echo(f"⏱️  Execution Time: {result['execution_time_ms']}ms")

    # Python info
    if result.get("python_info"):
        typer.echo(f"\n🐍 Python Environment:")
        typer.echo(f"   Version: {result['python_info'].get('python_version', 'N/A').split()[0]}")
        typer.echo(f"   Platform: {result['python_info'].get('platform', 'N/A')}")

    # Service checks
    if result.get("services"):
        typer.echo(f"\n🤖 LLM Services:")
        for service_name, service_result in result["services"].items():
            if service_result.get("available"):
                typer.echo(
                    f"   ✅ {service_name.upper()}: Available ({service_result.get('response_time_ms', 0)}ms)"
                )
                if service_result.get("models_count"):
                    typer.echo(f"      Models: {service_result['models_count']}")
            else:
                typer.echo(f"   ❌ {service_name.upper()}: Unavailable")
                if service_result.get("error"):
                    typer.echo(f"      Error: {service_result['error']}")

    # Summary
    summary = result.get("summary", {})
    typer.echo(f"\n📈 Summary:")
    typer.echo(f"   Total Services: {summary.get('total_services', 0)}")
    typer.echo(f"   Available: {summary.get('available_services', 0)}")
    typer.echo(f"   Unavailable: {summary.get('unavailable_services', 0)}")

    # Exit with error if critical
    if result["overall_status"] == "critical":
        raise typer.Exit(code=1)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
