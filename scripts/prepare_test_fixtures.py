#!/usr/bin/env python3
"""
Prepare test fixtures in optimal format for testing
Converts to MOV with PCM audio (lossless, mpv-compatible)
"""

import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


def remux_to_mov(input_file: Path, output_file: Path) -> bool:
    """
    Remux to MOV format (lossless, just changes container)
    MOV handles PCM audio perfectly and works with mpv
    """
    cmd = [
        "ffmpeg",
        "-i", str(input_file),
        "-c", "copy",  # Copy all streams (no re-encoding, lossless)
        "-y", str(output_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr[:200]}[/red]")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Prepare test fixtures in optimal format (MOV with PCM audio)"
    )
    parser.add_argument("input_dir", type=Path, help="Input directory with video files")
    parser.add_argument("-o", "--output", type=Path, help="Output directory (default: tests/fixtures/test_footage)")
    parser.add_argument("--format", choices=["mov", "mkv"], default="mov", 
                       help="Output format: mov (best for mpv) or mkv (default: mov)")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    
    if args.output:
        output_dir = Path(args.output)
    else:
        # Default to test fixtures directory
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
    console.print(f"[cyan]Remuxing to {args.format.upper()} format (lossless, mpv-compatible)...[/cyan]\n")
    
    converted = 0
    failed = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Remuxing...", total=len(video_files))
        
        for video_file in video_files:
            # Generate output filename
            output_file = output_dir / f"{video_file.stem}.{args.format}"
            
            if remux_to_mov(video_file, output_file):
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
    
    console.print(f"\n[green]✓ Test fixtures ready in {args.format.upper()} format![/green]")
    console.print("[cyan]MOV format preserves PCM audio and works perfectly with mpv[/cyan]")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

