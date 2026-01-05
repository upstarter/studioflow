"""
Complete Workflow Commands
Auto-complete workflows that tie all features together
"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.layout import Layout

from studioflow.core.workflow_complete import CompleteWorkflowEngine, WorkflowType
from studioflow.core.project_health import ProjectHealthChecker
from studioflow.core.export_validator import ExportValidator

console = Console()
app = typer.Typer()


@app.command()
def episode(
    project_name: str = typer.Argument(..., help="Project name"),
    footage_path: Path = typer.Argument(..., help="Path to footage"),
    transcript_path: Optional[Path] = typer.Option(None, "--transcript", "-t", help="Transcript file"),
    library_path: Optional[Path] = typer.Option(None, "--library", "-l", help="Library path"),
):
    """
    Complete episode workflow: import → organize → transcribe → auto-edit → ready
    
    One command handles everything needed to get a YouTube episode ready for editing.
    
    Examples:
        sf workflow episode EP001 /path/to/footage
        sf workflow episode EP001 /path/to/footage --transcript transcript.srt
    """
    
    if library_path is None:
        from studioflow.core.config import get_config
        config = get_config()
        library_path = config.storage.library or Path.home() / "Videos" / "StudioFlow" / "Library"
    
    console.print(Panel.fit(
        f"[bold cyan]Complete Episode Workflow[/bold cyan]\n"
        f"Project: {project_name}\n"
        f"Footage: {footage_path}",
        title="🚀 Starting Workflow",
        border_style="cyan"
    ))
    
    engine = CompleteWorkflowEngine()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        result = engine.execute_episode_workflow(
            project_name=project_name,
            footage_path=footage_path,
            transcript_path=transcript_path,
            library_path=library_path
        )
    
    # Display results
    _display_workflow_result(result, "Episode Workflow")


@app.command()
def import_workflow(
    source_path: Path = typer.Argument(..., help="Source path to import from"),
    project_name: str = typer.Argument(..., help="Project name"),
    transcribe: bool = typer.Option(False, "--transcribe", help="Transcribe imported media"),
    proxies: bool = typer.Option(False, "--proxies", help="Create proxy media"),
):
    """
    Complete import workflow: import → organize → (optional) transcribe → proxies
    
    Examples:
        sf workflow import /media/sdcard EP001
        sf workflow import /media/sdcard EP001 --transcribe --proxies
    """
    
    console.print(Panel.fit(
        f"[bold cyan]Import Workflow[/bold cyan]\n"
        f"Source: {source_path}\n"
        f"Project: {project_name}",
        title="📥 Starting Import",
        border_style="cyan"
    ))
    
    engine = CompleteWorkflowEngine()
    
    with Progress() as progress:
        result = engine.execute_import_workflow(
            source_path=source_path,
            project_name=project_name,
            transcribe=transcribe,
            create_proxies=proxies
        )
    
    _display_workflow_result(result, "Import Workflow")


@app.command()
def publish(
    video_path: Path = typer.Argument(..., help="Video file to publish"),
    project_name: Optional[str] = typer.Option(None, "--project", "-p", help="Project name"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate export"),
    thumbnail: bool = typer.Option(True, "--thumbnail/--no-thumbnail", help="Generate thumbnail"),
    upload: bool = typer.Option(False, "--upload", help="Upload to YouTube"),
):
    """
    Complete publish workflow: validate → thumbnail → (optional) upload
    
    Examples:
        sf workflow publish video.mp4
        sf workflow publish video.mp4 --project EP001 --upload
    """
    
    console.print(Panel.fit(
        f"[bold cyan]Publish Workflow[/bold cyan]\n"
        f"Video: {video_path}\n"
        f"Validate: {validate} | Thumbnail: {thumbnail} | Upload: {upload}",
        title="📤 Starting Publish",
        border_style="cyan"
    ))
    
    engine = CompleteWorkflowEngine()
    
    if not project_name:
        from studioflow.core.state import StateManager
        state = StateManager()
        project_name = state.current_project or "Unknown"
    
    with Progress() as progress:
        result = engine.execute_publish_workflow(
            video_path=video_path,
            project_name=project_name,
            validate=validate,
            generate_thumbnail=thumbnail,
            upload=upload
        )
    
    _display_workflow_result(result, "Publish Workflow")


def _display_workflow_result(result, workflow_name: str):
    """Display workflow result"""
    console.print("\n" + "="*60)
    console.print(f"[bold]{workflow_name} Results[/bold]")
    console.print("="*60 + "\n")
    
    # Status
    status_icon = "✅" if result.success else "❌"
    console.print(f"{status_icon} Status: {'Success' if result.success else 'Failed'}")
    console.print(f"⏱️  Duration: {result.duration:.1f} seconds\n")
    
    # Steps
    table = Table(title="Workflow Steps")
    table.add_column("Step", style="cyan", width=20)
    table.add_column("Status", style="white", width=12)
    table.add_column("Result", style="dim")
    
    for step in result.steps:
        status_icon = {
            "completed": "✅",
            "failed": "❌",
            "running": "⏳",
            "pending": "⏸️"
        }.get(step.status, "❓")
        
        result_text = ""
        if step.result:
            if isinstance(step.result, dict):
                if step.result.get("success"):
                    result_text = "Success"
                elif step.result.get("error"):
                    result_text = step.result.get("error", "Error")
                else:
                    result_text = "Completed"
            else:
                result_text = "Completed"
        
        table.add_row(step.name, f"{status_icon} {step.status.title()}", result_text)
    
    console.print(table)
    
    # Errors/Warnings
    if result.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result.errors:
            console.print(f"  ❌ {error}")
    
    if result.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  ⚠️  {warning}")
    
    # Next steps
    if result.success:
        console.print("\n[bold green]✓ Workflow completed successfully![/bold green]")
    else:
        console.print("\n[bold red]✗ Workflow completed with errors[/bold red]")
        console.print("Review errors above and retry failed steps manually.")


if __name__ == "__main__":
    app()


