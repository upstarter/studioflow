"""
AI-Powered Editing Commands
Automatic editing features using AI for silence removal, filler detection, and more
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple, NamedTuple
from datetime import datetime, timedelta
import tempfile

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from studioflow.core.state import StateManager
from studioflow.core.project import ProjectManager
from studioflow.core.config import get_config


console = Console()
app = typer.Typer()


class EditPoint(NamedTuple):
    """Represents an edit point in the video"""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    reason: str   # Why this was marked (silence, filler, etc)
    confidence: float  # 0-1 confidence score


# Common filler words to detect
FILLER_WORDS = [
    "um", "uh", "umm", "uhh", "ah", "ahh", "er", "err",
    "like", "you know", "sort of", "kind of", "basically",
    "actually", "literally", "right", "so", "well"
]

# Whisper model sizes
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]


def detect_silence_periods(
    audio_path: Path,
    threshold_db: float = -40.0,
    min_duration: float = 0.5
) -> List[EditPoint]:
    """
    Detect periods of silence in audio

    Args:
        audio_path: Path to audio file
        threshold_db: Volume threshold in dB (lower = more aggressive)
        min_duration: Minimum silence duration to consider (seconds)
    """
    edits = []

    # Use ffmpeg to detect silence
    cmd = [
        "ffmpeg",
        "-i", str(audio_path),
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_duration}",
        "-f", "null",
        "-"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Parse silence periods from stderr
        silence_pattern = r"silence_start: ([\d.]+).*?silence_end: ([\d.]+)"

        for match in re.finditer(silence_pattern, result.stderr, re.DOTALL):
            start = float(match.group(1))
            end = float(match.group(2))

            # Add edit point for silence
            edits.append(EditPoint(
                start=start,
                end=end,
                reason="silence",
                confidence=0.9
            ))

    except subprocess.TimeoutExpired:
        console.print("[yellow]Silence detection timed out[/yellow]")
    except Exception as e:
        console.print(f"[red]Error detecting silence: {e}[/red]")

    return edits


def transcribe_with_whisper(
    audio_path: Path,
    model_size: str = "base"
) -> Optional[Dict]:
    """
    Transcribe audio using OpenAI Whisper with word-level timestamps
    """
    try:
        # Check if whisper is available
        import whisper

        console.print(f"Loading Whisper model ({model_size})...")
        model = whisper.load_model(model_size)

        console.print("Transcribing audio...")
        result = model.transcribe(
            str(audio_path),
            word_timestamps=True,
            verbose=False
        )

        return result

    except ImportError:
        console.print("[yellow]Whisper not installed. Install with: pip install openai-whisper[/yellow]")

        # Fallback: try whisper CLI if available
        cmd = [
            "whisper",
            str(audio_path),
            "--model", model_size,
            "--output_format", "json",
            "--word_timestamps", "True"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except:
            pass

    return None


def detect_filler_words(
    transcript: Dict,
    filler_list: List[str] = None
) -> List[EditPoint]:
    """
    Detect filler words in transcript
    """
    if filler_list is None:
        filler_list = FILLER_WORDS

    edits = []

    # Process each segment
    for segment in transcript.get("segments", []):
        for word_data in segment.get("words", []):
            word = word_data.get("word", "").lower().strip()

            # Check if it's a filler word
            if any(filler in word for filler in filler_list):
                start = word_data.get("start", 0)
                end = word_data.get("end", start + 0.5)

                edits.append(EditPoint(
                    start=start - 0.1,  # Small buffer before
                    end=end + 0.1,      # Small buffer after
                    reason=f"filler: {word}",
                    confidence=0.8
                ))

    return edits


def merge_overlapping_edits(edits: List[EditPoint], buffer: float = 0.1) -> List[EditPoint]:
    """
    Merge overlapping or close edit points
    """
    if not edits:
        return []

    # Sort by start time
    sorted_edits = sorted(edits, key=lambda x: x.start)

    merged = []
    current = sorted_edits[0]

    for edit in sorted_edits[1:]:
        # Check if overlapping or very close
        if edit.start <= current.end + buffer:
            # Merge them
            current = EditPoint(
                start=min(current.start, edit.start),
                end=max(current.end, edit.end),
                reason=f"{current.reason} + {edit.reason}",
                confidence=max(current.confidence, edit.confidence)
            )
        else:
            merged.append(current)
            current = edit

    merged.append(current)
    return merged


def generate_trimmed_video(
    input_video: Path,
    output_video: Path,
    edits: List[EditPoint],
    keep_segments: bool = True
) -> bool:
    """
    Generate trimmed video by removing or keeping segments

    Args:
        keep_segments: If True, keep non-edit segments. If False, keep only edits.
    """
    if not edits:
        console.print("[yellow]No edits to apply[/yellow]")
        return False

    # Get video duration
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(input_video)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        duration = float(json.loads(result.stdout)["format"]["duration"])
    except:
        duration = 999999  # Fallback to large number

    # Generate segments to keep
    if keep_segments:
        # Keep everything except the edits (remove silence/fillers)
        keep = []
        last_end = 0

        for edit in edits:
            if edit.start > last_end:
                keep.append((last_end, edit.start))
            last_end = max(last_end, edit.end)

        # Add final segment
        if last_end < duration:
            keep.append((last_end, duration))
    else:
        # Keep only the edit points (extract highlights)
        keep = [(e.start, e.end) for e in edits]

    if not keep:
        console.print("[yellow]No segments to keep[/yellow]")
        return False

    # Create complex filter for concatenation
    filter_parts = []
    inputs = []

    for i, (start, end) in enumerate(keep):
        # Add input with trim
        inputs.extend([
            "-ss", str(start),
            "-to", str(end),
            "-i", str(input_video)
        ])

        # Add to filter
        filter_parts.append(f"[{i}:v][{i}:a]")

    # Build concat filter
    n = len(keep)
    filter_complex = f"{''.join(filter_parts)}concat=n={n}:v=1:a=1[outv][outa]"

    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-y",
        str(output_video)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        console.print("[red]Video generation timed out[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error generating video: {e}[/red]")
        return False


def export_edl(edits: List[EditPoint], video_path: Path, output_path: Path, fps: float = 29.97):
    """
    Export Edit Decision List (EDL) for DaVinci Resolve
    """
    with open(output_path, 'w') as f:
        f.write("TITLE: AI Auto-Edit\n")
        f.write(f"FCM: NON-DROP FRAME\n\n")

        for i, edit in enumerate(edits, 1):
            # Convert to timecode
            start_tc = seconds_to_timecode(edit.start, fps)
            end_tc = seconds_to_timecode(edit.end, fps)

            # EDL format: event_num reel_name cut_type duration source_in source_out record_in record_out
            f.write(f"{i:03d}  AX  V  C  {start_tc} {end_tc} {start_tc} {end_tc}\n")
            f.write(f"* FROM CLIP NAME: {video_path.name}\n")
            f.write(f"* COMMENT: {edit.reason}\n\n")


def seconds_to_timecode(seconds: float, fps: float = 29.97) -> str:
    """Convert seconds to timecode format HH:MM:SS:FF"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    frames = int((seconds % 1) * fps)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"


@app.command()
def trim_silence(
    video: Path,
    output: Optional[Path] = None,
    threshold: float = -40.0,
    min_silence: float = 0.5,
    buffer: float = 0.1
):
    """
    Remove silence from video automatically

    Args:
        video: Input video file
        threshold: Silence threshold in dB (default -40)
        min_silence: Minimum silence duration to remove (default 0.5s)
        buffer: Buffer to keep around speech (default 0.1s)
    """
    if not video.exists():
        console.print(f"[red]Video not found: {video}[/red]")
        return

    # Set output path
    if output is None:
        output = video.parent / f"{video.stem}_trimmed.mp4"

    console.print(Panel(
        f"[bold]AI Auto-Editor: Silence Removal[/bold]\n\n"
        f"Input: {video.name}\n"
        f"Threshold: {threshold} dB\n"
        f"Min silence: {min_silence}s",
        title="Trimming Silence",
        border_style="cyan"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:

        # Extract audio for analysis
        task = progress.add_task("Extracting audio...", total=4)

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.wav"

            # Extract audio
            cmd = [
                "ffmpeg",
                "-i", str(video),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "1",
                "-y",
                str(audio_path)
            ]

            subprocess.run(cmd, capture_output=True)
            progress.advance(task)

            # Detect silence
            progress.update(task, description="Detecting silence periods...")
            silence_edits = detect_silence_periods(audio_path, threshold, min_silence)
            progress.advance(task)

            # Add buffer around speech
            if buffer > 0:
                silence_edits = [
                    EditPoint(
                        start=max(0, e.start - buffer),
                        end=e.end + buffer,
                        reason=e.reason,
                        confidence=e.confidence
                    )
                    for e in silence_edits
                ]

            # Merge overlapping edits
            progress.update(task, description="Optimizing edit points...")
            silence_edits = merge_overlapping_edits(silence_edits)
            progress.advance(task)

            # Generate trimmed video
            progress.update(task, description="Generating trimmed video...")
            success = generate_trimmed_video(video, output, silence_edits, keep_segments=True)
            progress.advance(task)

    if success:
        # Calculate statistics
        original_duration = get_video_duration(video)
        new_duration = get_video_duration(output)
        saved_time = original_duration - new_duration
        saved_percent = (saved_time / original_duration * 100) if original_duration > 0 else 0

        console.print(Panel(
            f"[green]✓ Video trimmed successfully![/green]\n\n"
            f"Original: {format_duration(original_duration)}\n"
            f"Trimmed: {format_duration(new_duration)}\n"
            f"Removed: {format_duration(saved_time)} ({saved_percent:.1f}%)\n"
            f"Cuts made: {len(silence_edits)}\n\n"
            f"Output: [cyan]{output}[/cyan]",
            title="Success",
            border_style="green"
        ))
    else:
        console.print("[red]Failed to generate trimmed video[/red]")


@app.command()
def remove_fillers(
    video: Path,
    output: Optional[Path] = None,
    model: str = "base",
    custom_words: Optional[str] = None
):
    """
    Remove filler words using AI transcription

    Args:
        video: Input video file
        model: Whisper model size (tiny, base, small, medium, large)
        custom_words: Comma-separated list of additional filler words
    """
    if not video.exists():
        console.print(f"[red]Video not found: {video}[/red]")
        return

    # Set output path
    if output is None:
        output = video.parent / f"{video.stem}_no_fillers.mp4"

    # Parse custom words
    filler_list = FILLER_WORDS.copy()
    if custom_words:
        filler_list.extend([w.strip() for w in custom_words.split(",")])

    console.print(Panel(
        f"[bold]AI Auto-Editor: Filler Removal[/bold]\n\n"
        f"Input: {video.name}\n"
        f"Model: Whisper {model}\n"
        f"Filler words: {', '.join(filler_list[:10])}...",
        title="Removing Fillers",
        border_style="cyan"
    ))

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "audio.wav"

        with console.status("Extracting audio..."):
            # Extract audio
            cmd = [
                "ffmpeg",
                "-i", str(video),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",  # Whisper prefers 16kHz
                "-ac", "1",
                "-y",
                str(audio_path)
            ]

            subprocess.run(cmd, capture_output=True)

        # Transcribe with Whisper
        transcript = transcribe_with_whisper(audio_path, model)

        if not transcript:
            console.print("[red]Failed to transcribe audio[/red]")
            return

        # Detect filler words
        with console.status("Detecting filler words..."):
            filler_edits = detect_filler_words(transcript, filler_list)

        console.print(f"Found {len(filler_edits)} filler words")

        # Generate trimmed video
        with console.status("Generating edited video..."):
            success = generate_trimmed_video(video, output, filler_edits, keep_segments=True)

    if success:
        console.print(f"[green]✓[/green] Removed {len(filler_edits)} filler words")
        console.print(f"Output: [cyan]{output}[/cyan]")
    else:
        console.print("[red]Failed to generate edited video[/red]")


@app.command()
def auto_edit(
    video: Path,
    output: Optional[Path] = None,
    aggressive: bool = False,
    export_edl_flag: bool = typer.Option(False, "--export-edl/--no-export-edl")
):
    """
    Full auto-edit: remove silence AND filler words

    Args:
        video: Input video file
        aggressive: Use more aggressive settings
        export_edl: Export EDL file for Resolve
    """
    if not video.exists():
        console.print(f"[red]Video not found: {video}[/red]")
        return

    # Set output path
    if output is None:
        output = video.parent / f"{video.stem}_edited.mp4"

    # Set parameters based on mode
    if aggressive:
        threshold = -35.0  # More aggressive silence detection
        min_silence = 0.3
        buffer = 0.05
        model = "small"  # Better transcription
    else:
        threshold = -40.0
        min_silence = 0.5
        buffer = 0.1
        model = "base"

    console.print(Panel(
        f"[bold]AI Auto-Editor: Full Edit[/bold]\n\n"
        f"Input: {video.name}\n"
        f"Mode: {'Aggressive' if aggressive else 'Standard'}\n"
        f"Features: Silence removal + Filler removal",
        title="Auto-Editing",
        border_style="cyan"
    ))

    all_edits = []

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "audio.wav"

        # Extract audio
        with console.status("Extracting audio..."):
            cmd = [
                "ffmpeg",
                "-i", str(video),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",
                str(audio_path)
            ]

            subprocess.run(cmd, capture_output=True)

        # Detect silence
        with console.status("Detecting silence..."):
            silence_edits = detect_silence_periods(audio_path, threshold, min_silence)
            all_edits.extend(silence_edits)

        console.print(f"  Found {len(silence_edits)} silence periods")

        # Transcribe and detect fillers
        with console.status(f"Transcribing with Whisper {model}..."):
            transcript = transcribe_with_whisper(audio_path, model)

        if transcript:
            with console.status("Detecting filler words..."):
                filler_edits = detect_filler_words(transcript)
                all_edits.extend(filler_edits)

            console.print(f"  Found {len(filler_edits)} filler words")

        # Merge and optimize edits
        with console.status("Optimizing edit points..."):
            all_edits = merge_overlapping_edits(all_edits, buffer)

        console.print(f"  Total edit points: {len(all_edits)}")

        # Generate edited video
        with console.status("Generating edited video..."):
            success = generate_trimmed_video(video, output, all_edits, keep_segments=True)

        # Export EDL if requested
        if export_edl_flag and all_edits:
            edl_path = output.parent / f"{output.stem}.edl"
            export_edl(all_edits, video, edl_path)
            console.print(f"  Exported EDL: [cyan]{edl_path.name}[/cyan]")

    if success:
        # Calculate statistics
        original_duration = get_video_duration(video)
        new_duration = get_video_duration(output)
        saved_time = original_duration - new_duration
        saved_percent = (saved_time / original_duration * 100) if original_duration > 0 else 0

        # Show edit summary
        table = Table(title="Edit Summary", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value")

        table.add_row("Original Duration", format_duration(original_duration))
        table.add_row("Edited Duration", format_duration(new_duration))
        table.add_row("Time Saved", f"{format_duration(saved_time)} ({saved_percent:.1f}%)")
        table.add_row("Total Cuts", str(len(all_edits)))
        table.add_row("Silence Removed", str(len([e for e in all_edits if "silence" in e.reason])))
        table.add_row("Fillers Removed", str(len([e for e in all_edits if "filler" in e.reason])))

        console.print(table)
        console.print(f"\n[green]✓[/green] Output: [cyan]{output}[/cyan]")
    else:
        console.print("[red]Failed to generate edited video[/red]")


def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return float(json.loads(result.stdout)["format"]["duration"])
    except:
        return 0.0


def format_duration(seconds: float) -> str:
    """Format duration as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


@app.command()
def settings():
    """Show AI editing settings and recommendations"""

    table = Table(title="AI Auto-Editor Settings", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Conservative", style="green")
    table.add_column("Standard", style="yellow")
    table.add_column("Aggressive", style="red")

    table.add_row("Silence Threshold", "-45 dB", "-40 dB", "-35 dB")
    table.add_row("Min Silence", "0.7s", "0.5s", "0.3s")
    table.add_row("Buffer", "0.15s", "0.10s", "0.05s")
    table.add_row("Whisper Model", "tiny", "base", "small")
    table.add_row("Time Saved", "5-10%", "10-20%", "20-30%")

    console.print(table)

    console.print("\n[bold]Filler Words Detected:[/bold]")
    console.print(", ".join(FILLER_WORDS))

    console.print("\n[bold]Usage Examples:[/bold]")
    console.print("  sf ai trim-silence video.mp4")
    console.print("  sf ai remove-fillers video.mp4 --model small")
    console.print("  sf ai auto-edit video.mp4 --aggressive")
    console.print("  sf ai auto-edit video.mp4 --export-edl  # For Resolve")