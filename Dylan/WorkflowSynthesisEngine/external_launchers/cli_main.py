"""
Command-line interface for the script launcher using Click and Rich.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))

from core import (
    get_engine, get_registry, ScriptMetadata, ScriptParameter,
    ParameterManager, get_logger
)

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Script Launcher Pro - Production-ready Python script launcher.
    
    Manage and execute Python scripts with parameter configuration,
    real-time monitoring, and comprehensive logging.
    """
    pass


@cli.command()
@click.option('--enabled-only', is_flag=True, help='Show only enabled scripts')
@click.option('--tag', help='Filter by tag')
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def list(enabled_only, tag, format):
    """List all registered scripts."""
    registry = get_registry()
    
    if tag:
        scripts = registry.get_scripts_by_tag(tag)
    elif enabled_only:
        scripts = registry.get_enabled_scripts()
    else:
        scripts = registry.get_all_scripts()
    
    if format == 'json':
        # JSON output for agents
        data = [
            {
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'enabled': s.enabled,
                'tags': s.tags,
                'run_count': s.run_count,
                'success_count': s.success_count
            }
            for s in scripts
        ]
        console.print_json(json.dumps(data, indent=2))
    else:
        # Table output for humans
        table = Table(title=f"📋 Registered Scripts ({len(scripts)})")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Tags", style="yellow")
        table.add_column("Runs", justify="right")
        table.add_column("Success Rate", justify="right")
        
        for script in sorted(scripts, key=lambda s: s.name):
            status = "✓" if script.enabled else "✗"
            tags = ", ".join(script.tags[:3]) if script.tags else "-"
            success_rate = (
                f"{(script.success_count / script.run_count * 100):.0f}%"
                if script.run_count > 0
                else "-"
            )
            
            table.add_row(
                script.id[:8],
                script.name,
                status,
                tags,
                str(script.run_count),
                success_rate
            )
        
        console.print(table)


@cli.command()
@click.argument('script_id')
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
def info(script_id, format):
    """Show detailed information about a script."""
    registry = get_registry()
    script = registry.get_script(script_id)
    
    if not script:
        console.print(f"[red]Error:[/red] Script not found: {script_id}")
        sys.exit(1)
    
    if format == 'json':
        data = {
            'id': script.id,
            'name': script.name,
            'path': script.path,
            'description': script.description,
            'parameters': [
                {
                    'name': p.name,
                    'type': p.type,
                    'description': p.description,
                    'required': p.required,
                    'default': p.default
                }
                for p in script.parameters
            ],
            'tags': script.tags,
            'author': script.author,
            'version': script.version,
            'enabled': script.enabled,
            'run_count': script.run_count,
            'success_count': script.success_count,
            'failure_count': script.failure_count
        }
        console.print_json(json.dumps(data, indent=2))
    else:
        # Rich formatted output
        info_text = f"""
[bold cyan]Name:[/bold cyan] {script.name}
[bold cyan]ID:[/bold cyan] {script.id}
[bold cyan]Version:[/bold cyan] {script.version}
[bold cyan]Author:[/bold cyan] {script.author or 'Unknown'}
[bold cyan]Status:[/bold cyan] {'✓ Enabled' if script.enabled else '✗ Disabled'}

[bold cyan]Description:[/bold cyan]
{script.description}

[bold cyan]Path:[/bold cyan] {script.path}
[bold cyan]Tags:[/bold cyan] {', '.join(script.tags) if script.tags else 'None'}

[bold cyan]Statistics:[/bold cyan]
  Total Runs: {script.run_count}
  Successful: {script.success_count} ✓
  Failed: {script.failure_count} ✗
"""
        
        if script.last_run:
            info_text += f"  Last Run: {script.last_run}\n"
        
        console.print(Panel(info_text, title=f"Script Info: {script.name}", border_style="cyan"))
        
        # Parameters table
        if script.parameters:
            param_table = Table(title="Parameters")
            param_table.add_column("Name", style="bold")
            param_table.add_column("Type", style="cyan")
            param_table.add_column("Required", justify="center")
            param_table.add_column("Default")
            param_table.add_column("Description")
            
            for param in script.parameters:
                param_table.add_row(
                    param.name,
                    param.type,
                    "✓" if param.required else "",
                    str(param.default) if param.default is not None else "-",
                    param.description
                )
            
            console.print(param_table)


@cli.command()
@click.argument('script_id')
@click.option('--param', '-p', multiple=True, help='Parameter in format name=value')
@click.option('--preset', help='Load parameter preset')
@click.option('--async', 'async_mode', is_flag=True, help='Execute in background')
@click.option('--no-output', is_flag=True, help='Suppress output')
def launch(script_id, param, preset, async_mode, no_output):
    """Launch a registered script."""
    engine = get_engine()
    registry = get_registry()
    param_manager = ParameterManager()
    
    # Get script
    script = registry.get_script(script_id)
    if not script:
        console.print(f"[red]Error:[/red] Script not found: {script_id}")
        sys.exit(1)
    
    # Parse parameters
    parameters = {}
    
    # Load preset if specified
    if preset:
        preset_values = param_manager.load_parameter_preset(preset, script_id)
        if preset_values:
            parameters.update(preset_values)
        else:
            console.print(f"[yellow]Warning:[/yellow] Preset not found: {preset}")
    
    # Parse command-line parameters
    for p in param:
        if '=' not in p:
            console.print(f"[red]Error:[/red] Invalid parameter format: {p}")
            console.print("Use format: --param name=value")
            sys.exit(1)
        
        name, value = p.split('=', 1)
        parameters[name] = value
    
    # Launch
    console.print(f"[cyan]Launching script:[/cyan] {script.name}")
    
    if async_mode:
        # Async execution
        result = engine.launch_script(script_id, parameters, async_mode=True)
        console.print("[green]✓[/green] Script launched in background")
    else:
        # Sync execution with live output
        def output_callback(stream_name: str, line: str):
            if not no_output:
                if stream_name == 'stdout':
                    console.print(line)
                else:
                    console.print(f"[red]{line}[/red]")
        
        with console.status("[bold green]Executing...", spinner="dots"):
            result = engine.launch_script(
                script_id,
                parameters,
                output_callback=output_callback if not no_output else None,
                async_mode=False
            )
        
        # Display results
        if result.is_success():
            console.print("\n[green]✓ Execution completed successfully[/green]")
        else:
            console.print("\n[red]✗ Execution failed[/red]")
            if result.error_message:
                console.print(f"[red]Error:[/red] {result.error_message}")
        
        # Display metrics
        if result.metrics:
            metrics_text = f"""
[bold]Execution Metrics:[/bold]
  Duration: {result.metrics.duration:.2f}s
  Exit Code: {result.exit_code}
  Peak Memory: {result.metrics.peak_memory_mb:.1f} MB
"""
            if result.metrics.cpu_percent:
                avg_cpu = sum(result.metrics.cpu_percent) / len(result.metrics.cpu_percent)
                metrics_text += f"  Avg CPU: {avg_cpu:.1f}%\n"
            
            console.print(Panel(metrics_text, border_style="cyan"))
        
        sys.exit(0 if result.is_success() else 1)


@cli.command()
@click.argument('script_path')
@click.argument('args', nargs=-1)
def quick(script_path, args):
    """Quick launch a script without registration."""
    engine = get_engine()
    
    console.print(f"[cyan]Quick launching:[/cyan] {script_path}")
    
    def output_callback(stream_name: str, line: str):
        if stream_name == 'stdout':
            console.print(line)
        else:
            console.print(f"[red]{line}[/red]")
    
    result = engine.quick_launch(
        script_path,
        list(args),
        output_callback=output_callback
    )
    
    if result.is_success():
        console.print("\n[green]✓ Execution completed successfully[/green]")
        sys.exit(0)
    else:
        console.print("\n[red]✗ Execution failed[/red]")
        if result.error_message:
            console.print(f"[red]Error:[/red] {result.error_message}")
        sys.exit(1)


@cli.command()
@click.option('--limit', default=20, help='Number of entries to show')
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def history(limit, format):
    """Show execution history."""
    engine = get_engine()
    history_data = engine.get_execution_history(limit=limit)
    
    if format == 'json':
        console.print_json(json.dumps(history_data, indent=2))
    else:
        table = Table(title=f"📜 Execution History (Last {len(history_data)})")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Script", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Exit Code", justify="center")
        
        for entry in reversed(history_data):
            status_icon = "✓" if entry['status'] == 'completed' and entry['exit_code'] == 0 else "✗"
            status_color = "green" if status_icon == "✓" else "red"
            
            duration_str = f"{entry['duration']:.2f}s" if entry['duration'] else "-"
            exit_code_str = str(entry['exit_code']) if entry['exit_code'] is not None else "-"
            
            table.add_row(
                entry['timestamp'][:19],
                entry['script_name'],
                f"[{status_color}]{status_icon}[/{status_color}]",
                duration_str,
                exit_code_str
            )
        
        console.print(table)


@cli.command()
def interactive():
    """Start interactive mode."""
    from .interactive_mode import start_interactive
    start_interactive()


@cli.command()
def api():
    """Start the REST API server."""
    console.print("[cyan]Starting API server...[/cyan]")
    console.print("[green]API will be available at:[/green] http://localhost:8000")
    console.print("[green]API documentation:[/green] http://localhost:8000/docs")
    
    import uvicorn
    from api.rest_api import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


@cli.command()
def gui():
    """Start the GUI application."""
    console.print("[cyan]Starting GUI...[/cyan]")
    
    from gui import main
    main()


if __name__ == '__main__':
    cli()

