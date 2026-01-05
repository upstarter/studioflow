#!/usr/bin/env python3
"""
Remux test fixtures to MOV format for mpv compatibility
PCM audio in MP4 doesn't work with mpv, but MOV handles it perfectly
"""

import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


def remux_to_mov(input_file: Path, output_file: Path) -> bool:
    """Remux MP4 with PCM to MOV (lossless, just changes container)"""
    cmd = [
        "ffmpeg",
        "-i", str(input_file),
        "-c", "copy",  # Copy streams (no re-encoding, lossless)
        "-y", str(output_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error remuxing {input_file.name}: {e.stderr[:200]}[/red]")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Remux test fixtures to MOV for mpv compatibility")
    parser.add_argument("input_dir", type=Path, help="Input directory with MP4 files")
    parser.add_argument("-o", "--output", type=Path, help="Output directory (default: same as input)")
    parser.add_argument("--format", choices=["mov", "mkv"], default="mov", help="Output format (default: mov)")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output) if args.output else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_dir.exists():
        console.print(f"[red]Input directory not found: {input_dir}[/red]")
        return 1
    
    # Find MP4 files
    mp4_files = list(input_dir.glob("*.MP4")) + list(input_dir.glob("*.mp4"))
    
    if not mp4_files:
        console.print(f"[yellow]No MP4 files found in {input_dir}[/yellow]")
        return 1
    
    console.print(f"[cyan]Found {len(mp4_files)} MP4 file(s)[/cyan]")
    console.print(f"[cyan]Remuxing to {args.format.upper()} format for mpv compatibility...[/cyan]\n")
    
    converted = 0
    failed = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Remuxing...", total=len(mp4_files))
        
        for mp4_file in mp4_files:
            output_file = output_dir / f"{mp4_file.stem}.{args.format}"
            
            if remux_to_mov(mp4_file, output_file):
                size_mb = output_file.stat().st_size / (1024 * 1024)
                console.print(f"  [green]✓[/green] {output_file.name} ({size_mb:.1f}MB)")
                converted += 1
            else:
                failed.append(mp4_file.name)
            
            progress.update(task, advance=1)
    
    # Summary
    console.print(f"\n[green]✓[/green] Converted {converted}/{len(mp4_files)} files to {args.format.upper()}")
    
    if failed:
        console.print(f"[yellow]⚠[/yellow] {len(failed)} files failed:")
        for name in failed:
            console.print(f"  {name}")
    
    console.print(f"\n[cyan]Files ready in: {output_dir}[/cyan]")
    console.print("[cyan]MOV format works perfectly with mpv for PCM audio![/cyan]")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

