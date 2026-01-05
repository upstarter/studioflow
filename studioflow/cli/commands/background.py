"""
Background Services CLI Command
Manage auto-transcription and auto-rough-cut services
"""

import typer
import signal
import sys
import time
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout

from studioflow.core.background_services import BackgroundServices
from studioflow.core.state import StateManager
from studioflow.core.project import ProjectManager

state = StateManager()

console = Console()
app = typer.Typer()

# Global service instance
_service_instance: Optional[BackgroundServices] = None


def _get_service() -> BackgroundServices:
    """Get or create background service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = BackgroundServices(max_workers=4)
    return _service_instance


@app.command()
def start(
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project to watch (defaults to current)"),
    max_workers: int = typer.Option(4, "--workers", help="Number of parallel transcription workers"),
    daemon: bool = typer.Option(False, "--daemon", help="Run as daemon (background process)")
):
    """
    Start background services (auto-transcription and auto-rough-cut)
    
    Watches project footage directories and automatically:
    - Transcribes new video files
    - Generates rough cuts when all files are transcribed
    """
    service = BackgroundServices(max_workers=max_workers)
    
    # Get project to watch
    project_name = project or state.current_project
    if not project_name:
        console.print("[red]No project specified. Use --project or 'sf project select'[/red]")
        raise typer.Exit(1)
    
    manager = ProjectManager()
    proj = manager.get_project(project_name)
    if not proj:
        console.print(f"[red]Project not found: {project_name}[/red]")
        raise typer.Exit(1)
    
    # Start watching project
    footage_dir = proj.path / "01_footage"
    service.watch_project(proj.path, footage_dir)
    
    # Start service
    service.start()
    
    console.print(f"[green]✓[/green] Background services started")
    console.print(f"  Watching: {project_name}")
    console.print(f"  Workers: {max_workers}")
    console.print(f"  Footage dir: {footage_dir}")
    
    if daemon:
        console.print("\n[yellow]Running as daemon. Press Ctrl+C to stop.[/yellow]")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping services...[/yellow]")
            service.stop()
            console.print("[green]✓ Services stopped[/green]")
    else:
        # Interactive mode with live status
        console.print("\n[yellow]Press Ctrl+C to stop and view status[/yellow]\n")
        
        def handle_signal(sig, frame):
            service.stop()
            console.print("\n[green]✓ Services stopped[/green]")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_signal)
        
        try:
            with Live(console=console, refresh_per_second=2) as live:
                while service.running:
                    status = service.get_status()
                    status_table = _create_status_table(status)
                    live.update(status_table)
                    time.sleep(0.5)
        except KeyboardInterrupt:
            handle_signal(None, None)


@app.command()
def stop():
    """Stop background services"""
    global _service_instance
    if _service_instance and _service_instance.running:
        _service_instance.stop()
        console.print("[green]✓ Background services stopped[/green]")
    else:
        console.print("[yellow]No running services found[/yellow]")


@app.command()
def status():
    """Show status of background services"""
    service = _get_service()
    status = service.get_status()
    
    console.print(Panel(
        _create_status_table(status),
        title="Background Services Status",
        border_style="cyan"
    ))
    
    # Show job details if available
    if status['running']:
        details = service.get_job_details()
        
        if details['transcription_jobs']:
            console.print("\n[bold]Recent Transcription Jobs:[/bold]")
            table = Table(show_header=True, header_style="cyan")
            table.add_column("File")
            table.add_column("Status")
            table.add_column("Error")
            
            for job in details['transcription_jobs'][-10:]:  # Last 10 jobs
                table.add_row(
                    Path(job['video_file']).name,
                    job['status'],
                    job.get('error', '-')[:50] if job.get('error') else '-'
                )
            console.print(table)
        
        if details['rough_cut_jobs']:
            console.print("\n[bold]Rough Cut Jobs:[/bold]")
            table = Table(show_header=True, header_style="cyan")
            table.add_column("Directory")
            table.add_column("Status")
            table.add_column("EDL Path")
            table.add_column("Error")
            
            for job in details['rough_cut_jobs']:
                edl_path = job.get('edl_path', '-')
                if edl_path != '-':
                    edl_path = Path(edl_path).name
                table.add_row(
                    Path(job['footage_dir']).name,
                    job['status'],
                    edl_path,
                    job.get('error', '-')[:50] if job.get('error') else '-'
                )
            console.print(table)


def _create_status_table(status: dict) -> Table:
    """Create status table for display"""
    table = Table(show_header=False, box=None, padding=(0, 2))
    
    table.add_row("[bold]Status:[/bold]", "[green]Running[/green]" if status['running'] else "[red]Stopped[/red]")
    table.add_row("[bold]Watched Projects:[/bold]", str(status['watched_projects']))
    table.add_row("", "")
    
    # Transcription status
    trans = status['transcription']
    table.add_row("[bold cyan]Transcription:[/bold cyan]", "")
    table.add_row("  Pending:", str(trans['pending']))
    table.add_row("  Running:", str(trans['running']))
    table.add_row("  Completed:", f"[green]{trans['completed']}[/green]")
    table.add_row("  Failed:", f"[red]{trans['failed']}[/red]")
    table.add_row("  Queue:", str(status['queue_sizes']['transcription']))
    table.add_row("", "")
    
    # Rough cut status
    rc = status['rough_cut']
    table.add_row("[bold cyan]Rough Cut:[/bold cyan]", "")
    table.add_row("  Pending:", str(rc['pending']))
    table.add_row("  Running:", str(rc['running']))
    table.add_row("  Completed:", f"[green]{rc['completed']}[/green]")
    table.add_row("  Failed:", f"[red]{rc['failed']}[/red]")
    table.add_row("  Queue:", str(status['queue_sizes']['rough_cut']))
    
    return table


@app.command()
def watch(
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project to watch"),
    footage_dir: Optional[Path] = typer.Option(None, "--footage-dir", help="Footage directory path")
):
    """Add a project to watch list"""
    service = _get_service()
    
    project_name = project or state.current_project
    if not project_name:
        console.print("[red]No project specified. Use --project or 'sf project select'[/red]")
        raise typer.Exit(1)
    
    manager = ProjectManager()
    proj = manager.get_project(project_name)
    if not proj:
        console.print(f"[red]Project not found: {project_name}[/red]")
        raise typer.Exit(1)
    
    if footage_dir:
        footage_path = Path(footage_dir)
    else:
        footage_path = proj.path / "01_footage"
    
    service.watch_project(proj.path, footage_path)
    console.print(f"[green]✓[/green] Now watching: {project_name}")
    console.print(f"  Footage dir: {footage_path}")


@app.command()
def unwatch(
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project to unwatch")
):
    """Remove a project from watch list"""
    service = _get_service()
    
    project_name = project or state.current_project
    if not project_name:
        console.print("[red]No project specified. Use --project or 'sf project select'[/red]")
        raise typer.Exit(1)
    
    manager = ProjectManager()
    proj = manager.get_project(project_name)
    if not proj:
        console.print(f"[red]Project not found: {project_name}[/red]")
        raise typer.Exit(1)
    
    service.stop_watching(proj.path)
    console.print(f"[green]✓[/green] Stopped watching: {project_name}")

