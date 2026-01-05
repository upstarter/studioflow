"""
Eric's Workflow Commands
Custom workflow automation for Eric's video production pipeline
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


def episode(
    name: str = typer.Argument(None, help="Episode name"),
    import_path: Optional[Path] = typer.Option(None, "-i", "--import", help="Import footage from path"),
):
    """Create a new episode with full workflow automation"""
    console.print(f"[cyan]Creating episode: {name or 'Untitled'}[/cyan]")
    if import_path:
        console.print(f"[dim]Import from: {import_path}[/dim]")
    console.print("[yellow]Episode workflow coming soon[/yellow]")


def import_sony(
    path: Path = typer.Argument(..., help="Path to Sony footage"),
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Target project"),
):
    """Import Sony camera footage with metadata extraction"""
    console.print(f"[cyan]Importing Sony footage from: {path}[/cyan]")
    console.print("[yellow]Sony import workflow coming soon[/yellow]")


def create_proxies(
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project name"),
    quality: str = typer.Option("1080p", "-q", "--quality", help="Proxy quality"),
):
    """Create optimized proxy files for editing"""
    console.print(f"[cyan]Creating {quality} proxies[/cyan]")
    console.print("[yellow]Proxy generation coming soon[/yellow]")


def grade(
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project name"),
    lut: Optional[str] = typer.Option(None, "-l", "--lut", help="LUT to apply"),
):
    """Apply color grading to project"""
    console.print("[cyan]Color grading workflow[/cyan]")
    if lut:
        console.print(f"[dim]Using LUT: {lut}[/dim]")
    console.print("[yellow]Grading automation coming soon[/yellow]")


def export_youtube(
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project name"),
    quality: str = typer.Option("4k", "-q", "--quality", help="Export quality"),
):
    """Export optimized for YouTube"""
    console.print(f"[cyan]Exporting for YouTube at {quality}[/cyan]")
    console.print("[yellow]YouTube export coming soon[/yellow]")


def upload_episode(
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project name"),
    draft: bool = typer.Option(True, "--draft/--publish", help="Upload as draft"),
):
    """Upload episode to YouTube"""
    status = "draft" if draft else "public"
    console.print(f"[cyan]Uploading episode as {status}[/cyan]")
    console.print("[yellow]Upload workflow coming soon[/yellow]")


def check_lufs(
    file: Optional[Path] = typer.Argument(None, help="Audio/video file to analyze"),
    target: float = typer.Option(-14.0, "-t", "--target", help="Target LUFS"),
):
    """Check audio levels (LUFS) for broadcast compliance"""
    import subprocess
    import re

    if not file or not file.exists():
        console.print("[red]Please provide a valid audio/video file[/red]")
        return

    console.print(f"[cyan]Analyzing LUFS for:[/cyan] {file.name}")
    console.print(f"[dim]Target: {target} LUFS (YouTube/Streaming standard)[/dim]\n")

    # Use ffmpeg loudnorm filter for LUFS analysis
    cmd = [
        "ffmpeg", "-i", str(file),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        # Parse the JSON output from loudnorm
        output = result.stderr
        json_match = re.search(r'\{[^}]+\}', output, re.DOTALL)

        if json_match:
            import json
            lufs_data = json.loads(json_match.group())

            input_i = float(lufs_data.get("input_i", -99))
            input_tp = float(lufs_data.get("input_tp", -99))
            input_lra = float(lufs_data.get("input_lra", 0))

            # Display results
            console.print("[bold]Audio Analysis Results:[/bold]")
            console.print(f"  Integrated Loudness: [cyan]{input_i:.1f} LUFS[/cyan]")
            console.print(f"  True Peak: [cyan]{input_tp:.1f} dBTP[/cyan]")
            console.print(f"  Loudness Range: [cyan]{input_lra:.1f} LU[/cyan]")

            # Check against target
            diff = input_i - target
            console.print(f"\n[bold]Target Comparison ({target} LUFS):[/bold]")

            if abs(diff) <= 1.0:
                console.print(f"  [green]✓ Audio is within target range[/green]")
            elif diff < -1.0:
                console.print(f"  [yellow]⚠ Audio is {abs(diff):.1f} dB too quiet[/yellow]")
                console.print(f"  [dim]Suggestion: Normalize audio or increase gain by {abs(diff):.1f} dB[/dim]")
            else:
                console.print(f"  [yellow]⚠ Audio is {diff:.1f} dB too loud[/yellow]")
                console.print(f"  [dim]Suggestion: Reduce gain by {diff:.1f} dB[/dim]")

            # True peak check
            if input_tp > -1.0:
                console.print(f"\n  [red]⚠ True peak exceeds -1.0 dBTP - may cause clipping[/red]")
            else:
                console.print(f"\n  [green]✓ True peak is safe ({input_tp:.1f} dBTP)[/green]")

        else:
            # Fallback to volumedetect
            cmd_vol = [
                "ffmpeg", "-i", str(file),
                "-af", "volumedetect",
                "-f", "null", "-"
            ]
            result_vol = subprocess.run(cmd_vol, capture_output=True, text=True, timeout=60)

            mean_match = re.search(r'mean_volume:\s*([-\d.]+)', result_vol.stderr)
            max_match = re.search(r'max_volume:\s*([-\d.]+)', result_vol.stderr)

            if mean_match:
                mean_vol = float(mean_match.group(1))
                max_vol = float(max_match.group(1)) if max_match else 0

                console.print("[bold]Audio Analysis (volumedetect):[/bold]")
                console.print(f"  Mean Volume: [cyan]{mean_vol:.1f} dB[/cyan]")
                console.print(f"  Max Volume: [cyan]{max_vol:.1f} dB[/cyan]")

                # Rough LUFS estimate (not accurate but helpful)
                estimated_lufs = mean_vol - 10  # Rough approximation
                console.print(f"  Estimated LUFS: ~{estimated_lufs:.1f} (approximate)")
            else:
                console.print("[yellow]Could not analyze audio levels[/yellow]")

    except subprocess.TimeoutExpired:
        console.print("[red]Analysis timed out - file may be too long[/red]")
    except Exception as e:
        console.print(f"[red]Error analyzing audio: {e}[/red]")


def fix_lufs(
    file: Path = typer.Argument(..., help="Audio/video file to normalize"),
    target: float = typer.Option(-14.0, "-t", "--target", help="Target LUFS"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output file"),
):
    """Normalize audio to target LUFS (default: -14 for YouTube)"""
    import subprocess
    import re

    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        return

    # Default output name
    if not output:
        output = file.parent / f"{file.stem}_normalized{file.suffix}"

    console.print(f"[cyan]Normalizing audio to {target} LUFS[/cyan]")
    console.print(f"[dim]Input: {file.name}[/dim]")
    console.print(f"[dim]Output: {output.name}[/dim]\n")

    # Two-pass loudnorm for accurate normalization
    # Pass 1: Analyze
    console.print("[dim]Pass 1/2: Analyzing audio levels...[/dim]")
    analyze_cmd = [
        "ffmpeg", "-i", str(file),
        "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-"
    ]

    try:
        result = subprocess.run(analyze_cmd, capture_output=True, text=True, timeout=300)

        # Parse loudnorm output
        json_match = re.search(r'\{[^}]+\}', result.stderr, re.DOTALL)
        if not json_match:
            console.print("[red]Failed to analyze audio[/red]")
            return

        import json
        stats = json.loads(json_match.group())

        input_i = stats.get("input_i", "-24")
        input_tp = stats.get("input_tp", "-2")
        input_lra = stats.get("input_lra", "7")
        input_thresh = stats.get("input_thresh", "-34")
        target_offset = stats.get("target_offset", "0")

        console.print(f"[dim]  Current: {float(input_i):.1f} LUFS[/dim]")

        # Pass 2: Apply normalization with measured values
        console.print("[dim]Pass 2/2: Applying normalization...[/dim]")

        normalize_cmd = [
            "ffmpeg", "-i", str(file),
            "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true",
            "-c:v", "copy",  # Copy video stream without re-encoding
            "-c:a", "pcm_s16le",  # Keep uncompressed PCM for editing quality
            "-y", str(output)
        ]

        result = subprocess.run(normalize_cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0 and output.exists():
            # Verify the result
            verify_cmd = [
                "ffmpeg", "-i", str(output),
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                "-f", "null", "-"
            ]
            verify = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=120)

            verify_match = re.search(r'\{[^}]+\}', verify.stderr, re.DOTALL)
            if verify_match:
                verify_stats = json.loads(verify_match.group())
                new_lufs = float(verify_stats.get("input_i", -99))

                console.print(f"\n[green]✓ Audio normalized successfully![/green]")
                console.print(f"  Before: {float(input_i):.1f} LUFS")
                console.print(f"  After:  {new_lufs:.1f} LUFS")
                console.print(f"  Target: {target} LUFS")

                size_mb = output.stat().st_size / (1024 * 1024)
                console.print(f"\n  Output: {output}")
                console.print(f"  Size: {size_mb:.1f} MB")
            else:
                console.print(f"[green]✓ Normalized to: {output}[/green]")
        else:
            console.print(f"[red]Normalization failed[/red]")
            if result.stderr:
                console.print(f"[dim]{result.stderr[:200]}[/dim]")

    except subprocess.TimeoutExpired:
        console.print("[red]Processing timed out[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def short(
    source: Optional[Path] = typer.Argument(None, help="Source video for short"),
    duration: int = typer.Option(60, "-d", "--duration", help="Max duration in seconds"),
):
    """Create a YouTube Short from existing content"""
    console.print(f"[cyan]Creating Short (max {duration}s)[/cyan]")
    if source:
        console.print(f"[dim]From: {source}[/dim]")
    console.print("[yellow]Shorts creation coming soon[/yellow]")


def sanitize_names(
    directory: Path = typer.Argument(..., help="Directory with files to rename"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview changes without renaming"),
):
    """Sanitize filenames: remove spaces, parentheses, special chars"""
    import re

    if not directory.exists():
        console.print(f"[red]Directory not found: {directory}[/red]")
        return

    def sanitize(name: str) -> str:
        stem = Path(name).stem
        suffix = Path(name).suffix
        stem = stem.replace(' ', '_')
        stem = re.sub(r'[\(\)\[\]\{\}]', '_', stem)
        stem = re.sub(r'_+', '_', stem)
        stem = stem.strip('_')
        return f"{stem}{suffix}"

    # Find files that need renaming
    changes = []
    for f in directory.iterdir():
        if f.is_file():
            new_name = sanitize(f.name)
            if new_name != f.name:
                changes.append((f, f.parent / new_name))

    if not changes:
        console.print("[green]All filenames are already clean![/green]")
        return

    console.print(f"[cyan]Found {len(changes)} files to rename:[/cyan]\n")

    for old, new in changes:
        console.print(f"  {old.name}")
        console.print(f"  [green]→ {new.name}[/green]\n")

    if dry_run:
        console.print("[yellow]Dry run - no changes made. Use --apply to rename.[/yellow]")
    else:
        renamed = 0
        for old, new in changes:
            try:
                # Handle collision
                if new.exists():
                    stem = new.stem
                    suffix = new.suffix
                    for i in range(1, 100):
                        new = new.parent / f"{stem}_{i}{suffix}"
                        if not new.exists():
                            break
                old.rename(new)
                renamed += 1
            except Exception as e:
                console.print(f"[red]Failed: {old.name} - {e}[/red]")

        console.print(f"\n[green]✓ Renamed {renamed} files[/green]")


def my_workflow(
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project name"),
):
    """Run Eric's complete production workflow"""
    console.print("[bold cyan]Eric's Complete Workflow[/bold cyan]")
    console.print("""
Steps:
  1. Import Sony footage
  2. Create proxies
  3. Auto-organize by scene
  4. Apply base grade
  5. Export for review
  6. Final export for YouTube
  7. Upload as draft
    """)
    console.print("[yellow]Full workflow automation coming soon[/yellow]")
