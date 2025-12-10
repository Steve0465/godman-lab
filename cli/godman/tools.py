"""
CLI commands for ToolRunner execution

Provides Typer commands to execute registered tools from the command line.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from libs.tool_runner import ToolRunner, runner as global_runner


app = typer.Typer(help="Execute and manage registered tools")
console = Console()


def format_json(data: dict) -> str:
    """Format dictionary as pretty JSON"""
    return json.dumps(data, indent=2, default=str)


def print_result(result: dict, verbose: bool = False):
    """Pretty print tool execution result"""
    status = result["status"]
    
    # Status badge
    if status == "success":
        console.print(f"[bold green]✓ SUCCESS[/bold green]")
    else:
        console.print(f"[bold red]✗ ERROR[/bold red]")
    
    # Result panel
    if result["result"]:
        result_json = format_json(result["result"])
        syntax = Syntax(result_json, "json", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title="Result", border_style="green"))
    
    # Error panel
    if result["error"]:
        error_json = format_json(result["error"])
        syntax = Syntax(error_json, "json", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title="Error", border_style="red"))
    
    # Metadata
    if verbose:
        console.print(f"\n[dim]Execution time: {result['execution_time']}s[/dim]")
        console.print(f"[dim]Timestamp: {result['timestamp']}[/dim]")


@app.command("run")
def run_tool(
    name: str = typer.Option(..., "--name", "-n", help="Name of the registered tool to execute"),
    params: str = typer.Option("{}", "--params", "-p", help="Tool parameters as JSON string"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed execution info"),
    runner_path: Optional[str] = typer.Option(None, "--runner", help="Path to custom runner module")
):
    """
    Execute a registered tool by name with JSON parameters.
    
    Examples:
    
      # Run a simple tool
      godman tool run --name greet --params '{"name": "Alice", "count": 2}'
    
      # Run with short flags
      godman tool run -n add -p '{"x": 5, "y": 3}'
    
      # Run command-based tool
      godman tool run -n list_files -p '{"path": "."}'
    
      # Verbose output
      godman tool run -n calculate -p '{"value": 42}' --verbose
    """
    try:
        # Parse parameters
        try:
            parameters = json.loads(params)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON in --params: {e}[/red]")
            raise typer.Exit(1)
        
        # Execute tool
        if verbose:
            console.print(f"\n[bold]Executing:[/bold] {name}")
            console.print(f"[bold]Parameters:[/bold] {format_json(parameters)}\n")
        
        result = global_runner.run(name, parameters)
        
        # Print result
        print_result(result, verbose=verbose)
        
        # Exit with appropriate code
        sys.exit(0 if result["status"] == "success" else 1)
        
    except Exception as e:
        console.print(f"[red]Execution failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_tools(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed tool information")
):
    """
    List all registered tools.
    
    Examples:
    
      # List all tools
      godman tool list
    
      # List with detailed info
      godman tool list --verbose
    """
    tools = global_runner.list_tools()
    
    if not tools:
        console.print("[yellow]No tools registered[/yellow]")
        return
    
    console.print(f"\n[bold]Registered Tools:[/bold] {len(tools)}\n")
    
    if verbose:
        # Detailed view
        for name, info in tools.items():
            console.print(f"[bold cyan]{name}[/bold cyan]")
            console.print(f"  Description: {info['description'] or '[dim]No description[/dim]'}")
            console.print(f"  Schema: {format_json(info['schema'])}")
            console.print(f"  Command-based: {info['has_command']}")
            console.print()
    else:
        # Table view
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Tool Name", style="cyan")
        table.add_column("Description")
        table.add_column("Parameters", style="dim")
        table.add_column("Type", justify="center")
        
        for name, info in tools.items():
            desc = info['description'][:50] + "..." if len(info['description']) > 50 else info['description']
            params = ", ".join(info['schema'].keys()) or "[dim]none[/dim]"
            tool_type = "CMD" if info['has_command'] else "PY"
            table.add_row(name, desc, params, tool_type)
        
        console.print(table)


@app.command("info")
def tool_info(
    name: str = typer.Argument(..., help="Name of the tool")
):
    """
    Get detailed information about a specific tool.
    
    Examples:
    
      # Get tool info
      godman tool info greet
    
      # Get info for command-based tool
      godman tool info list_files
    """
    info = global_runner.get_tool_info(name)
    
    if not info:
        console.print(f"[red]Tool '{name}' not found[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold cyan]{info['name']}[/bold cyan]\n")
    
    # Description
    if info['description']:
        console.print(Panel(info['description'], title="Description", border_style="blue"))
    
    # Schema
    if info['schema']:
        schema_json = format_json(info['schema'])
        syntax = Syntax(schema_json, "json", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title="Parameter Schema", border_style="green"))
    
    # Command
    if info['command']:
        console.print(Panel(info['command'], title="Command Template", border_style="yellow"))
    
    # Type
    tool_type = "Command-based" if info['has_command'] else "Python function"
    console.print(f"\n[dim]Type: {tool_type}[/dim]")


@app.command("example")
def show_examples():
    """
    Show example usage of the tool command.
    
    Examples:
    
      # Show examples
      godman tool example
    """
    examples = """
[bold]Tool Command Examples[/bold]

[cyan]1. Register and run a simple tool:[/cyan]

   # In Python code:
   from libs.tool_runner import tool
   
   @tool(schema={"name": str, "age": int})
   def create_user(name: str, age: int):
       return {"user": name, "age": age}
   
   # From CLI:
   godman tool run -n create_user -p '{"name": "Alice", "age": 30}'

[cyan]2. Register a command-based tool:[/cyan]

   # In Python code:
   @tool(schema={"path": str}, command="ls -la {path}")
   def list_files(path: str):
       pass
   
   # From CLI:
   godman tool run -n list_files -p '{"path": "."}'

[cyan]3. List all registered tools:[/cyan]

   godman tool list
   godman tool list --verbose

[cyan]4. Get tool information:[/cyan]

   godman tool info create_user

[cyan]5. Complex parameters:[/cyan]

   godman tool run -n process_data -p '{
     "data": [1, 2, 3, 4, 5],
     "operation": "sum",
     "filter": true
   }'

[cyan]6. Check execution logs:[/cyan]

   tail -f ~/godman-lab/logs/tool_runner.log

[bold]Tips:[/bold]
- Always quote JSON parameters with single quotes
- Use --verbose flag for detailed execution info
- Tools are registered at import time
- Check logs for debugging
"""
    console.print(examples)


if __name__ == "__main__":
    app()
