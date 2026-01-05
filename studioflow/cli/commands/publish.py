"""
Publish/Export Commands for Various Platforms
Handles rendering and uploading to YouTube, Instagram, TikTok
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from studioflow.core.state import StateManager
from studioflow.core.project import ProjectManager
from studioflow.core.config import get_config, Platform


console = Console()
app = typer.Typer()


# Platform-specific export settings
PLATFORM_SETTINGS = {
    "youtube": {
        "resolution": "3840x2160",  # 4K
        "framerate": 29.97,
        "bitrate": "45M",
        "codec": "h264",
        "audio_bitrate": "320k",
        "format": "mp4",
        "aspect": "16:9"
    },
    "instagram": {
        "resolution": "1080x1080",  # Square for feed
        "framerate": 30,
        "bitrate": "8M",
        "codec": "h264",
        "audio_bitrate": "128k",
        "format": "mp4",
        "aspect": "1:1",
        "max_duration": 60  # seconds for feed posts
    },
    "instagram_reels": {
        "resolution": "1080x1920",  # Vertical
        "framerate": 30,
        "bitrate": "10M",
        "codec": "h264",
        "audio_bitrate": "128k",
        "format": "mp4",
        "aspect": "9:16",
        "max_duration": 90
    },
    "tiktok": {
        "resolution": "1080x1920",
        "framerate": 30,
        "bitrate": "12M",
        "codec": "h264",
        "audio_bitrate": "192k",
        "format": "mp4",
        "aspect": "9:16",
        "max_duration": 180  # 3 minutes
    },
    "twitter": {
        "resolution": "1280x720",
        "framerate": 30,
        "bitrate": "5M",
        "codec": "h264",
        "audio_bitrate": "128k",
        "format": "mp4",
        "aspect": "16:9",
        "max_duration": 140
    }
}


def render_for_platform(project_path: Path, platform: str, output_path: Path) -> bool:
    """
    Render video with platform-specific settings using ffmpeg
    """
    settings = PLATFORM_SETTINGS.get(platform, PLATFORM_SETTINGS["youtube"])

    # Find the main timeline/edit file (this would come from Resolve export)
    # For now, we'll look for any video in the project
    source_video = None
    media_dir = project_path / "01_MEDIA"

    if media_dir.exists():
        for ext in [".mp4", ".mov", ".mxf"]:
            videos = list(media_dir.rglob(f"*{ext}"))
            if videos:
                source_video = videos[0]  # Use first video as source
                break

    if not source_video:
        console.print("[red]No source video found in project[/red]")
        return False

    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(source_video),
        "-c:v", settings["codec"],
        "-b:v", settings["bitrate"],
        "-r", str(settings["framerate"]),
        "-s", settings["resolution"],
        "-c:a", "aac",
        "-b:a", settings["audio_bitrate"],
        "-movflags", "+faststart",  # For streaming
        "-y",  # Overwrite output
        str(output_path)
    ]

    # Add duration limit if specified
    if "max_duration" in settings:
        cmd.extend(["-t", str(settings["max_duration"])])

    try:
        # Run ffmpeg with progress
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Parse ffmpeg output for progress
        for line in process.stderr:
            if "time=" in line:
                # Extract time for progress
                console.print(f"  Encoding: {line.strip()}", end="\r")

        process.wait()
        return process.returncode == 0

    except FileNotFoundError:
        console.print("[red]ffmpeg not found. Please install ffmpeg.[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Render error: {e}[/red]")
        return False


@app.command()
def youtube(
    project_name: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    privacy: str = "private",
    upload: bool = True
):
    """
    Publish video to YouTube with optimal settings
    """
    state = StateManager()
    project_name = project_name or state.current_project

    if not project_name:
        console.print("[red]No project selected[/red]")
        return

    manager = ProjectManager()
    project = manager.get_project(project_name)

    if not project:
        console.print(f"[red]Project not found: {project_name}[/red]")
        return

    # Get video metadata
    if not title:
        title = Prompt.ask("Video title", default=project_name)

    if not description:
        # Check for description file
        desc_file = project.path / "07_DESCRIPTIONS" / "youtube.txt"
        if desc_file.exists():
            description = desc_file.read_text()
        else:
            description = Prompt.ask("Video description", default=f"Created with StudioFlow")

    if not tags:
        tags = Prompt.ask("Tags (comma separated)", default="")

    console.print(Panel(
        f"[bold]Publishing to YouTube[/bold]\n\n"
        f"Title: {title}\n"
        f"Privacy: {privacy}\n"
        f"Tags: {tags}",
        title="YouTube Upload",
        border_style="cyan"
    ))

    # Render video with YouTube settings
    output_path = project.path / "05_RENDERS" / f"{project_name}_youtube.mp4"
    output_path.parent.mkdir(exist_ok=True)

    with console.status("Rendering for YouTube..."):
        if not render_for_platform(project.path, "youtube", output_path):
            console.print("[red]Failed to render video[/red]")
            return

    file_size = output_path.stat().st_size / (1024**3)
    console.print(f"[green]✓[/green] Rendered video: {output_path.name} ({file_size:.2f} GB)")

    if upload:
        # YouTube upload would go here
        # This requires YouTube API setup which is complex
        console.print("\n[yellow]YouTube API upload not yet implemented[/yellow]")
        console.print("Video is ready at:")
        console.print(f"  [cyan]{output_path}[/cyan]")
        console.print("\nYou can upload manually at: https://youtube.com/upload")

    # Save metadata for future reference
    metadata = {
        "title": title,
        "description": description,
        "tags": tags.split(",") if tags else [],
        "rendered_at": datetime.now().isoformat(),
        "file": str(output_path),
        "platform": "youtube"
    }

    import json
    metadata_file = project.path / ".studioflow" / "youtube_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    console.print(f"\n[green]✓[/green] Metadata saved for future uploads")


@app.command()
def instagram(
    project_name: Optional[str] = None,
    post_type: str = "reels"  # reels, feed, story
):
    """
    Prepare video for Instagram (Reels/Feed/Story)
    """
    state = StateManager()
    project_name = project_name or state.current_project

    if not project_name:
        console.print("[red]No project selected[/red]")
        return

    manager = ProjectManager()
    project = manager.get_project(project_name)

    if not project:
        console.print(f"[red]Project not found: {project_name}[/red]")
        return

    # Determine platform variant
    if post_type == "reels":
        platform = "instagram_reels"
    else:
        platform = "instagram"

    output_path = project.path / "05_RENDERS" / f"{project_name}_{platform}.mp4"
    output_path.parent.mkdir(exist_ok=True)

    console.print(f"Rendering for Instagram {post_type.title()}...")

    with console.status(f"Rendering for {platform}..."):
        if not render_for_platform(project.path, platform, output_path):
            console.print("[red]Failed to render video[/red]")
            return

    settings = PLATFORM_SETTINGS[platform]
    console.print(f"[green]✓[/green] Video ready for Instagram {post_type.title()}:")
    console.print(f"  Resolution: {settings['resolution']}")
    console.print(f"  Aspect: {settings['aspect']}")
    console.print(f"  Max duration: {settings.get('max_duration', 'unlimited')} seconds")
    console.print(f"  File: [cyan]{output_path}[/cyan]")


@app.command()
def tiktok(
    project_name: Optional[str] = None
):
    """
    Prepare video for TikTok
    """
    state = StateManager()
    project_name = project_name or state.current_project

    if not project_name:
        console.print("[red]No project selected[/red]")
        return

    manager = ProjectManager()
    project = manager.get_project(project_name)

    if not project:
        console.print(f"[red]Project not found: {project_name}[/red]")
        return

    output_path = project.path / "05_RENDERS" / f"{project_name}_tiktok.mp4"
    output_path.parent.mkdir(exist_ok=True)

    with console.status("Rendering for TikTok..."):
        if not render_for_platform(project.path, "tiktok", output_path):
            console.print("[red]Failed to render video[/red]")
            return

    settings = PLATFORM_SETTINGS["tiktok"]
    console.print(f"[green]✓[/green] Video ready for TikTok:")
    console.print(f"  Resolution: {settings['resolution']} (vertical)")
    console.print(f"  Max duration: {settings['max_duration']} seconds")
    console.print(f"  File: [cyan]{output_path}[/cyan]")


@app.command()
def all(
    project_name: Optional[str] = None
):
    """
    Render for all major platforms
    """
    state = StateManager()
    project_name = project_name or state.current_project

    if not project_name:
        console.print("[red]No project selected[/red]")
        return

    platforms = ["youtube", "instagram_reels", "tiktok", "twitter"]

    console.print(f"Rendering for all platforms...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:

        task = progress.add_task("Rendering...", total=len(platforms))

        for platform in platforms:
            progress.update(task, description=f"Rendering for {platform}...")

            manager = ProjectManager()
            project = manager.get_project(project_name)
            output_path = project.path / "05_RENDERS" / f"{project_name}_{platform}.mp4"
            output_path.parent.mkdir(exist_ok=True)

            if render_for_platform(project.path, platform, output_path):
                console.print(f"  [green]✓[/green] {platform}")
            else:
                console.print(f"  [red]✗[/red] {platform}")

            progress.advance(task)

    console.print(f"\n[green]✓[/green] Multi-platform render complete!")
    console.print(f"Check renders in: {project.path / '05_RENDERS'}")