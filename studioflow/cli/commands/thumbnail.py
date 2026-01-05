"""
Thumbnail Generation Commands
Auto-generate YouTube thumbnails with templates and text overlays
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import random

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from studioflow.core.state import StateManager
from studioflow.core.project import ProjectManager
from studioflow.core.config import get_config


console = Console()
app = typer.Typer()


# Thumbnail templates with compositions
THUMBNAIL_TEMPLATES = {
    "viral": {
        "style": "high_contrast",
        "text_size": "huge",
        "colors": ["#FF0000", "#FFFF00", "#00FF00"],  # Red, Yellow, Green
        "effects": ["drop_shadow", "stroke", "glow"],
        "arrow_count": 3,
        "emoji_count": 2,
        "face_zoom": 1.5
    },
    "modern": {
        "style": "clean",
        "text_size": "large",
        "colors": ["#FFFFFF", "#000000", "#0066CC"],  # Clean colors
        "effects": ["subtle_shadow"],
        "arrow_count": 0,
        "emoji_count": 0,
        "face_zoom": 1.0
    },
    "tutorial": {
        "style": "professional",
        "text_size": "medium",
        "colors": ["#FFFFFF", "#2196F3"],  # White on blue
        "effects": ["drop_shadow"],
        "arrow_count": 1,
        "emoji_count": 0,
        "face_zoom": 1.0
    },
    "gaming": {
        "style": "neon",
        "text_size": "huge",
        "colors": ["#FF00FF", "#00FFFF", "#FFFF00"],  # Neon colors
        "effects": ["glow", "stroke", "distort"],
        "arrow_count": 2,
        "emoji_count": 3,
        "face_zoom": 1.3
    },
    "minimal": {
        "style": "simple",
        "text_size": "small",
        "colors": ["#333333", "#FFFFFF"],
        "effects": [],
        "arrow_count": 0,
        "emoji_count": 0,
        "face_zoom": 0.8
    }
}

# Text positioning presets
TEXT_POSITIONS = {
    "top": "10,50",
    "center": "10,360",
    "bottom": "10,600",
    "top_left": "50,100",
    "top_right": "900,100",
    "bottom_left": "50,600",
    "bottom_right": "900,600"
}

# Emoji mappings for viral thumbnails
VIRAL_EMOJIS = ["😱", "🤯", "💰", "🔥", "⚠️", "🚨", "💯", "😮", "🎯", "⭐"]


def extract_frame_from_video(video_path: Path, output_path: Path, time: str = "00:00:05") -> bool:
    """Extract a frame from video at specified time"""
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-ss", time,  # Seek to time
        "-frames:v", "1",  # Extract 1 frame
        "-q:v", "2",  # Quality
        "-y",  # Overwrite
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        return result.returncode == 0
    except:
        return False


def apply_text_overlay(
    image_path: Path,
    output_path: Path,
    text: str,
    template: str = "modern",
    position: str = "center"
) -> bool:
    """Apply text overlay to image using ImageMagick or ffmpeg"""

    tmpl = THUMBNAIL_TEMPLATES[template]

    # Build ffmpeg filter for text overlay
    filters = []

    # Main text
    font_size = {
        "huge": 120,
        "large": 80,
        "medium": 60,
        "small": 40
    }.get(tmpl["text_size"], 60)

    # Get position coordinates
    pos = TEXT_POSITIONS.get(position, TEXT_POSITIONS["center"])

    # Primary text with effects
    text_color = tmpl["colors"][0].replace("#", "0x") + "FF"  # Add alpha

    drawtext = f"drawtext=text='{text}':fontsize={font_size}:fontcolor={text_color}:x={pos.split(',')[0]}:y={pos.split(',')[1]}"

    # Add effects
    if "drop_shadow" in tmpl["effects"]:
        drawtext += ":shadowcolor=black:shadowx=3:shadowy=3"

    if "stroke" in tmpl["effects"]:
        drawtext += f":borderw=3:bordercolor=black"

    filters.append(drawtext)

    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(image_path),
        "-vf", ",".join(filters),
        "-y",
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        return result.returncode == 0
    except Exception as e:
        console.print(f"[red]Error applying text: {e}[/red]")
        return False


def create_thumbnail_from_template(
    background: Path,
    text: str,
    template: str,
    output_path: Path
) -> bool:
    """Create thumbnail using template and background image"""

    # First resize to YouTube thumbnail size (1280x720)
    resized = output_path.parent / "resized_temp.jpg"

    resize_cmd = [
        "ffmpeg",
        "-i", str(background),
        "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
        "-y",
        str(resized)
    ]

    try:
        subprocess.run(resize_cmd, capture_output=True, timeout=10)

        # Apply text overlay
        success = apply_text_overlay(resized, output_path, text, template, "center")

        # Cleanup
        resized.unlink(missing_ok=True)

        return success

    except Exception as e:
        console.print(f"[red]Error creating thumbnail: {e}[/red]")
        return False


@app.command()
def generate(
    project_name: Optional[str] = None,
    text: Optional[str] = None,
    template: str = "modern",
    source: Optional[str] = None,
    time: str = "00:00:05",
    position: str = "center"
):
    """
    Generate a thumbnail for your video

    Templates: viral, modern, tutorial, gaming, minimal
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

    # Get text for thumbnail
    if not text:
        text = Prompt.ask("Thumbnail text", default=project_name.replace("_", " "))

    # Get source for background
    if not source:
        # Try to find a video in the project
        media_dir = project.path / "01_MEDIA"
        videos = list(media_dir.rglob("*.mp4")) + list(media_dir.rglob("*.mov"))

        if videos:
            source = videos[0]
            console.print(f"Using video: {source.name}")
        else:
            console.print("[red]No video found. Specify --source[/red]")
            return
    else:
        source = Path(source)

    # Create thumbnails directory
    thumb_dir = project.path / "06_THUMBNAILS"
    thumb_dir.mkdir(exist_ok=True)

    # Generate thumbnail
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    thumb_path = thumb_dir / f"thumbnail_{template}_{timestamp}.jpg"

    console.print(f"\nGenerating [cyan]{template}[/cyan] thumbnail...")
    console.print(f"  Text: {text}")
    console.print(f"  Position: {position}")

    # Extract frame if source is video
    if source.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
        frame_path = thumb_dir / "frame_temp.jpg"

        with console.status("Extracting frame..."):
            if not extract_frame_from_video(source, frame_path, time):
                console.print("[red]Failed to extract frame[/red]")
                return

        background = frame_path
    else:
        background = source

    # Create thumbnail
    with console.status("Creating thumbnail..."):
        if create_thumbnail_from_template(background, text, template, thumb_path):
            console.print(f"[green]✓[/green] Thumbnail created: {thumb_path}")

            # Cleanup temp frame
            if background != source:
                background.unlink(missing_ok=True)
        else:
            console.print("[red]Failed to create thumbnail[/red]")


@app.command()
def batch(
    project_name: Optional[str] = None,
    text: Optional[str] = None,
    templates: Optional[str] = None
):
    """
    Generate thumbnails in multiple styles at once
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

    # Get text
    if not text:
        text = Prompt.ask("Thumbnail text", default=project_name.replace("_", " "))

    # Get templates to use
    if templates:
        template_list = templates.split(",")
    else:
        template_list = ["viral", "modern", "tutorial"]

    # Find source video
    media_dir = project.path / "01_MEDIA"
    videos = list(media_dir.rglob("*.mp4")) + list(media_dir.rglob("*.mov"))

    if not videos:
        console.print("[red]No video found in project[/red]")
        return

    source = videos[0]

    # Create thumbnails directory
    thumb_dir = project.path / "06_THUMBNAILS"
    thumb_dir.mkdir(exist_ok=True)

    # Extract frame once
    frame_path = thumb_dir / "frame_temp.jpg"

    console.print(f"Extracting frame from: {source.name}")
    if not extract_frame_from_video(source, frame_path, "00:00:05"):
        console.print("[red]Failed to extract frame[/red]")
        return

    # Generate thumbnails in each template
    console.print(f"\nGenerating {len(template_list)} thumbnail variants...")

    results = []
    for tmpl in template_list:
        if tmpl not in THUMBNAIL_TEMPLATES:
            console.print(f"[yellow]Unknown template: {tmpl}[/yellow]")
            continue

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = thumb_dir / f"thumbnail_{tmpl}_{timestamp}.jpg"

        with console.status(f"Creating {tmpl} thumbnail..."):
            if create_thumbnail_from_template(frame_path, text, tmpl, output):
                console.print(f"  [green]✓[/green] {tmpl}: {output.name}")
                results.append((tmpl, output))
            else:
                console.print(f"  [red]✗[/red] {tmpl}: failed")

    # Cleanup
    frame_path.unlink(missing_ok=True)

    # Show summary
    if results:
        console.print(f"\n[green]Generated {len(results)} thumbnails:[/green]")
        table = Table(show_header=True)
        table.add_column("Template", style="cyan")
        table.add_column("File")

        for tmpl, path in results:
            table.add_row(tmpl, path.name)

        console.print(table)


@app.command()
def templates():
    """List available thumbnail templates"""

    table = Table(title="Thumbnail Templates", show_header=True)
    table.add_column("Template", style="cyan")
    table.add_column("Style")
    table.add_column("Text Size")
    table.add_column("Effects")

    for name, tmpl in THUMBNAIL_TEMPLATES.items():
        effects = ", ".join(tmpl["effects"])
        table.add_row(
            name,
            tmpl["style"],
            tmpl["text_size"],
            effects or "none"
        )

    console.print(table)

    console.print("\nUsage:")
    console.print("  sf thumbnail generate --template viral")
    console.print("  sf thumbnail batch --templates 'viral,modern,tutorial'")


@app.command()
def preview(
    project_name: Optional[str] = None
):
    """Preview all thumbnails in project"""
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

    thumb_dir = project.path / "06_THUMBNAILS"

    if not thumb_dir.exists():
        console.print("No thumbnails directory found")
        return

    thumbnails = list(thumb_dir.glob("*.jpg")) + list(thumb_dir.glob("*.png"))

    if not thumbnails:
        console.print("No thumbnails found")
        return

    console.print(f"Found {len(thumbnails)} thumbnails:\n")

    for thumb in sorted(thumbnails):
        size_mb = thumb.stat().st_size / (1024 * 1024)
        console.print(f"  • {thumb.name} ({size_mb:.2f} MB)")

    console.print(f"\nThumbnails location: [cyan]{thumb_dir}[/cyan]")