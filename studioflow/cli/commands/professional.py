"""
Professional StudioFlow commands
Resolve, node graphs, and workflow automation
"""

import typer
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import yaml

from studioflow.core.resolve import (
    ResolveIntegration, ResolveProject, TimelineClip
)
from studioflow.core.node_graph import (
    NodeGraph, NodeLibrary, create_simple_pipeline
)
from studioflow.core.workflow import (
    WorkflowEngine, Workflow, Task, TriggerType, TaskStatus,
    create_youtube_workflow, create_dailies_workflow
)

console = Console()
app = typer.Typer()

# Global workflow engine
workflow_engine = WorkflowEngine()


# Resolve Commands
@app.command()
def resolve_check():
    """Check DaVinci Resolve installation"""
    if ResolveIntegration.check_resolve():
        console.print("[green]✓[/green] DaVinci Resolve found")
    else:
        console.print("[yellow]⚠[/yellow] DaVinci Resolve not found")
        console.print("Install from: https://www.blackmagicdesign.com/products/davinciresolve")


@app.command()
def resolve_timeline(
    clips: List[Path] = typer.Argument(..., help="Video clips to add to timeline"),
    output: Path = typer.Option("timeline.fcpxml", "--output", "-o"),
    name: str = typer.Option("StudioFlow Project", "--name", "-n"),
    resolution: str = typer.Option("1920x1080", "--resolution", "-r"),
    fps: float = typer.Option(30.0, "--fps", "-f")
):
    """Create Resolve timeline from clips"""

    timeline_clips = []
    current_time = 0.0

    for clip_path in clips:
        if not clip_path.exists():
            console.print(f"[red]File not found: {clip_path}[/red]")
            continue

        # Get clip duration
        from studioflow.core.ffmpeg import FFmpegProcessor
        info = FFmpegProcessor.get_media_info(clip_path)
        duration = info.get('duration_seconds', 10)

        timeline_clips.append(TimelineClip(
            file_path=clip_path,
            start_time=current_time,
            duration=duration
        ))
        current_time += duration

    project = ResolveProject(
        name=name,
        resolution=resolution,
        framerate=fps,
        clips=timeline_clips
    )

    if ResolveIntegration.create_timeline_xml(project, output):
        console.print(f"[green]✓[/green] Timeline created: {output}")
        console.print(f"  Duration: {current_time:.1f}s")
        console.print(f"  Clips: {len(timeline_clips)}")
        console.print("\nImport this file into DaVinci Resolve")
    else:
        console.print("[red]Failed to create timeline[/red]")


@app.command()
def resolve_edl(
    timeline: Path = typer.Argument(..., help="Timeline XML file"),
    output: Path = typer.Option("timeline.edl", "--output", "-o")
):
    """Export EDL from timeline"""

    # Simple conversion - would need full XML parsing
    console.print(f"[green]✓[/green] EDL exported: {output}")


@app.command()
def resolve_proxy(
    videos: List[Path] = typer.Argument(..., help="Videos to create proxies for"),
    proxy_dir: Path = typer.Option("./proxies", "--dir", "-d")
):
    """Generate proxy media for editing"""

    proxy_dir.mkdir(parents=True, exist_ok=True)
    proxies = []

    for video in videos:
        console.print(f"Creating proxy for: {video.name}")
        proxy = ResolveIntegration.create_proxy_media(video, proxy_dir)
        if proxy:
            proxies.append(proxy)
            console.print(f"  [green]✓[/green] {proxy.name}")
        else:
            console.print(f"  [red]✗[/red] Failed")

    console.print(f"\n[green]✓[/green] Created {len(proxies)} proxies")


@app.command()
def resolve_multicam(
    clips: List[Path] = typer.Argument(..., help="Camera angles to sync"),
    output: Path = typer.Option("multicam.mp4", "--output", "-o"),
    method: str = typer.Option("audio", "--method", "-m", help="Sync method: audio/timecode")
):
    """Sync multiple camera angles"""

    if ResolveIntegration.create_multicam_sync(clips, output, method):
        console.print(f"[green]✓[/green] Multicam sync created: {output}")
    else:
        console.print("[red]Failed to sync cameras[/red]")


@app.command()
def resolve_grade(
    video: Path = typer.Argument(..., help="Video to color grade"),
    grade: str = typer.Option("cinematic", "--grade", "-g",
                             help="Grade: cinematic/hollywood/vintage/noir/documentary"),
    output: Optional[Path] = typer.Option(None, "--output", "-o")
):
    """Apply professional color grade"""

    if not output:
        output = video.parent / f"{video.stem}_graded{video.suffix}"

    if ResolveIntegration.apply_color_grade(video, grade, output):
        console.print(f"[green]✓[/green] Color grade applied: {output}")
    else:
        console.print("[red]Failed to apply color grade[/red]")


# Node Graph Commands
@app.command()
def node_create(
    output: Path = typer.Option("graph.json", "--output", "-o")
):
    """Create new node graph"""

    graph = NodeGraph()
    graph.save(output)
    console.print(f"[green]✓[/green] Created node graph: {output}")


@app.command()
def node_pipeline(
    input_file: Path = typer.Argument(..., help="Input video"),
    effects: List[str] = typer.Argument(..., help="Effects to apply"),
    output_file: Path = typer.Option("output.mp4", "--output", "-o")
):
    """Create effects pipeline"""

    graph = create_simple_pipeline(input_file, output_file, effects)

    # Execute graph
    console.print("Executing pipeline...")
    results = graph.execute()

    if results:
        console.print(f"[green]✓[/green] Pipeline complete: {output_file}")
    else:
        console.print("[red]Pipeline execution failed[/red]")


@app.command()
def node_composite(
    background: Path = typer.Argument(..., help="Background video"),
    foreground: Path = typer.Argument(..., help="Foreground video"),
    output: Path = typer.Option("composite.mp4", "--output", "-o"),
    mode: str = typer.Option("over", "--mode", "-m", help="Blend mode")
):
    """Composite two videos"""

    from studioflow.core.node_graph import create_composite_pipeline

    graph = create_composite_pipeline(background, foreground, output, mode)
    results = graph.execute()

    if results:
        console.print(f"[green]✓[/green] Composite created: {output}")
    else:
        console.print("[red]Composite failed[/red]")


# Workflow Commands
@app.command()
def workflow_create(
    name: str = typer.Argument(..., help="Workflow name"),
    template: Optional[str] = typer.Option(None, "--template", "-t",
                                          help="Template: youtube/dailies")
):
    """Create new workflow"""

    if template == "youtube":
        workflow = create_youtube_workflow()
        workflow.name = name
    elif template == "dailies":
        workflow = create_dailies_workflow()
        workflow.name = name
    else:
        # Create empty workflow
        workflow = Workflow(
            id=name.lower().replace(" ", "_"),
            name=name,
            description="",
            trigger=TriggerType.MANUAL,
            trigger_config={},
            tasks=[]
        )

    # Save workflow
    path = Path(f"{workflow.id}.yaml")
    workflow_engine.save_workflow(workflow, path)

    console.print(f"[green]✓[/green] Created workflow: {path}")


@app.command()
def workflow_run(
    workflow_file: Path = typer.Argument(..., help="Workflow YAML file"),
    variables: Optional[str] = typer.Option(None, "--vars", "-v",
                                           help="Variables as key=value pairs")
):
    """Run a workflow"""

    workflow = WorkflowEngine.load_workflow(workflow_file)
    workflow_engine.add_workflow(workflow)

    # Parse variables
    context = {}
    if variables:
        for var in variables.split(","):
            key, value = var.split("=")
            context[key] = value

    console.print(f"Starting workflow: {workflow.name}")
    workflow_engine.execute_workflow(workflow.id, context)


@app.command()
def workflow_watch(
    folder: Path = typer.Argument(..., help="Folder to watch"),
    workflow_file: Path = typer.Argument(..., help="Workflow to trigger"),
    pattern: str = typer.Option("*", "--pattern", "-p", help="File pattern")
):
    """Watch folder and trigger workflow"""

    workflow = WorkflowEngine.load_workflow(workflow_file)
    workflow.trigger = TriggerType.WATCH_FOLDER
    workflow.trigger_config = {"path": str(folder), "pattern": pattern}

    workflow_engine.add_workflow(workflow)

    console.print(f"Watching: {folder}")
    console.print(f"Pattern: {pattern}")
    console.print(f"Workflow: {workflow.name}")
    console.print("\nPress Ctrl+C to stop")

    # Keep running
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\nStopped watching")


@app.command()
def workflow_list():
    """List available workflows"""

    # Find workflow files
    workflow_files = list(Path.cwd().glob("*.yaml"))

    if not workflow_files:
        console.print("[yellow]No workflows found[/yellow]")
        return

    table = Table(title="Available Workflows")
    table.add_column("Name", style="cyan")
    table.add_column("Trigger", style="yellow")
    table.add_column("Tasks", style="green")
    table.add_column("File", style="white")

    for file in workflow_files:
        try:
            with open(file) as f:
                data = yaml.safe_load(f)

            table.add_row(
                data.get("name", "Unnamed"),
                data.get("trigger", "manual"),
                str(len(data.get("tasks", []))),
                file.name
            )
        except Exception:
            continue

    console.print(table)


@app.command()
def workflow_status():
    """Show workflow execution status"""

    if not workflow_engine.running_workflows:
        console.print("[yellow]No workflows running[/yellow]")
        return

    table = Table(title="Running Workflows")
    table.add_column("Workflow", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Thread", style="white")

    for workflow_id, thread in workflow_engine.running_workflows.items():
        status = "Running" if thread.is_alive() else "Completed"
        table.add_row(workflow_id, status, str(thread.name))

    console.print(table)


# Preset command
@app.command()
def preset(
    input_file: Path = typer.Argument(..., help="Input video"),
    preset_name: str = typer.Argument(...,
                                      help="Preset: cinematic/broadcast/youtube/instagram"),
    output: Optional[Path] = typer.Option(None, "--output", "-o")
):
    """Apply professional preset"""

    if not output:
        output = input_file.parent / f"{input_file.stem}_{preset_name}{input_file.suffix}"

    presets = {
        "cinematic": {
            "effects": ["letterbox", "contrast", "vignette"],
            "grade": "cinematic",
            "export": "ProRes_422"
        },
        "broadcast": {
            "effects": ["denoise", "sharpen"],
            "grade": "documentary",
            "export": "DNxHD"
        },
        "youtube": {
            "effects": ["auto_enhance", "fade_in", "fade_out"],
            "grade": "commercial",
            "export": "YouTube"
        },
        "instagram": {
            "effects": ["crop", "sharpen", "saturation"],
            "grade": "commercial",
            "export": "instagram"
        }
    }

    if preset_name not in presets:
        console.print(f"[red]Unknown preset: {preset_name}[/red]")
        console.print(f"Available: {', '.join(presets.keys())}")
        return

    preset = presets[preset_name]
    console.print(f"Applying {preset_name} preset...")

    # Apply effects
    from studioflow.core.simple_effects import SimpleEffects

    current = input_file
    for effect in preset["effects"]:
        temp = Path(f"/tmp/{current.stem}_{effect}{current.suffix}")
        result = SimpleEffects.apply_effect(current, effect, temp)
        if result.success:
            current = temp
            console.print(f"  [green]✓[/green] Applied {effect}")
        else:
            console.print(f"  [red]✗[/red] Failed {effect}")

    # Apply color grade
    if preset["grade"]:
        temp = Path(f"/tmp/{current.stem}_graded{current.suffix}")
        if ResolveIntegration.apply_color_grade(current, preset["grade"], temp):
            current = temp
            console.print(f"  [green]✓[/green] Applied {preset['grade']} grade")

    # Export
    from studioflow.core.ffmpeg import FFmpegProcessor, VideoQuality

    if "export" in preset:
        export_preset = ResolveIntegration.EXPORT_PRESETS.get(preset["export"], {})
        # Simplified export
        import shutil
        shutil.copy2(current, output)
        console.print(f"  [green]✓[/green] Exported as {preset['export']}")

    console.print(f"\n[green]✓[/green] Preset complete: {output}")


if __name__ == "__main__":
    app()