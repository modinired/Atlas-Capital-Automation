"""
Interactive terminal UI mode with Rich.
"""

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core import get_engine, get_registry, ParameterManager

console = Console()


def start_interactive():
    """Start interactive mode."""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Script Launcher Pro[/bold cyan]\n"
        "Interactive Mode",
        border_style="cyan"
    ))
    
    engine = get_engine()
    registry = get_registry()
    param_manager = ParameterManager()
    
    while True:
        console.print("\n[bold]Main Menu:[/bold]")
        console.print("1. List scripts")
        console.print("2. Launch script")
        console.print("3. View script details")
        console.print("4. Quick launch")
        console.print("5. View history")
        console.print("6. Exit")
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == "1":
            _list_scripts_interactive(registry)
        
        elif choice == "2":
            _launch_script_interactive(engine, registry, param_manager)
        
        elif choice == "3":
            _view_script_details(registry)
        
        elif choice == "4":
            _quick_launch_interactive(engine)
        
        elif choice == "5":
            _view_history(engine)
        
        elif choice == "6":
            console.print("[cyan]Goodbye![/cyan]")
            break


def _list_scripts_interactive(registry):
    """List scripts interactively."""
    scripts = registry.get_all_scripts()
    
    if not scripts:
        console.print("[yellow]No scripts registered[/yellow]")
        return
    
    table = Table(title=f"📋 Registered Scripts ({len(scripts)})")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Name", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Description")
    
    for idx, script in enumerate(sorted(scripts, key=lambda s: s.name), 1):
        status = "✓" if script.enabled else "✗"
        table.add_row(
            str(idx),
            script.name,
            status,
            script.description[:60] + "..." if len(script.description) > 60 else script.description
        )
    
    console.print(table)


def _launch_script_interactive(engine, registry, param_manager):
    """Launch a script interactively."""
    scripts = registry.get_enabled_scripts()
    
    if not scripts:
        console.print("[yellow]No enabled scripts available[/yellow]")
        return
    
    # Display scripts
    table = Table(title="Select Script to Launch")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Name", style="bold")
    table.add_column("Parameters", justify="center")
    
    for idx, script in enumerate(sorted(scripts, key=lambda s: s.name), 1):
        table.add_row(
            str(idx),
            script.name,
            str(len(script.parameters))
        )
    
    console.print(table)
    
    # Select script
    try:
        choice = int(Prompt.ask("Select script number"))
        if choice < 1 or choice > len(scripts):
            console.print("[red]Invalid selection[/red]")
            return
    except ValueError:
        console.print("[red]Invalid input[/red]")
        return
    
    script = sorted(scripts, key=lambda s: s.name)[choice - 1]
    
    # Get parameters
    parameters = {}
    if script.parameters:
        console.print(f"\n[bold]Configure parameters for {script.name}:[/bold]")
        
        for param in script.parameters:
            desc = f"{param.name} ({param.type})"
            if param.required:
                desc += " [required]"
            if param.default is not None:
                desc += f" [default: {param.default}]"
            
            console.print(f"\n[cyan]{desc}[/cyan]")
            console.print(f"  {param.description}")
            
            if param.type == 'bool':
                value = Confirm.ask(f"  Enable {param.name}", default=param.default or False)
            else:
                default_str = str(param.default) if param.default is not None else ""
                value = Prompt.ask(f"  Value", default=default_str)
                
                if not value and param.required:
                    console.print("[red]This parameter is required[/red]")
                    return
            
            if value:
                parameters[param.name] = value
    
    # Confirm launch
    if not Confirm.ask(f"\nLaunch {script.name}?", default=True):
        console.print("[yellow]Launch cancelled[/yellow]")
        return
    
    # Launch
    console.print(f"\n[cyan]Launching {script.name}...[/cyan]\n")
    
    def output_callback(stream_name: str, line: str):
        if stream_name == 'stdout':
            console.print(line)
        else:
            console.print(f"[red]{line}[/red]")
    
    with console.status("[bold green]Executing...", spinner="dots"):
        result = engine.launch_script(
            script.id,
            parameters,
            output_callback=output_callback,
            async_mode=False
        )
    
    # Display results
    if result.is_success():
        console.print("\n[green]✓ Execution completed successfully[/green]")
    else:
        console.print("\n[red]✗ Execution failed[/red]")
    
    if result.metrics:
        console.print(f"Duration: {result.metrics.duration:.2f}s")
        console.print(f"Peak Memory: {result.metrics.peak_memory_mb:.1f} MB")
    
    Prompt.ask("\nPress Enter to continue")


def _view_script_details(registry):
    """View script details."""
    scripts = registry.get_all_scripts()
    
    if not scripts:
        console.print("[yellow]No scripts registered[/yellow]")
        return
    
    # Display scripts
    table = Table(title="Select Script")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Name", style="bold")
    
    for idx, script in enumerate(sorted(scripts, key=lambda s: s.name), 1):
        table.add_row(str(idx), script.name)
    
    console.print(table)
    
    # Select script
    try:
        choice = int(Prompt.ask("Select script number"))
        if choice < 1 or choice > len(scripts):
            console.print("[red]Invalid selection[/red]")
            return
    except ValueError:
        console.print("[red]Invalid input[/red]")
        return
    
    script = sorted(scripts, key=lambda s: s.name)[choice - 1]
    
    # Display details
    info_text = f"""
[bold cyan]Name:[/bold cyan] {script.name}
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
    
    console.print(Panel(info_text, title=f"Script Details", border_style="cyan"))
    
    if script.parameters:
        param_table = Table(title="Parameters")
        param_table.add_column("Name", style="bold")
        param_table.add_column("Type", style="cyan")
        param_table.add_column("Required", justify="center")
        param_table.add_column("Description")
        
        for param in script.parameters:
            param_table.add_row(
                param.name,
                param.type,
                "✓" if param.required else "",
                param.description
            )
        
        console.print(param_table)
    
    Prompt.ask("\nPress Enter to continue")


def _quick_launch_interactive(engine):
    """Quick launch a script."""
    script_path = Prompt.ask("Enter script path")
    
    if not Path(script_path).exists():
        console.print("[red]Script file not found[/red]")
        return
    
    console.print(f"\n[cyan]Quick launching {script_path}...[/cyan]\n")
    
    def output_callback(stream_name: str, line: str):
        if stream_name == 'stdout':
            console.print(line)
        else:
            console.print(f"[red]{line}[/red]")
    
    result = engine.quick_launch(script_path, [], output_callback=output_callback)
    
    if result.is_success():
        console.print("\n[green]✓ Execution completed successfully[/green]")
    else:
        console.print("\n[red]✗ Execution failed[/red]")
    
    Prompt.ask("\nPress Enter to continue")


def _view_history(engine):
    """View execution history."""
    history_data = engine.get_execution_history(limit=20)
    
    if not history_data:
        console.print("[yellow]No execution history[/yellow]")
        Prompt.ask("\nPress Enter to continue")
        return
    
    table = Table(title=f"📜 Execution History (Last {len(history_data)})")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Script", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Duration", justify="right")
    
    for entry in reversed(history_data):
        status_icon = "✓" if entry['status'] == 'completed' and entry['exit_code'] == 0 else "✗"
        status_color = "green" if status_icon == "✓" else "red"
        duration_str = f"{entry['duration']:.2f}s" if entry['duration'] else "-"
        
        table.add_row(
            entry['timestamp'][:19],
            entry['script_name'],
            f"[{status_color}]{status_icon}[/{status_color}]",
            duration_str
        )
    
    console.print(table)
    Prompt.ask("\nPress Enter to continue")

