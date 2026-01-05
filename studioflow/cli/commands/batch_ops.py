"""
Enhanced Batch Operations
Parallel processing for transcription, AI editing, thumbnails, etc.
"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from studioflow.core.batch_processor import BatchProcessor, BatchResult
from studioflow.core.transcription import TranscriptionService
from studioflow.core.intelligent_editor import IntelligentEditor
from studioflow.core.ffmpeg import FFmpegProcessor
from studioflow.core.thumbnail import ThumbnailGenerator
from studioflow.core.media import MediaScanner

console = Console()
app = typer.Typer()


def _transcribe_operation(file: Path, **kwargs) -> BatchResult:
    """Transcribe a single file"""
    import time
    start = time.time()
    
    try:
        service = TranscriptionService()
        result = service.transcribe(file, **kwargs)
        
        if result.get("success"):
            return BatchResult(
                file=file,
                success=True,
                output=result.get("output_files", {}).get("srt"),
                duration=time.time() - start
            )
        else:
            return BatchResult(
                file=file,
                success=False,
                error=result.get("error", "Unknown error"),
                duration=time.time() - start
            )
    except Exception as e:
        return BatchResult(
            file=file,
            success=False,
            error=str(e),
            duration=time.time() - start
        )


def _trim_silence_operation(file: Path, output_dir: Path, **kwargs) -> BatchResult:
    """Trim silence from a single file"""
    import time
    from studioflow.cli.commands.ai import auto_edit as ai_auto_edit
    
    start = time.time()
    
    try:
        output = output_dir / f"{file.stem}_trimmed{file.suffix}"
        
        # Use existing auto_edit function
        threshold = kwargs.get('threshold', -40.0)
        min_silence = kwargs.get('min_silence', 0.5)
        
        # Call the auto_edit command function
        # For now, use FFmpeg directly
        from studioflow.core.ffmpeg import FFmpegProcessor
        result = FFmpegProcessor.auto_cut_silence(file, output, threshold, min_silence)
        
        return BatchResult(
            file=file,
            success=result.success,
            output=output if result.success else None,
            error=result.error_message if not result.success else None,
            duration=time.time() - start
        )
    except Exception as e:
        return BatchResult(
            file=file,
            success=False,
            error=str(e),
            duration=time.time() - start
        )


@app.command()
def transcribe(
    path: Path = typer.Argument(..., help="Directory or file pattern"),
    recursive: bool = typer.Option(True, "--recursive", "-r", help="Recursive search"),
    model: str = typer.Option("base", "--model", "-m", help="Whisper model"),
    parallel: int = typer.Option(2, "--parallel", "-p", help="Parallel jobs"),
    output_format: str = typer.Option("all", "--format", "-f", help="Output format: srt/vtt/txt/json/all"),
):
    """
    Batch transcribe multiple video/audio files
    
    Examples:
        sf batch transcribe /mnt/ingest/Camera
        sf batch transcribe /path/to/videos --model large --parallel 4
        sf batch transcribe "*.mp4" --recursive
    """
    
    # Find files
    scanner = MediaScanner()
    
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = [f.path for f in scanner.scan(path, recursive=recursive) if f.type.value in ["video", "audio"]]
    else:
        # Pattern
        files = list(Path.cwd().rglob(str(path)))
    
    if not files:
        console.print(f"[yellow]No media files found[/yellow]")
        return
    
    console.print(f"[cyan]Found {len(files)} file(s) to transcribe[/cyan]\n")
    
    # Determine output formats
    formats = ["srt", "vtt", "txt", "json"] if output_format == "all" else [output_format]
    
    # Process
    processor = BatchProcessor(max_workers=parallel)
    results = processor.process(
        files,
        _transcribe_operation,
        operation_name="Transcribing",
        model=model,
        output_formats=formats
    )
    
    # Summary
    summary = processor.get_summary()
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total: {summary['total']}")
    console.print(f"  Successful: [green]{summary['successful']}[/green]")
    console.print(f"  Failed: [red]{summary['failed']}[/red]")
    console.print(f"  Success rate: {summary['success_rate']*100:.1f}%")
    
    if summary['failed'] > 0:
        console.print(f"\n[yellow]Failed files:[/yellow]")
        for result in results:
            if not result.success:
                console.print(f"  ✗ {result.file.name}: {result.error}")


@app.command()
def trim_silence(
    path: Path = typer.Argument(..., help="Directory or file pattern"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    threshold: float = typer.Option(-40.0, "--threshold", help="Silence threshold (dB)"),
    min_silence: float = typer.Option(0.5, "--min-silence", help="Minimum silence duration (s)"),
    parallel: int = typer.Option(2, "--parallel", "-p", help="Parallel jobs"),
):
    """Batch remove silence from multiple videos"""
    
    # Find files
    scanner = MediaScanner()
    
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = [f.path for f in scanner.scan(path) if f.type.value == "video"]
    else:
        files = list(Path.cwd().rglob(str(path)))
    
    if not files:
        console.print(f"[yellow]No video files found[/yellow]")
        return
    
    if not output_dir:
        output_dir = path if path.is_dir() else path.parent
        output_dir = output_dir / "trimmed"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[cyan]Found {len(files)} file(s) to process[/cyan]\n")
    
    # Process
    processor = BatchProcessor(max_workers=parallel)
    results = processor.process(
        files,
        _trim_silence_operation,
        operation_name="Trimming Silence",
        output_dir=output_dir,
        threshold=threshold,
        min_silence=min_silence
    )
    
    # Summary
    summary = processor.get_summary()
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Output directory: {output_dir}")
    console.print(f"  Successful: [green]{summary['successful']}[/green]")
    console.print(f"  Failed: [red]{summary['failed']}[/red]")


@app.command()
def thumbnails(
    path: Path = typer.Argument(..., help="Directory or file pattern"),
    template: str = typer.Option("viral", "--template", "-t", help="Thumbnail template"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    parallel: int = typer.Option(4, "--parallel", "-p", help="Parallel jobs"),
):
    """Batch generate thumbnails for multiple videos"""
    
    # Find files
    scanner = MediaScanner()
    
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = [f.path for f in scanner.scan(path) if f.type.value == "video"]
    else:
        files = list(Path.cwd().rglob(str(path)))
    
    if not files:
        console.print(f"[yellow]No video files found[/yellow]")
        return
    
    if not output_dir:
        output_dir = path if path.is_dir() else path.parent
        output_dir = output_dir / "thumbnails"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[cyan]Found {len(files)} file(s) to process[/cyan]\n")
    
    # Process (using existing thumbnail generator)
    from studioflow.cli.commands.thumbnail import generate as gen_thumbnail
    
    processor = BatchProcessor(max_workers=parallel)
    
    def thumbnail_op(file: Path, **kwargs) -> BatchResult:
        import time
        start = time.time()
        try:
            output = output_dir / f"{file.stem}_thumb.png"
            # Call thumbnail generation
            result = gen_thumbnail(
                project_name=None,
                text=file.stem,
                template=template,
                source=str(file)
            )
            return BatchResult(
                file=file,
                success=True,
                output=output,
                duration=time.time() - start
            )
        except Exception as e:
            return BatchResult(
                file=file,
                success=False,
                error=str(e),
                duration=time.time() - start
            )
    
    results = processor.process(
        files,
        thumbnail_op,
        operation_name="Generating Thumbnails",
        template=template
    )
    
    # Summary
    summary = processor.get_summary()
    console.print(f"\n[green]✓ Generated {summary['successful']} thumbnails in {output_dir}[/green]")


if __name__ == "__main__":
    app()

