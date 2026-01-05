"""
Simplified StudioFlow commands
Focus on what matters: import -> edit -> export -> upload
"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

from studioflow.core.ffmpeg import FFmpegProcessor
from studioflow.core.simple_effects import SimpleEffects
from studioflow.core.simple_templates import create_project, list_templates
from studioflow.core.verify import FileVerifier
from studioflow.core.media import MediaImporter
from studioflow.core.youtube_api import YouTubeAPIService
from studioflow.core.transcription import TranscriptionService

console = Console()
app = typer.Typer()


@app.command()
def new(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("basic", "--template", "-t", help="Template: youtube/podcast/short/basic")
):
    """Create a new project"""
    base_path = Path.home() / "StudioFlow"
    project_path = create_project(name, template, base_path)

    console.print(f"[green]✓[/green] Created project: {project_path}")
    console.print(f"\nNext steps:")
    console.print(f"  cd {project_path}")
    console.print(f"  sf import /path/to/media")


@app.command()
def import_media(
    source: Path = typer.Argument(..., help="Source folder or device"),
    verify: bool = typer.Option(True, "--verify/--no-verify", help="Verify file integrity")
):
    """Import media files with verification"""
    if not source.exists():
        console.print(f"[red]Source not found: {source}[/red]")
        raise typer.Exit(1)

    # Find media files
    media_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.mp3', '.wav', '.jpg', '.png'}
    media_files = []

    for ext in media_extensions:
        media_files.extend(source.rglob(f"*{ext}"))

    if not media_files:
        console.print("[yellow]No media files found[/yellow]")
        return

    console.print(f"Found {len(media_files)} media files")

    # Import with verification
    imported = 0
    failed = []

    for file in track(media_files, description="Importing..."):
        if verify:
            valid, error = FileVerifier.verify_media_file(file)
            if not valid:
                failed.append((file, error))
                continue

        # Copy to project (simplified - just copy to Media folder)
        dest = Path.cwd() / "01_Media" / file.name
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            import shutil
            shutil.copy2(file, dest)

            # Verify copy if requested
            if verify and not FileVerifier.compare_files(file, dest):
                failed.append((file, "Copy verification failed"))
                dest.unlink()
                continue

            imported += 1
        except Exception as e:
            failed.append((file, str(e)))

    # Report results
    console.print(f"\n[green]✓[/green] Imported {imported} files")

    if failed:
        console.print(f"[yellow]⚠[/yellow] {len(failed)} files failed:")
        for file, error in failed[:5]:  # Show first 5
            console.print(f"  {file.name}: {error}")


@app.command()
def cut(
    input_file: Path = typer.Argument(..., help="Input video"),
    start: float = typer.Argument(..., help="Start time in seconds"),
    duration: float = typer.Argument(..., help="Duration in seconds"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file")
):
    """Cut a segment from video"""
    if not output:
        output = input_file.stem + "_cut.mp4"

    if FFmpegProcessor.cut_video(input_file, output, start, duration):
        console.print(f"[green]✓[/green] Cut saved to: {output}")
    else:
        console.print(f"[red]Failed to cut video[/red]")


@app.command()
def concat(
    files: List[Path] = typer.Argument(..., help="Video files to concatenate"),
    output: Path = typer.Option("output.mp4", "--output", "-o", help="Output file")
):
    """Concatenate multiple videos"""
    # Check all files exist
    for file in files:
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(1)

    if FFmpegProcessor.concat_videos(files, output):
        console.print(f"[green]✓[/green] Concatenated {len(files)} videos to: {output}")
    else:
        console.print(f"[red]Failed to concatenate videos[/red]")


@app.command()
def export(
    input_file: Path = typer.Argument(..., help="Input video"),
    platform: str = typer.Option("youtube", "--platform", "-p", help="Platform: youtube/instagram/tiktok"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file")
):
    """Export video optimized for platform"""
    if not output:
        output = Path(f"{input_file.stem}_{platform}.mp4")

    console.print(f"Exporting for {platform}...")

    if FFmpegProcessor.export_for_platform(input_file, platform, output):
        info = FFmpegProcessor.get_media_info(output)
        size_mb = output.stat().st_size / (1024 * 1024)

        console.print(f"[green]✓[/green] Exported to: {output}")
        console.print(f"  Size: {size_mb:.1f} MB")
        console.print(f"  Duration: {info.get('format', {}).get('duration', 'unknown')}s")
    else:
        console.print(f"[red]Failed to export video[/red]")


@app.command()
def effect(
    input_file: Path = typer.Argument(..., help="Input video"),
    effect_name: str = typer.Argument(..., help="Effect: fade_in/fade_out/blur/brightness/contrast"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    **params  # Accept effect parameters
):
    """Apply simple effect to video"""
    if not output:
        output = Path(f"{input_file.stem}_{effect_name}.mp4")

    if SimpleEffects.apply_effect(input_file, effect_name, output, params):
        console.print(f"[green]✓[/green] Applied {effect_name} to: {output}")
    else:
        console.print(f"[red]Failed to apply effect[/red]")


@app.command()
def audio(
    input_file: Path = typer.Argument(..., help="Input video or audio"),
    action: str = typer.Option("normalize", "--action", "-a", help="Action: normalize/extract"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    target_lufs: float = typer.Option(-16.0, "--lufs", help="Target LUFS for normalization")
):
    """Audio operations"""
    if action == "normalize":
        if not output:
            output = Path(f"{input_file.stem}_normalized{input_file.suffix}")

        if SimpleEffects.normalize_audio(input_file, output, target_lufs):
            console.print(f"[green]✓[/green] Normalized audio to {target_lufs} LUFS: {output}")
        else:
            console.print(f"[red]Failed to normalize audio[/red]")

    elif action == "extract":
        if not output:
            output = Path(f"{input_file.stem}.wav")

        if FFmpegProcessor.extract_audio(input_file, output):
            console.print(f"[green]✓[/green] Extracted audio to: {output}")
        else:
            console.print(f"[red]Failed to extract audio[/red]")


@app.command()
def thumbnail(
    video_file: Path = typer.Argument(..., help="Video file"),
    timestamp: float = typer.Option(1.0, "--time", "-t", help="Timestamp in seconds"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file")
):
    """Generate thumbnail from video"""
    if not output:
        output = Path(f"{video_file.stem}_thumb.jpg")

    if FFmpegProcessor.generate_thumbnail(video_file, output, timestamp):
        console.print(f"[green]✓[/green] Thumbnail saved to: {output}")
    else:
        console.print(f"[red]Failed to generate thumbnail[/red]")


@app.command()
def transcribe(
    audio_file: Optional[Path] = typer.Argument(None, help="Audio or video file (auto-detects if not provided)"),
    model: str = typer.Option("base", "--model", "-m", help="Whisper model size"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    all_files: bool = typer.Option(False, "--all", "-a", help="Transcribe all detected files"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Transcribe audio using Whisper (auto-detects project footage if no file specified)"""
    from studioflow.core.project_context import ProjectContextManager

    # Smart context detection if no file provided
    if audio_file is None:
        files, description = ProjectContextManager.get_files_for_command("transcribe")

        if not files:
            console.print("[yellow]No files found. Specify a file: sf transcribe <file>[/yellow]")
            return

        console.print(f"[cyan]Auto-detected:[/cyan] {description}")
        for f in files[:5]:
            console.print(f"  • {f.name}")
        if len(files) > 5:
            console.print(f"  ... and {len(files) - 5} more")

        if not yes:
            confirm = typer.confirm(f"\nTranscribe {'all ' + str(len(files)) + ' files' if all_files else 'first file'}?")
            if not confirm:
                return

        if all_files:
            # Batch transcribe
            for i, f in enumerate(files, 1):
                console.print(f"\n[cyan][{i}/{len(files)}] Transcribing: {f.name}[/cyan]")
                _transcribe_single(f, model, output=f.parent / f"{f.stem}.srt")
            return
        else:
            audio_file = files[0]

    if not output:
        output = Path(f"{audio_file.stem}.srt")

    _transcribe_single(audio_file, model, output)


def _transcribe_single(audio_file: Path, model: str, output: Path):
    """Transcribe a single file"""
    try:
        service = TranscriptionService()
        result = service.transcribe(audio_file, model=model)

        if not result.get("success", False):
            console.print(f"[red]Transcription failed: {result.get('error', 'Unknown error')}[/red]")
            return

        # Check if SRT was generated by the service
        output_files = result.get("output_files", {})
        if "srt" in output_files and output_files["srt"].exists():
            # Copy to requested output location if different
            if output != output_files["srt"]:
                import shutil
                shutil.copy(output_files["srt"], output)
            console.print(f"[green]✓[/green] Transcription saved to: {output}")
        else:
            # Generate SRT from segments if available
            segments = result.get("segments", [])
            if segments:
                srt_content = service._generate_srt_content(result)
                output.write_text(srt_content)
                console.print(f"[green]✓[/green] Transcription saved to: {output}")
            else:
                console.print(f"[yellow]Warning: No segments found in transcription[/yellow]")

        # Show preview
        text = result.get("text", "")
        if text:
            preview = text[:200] + "..." if len(text) > 200 else text
            console.print(f"\nPreview: {preview}")

    except Exception as e:
        console.print(f"[red]Transcription failed: {e}[/red]")


@app.command()
def upload(
    video_file: Path = typer.Argument(..., help="Video file to upload"),
    platform: str = typer.Option("youtube", "--platform", "-p", help="Platform to upload to"),
    title: Optional[str] = typer.Option(None, "--title", help="Video title"),
    description: Optional[str] = typer.Option(None, "--description", help="Video description")
):
    """Upload video to platform"""
    if platform == "youtube":
        try:
            service = YouTubeAPIService()

            if not title:
                title = video_file.stem.replace("_", " ").title()

            if not description:
                description = f"Uploaded with StudioFlow"

            console.print(f"Uploading to YouTube: {title}")

            result = service.upload_video(
                video_path=video_file,
                title=title,
                description=description
            )

            if result.get("id"):
                console.print(f"[green]✓[/green] Uploaded successfully!")
                console.print(f"  Video ID: {result['id']}")
                console.print(f"  URL: https://youtube.com/watch?v={result['id']}")
            else:
                console.print(f"[red]Upload failed[/red]")

        except Exception as e:
            console.print(f"[red]Upload error: {e}[/red]")
            console.print("[yellow]Have you authenticated? Run: sf youtube auth[/yellow]")
    else:
        console.print(f"[yellow]Platform {platform} not yet supported[/yellow]")


@app.command()
def info(
    file_path: Path = typer.Argument(..., help="Media file")
):
    """Show media file information"""
    info = FFmpegProcessor.get_media_info(file_path)

    if not info:
        console.print(f"[red]Could not read file info[/red]")
        return

    # Display info
    format_info = info.get("format", {})
    video_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), {})

    panel_content = f"""
[bold]File:[/bold] {file_path.name}
[bold]Format:[/bold] {format_info.get('format_name', 'unknown')}
[bold]Duration:[/bold] {float(format_info.get('duration', 0)):.1f}s
[bold]Size:[/bold] {int(format_info.get('size', 0)) / (1024*1024):.1f} MB
[bold]Bitrate:[/bold] {int(format_info.get('bit_rate', 0)) / 1000:.0f} kbps

[bold cyan]Video:[/bold cyan]
  Codec: {video_stream.get('codec_name', 'none')}
  Resolution: {video_stream.get('width', 0)}x{video_stream.get('height', 0)}
  FPS: {eval(video_stream.get('r_frame_rate', '0/1')) if video_stream.get('r_frame_rate') else 0:.2f}

[bold cyan]Audio:[/bold cyan]
  Codec: {audio_stream.get('codec_name', 'none')}
  Sample Rate: {audio_stream.get('sample_rate', 0)} Hz
  Channels: {audio_stream.get('channels', 0)}
"""

    console.print(Panel(panel_content, title="Media Information", border_style="blue"))


# Episode/Doc/Film Commands (Simplified)

@app.command()
def episode(
    number: int = typer.Argument(..., help="Episode number (e.g., 3 for EP003)"),
    title: str = typer.Argument(..., help="Episode title"),
    resolution: str = typer.Option("4K", "--resolution", "-r", help="Resolution (4K/1080p)"),
    framerate: str = typer.Option("60fps", "--framerate", "-f", help="Framerate")
):
    """Create a new episode with full automation support"""
    from studioflow.core.project import create_episode

    result = create_episode(number, title, resolution=resolution, framerate=framerate)

    if not result.success:
        console.print(f"[red]Error:[/red] {result.error}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Next steps:[/bold cyan]")
    console.print(f"  1. Import media: sf import {result.project_path} /path/to/footage")
    console.print(f"  2. Edit in DaVinci Resolve")
    console.print(f"  3. Transcribe: sf transcribe {result.data['episode_id']}")
    console.print(f"  4. Upload: sf upload {result.data['episode_id']}")


@app.command()
def doc(
    number: int = typer.Argument(..., help="Documentary number (e.g., 1 for DOC001)"),
    title: str = typer.Argument(..., help="Documentary title")
):
    """Create a new documentary project"""
    from studioflow.core.project import create_doc

    result = create_doc(number, title)

    if not result.success:
        console.print(f"[red]Error:[/red] {result.error}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Documentary workflow:[/bold cyan]")
    console.print(f"  1. Import interviews: sf import {result.project_path}/01_footage/INTERVIEWS")
    console.print(f"  2. Transcribe: sf transcribe {result.data['doc_id']}")
    console.print(f"  3. Edit in DaVinci Resolve")
    console.print(f"  4. Archive when done: sf archive {result.data['doc_id']}")


@app.command()
def film(
    number: int = typer.Argument(..., help="Film number (e.g., 1 for FLM001)"),
    title: str = typer.Argument(..., help="Film title")
):
    """Create a new film project (hobby/experimental)"""
    from studioflow.core.project import create_film

    result = create_film(number, title)

    if not result.success:
        console.print(f"[red]Error:[/red] {result.error}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Film workflow:[/bold cyan]")
    console.print(f"  1. Organize footage in: {result.project_path}/01_footage")
    console.print(f"  2. Edit in DaVinci Resolve (manual workflow)")
    console.print(f"  3. Archive when done: sf archive {result.data['film_id']}")


if __name__ == "__main__":
    app()