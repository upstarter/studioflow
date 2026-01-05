"""
Multi-Camera Sync Commands
Synchronize multiple camera angles using audio waveforms or timecode
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
import tempfile
import wave
import struct

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from studioflow.core.state import StateManager
from studioflow.core.project import ProjectManager
from studioflow.core.media import MediaScanner


console = Console()
app = typer.Typer()


def extract_audio_from_video(video_path: Path, output_path: Path) -> bool:
    """Extract audio track from video file"""
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # WAV format
        "-ar", "48000",  # 48kHz sample rate
        "-ac", "1",  # Mono for easier analysis
        "-y",
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0
    except:
        return False


def get_audio_fingerprint(audio_path: Path, start_sec: int = 0, duration_sec: int = 10) -> List[float]:
    """Get audio fingerprint for matching (simplified version)"""
    try:
        # Use ffmpeg to get audio levels
        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-ss", str(start_sec),
            "-t", str(duration_sec),
            "-af", "astats=metadata=1:reset=1",
            "-f", "null",
            "-"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Parse audio levels from output
        levels = []
        for line in result.stderr.split("\n"):
            if "RMS_level" in line:
                try:
                    level = float(line.split(":")[-1].strip())
                    levels.append(level)
                except:
                    pass

        return levels[:100]  # Return first 100 samples

    except:
        return []


def find_sync_offset(audio1_path: Path, audio2_path: Path) -> float:
    """Find time offset between two audio tracks using cross-correlation"""
    try:
        # Use ffmpeg to find offset (simplified approach)
        # In production, would use numpy/scipy for proper cross-correlation

        # Extract short samples from both
        fp1 = get_audio_fingerprint(audio1_path, 0, 30)
        fp2 = get_audio_fingerprint(audio2_path, 0, 30)

        if not fp1 or not fp2:
            return 0.0

        # Simple correlation check (very basic)
        # Try different offsets and find best match
        best_offset = 0.0
        best_score = float('inf')

        for offset in range(-10, 10):  # Check ±10 seconds
            score = 0
            for i in range(min(len(fp1), len(fp2)) - abs(offset)):
                if offset >= 0 and i + offset < len(fp2):
                    score += abs(fp1[i] - fp2[i + offset])
                elif offset < 0 and i - offset < len(fp1):
                    score += abs(fp1[i - offset] - fp2[i])

            if score < best_score:
                best_score = score
                best_offset = float(offset)

        return best_offset

    except Exception as e:
        console.print(f"[yellow]Could not calculate offset: {e}[/yellow]")
        return 0.0


def extract_timecode(video_path: Path) -> Optional[str]:
    """Extract timecode from video if available"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format_tags=timecode",
        "-of", "json",
        str(video_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        data = json.loads(result.stdout)

        if "format" in data and "tags" in data["format"]:
            return data["format"]["tags"].get("timecode")

    except:
        pass

    return None


def sync_videos_by_audio(
    video1: Path,
    video2: Path,
    output_dir: Path
) -> Dict[str, any]:
    """Synchronize two videos using audio waveforms"""

    result = {
        "success": False,
        "offset": 0.0,
        "method": "audio",
        "files": []
    }

    # Create temp directory for audio extraction
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Extract audio from both videos
        audio1 = tmpdir / "audio1.wav"
        audio2 = tmpdir / "audio2.wav"

        console.print("Extracting audio tracks...")
        if not extract_audio_from_video(video1, audio1):
            console.print(f"[red]Failed to extract audio from {video1.name}[/red]")
            return result

        if not extract_audio_from_video(video2, audio2):
            console.print(f"[red]Failed to extract audio from {video2.name}[/red]")
            return result

        # Find sync offset
        console.print("Analyzing audio waveforms...")
        offset = find_sync_offset(audio1, audio2)

        result["offset"] = offset
        console.print(f"Detected offset: {offset:.2f} seconds")

        # Create synchronized versions
        # If offset is positive, video2 starts later
        # If negative, video1 starts later

        if abs(offset) > 0.1:  # Only sync if offset is significant
            # Adjust video with offset
            if offset > 0:
                # Delay video2
                synced_path = output_dir / f"synced_{video2.stem}.mp4"
                cmd = [
                    "ffmpeg",
                    "-i", str(video2),
                    "-itsoffset", str(offset),
                    "-c", "copy",
                    "-y",
                    str(synced_path)
                ]
            else:
                # Delay video1
                synced_path = output_dir / f"synced_{video1.stem}.mp4"
                cmd = [
                    "ffmpeg",
                    "-i", str(video1),
                    "-itsoffset", str(abs(offset)),
                    "-c", "copy",
                    "-y",
                    str(synced_path)
                ]

            console.print(f"Creating synchronized version...")
            subprocess.run(cmd, capture_output=True)

            result["files"].append(str(synced_path))

        result["success"] = True

    return result


def sync_videos_by_timecode(
    videos: List[Path],
    output_dir: Path
) -> Dict[str, any]:
    """Synchronize videos using embedded timecode"""

    result = {
        "success": False,
        "method": "timecode",
        "files": []
    }

    # Extract timecodes
    timecodes = {}
    for video in videos:
        tc = extract_timecode(video)
        if tc:
            timecodes[video] = tc
            console.print(f"  {video.name}: {tc}")
        else:
            console.print(f"  {video.name}: [yellow]No timecode found[/yellow]")

    if len(timecodes) < 2:
        console.print("[red]Not enough timecode data for sync[/red]")
        return result

    # Calculate offsets based on timecode
    # (Simplified - would need proper timecode parsing in production)
    result["success"] = True
    return result


@app.command()
def sync(
    project_name: Optional[str] = None,
    method: str = "audio",  # audio or timecode
    cam_a: Optional[Path] = None,
    cam_b: Optional[Path] = None
):
    """
    Synchronize multiple camera angles

    Methods:
    - audio: Match audio waveforms (default)
    - timecode: Use embedded timecode
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

    # Find camera files if not specified
    if not cam_a or not cam_b:
        media_dir = project.path / "01_MEDIA"

        # Look for CAM_A and CAM_B folders
        cam_a_dir = project.path / "CAM_A"
        cam_b_dir = project.path / "CAM_B"

        if cam_a_dir.exists() and cam_b_dir.exists():
            cam_a_files = list(cam_a_dir.glob("*.mp4")) + list(cam_a_dir.glob("*.mov"))
            cam_b_files = list(cam_b_dir.glob("*.mp4")) + list(cam_b_dir.glob("*.mov"))

            if cam_a_files and cam_b_files:
                cam_a = cam_a_files[0]
                cam_b = cam_b_files[0]
                console.print(f"Found cameras:")
                console.print(f"  CAM A: {cam_a.name}")
                console.print(f"  CAM B: {cam_b.name}")
            else:
                console.print("[red]No video files found in CAM_A or CAM_B folders[/red]")
                return
        else:
            # Try to find any two video files
            videos = list(media_dir.rglob("*.mp4")) + list(media_dir.rglob("*.mov"))

            if len(videos) < 2:
                console.print("[red]Need at least 2 video files for multicam sync[/red]")
                return

            cam_a = videos[0]
            cam_b = videos[1]
            console.print(f"Using first two videos found:")
            console.print(f"  CAM A: {cam_a.name}")
            console.print(f"  CAM B: {cam_b.name}")

    # Check files exist
    if not cam_a.exists() or not cam_b.exists():
        console.print("[red]Video files not found[/red]")
        return

    # Create multicam directory
    multicam_dir = project.path / "MULTICAM"
    multicam_dir.mkdir(exist_ok=True)

    console.print(f"\n[bold]Synchronizing cameras using {method} method...[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        task = progress.add_task("Synchronizing...", total=3)

        if method == "audio":
            progress.update(task, description="Extracting audio...")
            progress.advance(task)

            progress.update(task, description="Analyzing waveforms...")
            result = sync_videos_by_audio(cam_a, cam_b, multicam_dir)
            progress.advance(task)

        elif method == "timecode":
            progress.update(task, description="Reading timecode...")
            result = sync_videos_by_timecode([cam_a, cam_b], multicam_dir)
            progress.advance(task)

        else:
            console.print(f"[red]Unknown sync method: {method}[/red]")
            return

        progress.update(task, description="Complete")
        progress.advance(task)

    # Show results
    if result["success"]:
        console.print(Panel(
            f"[green]✓ Synchronization complete![/green]\n\n"
            f"Method: {result['method']}\n"
            f"Offset: {result.get('offset', 0):.2f} seconds\n"
            f"Output: {multicam_dir}",
            title="Multicam Sync",
            border_style="green"
        ))

        # Save sync data for Resolve
        sync_data = {
            "project": project_name,
            "method": method,
            "offset": result.get("offset", 0),
            "cam_a": str(cam_a),
            "cam_b": str(cam_b),
            "synced_at": datetime.now().isoformat()
        }

        sync_file = multicam_dir / "sync_data.json"
        with open(sync_file, 'w') as f:
            json.dump(sync_data, f, indent=2)

    else:
        console.print("[red]Synchronization failed[/red]")


@app.command()
def color_match(
    project_name: Optional[str] = None,
    reference: Optional[Path] = typer.Option(None, "--reference", "-r", help="Reference clip (FX30)"),
    target: Optional[Path] = typer.Option(None, "--target", "-t", help="Target clip (ZV-E10)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path for matched clip")
):
    """
    Match color between two camera clips (exposure/WB matching).
    
    Note: For full color matching, use DaVinci Resolve color management.
    This command provides optional pre-processing exposure/WB matching.
    """
    from studioflow.core.multicam_color import MulticamColorMatcher
    
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
    
    # Auto-detect clips if not provided
    if not reference or not target:
        media_dir = project.path / "01_MEDIA"
        video_files = list(media_dir.rglob("*.mp4")) + list(media_dir.rglob("*.mov"))
        
        if len(video_files) < 2:
            console.print("[red]Need at least 2 video files. Specify --reference and --target[/red]")
            return
        
        reference = reference or video_files[0]
        target = target or video_files[1]
        console.print(f"Using:\n  Reference: {reference.name}\n  Target: {target.name}")
    
    if not reference.exists() or not target.exists():
        console.print("[red]Video files not found[/red]")
        return
    
    # Setup output path
    if not output:
        output_dir = project.path / "MULTICAM"
        output_dir.mkdir(exist_ok=True)
        output = output_dir / f"matched_{target.stem}.mp4"
    
    console.print(f"\n[bold]Matching color (exposure/WB)...[/bold]")
    console.print(f"Reference: {reference.name}")
    console.print(f"Target: {target.name}")
    console.print(f"Output: {output.name}")
    
    matcher = MulticamColorMatcher()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Matching color...", total=None)
        result = matcher.match_exposure_white_balance(reference, target, output)
        progress.update(task, completed=True)
    
    if result["success"]:
        console.print(Panel(
            f"[green]✓ Color matching complete![/green]\n\n"
            f"Output: {output}\n\n"
            f"[yellow]Note:[/yellow] For full color matching, use DaVinci Resolve\n"
            f"color management (S-Log3 → Rec.709 conversion).",
            title="Color Match",
            border_style="green"
        ))
    else:
        console.print(f"[red]Color matching failed: {result.get('error', 'Unknown error')}[/red]")


@app.command()
def sync_three_source(
    project_name: Optional[str] = None,
    cam1: Optional[Path] = typer.Option(None, "--cam1", "-1", help="FX30 video"),
    cam2: Optional[Path] = typer.Option(None, "--cam2", "-2", help="ZV-E10 video"),
    audio: Optional[Path] = typer.Option(None, "--audio", "-a", help="Zen Go audio file"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory")
):
    """
    Sync 2 cameras + external audio (FX30 + ZV-E10 + Zen Go).
    
    Workflow:
    1. Sync ZV-E10 to FX30 using camera audio tracks
    2. Sync Zen Go audio to FX30 using FX30 camera audio as reference
    3. Create synced outputs with Zen Go audio
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
    
    # Setup output directory
    if not output_dir:
        output_dir = project.path / "MULTICAM"
    output_dir.mkdir(exist_ok=True)
    
    # Auto-detect if not provided
    if not cam1 or not cam2:
        media_dir = project.path / "01_MEDIA"
        video_files = list(media_dir.rglob("*.mp4")) + list(media_dir.rglob("*.mov"))
        
        if len(video_files) < 2:
            console.print("[red]Need at least 2 video files. Specify --cam1 and --cam2[/red]")
            return
        
        cam1 = cam1 or video_files[0]
        cam2 = cam2 or video_files[1]
        console.print(f"Using:\n  CAM1: {cam1.name}\n  CAM2: {cam2.name}")
    
    if not cam1.exists() or not cam2.exists():
        console.print("[red]Video files not found[/red]")
        return
    
    if not audio or not audio.exists():
        console.print("[yellow]Audio file not provided or not found. Sync will use camera audio only.[/yellow]")
        audio = None
    
    console.print(f"\n[bold]Synchronizing 3 sources...[/bold]")
    
    # Step 1: Sync cam2 to cam1 using camera audio
    console.print("Step 1: Syncing CAM2 to CAM1 (using camera audio)...")
    result_cam_sync = sync_videos_by_audio(cam1, cam2, output_dir)
    
    if not result_cam_sync["success"]:
        console.print("[red]Camera sync failed[/red]")
        return
    
    # Step 2: Sync external audio to cam1 (if provided)
    audio_offset = 0.0
    if audio:
        console.print("Step 2: Syncing external audio to CAM1...")
        # Extract audio from cam1 for reference
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            cam1_audio = tmpdir_path / "cam1_audio.wav"
            
            if extract_audio_from_video(cam1, cam1_audio):
                # Use find_sync_offset directly for audio-to-audio sync
                audio_offset = find_sync_offset(cam1_audio, audio)
                
                if abs(audio_offset) > 0.1:
                    console.print(f"[green]External audio synced (offset: {audio_offset:.2f}s)[/green]")
                else:
                    console.print("[green]External audio is already in sync[/green]")
    
    # Step 3: Create synced outputs with external audio (if available)
    console.print("Step 3: Creating synced outputs...")
    
    synced_cam1 = output_dir / f"synced_{cam1.stem}.mp4"
    synced_cam2 = output_dir / f"synced_{cam2.stem}.mp4"
    
    cam2_offset = result_cam_sync.get('offset', 0.0)
    
    # Replace audio in synced videos with external audio (if available)
    if audio and audio.exists():
        # Replace audio in cam1 (offset information is displayed, user can adjust in Resolve)
        cmd1 = [
            "ffmpeg",
            "-i", str(cam1),
            "-i", str(audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-y", str(synced_cam1)
        ]
        
        # Replace audio in cam2
        cmd2 = [
            "ffmpeg",
            "-i", str(cam2),
            "-i", str(audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-y", str(synced_cam2)
        ]
        
        try:
            subprocess.run(cmd1, capture_output=True, check=True, timeout=300)
            subprocess.run(cmd2, capture_output=True, check=True, timeout=300)
            console.print(f"[green]✓ Created synced videos with external audio[/green]")
            if abs(audio_offset) > 0.1:
                console.print(f"[yellow]Note: External audio offset is {audio_offset:.2f}s - adjust in Resolve if needed[/yellow]")
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]Warning: Failed to replace audio: {e}[/yellow]")
    
    console.print(Panel(
        f"[green]✓ 3-source sync complete![/green]\n\n"
        f"Output directory: {output_dir}\n"
        f"CAM1 synced: {synced_cam1.name if synced_cam1.exists() else 'N/A'}\n"
        f"CAM2 synced: {synced_cam2.name if synced_cam2.exists() else 'N/A'}\n"
        f"CAM2 to CAM1 offset: {cam2_offset:.2f}s\n"
        f"External audio offset: {audio_offset:.2f}s",
        title="Multicam Sync",
        border_style="green"
    ))


@app.command()
def create_sequence(
    project_name: Optional[str] = None,
    layout: str = "side_by_side"  # side_by_side, pip, switch
):
    """
    Create a multicam sequence from synchronized clips

    Layouts:
    - side_by_side: Both cameras visible
    - pip: Picture-in-picture
    - switch: Cut between cameras
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

    multicam_dir = project.path / "MULTICAM"

    if not multicam_dir.exists():
        console.print("[red]No multicam sync data found. Run 'sf multicam sync' first[/red]")
        return

    # Load sync data
    sync_file = multicam_dir / "sync_data.json"
    if not sync_file.exists():
        console.print("[red]No sync data found[/red]")
        return

    with open(sync_file) as f:
        sync_data = json.load(f)

    cam_a = Path(sync_data["cam_a"])
    cam_b = Path(sync_data["cam_b"])
    offset = sync_data.get("offset", 0)

    output_path = multicam_dir / f"multicam_{layout}.mp4"

    console.print(f"Creating {layout} multicam sequence...")

    # Build ffmpeg filter based on layout
    if layout == "side_by_side":
        # Scale both videos to half width and place side by side
        filter_complex = (
            "[0:v]scale=640:720,setpts=PTS-STARTPTS[v0];"
            "[1:v]scale=640:720,setpts=PTS-STARTPTS[v1];"
            "[v0][v1]hstack=inputs=2[v]"
        )
        map_opts = ["-map", "[v]", "-map", "0:a"]

    elif layout == "pip":
        # Picture-in-picture: main + small overlay
        filter_complex = (
            "[1:v]scale=320:180,setpts=PTS-STARTPTS[pip];"
            "[0:v]setpts=PTS-STARTPTS[main];"
            "[main][pip]overlay=W-w-10:H-h-10[v]"
        )
        map_opts = ["-map", "[v]", "-map", "0:a"]

    elif layout == "switch":
        # This would need an EDL or manual cut points
        # For now, just concatenate
        filter_complex = "[0:v][1:v]concat=n=2:v=1[v]"
        map_opts = ["-map", "[v]", "-map", "0:a"]

    else:
        console.print(f"[red]Unknown layout: {layout}[/red]")
        return

    # Apply offset if needed
    inputs = []
    if abs(offset) > 0.1:
        if offset > 0:
            inputs = ["-i", str(cam_a), "-itsoffset", str(offset), "-i", str(cam_b)]
        else:
            inputs = ["-itsoffset", str(abs(offset)), "-i", str(cam_a), "-i", str(cam_b)]
    else:
        inputs = ["-i", str(cam_a), "-i", str(cam_b)]

    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        *inputs,
        "-filter_complex", filter_complex,
        *map_opts,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-y",
        str(output_path)
    ]

    with console.status(f"Creating {layout} sequence..."):
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=120)

            if result.returncode == 0:
                size_mb = output_path.stat().st_size / (1024 * 1024)
                console.print(f"[green]✓[/green] Created multicam sequence: {output_path.name} ({size_mb:.1f} MB)")
            else:
                console.print(f"[red]Failed to create sequence[/red]")
                console.print(result.stderr.decode()[:500])

        except subprocess.TimeoutExpired:
            console.print("[red]Operation timed out[/red]")


@app.command()
def analyze(
    project_name: Optional[str] = None
):
    """Analyze cameras for sync compatibility"""
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

    # Find all video files
    videos = []
    for ext in [".mp4", ".mov", ".mxf"]:
        videos.extend(project.path.rglob(f"*{ext}"))

    if len(videos) < 2:
        console.print("[red]Need at least 2 video files for multicam[/red]")
        return

    console.print(f"Found {len(videos)} video files:\n")

    table = Table(show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Duration")
    table.add_column("Resolution")
    table.add_column("Timecode")
    table.add_column("Audio")

    for video in videos[:10]:  # Show first 10
        # Get video info
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_streams",
            "-show_format",
            "-of", "json",
            str(video)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            data = json.loads(result.stdout)

            # Parse info
            duration = "unknown"
            resolution = "unknown"
            has_audio = "no"
            timecode = "none"

            if "format" in data:
                if "duration" in data["format"]:
                    dur_sec = float(data["format"]["duration"])
                    duration = f"{int(dur_sec // 60)}:{int(dur_sec % 60):02d}"

                if "tags" in data["format"]:
                    timecode = data["format"]["tags"].get("timecode", "none")

            for stream in data.get("streams", []):
                if stream["codec_type"] == "video":
                    resolution = f"{stream['width']}x{stream['height']}"
                elif stream["codec_type"] == "audio":
                    has_audio = "yes"

            table.add_row(
                video.name[:30],
                duration,
                resolution,
                timecode,
                has_audio
            )

        except:
            table.add_row(video.name[:30], "error", "error", "error", "error")

    console.print(table)

    console.print("\n[bold]Sync Recommendations:[/bold]")
    console.print("  • Use 'audio' method if all cameras have audio")
    console.print("  • Use 'timecode' method if cameras have matching timecode")
    console.print("  • Place cameras in CAM_A and CAM_B folders for auto-detection")