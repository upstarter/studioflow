"""
Health Dashboard Commands
Project health monitoring and status
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.columns import Columns
from rich import box

from studioflow.core.project_health import ProjectHealthChecker, HealthStatus
from studioflow.core.state import StateManager

console = Console()
app = typer.Typer()


@app.command()
def status(
    project_name: Optional[str] = typer.Option(None, "--project", "-p", help="Project name"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
):
    """Show project health dashboard"""
    
    checker = ProjectHealthChecker()
    health = checker.check_health(project_name)
    
    # Header
    status_colors = {
        HealthStatus.EXCELLENT: "green",
        HealthStatus.GOOD: "green",
        HealthStatus.WARNING: "yellow",
        HealthStatus.ERROR: "red",
        HealthStatus.UNKNOWN: "dim"
    }
    
    status_color = status_colors.get(health.overall_status, "white")
    status_icons = {
        HealthStatus.EXCELLENT: "✨",
        HealthStatus.GOOD: "✓",
        HealthStatus.WARNING: "⚠️",
        HealthStatus.ERROR: "❌",
        HealthStatus.UNKNOWN: "❓"
    }
    
    icon = status_icons.get(health.overall_status, "❓")
    
    console.print(Panel.fit(
        f"[bold {status_color}]{icon} {health.overall_status.value.upper()}[/bold {status_color}]\n"
        f"Project: [cyan]{health.project_name}[/cyan]\n"
        f"Path: {health.project_path}",
        title="Project Health",
        border_style=status_color
    ))
    
    # Health checks table
    console.print("\n[bold]Health Checks:[/bold]\n")
    
    table = Table(show_header=True, box=box.ROUNDED)
    table.add_column("Check", style="cyan", width=25)
    table.add_column("Status", width=12)
    table.add_column("Message", style="white")
    table.add_column("Action", style="dim", width=30)
    
    for check in sorted(health.checks, key=lambda c: c.priority, reverse=True):
        status_icon = {
            HealthStatus.EXCELLENT: "✨",
            HealthStatus.GOOD: "✓",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.ERROR: "❌"
        }.get(check.status, "❓")
        
        table.add_row(
            check.name,
            f"{status_icon} {check.status.value.title()}",
            check.message,
            check.action or "-"
        )
    
    console.print(table)
    
    # Next steps
    if health.next_steps:
        console.print("\n[bold]Next Steps:[/bold]")
        for i, step in enumerate(health.next_steps, 1):
            console.print(f"  {i}. [cyan]{step}[/cyan]")
    
    # Detailed stats
    if detailed:
        console.print("\n[bold]Detailed Statistics:[/bold]\n")
        
        # Media stats
        if health.media_stats:
            console.print("[cyan]Media:[/cyan]")
            console.print(f"  Files: {health.media_stats.get('file_count', 0)}")
            console.print(f"  Size: {health.media_stats.get('total_size_gb', 0):.2f} GB")
        
        # Resolve stats
        if health.resolve_status:
            console.print("\n[cyan]Resolve:[/cyan]")
            console.print(f"  Connected: {'Yes' if health.resolve_status.get('connected') else 'No'}")
            console.print(f"  Project Synced: {'Yes' if health.resolve_status.get('project_exists') else 'No'}")


@app.command()
def quick():
    """Quick dashboard overview"""
    
    from studioflow.core.config import get_config
    
    state = StateManager()
    config = get_config()
    
    # Create compact dashboard
    layout = Layout()
    
    # Header
    current_project = state.current_project or "None"
    console.print(f"[bold cyan]StudioFlow Dashboard[/bold cyan]\n")
    
    # Quick stats in columns
    checker = ProjectHealthChecker()
    health = checker.check_health()
    
    columns = []
    
    # Project status
    status_color = {
        HealthStatus.EXCELLENT: "green",
        HealthStatus.GOOD: "green",
        HealthStatus.WARNING: "yellow",
        HealthStatus.ERROR: "red"
    }.get(health.overall_status, "dim")
    
    columns.append(Panel(
        f"[bold]Project[/bold]\n"
        f"{health.project_name}\n"
        f"[{status_color}]{health.overall_status.value.title()}[/{status_color}]",
        border_style=status_color
    ))
    
    # Media stats
    media_info = f"Files: {health.media_stats.get('file_count', 0)}\n"
    media_info += f"Size: {health.media_stats.get('total_size_gb', 0):.1f} GB"
    
    columns.append(Panel(
        f"[bold]Media[/bold]\n{media_info}",
        border_style="cyan"
    ))
    
    # Issues count
    issues = len(health.errors) + len(health.warnings)
    issue_color = "red" if health.errors else "yellow" if health.warnings else "green"
    
    columns.append(Panel(
        f"[bold]Issues[/bold]\n"
        f"[red]Errors: {len(health.errors)}[/red]\n"
        f"[yellow]Warnings: {len(health.warnings)}[/yellow]",
        border_style=issue_color
    ))
    
    console.print(Columns(columns))
    
    # Quick actions
    if health.next_steps:
        console.print("\n[bold]Quick Actions:[/bold]")
        for i, step in enumerate(health.next_steps[:3], 1):
            console.print(f"  {i}. {step}")


if __name__ == "__main__":
    app()


