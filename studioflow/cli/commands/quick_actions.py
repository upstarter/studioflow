"""
Quick Actions Menu
Interactive menu for common operations
"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from studioflow.core.state import StateManager
from studioflow.core.project_health import ProjectHealthChecker

console = Console()
app = typer.Typer()


@app.command()
def menu():
    """Interactive quick actions menu"""
    
    while True:
        console.print("\n" + "="*60)
        console.print("[bold cyan]StudioFlow Quick Actions[/bold cyan]")
        console.print("="*60 + "\n")
        
        # Show current project status
        state = StateManager()
        current_project = state.current_project
        
        if current_project:
            console.print(f"[dim]Current Project:[/dim] [cyan]{current_project}[/cyan]\n")
        
        # Main menu
        actions = [
            ("1", "Start New Project", "Create a new video project"),
            ("2", "Import Media", "Import from SD card or folder"),
            ("3", "Batch Transcribe", "Transcribe multiple videos"),
            ("4", "Auto-Edit Episode", "Complete episode workflow"),
            ("5", "Generate Thumbnails", "Create YouTube thumbnails"),
            ("6", "Export for YouTube", "Export with validation"),
            ("7", "Project Health", "Check project status"),
            ("8", "Open in Resolve", "Sync and open Resolve project"),
            ("9", "Quick Dashboard", "Show project overview"),
            ("0", "Exit", "Exit menu"),
        ]
        
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("", style="cyan", width=3)
        table.add_column("Action", style="white", width=25)
        table.add_column("Description", style="dim")
        
        for num, action, desc in actions:
            table.add_row(num, action, desc)
        
        console.print(table)
        
        # Get choice
        choice = Prompt.ask("\n[bold]Select action[/bold]", default="0")
        
        if choice == "0":
            console.print("[yellow]Goodbye![/yellow]")
            break
        elif choice == "1":
            _action_new_project()
        elif choice == "2":
            _action_import_media()
        elif choice == "3":
            _action_batch_transcribe()
        elif choice == "4":
            _action_auto_edit()
        elif choice == "5":
            _action_thumbnails()
        elif choice == "6":
            _action_export()
        elif choice == "7":
            _action_health()
        elif choice == "8":
            _action_resolve()
        elif choice == "9":
            _action_dashboard()
        else:
            console.print("[yellow]Invalid choice[/yellow]")


def _action_new_project():
    """New project action"""
    console.print("\n[bold cyan]Create New Project[/bold cyan]\n")
    
    name = Prompt.ask("Project name")
    template = Prompt.ask("Template", default="youtube", choices=["youtube", "tutorial", "vlog", "doc"])
    
    from studioflow.cli.commands.project import create
    create(name, template=template)


def _action_import_media():
    """Import media action"""
    console.print("\n[bold cyan]Import Media[/bold cyan]\n")
    
    source = Prompt.ask("Source path")
    
    if not Path(source).exists():
        console.print(f"[red]Path not found: {source}[/red]")
        return
    
    from studioflow.cli.main import import_media
    import_media(Path(source))


def _action_batch_transcribe():
    """Batch transcribe action"""
    console.print("\n[bold cyan]Batch Transcribe[/bold cyan]\n")
    
    path = Prompt.ask("Directory or file pattern")
    recursive = Confirm.ask("Recursive search?", default=True)
    
    from studioflow.cli.commands.batch_ops import transcribe
    transcribe(Path(path), recursive=recursive)


def _action_auto_edit():
    """Auto-edit action"""
    console.print("\n[bold cyan]Auto-Edit Episode[/bold cyan]\n")
    
    project = Prompt.ask("Project name")
    footage = Prompt.ask("Footage path")
    
    if not Path(footage).exists():
        console.print(f"[red]Path not found: {footage}[/red]")
        return
    
    transcript = Prompt.ask("Transcript path (optional)", default="")
    transcript_path = Path(transcript) if transcript else None
    
    from studioflow.cli.commands.auto_edit import episode
    episode(project, Path(footage), transcript_path=transcript_path)


def _action_thumbnails():
    """Generate thumbnails action"""
    console.print("\n[bold cyan]Generate Thumbnails[/bold cyan]\n")
    
    project = Prompt.ask("Project name", default=StateManager().current_project or "")
    
    from studioflow.cli.commands.thumbnail import generate
    generate(project_name=project if project else None)


def _action_export():
    """Export action"""
    console.print("\n[bold cyan]Export for YouTube[/bold cyan]\n")
    
    video = Prompt.ask("Video file path")
    
    if not Path(video).exists():
        console.print(f"[red]File not found: {video}[/red]")
        return
    
    validate = Confirm.ask("Validate export?", default=True)
    
    from studioflow.cli.commands.workflow import publish
    publish(Path(video), validate=validate)


def _action_health():
    """Health check action"""
    from studioflow.cli.commands.dashboard import status
    status()


def _action_resolve():
    """Open in Resolve action"""
    state = StateManager()
    project = state.current_project
    
    if not project:
        console.print("[yellow]No project selected[/yellow]")
        return
    
    from studioflow.cli.commands.resolve import sync
    sync(project)


def _action_dashboard():
    """Dashboard action"""
    from studioflow.cli.commands.dashboard import quick
    quick()


if __name__ == "__main__":
    app()


