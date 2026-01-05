"""
Rough Cut CLI Command
Smart context-aware rough cut generation
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from studioflow.core.rough_cut import RoughCutEngine, CutStyle, RoughCutPlan
from studioflow.core.project_context import ProjectContextManager

console = Console()
app = typer.Typer()


@app.command()
def rough_cut(
    footage_dir: Optional[Path] = typer.Argument(None, help="Footage directory (auto-detects if not provided)"),
    style: str = typer.Option("doc", "-s", "--style", help="Style: doc, interview, episode, tutorial, review, unboxing, comparison, setup, explainer"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output EDL/FCPXML path"),
    target_duration: Optional[float] = typer.Option(None, "-d", "--duration", help="Target duration in minutes"),
    preview: bool = typer.Option(True, "--preview/--no-preview", help="Show preview before generating"),
    format: str = typer.Option("edl", "-f", "--format", help="Output format: edl, fcpxml"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
    audio_markers: bool = typer.Option(False, "--audio-markers/--no-audio-markers", help="Use audio markers for segment extraction (if markers detected)"),
):
    """
    Create intelligent rough cut from footage + transcripts.

    Styles:
      doc       - Documentary: slow pacing, story arc, let moments breathe
      interview - Interview: Q&A structure, highlight best answers
      episode   - YouTube episode: fast cuts, hook first, high energy
      tutorial  - Tutorial: aggressive jump cuts, step-by-step, screen recording aware
      review    - Product review: feature detection, pros/cons, verdict
      unboxing  - Unboxing: reveal detection, reaction prioritization
      comparison - Comparison: product switching, side-by-side analysis
      setup     - Setup guide: step detection, screen recording priority
      explainer - Explainer: concept detection, educational pacing
    """

    # Validate style
    try:
        cut_style = CutStyle(style)
    except ValueError:
        console.print(f"[red]Invalid style: {style}[/red]")
        console.print("Valid styles: doc, interview, episode, tutorial, review, unboxing, comparison, setup, explainer")
        raise typer.Exit(1)

    # Smart context detection
    if footage_dir is None:
        files, description = ProjectContextManager.get_files_for_command("rough-cut")

        if not files:
            console.print("[yellow]No footage found. Specify a directory: sf rough-cut /path/to/footage[/yellow]")
            raise typer.Exit(1)

        footage_dir = files[0]  # get_files_for_command returns folder for rough-cut
        console.print(f"[cyan]Auto-detected:[/cyan] {description}")
        console.print(f"[dim]Path: {footage_dir}[/dim]\n")

    if not footage_dir.exists():
        console.print(f"[red]Directory not found: {footage_dir}[/red]")
        raise typer.Exit(1)

    # Initialize engine
    engine = RoughCutEngine()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # Analyze clips
        task = progress.add_task("Analyzing clips and transcripts...", total=None)
        clips = engine.analyze_clips(footage_dir)
        progress.update(task, completed=True)

        if not clips:
            console.print("[yellow]No video clips found in directory[/yellow]")
            raise typer.Exit(1)

        # Show analysis summary
        console.print(f"\n[bold]Analyzed {len(clips)} clips:[/bold]")

        table = Table(show_header=True, header_style="cyan")
        table.add_column("Clip", style="white")
        table.add_column("Duration", justify="right")
        table.add_column("Speech", justify="center")
        table.add_column("Topics", style="dim")

        total_duration = 0
        clips_with_speech = 0

        for clip in clips:
            total_duration += clip.duration
            if clip.has_speech:
                clips_with_speech += 1

            table.add_row(
                clip.file_path.name[:30] + "..." if len(clip.file_path.name) > 30 else clip.file_path.name,
                f"{clip.duration:.1f}s",
                "✓" if clip.has_speech else "✗",
                ", ".join(clip.topics[:3]) if clip.topics else "-"
            )

        console.print(table)
        console.print(f"\n[dim]Total: {total_duration/60:.1f} min, {clips_with_speech}/{len(clips)} with transcripts[/dim]")

        # Create rough cut plan
        task = progress.add_task(f"Creating {style} rough cut...", total=None)

        target_mins = target_duration * 60 if target_duration else None
        # Use smart features for documentaries (now optimized and tested!)
        use_smart = (cut_style == CutStyle.DOC)
        plan = engine.create_rough_cut(
            cut_style, 
            target_duration=target_mins, 
            use_smart_features=use_smart,
            use_audio_markers=audio_markers
        )
        progress.update(task, completed=True)

    # Show preview
    if preview:
        console.print(Panel(
            engine.get_summary(plan),
            title=f"Rough Cut Preview - {style.upper()}",
            border_style="cyan"
        ))

        # Show structure
        console.print("\n[bold]Timeline Structure:[/bold]")
        for section, segs in plan.structure.items():
            if segs:
                dur = sum(s.end_time - s.start_time for s in segs)
                console.print(f"  [cyan]{section}[/cyan]: {len(segs)} segments ({dur:.1f}s)")
                for seg in segs[:2]:  # Show first 2 of each section
                    preview_text = seg.text[:50] + "..." if len(seg.text) > 50 else seg.text
                    console.print(f"    [dim]• {preview_text}[/dim]")
                if len(segs) > 2:
                    console.print(f"    [dim]... and {len(segs) - 2} more[/dim]")

        if not yes:
            confirm = typer.confirm(f"\nGenerate {format.upper()} file?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)

    # Generate output
    if output is None:
        ctx = ProjectContextManager.detect_context()
        if ctx.project_path:
            output = ctx.project_path / f"rough_cut_{style}.{format}"
        else:
            output = footage_dir / f"rough_cut_{style}.{format}"

    if format == "edl":
        engine.export_edl(plan, output)
    elif format == "fcpxml":
        engine.export_fcpxml(plan, output)
    else:
        console.print(f"[red]Unknown format: {format}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[green]✓ Rough cut saved to: {output}[/green]")
    console.print(f"[dim]Import this file into DaVinci Resolve to start editing[/dim]")

    # Show next steps
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Open DaVinci Resolve")
    console.print(f"  2. File → Import → Timeline → {output.name}")
    console.print("  3. Refine the rough cut")
    console.print("  4. Add B-roll, music, graphics from Power Bins")


@app.command()
def hook_tests(
    footage_dir: Optional[Path] = typer.Argument(None, help="Footage directory (auto-detects if not provided)"),
    output_dir: Optional[Path] = typer.Option(None, "-o", "--output", help="Project root directory (defaults to detected project)"),
    max_hooks: int = typer.Option(5, "--max", "-m", help="Maximum number of hook candidates to generate"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
):
    """
    Generate multiple hook test timelines for A/B testing on YouTube.
    
    Creates hook candidates from first 60 seconds of footage and exports each
    as separate timelines to 04_TIMELINES/02_HOOK_TESTS/ for Resolve import.
    
    Each hook test can be rendered and uploaded as unlisted YouTube videos
    to test retention before final video release.
    """
    
    # Smart context detection
    if footage_dir is None:
        files, description = ProjectContextManager.get_files_for_command("rough-cut")
        
        if not files:
            console.print("[yellow]No footage found. Specify a directory: sf rough-cut hook-tests /path/to/footage[/yellow]")
            raise typer.Exit(1)
        
        footage_dir = files[0]
        console.print(f"[cyan]Auto-detected:[/cyan] {description}")
        console.print(f"[dim]Path: {footage_dir}[/dim]\n")
    
    if not footage_dir.exists():
        console.print(f"[red]Directory not found: {footage_dir}[/red]")
        raise typer.Exit(1)
    
    # Determine output directory
    if output_dir is None:
        ctx = ProjectContextManager.detect_context()
        if ctx.project_path:
            output_dir = ctx.project_path
        else:
            # Use footage directory parent as project root
            output_dir = footage_dir.parent
    
    console.print(f"[cyan]Output directory:[/cyan] {output_dir}")
    
    # Initialize engine
    engine = RoughCutEngine()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Analyze clips
        task = progress.add_task("Analyzing clips for hook candidates...", total=None)
        clips = engine.analyze_clips(footage_dir)
        progress.update(task, completed=True)
        
        if not clips:
            console.print("[yellow]No video clips found in directory[/yellow]")
            raise typer.Exit(1)
        
        # Generate hook test timelines
        task = progress.add_task("Generating hook test timelines...", total=None)
        exported_files = engine.generate_hook_test_timelines(clips, output_dir, max_hooks=max_hooks)
        progress.update(task, completed=True)
    
    if not exported_files:
        console.print("[yellow]No hook candidates found. Try different footage or check transcripts.[/yellow]")
        raise typer.Exit(1)
    
    # Show results
    hook_tests_dir = output_dir / "04_TIMELINES" / "02_HOOK_TESTS"
    
    console.print(f"\n[green]✓ Generated {len(exported_files)} hook test files[/green]")
    console.print(f"[dim]Location: {hook_tests_dir}[/dim]\n")
    
    # Show summary
    summary_file = hook_tests_dir / "HOOK_TESTS_SUMMARY.txt"
    if summary_file.exists():
        console.print(Panel(
            summary_file.read_text(),
            title="Hook Tests Summary",
            border_style="cyan"
        ))
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Open DaVinci Resolve")
    console.print("  2. File → Import → Timeline → Import AAF, EDL, XML, FCPXML...")
    console.print(f"  3. Select .fcpxml files from {hook_tests_dir}")
    console.print("  4. Each hook test will be imported as a separate timeline")
    console.print("  5. Render each timeline (1080p, 16-20Mbps)")
    console.print("  6. Upload as unlisted YouTube videos")
    console.print("  7. Compare retention analytics after 24-48 hours")
    console.print("  8. Select best performing hook for final video")


if __name__ == "__main__":
    app()
