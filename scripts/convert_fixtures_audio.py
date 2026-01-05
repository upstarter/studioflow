#!/usr/bin/env python3
"""
Convert test fixtures to optimal format for testing
Converts PCM audio to FLAC (lossless) or AAC (lossy but compatible)
MOV container with H.264 video (copied) and compatible audio
"""

import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


def convert_to_test_format(input_file: Path, output_file: Path, audio_codec: str = "flac") -> bool:
    """
    Convert to test fixture format
    
    Handles non-standard PCM (ipcm) by extracting to WAV first, then converting
    
    Args:
        audio_codec: "flac" (lossless) or "aac" (lossy but smaller, more compatible)
    """
    import tempfile
    
    # Step 1: Extract audio to WAV (handles non-standard PCM formats)
    temp_audio = Path(tempfile.mktemp(suffix=".wav"))
    
    try:
        # Extract audio to standard PCM WAV
        extract_cmd = [
            "ffmpeg",
            "-i", str(input_file),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # Standard PCM
            "-ar", "48000",  # Sample rate
            "-ac", "2",  # Stereo
            "-y", str(temp_audio)
        ]
        
        result = subprocess.run(extract_cmd, capture_output=True, text=True, check=True)
        
        # Step 2: Combine video (copied) with converted audio
        if audio_codec == "flac":
            audio_args = ["-c:a", "flac", "-compression_level", "5"]  # Lossless
        else:  # aac
            audio_args = ["-c:a", "aac", "-b:a", "320k"]  # High quality AAC
        
        combine_cmd = [
            "ffmpeg",
            "-i", str(input_file),  # Video source
            "-i", str(temp_audio),  # Audio source
            "-map", "0:v:0",  # Map video from first input
            "-map", "1:a:0",  # Map audio from second input
            "-c:v", "copy",  # Copy video (no re-encoding)
            *audio_args,
            "-y", str(output_file)
        ]
        
        result = subprocess.run(combine_cmd, capture_output=True, text=True, check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr[:200] if e.stderr else str(e)}[/red]")
        return False
    finally:
        # Cleanup temp file
        if temp_audio.exists():
            temp_audio.unlink()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert test fixtures to optimal format for testing"
    )
    parser.add_argument("input_dir", type=Path, help="Input directory with video files")
    parser.add_argument("-o", "--output", type=Path, help="Output directory")
    parser.add_argument("--audio", choices=["flac", "aac"], default="flac",
                       help="Audio codec: flac (lossless) or aac (lossy, smaller) - default: flac")
    parser.add_argument("--format", choices=["mov", "mkv"], default="mov",
                       help="Container format (default: mov)")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    
    if args.output:
        output_dir = Path(args.output)
    else:
        script_dir = Path(__file__).parent.parent
        output_dir = script_dir / "tests" / "fixtures" / "test_footage"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_dir.exists():
        console.print(f"[red]Input directory not found: {input_dir}[/red]")
        return 1
    
    # Find video files
    video_files = []
    for ext in ["*.MP4", "*.mp4", "*.MOV", "*.mov", "*.MKV", "*.mkv"]:
        video_files.extend(input_dir.glob(ext))
    
    if not video_files:
        console.print(f"[yellow]No video files found in {input_dir}[/yellow]")
        return 1
    
    console.print(f"[cyan]Found {len(video_files)} video file(s)[/cyan]")
    console.print(f"[cyan]Converting to {args.format.upper()} with {args.audio.upper()} audio...[/cyan]\n")
    
    converted = 0
    failed = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Converting...", total=len(video_files))
        
        for video_file in video_files:
            output_file = output_dir / f"{video_file.stem}.{args.format}"
            
            if convert_to_test_format(video_file, output_file, args.audio):
                size_mb = output_file.stat().st_size / (1024 * 1024)
                console.print(f"  [green]✓[/green] {output_file.name} ({size_mb:.1f}MB)")
                converted += 1
            else:
                failed.append(video_file.name)
            
            progress.update(task, advance=1)
    
    # Summary
    console.print(f"\n[green]✓[/green] Converted {converted}/{len(video_files)} files")
    console.print(f"[cyan]Output: {output_dir}[/cyan]")
    
    if failed:
        console.print(f"[yellow]⚠[/yellow] {len(failed)} files failed:")
        for name in failed:
            console.print(f"  {name}")
    
    audio_desc = "lossless" if args.audio == "flac" else "high-quality lossy"
    console.print(f"\n[green]✓ Test fixtures ready![/green]")
    console.print(f"[cyan]Format: {args.format.upper()} with {args.audio.upper()} audio ({audio_desc})[/cyan]")
    console.print("[cyan]This format works perfectly with mpv and all testing tools[/cyan]")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

