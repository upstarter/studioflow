"""
Media Normalization CLI Commands
Normalize footage for consistent editing workflow
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table

from studioflow.core.media_normalizer import MediaNormalizer, NormalizationResult

console = Console()
app = typer.Typer()


@app.command()
def footage(
    input_dir: Path = typer.Argument(..., help="Input directory with raw footage"),
    output_dir: Optional[Path] = typer.Option(None, "-o", "--output", help="Output directory for normalized footage (defaults to input_dir/01_FOOTAGE_NORMALIZED)"),
    preserve_originals: bool = typer.Option(True, "--preserve/--no-preserve", help="Copy originals to separate directory"),
    original_dir: Optional[Path] = typer.Option(None, "--originals", help="Directory for original files (defaults to output_dir/../00_ORIGINALS)"),
    lufs: float = typer.Option(-14.0, "--lufs", help="Target LUFS level"),
):
    """
    Normalize all footage in a directory for editing workflow.
    
    Creates a clean footage directory with:
    - Audio normalized to -14 LUFS (YouTube standard)
    - PCM audio codec (professional editing standard)
    - Clean filenames (optimized for audio markers)
    
    Optionally preserves originals in a separate directory.
    
    Examples:
        sf normalize footage /path/to/raw/footage
        sf normalize footage /path/to/raw -o /path/to/normalized --no-preserve
    """
    if not input_dir.exists():
        console.print(f"[red]Input directory not found: {input_dir}[/red]")
        raise typer.Exit(1)
    
    # Default output directory
    if output_dir is None:
        output_dir = input_dir.parent / "01_FOOTAGE_NORMALIZED"
    
    # Default originals directory
    if preserve_originals and original_dir is None:
        original_dir = output_dir.parent / "00_ORIGINALS"
    
    normalizer = MediaNormalizer(target_lufs=lufs)
    
    console.print(f"[cyan]Normalizing footage...[/cyan]")
    console.print(f"[dim]Input: {input_dir}[/dim]")
    console.print(f"[dim]Output: {output_dir}[/dim]")
    console.print(f"[dim]Target LUFS: {lufs}[/dim]\n")
    
    results = normalizer.normalize_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        preserve_originals=preserve_originals,
        original_dir=original_dir
    )
    
    # Display results
    console.print(f"\n[bold]Normalization Results:[/bold]")
    console.print(f"  [green]✓ Success: {len(results['success'])} files[/green]")
    if results['failed']:
        console.print(f"  [red]✗ Failed: {len(results['failed'])} files[/red]")
        for result in results['failed'][:5]:  # Show first 5 failures
            console.print(f"    - {result.input_file.name}: {result.error_message}")
    
    if len(results['success']) > 0:
        console.print(f"\n[green]✓ Normalized footage ready at: {output_dir}[/green]")


@app.command()
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


@app.command()
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
