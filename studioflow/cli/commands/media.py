"""Media Import Commands"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from studioflow.core.media import MediaScanner, MediaImporter
from studioflow.core.project import ProjectManager
from studioflow.core.state import StateManager
from studioflow.core.transcription import TranscriptionService
from studioflow.core.auto_import import AutoImportService


console = Console()
app = typer.Typer()


@app.command()
def scan(path: Path):
    """Scan path for media files"""
    scanner = MediaScanner()
    files = scanner.scan(path)

    console.print(f"Found {len(files)} media files")
    return files


@app.command()
def import_file(file_path: Path, project: str):
    """Import single file"""
    # Implementation
    pass


@app.command()
def transcribe(
    file_path: Path = typer.Argument(..., help="Audio/video file to transcribe"),
    model: str = typer.Option("base", help="Whisper model (tiny/base/small/medium/large)"),
    language: str = typer.Option("auto", help="Language code or 'auto' for detection"),
    formats: str = typer.Option("srt,vtt,txt", help="Output formats (comma-separated)"),
    chapters: bool = typer.Option(False, help="Extract YouTube chapters from transcript")
):
    """
    Transcribe audio/video using Whisper AI

    Examples:
        sf media transcribe video.mp4
        sf media transcribe audio.mp3 --model small
        sf media transcribe video.mp4 --formats srt,vtt,txt,json --chapters
    """
    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    # Parse output formats
    output_formats = [fmt.strip() for fmt in formats.split(",")]

    # Initialize transcription service
    service = TranscriptionService()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Add transcription task
        task = progress.add_task(
            f"Transcribing {file_path.name} with Whisper {model} model...",
            total=None
        )

        # Perform transcription
        result = service.transcribe(
            audio_path=file_path,
            model=model,
            language=language,
            output_formats=output_formats
        )

        progress.update(task, completed=True)

    if not result["success"]:
        console.print(f"[red]Transcription failed: {result.get('error')}[/red]")
        raise typer.Exit(1)

    # Display results
    console.print("\n[green]✓ Transcription complete![/green]\n")

    # Create results table
    table = Table(title="Transcription Results")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    if "language" in result:
        table.add_row("Language", result["language"])
    if "duration" in result:
        duration = result["duration"]
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        table.add_row("Duration", f"{minutes}:{seconds:02d}")
    if "segments" in result:
        table.add_row("Segments", str(result["segments"]))

    console.print(table)

    # Display output files
    if "output_files" in result and result["output_files"]:
        console.print("\n[bold]Generated files:[/bold]")
        for fmt, path in result["output_files"].items():
            console.print(f"  • {fmt.upper()}: {path}")

    # Extract chapters if requested
    if chapters and "json" in result.get("output_files", {}):
        json_path = result["output_files"]["json"]
        chapters_list = service.extract_chapters(json_path)

        if chapters_list:
            console.print("\n[bold]YouTube Chapters:[/bold]")
            for chapter in chapters_list:
                console.print(f"  {chapter['timestamp']} - {chapter['title']}")

    # Show sample of transcript
    if result.get("text"):
        text_sample = result["text"][:500]
        if len(result["text"]) > 500:
            text_sample += "..."
        console.print(f"\n[bold]Transcript sample:[/bold]\n{text_sample}")

    return result


@app.command()
def unified(
    source_path: Path = typer.Argument(..., help="Mount point of SD card OR ingest pool directory"),
    codeword: Optional[str] = typer.Option(None, "--codeword", "-c", help="Project codeword (e.g., 'compliant_ape')"),
    from_ingest: bool = typer.Option(False, "--from-ingest", help="Source is ingest pool (already copied), not SD card"),
    normalize: bool = typer.Option(True, "--normalize/--no-normalize", help="Normalize audio (Phase 1: Immediate)"),
    transcribe: bool = typer.Option(True, "--transcribe/--no-transcribe", help="Generate transcripts (Phase 2: Background)"),
    markers: bool = typer.Option(True, "--markers/--no-markers", help="Detect audio markers (Phase 2: Background)"),
    rough_cut: bool = typer.Option(False, "--rough-cut/--no-rough-cut", help="Generate rough cut (Phase 3: On-Demand)"),
    resolve: bool = typer.Option(False, "--resolve/--no-resolve", help="Setup Resolve project (Phase 3: On-Demand)"),
):
    """
    Complete unified import pipeline: SD card → Ready-to-edit project
    
    Processing Phases:
    - Phase 1 (Immediate): Import, Normalize, Proxies
    - Phase 2 (Background): Transcription, Marker Detection
    - Phase 3 (On-Demand): Rough Cut, Resolve Setup
    
    Project Selection Priority:
    1. SD card label for project name
    2. Active project if set
    3. Auto-create codeword-YYYYMMDD_Import if none
    
    Library Path:
    - Uses /mnt/library/PROJECTS/ if exists
    - Fallback to config.storage.active
    
    Project naming: codeword-YYYYMMDD_Import
    - Codeword from: SD card label, --codeword flag, or active project
    - Example: compliant_ape-20260104_Import
    
    Examples:
        sf import unified /media/user/SDCARD
        sf import unified /media/user/SDCARD --codeword compliant_ape
        sf import unified /mnt/nas/Scratch/Ingest/2026-01-04 --from-ingest
        sf import unified /media/user/SDCARD --rough-cut --resolve
    """
    from studioflow.core.unified_import import UnifiedImportPipeline
    
    if not source_path.exists():
        console.print(f"[red]Source path not found: {source_path}[/red]")
        raise typer.Exit(1)
    
    pipeline = UnifiedImportPipeline()
    
    result = pipeline.process_sd_card(
        source_path=source_path,
        codeword=codeword,
        from_ingest=from_ingest,
        normalize_audio=normalize,
        transcribe=transcribe,
        detect_markers=markers,
        generate_rough_cut=rough_cut,
        setup_resolve=resolve
    )
    
    if result.success:
        console.print(f"\n[bold green]✅ Import Pipeline Complete![/bold green]")
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Files imported: {result.files_imported}")
        console.print(f"  Files normalized: {result.files_normalized}")
        console.print(f"  Proxies created: {result.proxies_created}")
        console.print(f"  Transcripts: {result.transcripts_generated}")
        console.print(f"  Markers detected: {result.markers_detected}")
        console.print(f"  Segments extracted: {result.segments_extracted}")
        console.print(f"  Rough cut: {'✓' if result.rough_cut_created else '✗'}")
        console.print(f"  Resolve project: {'✓' if result.resolve_project_created else '✗'}")
        console.print(f"\n[bold]Project:[/bold] {result.project_path}")
        console.print(f"[dim]Next: Open DaVinci Resolve or run 'sf edit'[/dim]")
    else:
        console.print(f"\n[bold red]✗ Import Pipeline Failed[/bold red]")
        for error in result.errors:
            console.print(f"  [red]Error:[/red] {error}")
        for warning in result.warnings:
            console.print(f"  [yellow]Warning:[/yellow] {warning}")
        raise typer.Exit(1)
    
    return result


@app.command()
def auto_import(
    mount_point: Path = typer.Argument(..., help="Mount point of SD card"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch for changes"),
    notify: bool = typer.Option(True, "--notify", help="Send desktop notifications")
):
    """
    Auto-import media from camera SD cards

    Features:
    - Detects camera type (FX30, ZV-E10, etc)
    - Copies to ingest pool with verification
    - Organizes into current project
    - Generates proxies
    - Creates Resolve timeline

    Examples:
        sf media auto-import /path/to/sd-card
        sf media auto-import /dev/sdb1 --watch
    """
    service = AutoImportService()

    if not mount_point.exists():
        console.print(f"[red]Mount point not found: {mount_point}[/red]")
        raise typer.Exit(1)

    # Run import
    result = service.process_device(str(mount_point))

    if result == 0:
        console.print("[green]✓ Import completed successfully[/green]")
    else:
        console.print("[red]✗ Import failed[/red]")
        raise typer.Exit(result)

    return result