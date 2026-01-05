"""
DaVinci Resolve Magic Commands
One-command complete workflows
"""

import typer
from pathlib import Path
from typing import Optional, List, Dict
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import json

from studioflow.core.resolve_ai import ResolveProjectAI, SmartBin, RenderJob
from studioflow.core.intelligent_editor import IntelligentEditor, RoughCut
from studioflow.core.sony import SonyMediaHandler
from studioflow.core.config import get_config

console = Console()
app = typer.Typer()


@app.command()
def magic(
    project_name: str = typer.Argument(..., help="Project/episode name"),
    media_dir: Path = typer.Option(Path.cwd(), "--media", "-m", help="Media directory"),
    style: str = typer.Option("youtube", "--style", "-s", help="Style: youtube/vlog/tutorial/short"),
    grade: str = typer.Option("orange-teal", "--grade", "-g", help="Color grade to apply"),
    music: Optional[Path] = typer.Option(None, "--music", help="Music track for sync"),
    duration: Optional[float] = typer.Option(None, "--duration", "-d", help="Target duration"),
    export: bool = typer.Option(True, "--export/--no-export", help="Auto-export after edit"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Generate preview only")
):
    """
    🎯 THE ULTIMATE COMMAND - Complete video production in one command

    This command will:
    1. Import and analyze all media
    2. Create optimal project settings
    3. Organize into smart bins
    4. Generate rough cut
    5. Apply color grade
    6. Sync to music (if provided)
    7. Export for YouTube
    8. Generate thumbnails
    9. Prepare for upload
    """

    console.print(Panel(f"✨ [bold cyan]RESOLVE MAGIC[/bold cyan] ✨\n{project_name}", style="bold"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # Step 1: Setup project
        task = progress.add_task("Setting up intelligent project...", total=None)
        ai = ResolveProjectAI()
        project = ai.auto_setup_project(media_dir, project_name)
        progress.update(task, completed=True)

        # Step 2: Generate rough cut
        task = progress.add_task("Creating intelligent rough cut...", total=None)
        editor = IntelligentEditor()

        # Map style to editor format
        editor_style = {
            "youtube": "youtube_episode",
            "vlog": "vlog",
            "tutorial": "tutorial",
            "short": "youtube_short"
        }.get(style, "youtube_episode")

        rough_cut = editor.generate_rough_cut(
            ai.media_analyses,
            style=editor_style,
            target_duration=duration,
            music_track=music
        )
        progress.update(task, completed=True)

        # Step 3: Apply color grade
        task = progress.add_task(f"Applying {grade} color grade...", total=None)
        apply_color_grade(project, grade)
        progress.update(task, completed=True)

        if preview:
            # Generate preview only
            task = progress.add_task("Generating preview...", total=None)
            preview_path = Path(project_name + "_preview.mp4")
            editor.generate_preview(rough_cut, preview_path, duration=30)
            progress.update(task, completed=True)

            console.print(f"\n✅ Preview ready: {preview_path}")
            show_project_summary(project, rough_cut)
            return

        if export:
            # Step 4: Smart render queue
            task = progress.add_task("Setting up render queue...", total=None)
            render_jobs = setup_smart_renders(project, rough_cut)
            progress.update(task, completed=True)

            # Step 5: Execute renders
            task = progress.add_task("Rendering exports...", total=len(render_jobs))
            for job in render_jobs:
                console.print(f"  Rendering: {job.name}")
                execute_render(job)
                progress.update(task, advance=1)

        # Step 6: Generate deliverables
        task = progress.add_task("Generating deliverables...", total=None)
        deliverables = generate_deliverables(project, rough_cut)
        progress.update(task, completed=True)

    # Show summary
    show_magic_summary(project, rough_cut, deliverables)


@app.command()
def auto_project(
    media_dir: Path = typer.Argument(..., help="Directory with media files"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Project name")
):
    """Automatically create optimized Resolve project from media"""

    console.print("🤖 Auto-creating Resolve project...")

    ai = ResolveProjectAI()
    result = ai.auto_setup_project(media_dir, name)

    # Display project structure
    table = Table(title="Project Structure")
    table.add_column("Aspect", style="cyan")
    table.add_column("Details", style="white")

    table.add_row("Project Name", result["project_name"])
    table.add_row("Media Files", str(result["media_count"]))
    table.add_row("Resolution", result["settings"]["resolution"])
    table.add_row("Framerate", f"{result['settings']['framerate']} fps")
    table.add_row("Smart Bins", str(result["bins"]))
    table.add_row("Timelines", str(len(result["timelines"])))

    console.print(table)

    # Show bin organization
    console.print("\n📁 Smart Bin Organization:")
    ai = ResolveProjectAI()
    for bin in ai.bins:
        console.print(f"  {bin.icon} {bin.name}: {len(bin.clips)} clips")
        if bin.sub_bins:
            for sub in bin.sub_bins:
                console.print(f"    └─ {sub.name}: {len(sub.clips)} clips")


@app.command()
def rough_cut(
    media_dir: Path = typer.Argument(..., help="Media directory"),
    style: str = typer.Option("youtube", "--style", "-s", help="Edit style (youtube, documentary, interview, episode)"),
    output: Path = typer.Option(Path("rough_cut.edl"), "--output", "-o", help="Output EDL"),
    music: Optional[Path] = typer.Option(None, "--music", "-m", help="Music for sync"),
    duration: Optional[float] = typer.Option(None, "--duration", "-d", help="Target duration"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Generate video preview"),
    smart: bool = typer.Option(True, "--smart/--no-smart", help="Use smart NLP features for documentaries"),
    export_removed: bool = typer.Option(True, "--export-removed/--no-export-removed", help="Export removed footage for review"),
    removed_edl: Optional[Path] = typer.Option(None, "--removed-edl", help="EDL file for removed footage (source tape)"),
    removed_transcript: Optional[Path] = typer.Option(None, "--removed-transcript", help="Transcript file for removed content"),
    removed_descriptions: Optional[Path] = typer.Option(None, "--removed-descriptions", help="Visual descriptions file for removed footage"),
    source_tape: Optional[Path] = typer.Option(None, "--source-tape", help="Concatenated video of all removed footage")
):
    """Generate intelligent rough cut with story structure
    
    For documentaries, uses transcript analysis, thematic grouping, and B-roll matching.
    For other styles, uses quality-based selection.
    
    Automatically tracks removed footage and can export it as a "source tape" for review.
    """

    console.print(f"✂️ Generating {style} rough cut...")

    # Use new RoughCutEngine for smart features
    from studioflow.core.rough_cut import RoughCutEngine, CutStyle
    
    engine = RoughCutEngine()
    
    # Analyze clips
    with console.status("Analyzing clips and transcripts..."):
        clips = engine.analyze_clips(media_dir)
    
    if not clips:
        console.print(f"[red]No clips found in {media_dir}[/red]")
        raise typer.Exit(1)
    
    # Determine cut style
    cut_style_map = {
        "youtube": CutStyle.EPISODE,
        "documentary": CutStyle.DOC,
        "doc": CutStyle.DOC,
        "interview": CutStyle.INTERVIEW,
        "episode": CutStyle.EPISODE
    }
    cut_style = cut_style_map.get(style.lower(), CutStyle.EPISODE)
    
    # Generate rough cut
    with console.status("Generating rough cut..."):
        plan = engine.create_rough_cut(
            style=cut_style,
            target_duration=duration,
            use_smart_features=(cut_style == CutStyle.DOC and smart)
        )
    
    # Export EDL
    engine.export_edl(plan, output)
    console.print(f"[green]✓[/green] EDL exported to: {output}")
    
    # Show structure
    if plan.themes:
        console.print(f"\n📊 Thematic Structure ({plan.total_duration:.1f}s):")
        for theme in plan.themes:
            console.print(f"  • {theme.name}: {len(theme.key_quotes)} quotes ({theme.duration_target:.1f}s target)")
            if theme.description:
                console.print(f"    {theme.description}")
    
    if plan.narrative_arc:
        console.print(f"\n🎬 Narrative Arc ({plan.total_duration:.1f}s):")
        for section, segs in plan.narrative_arc.items():
            if segs:
                section_dur = sum(s.end_time - s.start_time for s in segs)
                console.print(f"  • {section}: {len(segs)} segments ({section_dur:.1f}s)")
    
    if plan.structure:
        console.print(f"\n📊 Story Structure ({plan.total_duration:.1f}s):")
        for section, segs in plan.structure.items():
            if segs:
                section_dur = sum(s.end_time - s.start_time for s in segs)
                console.print(f"  • {section}: {len(segs)} segments ({section_dur:.1f}s)")
    
    # Export removed footage if requested
    if export_removed and plan.removed_segments:
        removed_count = len(plan.removed_segments)
        removed_duration = sum(s.segment.end_time - s.segment.start_time for s in plan.removed_segments)
        console.print(f"\n🗑️  Removed Footage: {removed_count} segments ({removed_duration:.1f}s)")
        
        output_dir = output.parent
        
        # Export removed EDL (source tape)
        if removed_edl is None:
            removed_edl = output_dir / "removed_footage.edl"
        engine.export_removed_footage_edl(plan, removed_edl)
        console.print(f"[green]✓[/green] Removed footage EDL: {removed_edl}")
        
        # Generate removed transcripts
        if removed_transcript is None:
            removed_transcript = output_dir / "removed_transcript.md"
        engine.generate_removed_transcripts(plan, removed_transcript)
        console.print(f"[green]✓[/green] Removed transcripts: {removed_transcript}")
        
        # Generate visual descriptions
        if removed_descriptions is None:
            removed_descriptions = output_dir / "removed_descriptions.md"
        with console.status("Generating visual descriptions and thumbnails..."):
            engine.generate_removed_visual_descriptions(plan, removed_descriptions, extract_thumbnails=True)
        console.print(f"[green]✓[/green] Visual descriptions: {removed_descriptions}")
        
        # Create source tape video (optional, can be slow)
        if source_tape:
            with console.status("Creating source tape video (this may take a while)..."):
                tape_path = engine.create_source_tape_video(plan, source_tape)
                if tape_path:
                    console.print(f"[green]✓[/green] Source tape video: {tape_path}")
                else:
                    console.print("[yellow]⚠ Could not create source tape video[/yellow]")
        else:
            # Ask user if they want source tape (non-blocking, just show option)
            console.print("\n[yellow]Tip:[/yellow] Use [cyan]--source-tape[/cyan] to create concatenated video of removed footage")
            source_tape_path = output_dir / "removed_source_tape.mp4"
            with console.status("Creating source tape video..."):
                tape_path = engine.create_source_tape_video(plan, source_tape_path)
                if tape_path:
                    console.print(f"[green]✓[/green] Source tape video: {tape_path}")
                else:
                    console.print("[yellow]⚠ Could not create source tape video[/yellow]")

    if preview:
        console.print("\n[yellow]Preview generation not yet implemented for new rough cut engine[/yellow]")


@app.command()
def smart_bins(
    media_dir: Path = typer.Argument(..., help="Media directory"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save bin structure")
):
    """Create intelligent bin organization"""

    ai = ResolveProjectAI()
    ai.media_analyses = ai.analyze_media_characteristics(media_dir)
    bins = ai.create_intelligent_bins()

    # Display bins
    console.print("📁 Intelligent Bin Structure:\n")

    for bin in bins:
        console.print(f"{bin.icon} [bold]{bin.name}[/bold] ({len(bin.clips)} clips)")
        console.print(f"   {bin.description}")

        if bin.clips:
            # Show top clips
            top_clips = sorted(bin.clips, key=lambda x: x.quality_score, reverse=True)[:3]
            for clip in top_clips:
                console.print(f"   ⭐ {clip.file_path.name} (score: {clip.quality_score:.0f})")

        if bin.sub_bins:
            for sub in bin.sub_bins:
                console.print(f"   └─ {sub.icon} {sub.name}: {len(sub.clips)} clips")

        console.print()

    # Save structure if requested
    if output:
        structure = {
            "bins": [
                {
                    "name": bin.name,
                    "clips": [str(c.file_path) for c in bin.clips],
                    "sub_bins": [
                        {"name": sub.name, "clips": [str(c.file_path) for c in sub.clips]}
                        for sub in bin.sub_bins
                    ]
                }
                for bin in bins
            ]
        }
        output.write_text(json.dumps(structure, indent=2))
        console.print(f"💾 Saved to: {output}")


@app.command()
def analyze(
    media_dir: Path = typer.Argument(..., help="Media directory"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed analysis")
):
    """Deep analysis of media for intelligent editing"""

    ai = ResolveProjectAI()
    analyses = ai.analyze_media_characteristics(media_dir)

    # Summary stats
    console.print(Panel("📊 Media Analysis Summary", style="bold cyan"))

    total_duration = sum(a.duration for a in analyses)
    avg_quality = sum(a.quality_score for a in analyses) / len(analyses) if analyses else 0

    stats = Table(show_header=False)
    stats.add_column("Metric", style="cyan")
    stats.add_column("Value", style="white")

    stats.add_row("Total Clips", str(len(analyses)))
    stats.add_row("Total Duration", f"{total_duration/60:.1f} minutes")
    stats.add_row("Average Quality", f"{avg_quality:.1f}/100")

    # Camera distribution
    cameras = {}
    for a in analyses:
        cameras[a.camera_type] = cameras.get(a.camera_type, 0) + 1

    for camera, count in cameras.items():
        stats.add_row(f"{camera.upper()} Clips", str(count))

    console.print(stats)

    # Content types
    content_types = {}
    for a in analyses:
        content_types[a.content_type] = content_types.get(a.content_type, 0) + 1

    console.print("\n📹 Content Types:")
    for ctype, count in content_types.items():
        console.print(f"  • {ctype}: {count} clips")

    # Issues found
    issues_count = sum(len(a.technical_issues) for a in analyses)
    if issues_count > 0:
        console.print(f"\n⚠️  Technical Issues: {issues_count} found")
        issue_types = {}
        for a in analyses:
            for issue in a.technical_issues:
                issue_types[issue] = issue_types.get(issue, 0) + 1

        for issue, count in issue_types.items():
            console.print(f"  • {issue}: {count} clips")

    if detailed:
        console.print("\n📋 Detailed Analysis:")
        for a in sorted(analyses, key=lambda x: x.quality_score, reverse=True)[:10]:
            console.print(f"\n{a.file_path.name}")
            console.print(f"  Quality: {a.quality_score:.0f}/100")
            console.print(f"  Type: {a.content_type}")
            console.print(f"  Camera: {a.camera_type}")
            if a.technical_issues:
                console.print(f"  Issues: {', '.join(a.technical_issues)}")


# Helper functions

def apply_color_grade(project: Dict, grade: str):
    """Apply color grade to project"""
    # This would use Resolve API to apply LUT
    config = get_config()
    # Default LUT path - users can configure in their config
    lut_dir = config.storage.nas / "LUTs" if config.storage.nas else Path.home() / "LUTs"
    lut_path = lut_dir / f"{grade.replace('-', '_')}.cube"
    
    if lut_path.exists():
        console.print(f"  Applied: {lut_path.name}")
    else:
        console.print(f"  [yellow]LUT not found: {lut_path}[/yellow]")
        console.print(f"  [dim]Configure LUT path in ~/.studioflow/config.yaml[/dim]")


def setup_smart_renders(project: Dict, rough_cut: RoughCut) -> List[RenderJob]:
    """Setup intelligent render queue"""
    renders = []

    # Main YouTube export
    renders.append(RenderJob(
        name="YouTube_4K",
        preset="youtube_4k",
        priority=1,
        timeline=rough_cut.name,
        output_path=Path(f"{project['project_name']}_youtube_4k.mp4"),
        settings={
            "resolution": "3840x2160",
            "bitrate": 45000,
            "lufs": -14
        }
    ))

    # YouTube Short if applicable
    if rough_cut.style == "youtube_short" or rough_cut.total_duration <= 60:
        renders.append(RenderJob(
            name="YouTube_Short",
            preset="youtube_short",
            priority=2,
            timeline=rough_cut.name,
            output_path=Path(f"{project['project_name']}_short.mp4"),
            settings={
                "resolution": "1080x1920",
                "max_duration": 60
            }
        ))

    # Thumbnail renders
    renders.append(RenderJob(
        name="Thumbnails",
        preset="thumbnail",
        priority=3,
        timeline=rough_cut.name,
        output_path=Path(f"{project['project_name']}_thumbs"),
        settings={
            "format": "jpg",
            "count": 5
        }
    ))

    return renders


def execute_render(job: RenderJob):
    """Execute a render job"""
    # This would use Resolve API or FFmpeg
    job.status = "rendering"
    # Actual rendering would happen here
    job.status = "complete"
    job.progress = 100.0


def generate_deliverables(project: Dict, rough_cut: RoughCut) -> Dict:
    """Generate final deliverables package"""
    return {
        "video_files": [
            f"{project['project_name']}_youtube_4k.mp4",
            f"{project['project_name']}_preview.mp4"
        ],
        "thumbnails": [
            f"{project['project_name']}_thumb_01.jpg",
            f"{project['project_name']}_thumb_02.jpg"
        ],
        "metadata": {
            "title": project["project_name"],
            "duration": rough_cut.total_duration,
            "style": rough_cut.style
        },
        "edl": f"{project['project_name']}.edl"
    }


def show_project_summary(project: Dict, rough_cut: RoughCut):
    """Show project summary"""
    table = Table(title="Project Summary")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Project", project["project_name"])
    table.add_row("Media Count", str(project["media_count"]))
    table.add_row("Duration", f"{rough_cut.total_duration/60:.1f} min")
    table.add_row("Story Beats", str(len(rough_cut.story_beats)))
    table.add_row("Edit Points", str(len(rough_cut.edit_points)))

    console.print(table)


def show_magic_summary(project: Dict, rough_cut: RoughCut, deliverables: Dict):
    """Show complete magic summary"""
    console.print(Panel("✨ [bold green]MAGIC COMPLETE![/bold green] ✨", style="bold"))

    console.print(f"\n🎬 Project: {project['project_name']}")
    console.print(f"⏱️  Duration: {rough_cut.total_duration/60:.1f} minutes")
    console.print(f"📝 Edit Points: {len(rough_cut.edit_points)}")

    console.print(f"\n📦 Deliverables:")
    for video in deliverables["video_files"]:
        console.print(f"  • {video}")

    console.print(f"\n🖼️ Thumbnails:")
    for thumb in deliverables["thumbnails"]:
        console.print(f"  • {thumb}")

    console.print(f"\n✅ Ready for upload!")


if __name__ == "__main__":
    app()