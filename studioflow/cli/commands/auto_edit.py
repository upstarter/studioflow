"""
Auto-Editing Commands
Intelligent automation for YouTube episode editing
"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from studioflow.core.auto_editing import AutoEditingEngine, AutoEditConfig
from studioflow.core.resolve_api import ResolveDirectAPI

console = Console()
app = typer.Typer()


@app.command()
def episode(
    project_name: str = typer.Argument(..., help="Project name"),
    footage_path: Path = typer.Argument(..., help="Path to footage directory"),
    transcript_path: Optional[Path] = typer.Option(None, "--transcript", "-t", help="Path to transcript file"),
    template: str = typer.Option("youtube_episode", "--template", help="Episode template"),
    library_path: Optional[Path] = typer.Option(None, "--library", "-l", help="Library path"),
    no_timeline: bool = typer.Option(False, "--no-timeline", help="Skip timeline creation"),
    no_power_bins: bool = typer.Option(False, "--no-power-bins", help="Skip power bin setup"),
):
    """
    Complete auto-editing workflow for YouTube episode
    
    Creates smart bins, power bins, chapters, and initial timeline assembly.
    
    Examples:
        sf auto-edit episode EP001 /path/to/footage
        sf auto-edit episode EP001 /path/to/footage --transcript transcript.srt
        sf auto-edit episode EP001 /path/to/footage --template tutorial
    """
    
    if library_path is None:
        from studioflow.core.config import get_config
        config = get_config()
        library_path = config.storage.studio or Path.home() / "Videos" / "StudioFlow" / "Studio"
    
    console.print(Panel.fit(
        f"[bold cyan]Auto-Editing Episode: {project_name}[/bold cyan]\n"
        f"Footage: {footage_path}\n"
        f"Template: {template}",
        title="🚀 Starting Auto-Edit",
        border_style="cyan"
    ))
    
    # Create config
    config = AutoEditConfig(
        project_name=project_name,
        footage_path=footage_path,
        transcript_path=transcript_path,
        template=template,
        library_path=library_path,
        create_timeline=not no_timeline,
        create_power_bins=not no_power_bins,
    )
    
    # Run auto-editing
    engine = AutoEditingEngine(config)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing episode...", total=None)
        
        try:
            results = engine.process_episode()
            progress.update(task, completed=True)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    # Display results
    console.print("\n[bold green]✓ Auto-editing complete![/bold green]\n")
    
    # Smart bins summary
    if results.get("smart_bins"):
        bins = results["smart_bins"]
        console.print("[bold]Smart Bins Created:[/bold]")
        table = Table(show_header=False)
        table.add_column("Bin", style="cyan")
        table.add_column("Clips", style="green")
        
        for bin_name, clip_count in bins.get("clips_organized", {}).items():
            table.add_row(bin_name, str(clip_count))
        
        console.print(table)
        console.print()
    
    # Power bins summary
    if results.get("power_bins"):
        pb = results["power_bins"]
        console.print(f"[bold]Power Bins:[/bold] {pb.get('total_assets', 0)} assets imported")
    
    # Chapters summary
    if results.get("chapters"):
        chapters = results["chapters"]
        console.print(f"[bold]Chapters Generated:[/bold] {len(chapters)}")
        
        console.print("\n[bold]Chapters:[/bold]")
        for chapter in chapters[:10]:  # Show first 10
            timestamp = f"{int(chapter.timestamp//60)}:{int(chapter.timestamp%60):02d}"
            console.print(f"  {timestamp} - {chapter.title}")
        
        if len(chapters) > 10:
            console.print(f"  ... and {len(chapters) - 10} more")
    
    # Timeline summary
    if results.get("timeline"):
        timeline = results["timeline"]
        console.print(f"\n[bold]Timeline:[/bold] {timeline.get('name', 'N/A')} created")
        console.print(f"  Clips: {timeline.get('clips', 0)}")
        console.print(f"  Chapters: {timeline.get('chapters', 0)}")
    
    console.print(Panel(
        "[green]✓ Episode is ready for editing![/green]\n\n"
        "[bold]Next steps:[/bold]\n"
        "  1. Open DaVinci Resolve\n"
        "  2. Review smart bins and timeline\n"
        "  3. Refine and add final touches\n"
        "  4. Export: sf export youtube video.mp4",
        title="Ready",
        border_style="green"
    ))


@app.command()
def smart_bins(
    project_name: str = typer.Argument(..., help="Project name"),
    footage_path: Path = typer.Argument(..., help="Path to footage"),
):
    """Create smart bins for organizing footage"""
    
    config = AutoEditConfig(
        project_name=project_name,
        footage_path=footage_path,
        create_smart_bins=True,
        create_timeline=False,
        create_power_bins=False,
    )
    
    engine = AutoEditingEngine(config)
    results = engine.create_smart_bins(engine._analyze_footage())
    
    if results.get("error"):
        console.print(f"[red]Error:[/red] {results['error']}")
        raise typer.Exit(1)
    
    console.print(f"[green]✓ Created {results.get('bins_created', 0)} smart bins[/green]")


@app.command()
def power_bins(
    sync: bool = typer.Option(False, "--sync", help="Sync NAS/Media assets to power bins"),
):
    """
    Sync Power Bins from NAS/Media library
    
    Examples:
        sf auto-edit power-bins --sync
        sf power-bins sync  # Use dedicated command for more options
    """
    
    if sync:
        from studioflow.core.auto_editing import AutoEditingEngine, AutoEditConfig
        from studioflow.core.resolve_api import ResolveDirectAPI
        
        resolve_api = ResolveDirectAPI()
        if not resolve_api.is_connected():
            console.print("[red]Resolve not connected[/red]")
            return
        
        config = AutoEditConfig(
            project_name="temp",
            footage_path=Path("/tmp"),
            create_power_bins=True
        )
        
        engine = AutoEditingEngine(config)
        engine.resolve_api = resolve_api
        
        result = engine.setup_power_bins()
        
        if result.get("error"):
            console.print(f"[red]Error:[/red] {result['error']}")
        else:
            total = result.get("total_assets", 0)
            from studioflow.core.power_bins_config import PowerBinsConfig
            asset_path = PowerBinsConfig.get_base_path()
            path_display = str(asset_path) if asset_path else "asset library"
            console.print(f"[green]✓ Synced {total} assets from {path_display}[/green]")
            console.print("\n[yellow]Tip:[/yellow] Drag '_POWER_BINS' to Power Bins in Resolve for persistence")
    else:
        console.print("[yellow]Use --sync to sync assets, or use 'sf power-bins' for more options[/yellow]")
        console.print("\n[yellow]Examples:[/yellow]")
        console.print("  sf power-bins validate         # Check structure")
        console.print("  sf power-bins create-structure # Create directories")
        console.print("  sf power-bins sync             # Sync with Resolve")


@app.command()
def chapters(
    transcript_path: Path = typer.Argument(..., help="Transcript file (SRT or JSON)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    min_duration: float = typer.Option(60.0, "--min-duration", help="Minimum chapter duration (seconds)"),
    format: str = typer.Option("youtube", "--format", "-f", help="Output format: youtube/markers/json"),
):
    """
    Generate chapters from transcript
    
    Examples:
        sf auto-edit chapters transcript.srt
        sf auto-edit chapters transcript.json --format youtube --output chapters.txt
    """
    
    from studioflow.core.auto_editing import AutoEditingEngine, AutoEditConfig
    from pathlib import Path as PPath
    
    config = AutoEditConfig(
        project_name="temp",
        footage_path=PPath("/tmp"),
        transcript_path=transcript_path,
        min_chapter_length=min_duration,
    )
    
    engine = AutoEditingEngine(config)
    chapters = engine.generate_chapters_from_transcript()
    
    if not chapters:
        console.print("[yellow]No chapters detected in transcript[/yellow]")
        return
    
    # Output chapters
    if format == "youtube":
        # YouTube description format
        lines = []
        for chapter in chapters:
            timestamp = engine._format_youtube_timestamp(chapter.timestamp)
            lines.append(f"{timestamp} {chapter.title}")
        
        output_text = "\n".join(lines)
        
        if output:
            output.write_text(output_text)
            console.print(f"[green]✓ Chapters saved to {output}[/green]")
        else:
            console.print("\n[bold]YouTube Chapter Format:[/bold]")
            console.print(Panel(output_text, border_style="cyan"))
    
    elif format == "json":
        import json
        data = [
            {
                "timestamp": ch.timestamp,
                "title": ch.title,
                "description": ch.description,
            }
            for ch in chapters
        ]
        
        output_text = json.dumps(data, indent=2)
        
        if output:
            output.write_text(output_text)
            console.print(f"[green]✓ Chapters saved to {output}[/green]")
        else:
            console.print(output_text)
    
    # Display summary
    console.print(f"\n[bold]Generated {len(chapters)} chapters:[/bold]")
    table = Table()
    table.add_column("Time", style="cyan")
    table.add_column("Title", style="white")
    
    for chapter in chapters[:20]:
        timestamp = f"{int(chapter.timestamp//60)}:{int(chapter.timestamp%60):02d}"
        table.add_row(timestamp, chapter.title)
    
    console.print(table)
    
    if len(chapters) > 20:
        console.print(f"\n[dim]... and {len(chapters) - 20} more[/dim]")


@app.command()
def timeline(
    project_name: str = typer.Argument(..., help="Project name"),
    name: str = typer.Option("01_AUTO_ASSEMBLY", "--name", "-n", help="Timeline name"),
):
    """Create smart timeline assembly"""
    
    api = ResolveDirectAPI()
    
    if not api.is_connected():
        console.print("[red]Resolve not connected[/red]")
        raise typer.Exit(1)
    
    # Load project
    api.create_project(project_name)
    
    # Create timeline
    media_pool = api.media_pool
    timeline = media_pool.CreateEmptyTimeline(name)
    
    if timeline:
        console.print(f"[green]✓ Timeline '{name}' created[/green]")
    else:
        console.print(f"[red]Failed to create timeline[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

