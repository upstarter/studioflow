"""
Eric's specific StudioFlow commands
Optimized for Sony FX30/ZVE10 → Resolve → YouTube workflow
"""

import typer
import json
import subprocess
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from datetime import datetime

from studioflow.core.my_config import MySetup
from studioflow.core.sony import SonyMediaHandler, SonyToResolve, SonyClip
from studioflow.core.ffmpeg import FFmpegProcessor, VideoQuality
from studioflow.core.youtube_api import YouTubeAPIService

console = Console()
app = typer.Typer()


# Episode Management (Updated to use new unified structure)
@app.command()
def episode(
    number: int = typer.Argument(..., help="Episode number"),
    title: str = typer.Argument(..., help="Episode title"),
    action: str = typer.Option("new", "--action", "-a", help="new/import/edit/export/upload")
):
    """Manage YouTube episodes (uses new 8-folder structure)"""
    from studioflow.core.project import create_episode

    if action == "new":
        # Use new unified create_episode function
        result = create_episode(number, title)

        if not result.success:
            console.print(f"[red]Error:[/red] {result.error}")
            raise typer.Exit(1)

        console.print("\n[bold cyan]Next steps:[/bold cyan]")
        console.print(f"  1. Import media: sf import-sony --output {result.project_path}/01_footage")
        console.print(f"  2. Edit in DaVinci Resolve")
        console.print(f"  3. Export: sf export-youtube EP{number:03d}")

    elif action == "import":
        # Import media for episode
        console.print(f"Importing media for Episode {number}")
        episode_id = f"EP{number:03d}_{title.replace(' ', '_')}"
        episode_path = Path(f"/mnt/library/EPISODES/{episode_id}")
        import_sony(episode_path / "01_footage")

    elif action == "export":
        # Export episode with YouTube settings
        episode_id = f"EP{number:03d}_{title.replace(' ', '_')}"
        episode_path = Path(f"/mnt/library/EPISODES/{episode_id}")
        resolve_file = episode_path / "03_resolve" / "PROJECT" / f"{episode_id}.drp"
        if resolve_file.exists():
            export_youtube(resolve_file, episode_path / "05_exports")
        else:
            console.print("[red]No Resolve project found[/red]")
            console.print(f"Expected: {resolve_file}")


@app.command()
def import_sony(
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    card_path: Optional[Path] = typer.Option(None, "--card", "-c", help="Camera card path"),
    smart_folders: bool = typer.Option(False, "--smart-folders", help="Analyze folder structure"),
    smart_marks: bool = typer.Option(False, "--smart-marks", help="Detect protection marks"),
    organize_by_scene: bool = typer.Option(False, "--organize-scenes", help="Organize by folder scenes")
):
    """Import from Sony FX30/ZV-E10 cameras with intelligent organization"""

    # Default paths for camera cards
    if not card_path:
        # Check common mount points
        possible_paths = [
            Path("/media") / "FX30",
            Path("/media") / "ZVE10",
            Path("/Volumes") / "SONY",
            Path("/mnt") / "camera"
        ]

        for path in possible_paths:
            if path.exists():
                card_path = path
                break

        if not card_path:
            card_path = Path("/media/camera")  # fallback

    if not output_dir:
        output_dir = Path.cwd() / "01_RAW"

    console.print(f"🎬 Importing Sony media from: {card_path}")

    # Enhanced import with folder intelligence
    if smart_folders:
        from studioflow.core.folder_intelligence import FolderIntelligence

        folder_ai = FolderIntelligence()
        shoot_structure = folder_ai.analyze_folder_structure(card_path)

        # Show folder analysis
        console.print(Panel(folder_ai.generate_folder_report(shoot_structure), title="📁 Folder Structure Analysis"))

        # Organize by folder structure
        if organize_by_scene:
            organize_by_folder_structure(shoot_structure, output_dir)
            return

    # Traditional Sony clip detection
    clips = SonyMediaHandler.detect_sony_media(card_path)

    # Enhanced marking detection
    if smart_marks:
        from studioflow.core.safe_marking import SafeMarkingWorkflow

        marking_workflow = SafeMarkingWorkflow()
        marking_results = marking_workflow.process_card(card_path)

        console.print(f"\n🔍 Smart Marking Analysis:")
        console.print(f"   🔒 Protected clips: {marking_results['protected_clips']}")
        console.print(f"   ⭐ Hero clips: {len(marking_results['hero_clips'])}")
        console.print(f"   ✅ Good clips: {len(marking_results['good_clips'])}")

    # Show summary
    fx30_count = len(clips.get("fx30", []))
    zve10_count = len(clips.get("zve10", []))

    if fx30_count == 0 and zve10_count == 0:
        console.print("[yellow]No Sony media found[/yellow]")
        return

    # Display found clips
    table = Table(title="Sony Media Detected")
    table.add_column("Camera", style="cyan")
    table.add_column("Clips", style="yellow")
    table.add_column("Duration", style="green")
    table.add_column("Size", style="white")

    if fx30_count > 0:
        fx30_clips = clips["fx30"]
        duration = sum(c.duration for c in fx30_clips) / 60
        size = sum(c.file_size_gb for c in fx30_clips)
        table.add_row("FX30", str(fx30_count), f"{duration:.1f} min", f"{size:.1f} GB")

    if zve10_count > 0:
        zve10_clips = clips["zve10"]
        duration = sum(c.duration for c in zve10_clips) / 60
        size = sum(c.file_size_gb for c in zve10_clips)
        table.add_row("ZV-E10", str(zve10_count), f"{duration:.1f} min", f"{size:.1f} GB")

    console.print(table)

    # Organize by camera
    if typer.confirm("Import and organize?"):
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Organizing media...", total=None)
            SonyMediaHandler.organize_by_camera(clips, output_dir)

        # Generate report
        report = SonyMediaHandler.generate_camera_report(clips)
        console.print(Panel(report, title="Import Complete"))

        # Create proxies?
        if typer.confirm("Generate editing proxies?"):
            create_proxies(output_dir)


@app.command()
def create_proxies(
    media_dir: Path = typer.Argument(..., help="Directory with media files")
):
    """Create ProRes proxies for Resolve"""

    media_files = list(media_dir.rglob("*.MP4"))
    if not media_files:
        console.print("[yellow]No media files found[/yellow]")
        return

    proxy_dir = media_dir.parent / "02_Proxies"
    proxy_dir.mkdir(exist_ok=True)

    console.print(f"Creating proxies for {len(media_files)} files...")

    with Progress() as progress:
        task = progress.add_task("[cyan]Creating proxies...", total=len(media_files))

        for file in media_files:
            # Detect camera
            camera = MySetup.detect_camera_from_file(file)

            clip = SonyClip(
                file_path=file,
                camera=camera,
                clip_name=file.stem,
                date_shot=datetime.fromtimestamp(file.stat().st_mtime),
                duration=0,
                resolution="",
                framerate=29.97,
                color_profile="S-Log3" if camera == "fx30" else "Standard",
                file_size_gb=file.stat().st_size / (1024**3)
            )

            proxy_path = SonyMediaHandler.create_proxy_media(clip, proxy_dir)
            if proxy_path:
                console.print(f"  ✅ {file.name} → {proxy_path.name}")

            progress.update(task, advance=1)

    console.print("[green]✅ Proxies created[/green]")


@app.command()
def grade(
    video_path: Path = typer.Argument(..., help="Video to grade"),
    lut: str = typer.Option("orange-teal", "--lut", "-l", help="LUT to apply"),
    output: Optional[Path] = typer.Option(None, "--output", "-o")
):
    """Apply color grade with Eric's LUTs"""

    if not output:
        output = video_path.parent / f"{video_path.stem}_graded{video_path.suffix}"

    # Map friendly names to config
    lut_map = {
        "orange-teal": "orange_teal",
        "ot": "orange_teal",
        "cinematic": "cinematic",
        "youtube": "youtube",
        "slog3": "sony_slog3_rec709"
    }

    lut_name = lut_map.get(lut.lower(), "orange_teal")

    console.print(f"Applying {lut_name} grade...")

    result = SonyToResolve.apply_orange_teal_grade(video_path, output)

    if result.success:
        console.print(f"[green]✅ Graded: {output}[/green]")
    else:
        console.print(f"[red]Failed: {result.error_message}[/red]")


@app.command()
def export_youtube(
    input_file: Path = typer.Argument(..., help="Video to export"),
    quality: str = typer.Option("4k", "--quality", "-q", help="4k/1080/short"),
    output_dir: Optional[Path] = typer.Option(None, "--dir", "-d")
):
    """Export with YouTube optimized settings"""

    if not output_dir:
        output_dir = input_file.parent

    # YouTube specs
    specs = {
        "4k": {
            "resolution": "3840x2160",
            "bitrate": 45000,  # YouTube recommended
            "preset": "youtube_4k"
        },
        "1080": {
            "resolution": "1920x1080",
            "bitrate": 8000,
            "preset": "youtube_1080"
        },
        "short": {
            "resolution": "1080x1920",  # Vertical
            "bitrate": 12000,
            "preset": "youtube_short"
        }
    }

    spec = specs.get(quality, specs["4k"])
    output_file = output_dir / f"{input_file.stem}_youtube_{quality}.mp4"

    console.print(f"Exporting for YouTube {quality.upper()}...")
    console.print(f"  Resolution: {spec['resolution']}")
    console.print(f"  Bitrate: {spec['bitrate']} kbps")
    console.print(f"  Audio: -14 LUFS (YouTube standard)")

    # Export with YouTube settings
    cmd = [
        "ffmpeg", "-i", str(input_file),
        "-vf", f"scale={spec['resolution']}",
        "-c:v", "libx264",
        "-preset", "slow",
        "-b:v", f"{spec['bitrate']}k",
        "-maxrate", f"{int(spec['bitrate'] * 1.5)}k",
        "-bufsize", f"{spec['bitrate'] * 2}k",
        "-profile:v", "high",
        "-level", "4.2",
        "-c:a", "aac",
        "-b:a", "320k",
        "-ar", "48000",
        "-af", "loudnorm=I=-14:TP=-1:LRA=11",  # YouTube loudness
        "-movflags", "+faststart",  # Optimize for streaming
        "-y", str(output_file)
    ]

    with Progress() as progress:
        task = progress.add_task("[cyan]Exporting...", total=100)
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)

        for line in process.stderr:
            # Parse FFmpeg progress (simplified)
            if "time=" in line:
                progress.update(task, advance=1)

        process.wait()

    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024**2)
        console.print(f"[green]✅ Exported: {output_file} ({size_mb:.1f} MB)[/green]")

        # Check YouTube requirements
        if quality == "4k" and size_mb > 128000:  # 128GB limit
            console.print("[yellow]⚠️  File exceeds YouTube's 128GB limit[/yellow]")
    else:
        console.print("[red]Export failed[/red]")


@app.command()
def upload_episode(
    video_file: Path = typer.Argument(..., help="Video file to upload"),
    episode_number: int = typer.Argument(..., help="Episode number"),
    title: str = typer.Argument(..., help="Episode title"),
    description: Optional[str] = typer.Option("", "--desc", "-d")
):
    """Upload episode to YouTube with metadata"""

    # Generate YouTube metadata
    metadata = MySetup.get_youtube_metadata(episode_number, title, description)

    console.print(f"Uploading Episode {episode_number}: {title}")
    console.print(f"  Title: {metadata['title']}")
    console.print(f"  Tags: {', '.join(metadata['tags'][:3])}...")

    # Upload to YouTube
    service = YouTubeAPIService()
    result = service.upload_video(
        video_path=video_file,
        title=metadata["title"],
        description=metadata["description"],
        tags=metadata["tags"],
        category=metadata["category"],
        privacy_status=metadata["visibility"]
    )

    if result and result.get("id"):
        video_id = result["id"]
        url = f"https://youtube.com/watch?v={video_id}"
        console.print(f"[green]✅ Uploaded successfully![/green]")
        console.print(f"   URL: {url}")

        # Save URL to episode metadata
        episode_path = video_file.parent.parent
        metadata_file = episode_path / "episode.json"
        if metadata_file.exists():
            import json
            data = json.loads(metadata_file.read_text())
            data["youtube_url"] = url
            data["youtube_id"] = video_id
            data["uploaded"] = datetime.now().isoformat()
            metadata_file.write_text(json.dumps(data, indent=2))
    else:
        console.print("[red]Upload failed[/red]")


@app.command()
def check_lufs(
    video_file: Path = typer.Argument(..., help="Video to check")
):
    """Check if audio meets YouTube -14 LUFS standard"""

    console.print("Analyzing audio levels...")

    # Analyze loudness
    cmd = [
        "ffmpeg", "-i", str(video_file),
        "-af", "loudnorm=I=-14:print_format=json",
        "-f", "null", "-"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Parse loudness from stderr
        import re
        import json

        # Find JSON in output
        json_match = re.search(r'\{[^}]+\}', result.stderr[::-1])
        if json_match:
            stats = json.loads(json_match.group()[::-1])

            input_i = float(stats.get("input_i", -99))
            input_tp = float(stats.get("input_tp", -99))
            input_lra = float(stats.get("input_lra", 0))

            # Display results
            table = Table(title="Audio Loudness Analysis")
            table.add_column("Measurement", style="cyan")
            table.add_column("Current", style="yellow")
            table.add_column("YouTube Target", style="green")
            table.add_column("Status", style="white")

            # Integrated loudness
            lufs_status = "✅" if -15 <= input_i <= -13 else "❌"
            table.add_row(
                "Integrated Loudness",
                f"{input_i:.1f} LUFS",
                "-14 LUFS",
                lufs_status
            )

            # True peak
            tp_status = "✅" if input_tp <= -1 else "⚠️"
            table.add_row(
                "True Peak",
                f"{input_tp:.1f} dB",
                "-1 dB max",
                tp_status
            )

            # Loudness range
            lra_status = "✅" if 7 <= input_lra <= 20 else "⚠️"
            table.add_row(
                "Loudness Range",
                f"{input_lra:.1f} LU",
                "7-20 LU",
                lra_status
            )

            console.print(table)

            # Recommendations
            if input_i < -15:
                console.print("\n[yellow]Audio is too quiet. YouTube will turn it up.[/yellow]")
                console.print("Fix: sf fix video.mp4 quiet")
            elif input_i > -13:
                console.print("\n[yellow]Audio is too loud. YouTube will turn it down.[/yellow]")
                console.print("Fix: sf normalize video.mp4")
            else:
                console.print("\n[green]✅ Audio levels are perfect for YouTube![/green]")

    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")


@app.command()
def short(
    video_file: Path = typer.Argument(..., help="Video to convert to short"),
    start: Optional[float] = typer.Option(None, "--start", "-s", help="Start time"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Short title")
):
    """Create YouTube Short (vertical, <60s)"""

    output = video_file.parent / f"{video_file.stem}_short.mp4"

    console.print("Creating YouTube Short...")

    # Get video info
    info = FFmpegProcessor.get_media_info(video_file)
    duration = info.get("duration_seconds", 60)

    # Calculate best 60 second segment if not specified
    if start is None:
        start = max(0, (duration - 60) / 2)  # Middle minute

    # Convert to vertical format with YouTube Shorts specs
    cmd = [
        "ffmpeg", "-i", str(video_file),
        "-ss", str(start),
        "-t", "60",  # Max 60 seconds
        "-vf", (
            "crop=ih*9/16:ih,"  # Crop to 9:16
            "scale=1080:1920"  # YouTube Shorts resolution
        ),
        "-c:v", "libx264",
        "-preset", "medium",
        "-b:v", "12000k",  # Higher bitrate for shorts
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "48000"
    ]

    if title:
        # Add title text overlay
        cmd[5] += f",drawtext=text='{title}':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=100:enable='lt(t,3)'"

    cmd.extend(["-y", str(output)])

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        console.print(f"[green]✅ Short created: {output}[/green]")
        console.print("  Duration: <60 seconds ✅")
        console.print("  Format: 9:16 vertical ✅")
        console.print("  Ready for YouTube Shorts!")
    except subprocess.CalledProcessError:
        console.print("[red]Failed to create short[/red]")


@app.command()
def my_workflow(
    card_path: Path = typer.Argument(..., help="Camera card path")
):
    """Eric's complete workflow: Import → Grade → Export → Upload"""

    console.print(Panel("🎬 Eric's YouTube Episode Workflow", style="bold cyan"))

    # Step 1: Import
    console.print("\n[cyan]Step 1: Importing Sony media...[/cyan]")
    clips = SonyMediaHandler.detect_sony_media(card_path)

    # Step 2: Create episode
    episode_num = int(input("Episode number: "))
    episode_title = input("Episode title: ")

    episode_path = MySetup.get_episode_path(episode_num, episode_title.replace(" ", "_"))
    episode_path.mkdir(parents=True, exist_ok=True)

    # Organize media
    SonyMediaHandler.organize_by_camera(clips, episode_path / "01_RAW")

    # Step 3: Create proxies
    console.print("\n[cyan]Step 2: Creating ProRes proxies...[/cyan]")
    create_proxies(episode_path / "01_RAW")

    # Step 4: Generate Resolve timeline
    console.print("\n[cyan]Step 3: Creating Resolve timeline...[/cyan]")
    all_clips = clips.get("fx30", []) + clips.get("zve10", [])
    timeline = SonyToResolve.create_timeline_from_sony(all_clips, f"EP{episode_num:03d}_{episode_title}")
    console.print(f"  Timeline: {timeline}")

    console.print("\n[yellow]Step 4: Edit in DaVinci Resolve[/yellow]")
    console.print("  1. Import the timeline XML")
    console.print("  2. Apply S-Log3 to Rec.709 LUT")
    console.print("  3. Apply orange/teal grade")
    console.print("  4. Export with YouTube 4K preset")

    console.print("\n[cyan]Ready for editing in Resolve![/cyan]")


if __name__ == "__main__":
    app()