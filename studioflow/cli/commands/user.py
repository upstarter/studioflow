"""
User-focused commands for StudioFlow
Practical everyday features
"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track, Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from datetime import datetime
import time
import shutil

from studioflow.core.user_utils import UserUtils, ProjectStatus, QualityReport
from studioflow.core.ffmpeg import FFmpegProcessor
from studioflow.core.simple_effects import SimpleEffects

console = Console()
app = typer.Typer()


@app.command()
def status():
    """Show current project status and recent work"""

    status = UserUtils.get_status()

    # Project info
    if status.current_project:
        console.print(Panel(f"[cyan]{status.current_project}[/cyan]", title="Current Project"))
    else:
        console.print("[yellow]No active project[/yellow]")

    # Recent files
    if status.recent_files:
        console.print("\n[bold]Recent Files (last 24h):[/bold]")
        for file in status.recent_files[:5]:
            time_ago = datetime.now() - file['modified']
            hours = time_ago.total_seconds() / 3600
            console.print(f"  • {Path(file['path']).name} ({file['size_mb']:.1f}MB) - {hours:.1f}h ago")

    # Disk space
    if status.disk_usage:
        used_pct = status.disk_usage['percent_used']
        color = "green" if used_pct < 70 else "yellow" if used_pct < 90 else "red"
        console.print(f"\n[bold]Disk Space:[/bold]")
        console.print(f"  [{color}]▓[/{color}]" * int(used_pct/5) + "░" * (20 - int(used_pct/5)))
        console.print(f"  {status.disk_usage['free_gb']:.1f}GB free of {status.disk_usage['total_gb']:.1f}GB")

    # Last commands
    if status.last_commands:
        console.print("\n[bold]Recent Commands:[/bold]")
        for cmd in status.last_commands[-3:]:
            console.print(f"  $ {cmd}")


@app.command()
def check(
    file_path: Path = typer.Argument(..., help="Media file to check"),
    autofix: bool = typer.Option(False, "--fix", "-f", help="Auto-fix issues")
):
    """Check media quality and find issues"""

    console.print(f"Checking: {file_path.name}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task("Analyzing...", total=None)
        report = UserUtils.check_quality(file_path)

    # Show results
    if not report.issues and not report.warnings:
        console.print("[green]✅ File looks good![/green]")
        return

    # Issues
    if report.issues:
        console.print("\n[red]Issues Found:[/red]")
        for issue in report.issues:
            console.print(f"  ❌ {issue}")

    # Warnings
    if report.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in report.warnings:
            console.print(f"  ⚠️  {warning}")

    # Suggestions
    if report.suggestions:
        console.print("\n[cyan]Suggestions:[/cyan]")
        for suggestion in report.suggestions:
            console.print(f"  💡 {suggestion}")

    # Auto-fix
    if autofix and report.can_autofix:
        if typer.confirm("\nAuto-fix issues?"):
            console.print("Fixing...")
            # Determine fix type from warnings
            if any("quiet" in w.lower() for w in report.warnings):
                fixed = UserUtils.smart_fix(file_path, "quiet")
            elif any("black" in w.lower() for w in report.warnings):
                fixed = UserUtils.smart_fix(file_path, "black")
            elif any("dark" in w.lower() for w in report.warnings):
                fixed = UserUtils.smart_fix(file_path, "dark")

            if fixed:
                console.print(f"[green]✅ Fixed! Output: {fixed}[/green]")


@app.command()
def fix(
    file_path: Path = typer.Argument(..., help="Media file to fix"),
    issue: str = typer.Argument(..., help="Issue to fix: quiet/dark/shaky/black")
):
    """Fix common media issues"""

    console.print(f"Fixing {issue} issue in {file_path.name}")

    # Create snapshot
    UserUtils.snapshot(file_path, f"before_fix_{issue}")
    console.print("[dim]Snapshot created[/dim]")

    # Fix issue
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task(f"Fixing {issue}...", total=100)

        # Simulate progress (in reality would track FFmpeg)
        for i in range(100):
            time.sleep(0.02)
            progress.update(task, advance=1)

        fixed = UserUtils.smart_fix(file_path, issue)

    if fixed:
        console.print(f"[green]✅ Fixed! Output: {fixed}[/green]")
    else:
        console.print(f"[red]Failed to fix {issue}[/red]")


@app.command()
def preview(
    file_path: Path = typer.Argument(..., help="Media file"),
    effect: Optional[str] = typer.Option(None, "--effect", "-e", help="Effect to preview"),
    duration: float = typer.Option(5.0, "--duration", "-d", help="Preview duration")
):
    """Generate quick preview"""

    console.print(f"Creating {duration}s preview...")

    preview_path = UserUtils.quick_preview(file_path, effect, duration)

    if preview_path:
        console.print(f"[green]✅ Preview: {preview_path}[/green]")

        # Try to play it
        import subprocess
        try:
            # Try common video players
            for player in ["mpv", "vlc", "ffplay"]:
                if shutil.which(player):
                    subprocess.run([player, str(preview_path)], check=False)
                    break
        except:
            console.print(f"Open manually: {preview_path}")
    else:
        console.print("[red]Failed to create preview[/red]")


@app.command()
def snapshot(
    file_path: Path = typer.Argument(..., help="File to snapshot"),
    label: Optional[str] = typer.Option(None, "--label", "-l", help="Snapshot label")
):
    """Create backup snapshot"""

    snapshot_path = UserUtils.snapshot(file_path, label)
    console.print(f"[green]✅ Snapshot created: {snapshot_path}[/green]")


@app.command()
def undo(
    file_path: Path = typer.Argument(..., help="File to restore")
):
    """Restore from last snapshot"""

    if UserUtils.undo(file_path):
        console.print(f"[green]✅ Restored {file_path.name} from snapshot[/green]")
    else:
        console.print(f"[red]No snapshot found for {file_path.name}[/red]")


@app.command()
def quick(
    file_path: Path = typer.Argument(..., help="Video to process"),
    platform: Optional[str] = typer.Option(None, "--platform", "-p")
):
    """Quick processing with smart defaults"""

    # Get learned defaults
    defaults = UserUtils.get_smart_defaults()
    platform = platform or defaults.get("platform", "youtube")

    console.print(f"Quick processing for {platform}")

    tasks = []

    # Always normalize audio if enabled
    if defaults.get("auto_normalize", True):
        tasks.append(("Normalizing audio", "normalize"))

    # Platform-specific
    if platform == "youtube":
        tasks.append(("Adding fade in", "fade_in"))
        tasks.append(("Adding fade out", "fade_out"))
        tasks.append(("Exporting for YouTube", "export"))
    elif platform == "instagram":
        tasks.append(("Cropping to square", "crop_square"))
        tasks.append(("Exporting for Instagram", "export"))

    # Execute tasks
    current = file_path
    with Progress() as progress:
        main_task = progress.add_task("[cyan]Processing...", total=len(tasks))

        for task_name, task_type in tasks:
            progress.update(main_task, description=f"[cyan]{task_name}...")

            if task_type == "normalize":
                output = current.parent / f"{current.stem}_normalized{current.suffix}"
                result = FFmpegProcessor.normalize_audio(current, output)
                if result.success:
                    current = output
            elif task_type == "fade_in":
                output = current.parent / f"{current.stem}_fade{current.suffix}"
                result = SimpleEffects.apply_effect(current, "fade_in", output)
                if result.success:
                    current = output
            elif task_type == "export":
                output = current.parent / f"{current.stem}_{platform}{current.suffix}"
                result = FFmpegProcessor.export_for_platform(current, platform, output)
                if result.success:
                    current = output

            progress.update(main_task, advance=1)

            # Learn pattern
            UserUtils.learn_pattern(task_type, {"platform": platform})

    console.print(f"[green]✅ Quick processing complete: {current}[/green]")


@app.command()
def typical(
    file_path: Path = typer.Argument(..., help="Video to process")
):
    """Run your typical workflow"""

    console.print("Running typical workflow...")

    # Based on your actual usage patterns:
    # 1. Cut first 2 seconds (handles camera start delay)
    # 2. Normalize audio to -16 LUFS
    # 3. Add subtle fade in/out
    # 4. Export for YouTube
    # 5. Generate thumbnail

    workflow = [
        ("Trimming start", lambda f: FFmpegProcessor.cut_video(f, f.parent / f"{f.stem}_trimmed.mp4", 2, None)),
        ("Normalizing audio", lambda f: FFmpegProcessor.normalize_audio(f, f.parent / f"{f.stem}_norm.mp4")),
        ("Adding fades", lambda f: SimpleEffects.apply_multiple(f, ["fade_in", "fade_out"], f.parent / f"{f.stem}_faded.mp4")),
        ("Exporting for YouTube", lambda f: FFmpegProcessor.export_for_platform(f, "youtube", f.parent / f"{f.stem}_youtube.mp4")),
        ("Generating thumbnail", lambda f: FFmpegProcessor.generate_thumbnail(f, best_frame=True))
    ]

    current = file_path
    outputs = []

    with Progress() as progress:
        task = progress.add_task("[cyan]Processing typical workflow...", total=len(workflow))

        for step_name, step_func in workflow:
            progress.update(task, description=f"[cyan]{step_name}...")
            result = step_func(current)

            if hasattr(result, 'success') and result.success:
                if result.output_path:
                    current = result.output_path
                    outputs.append(current)
            elif isinstance(result, Path):
                current = result
                outputs.append(current)

            progress.update(task, advance=1)

    console.print("\n[green]✅ Typical workflow complete![/green]")
    console.print("Outputs:")
    for output in outputs:
        console.print(f"  • {output}")


@app.command()
def recent():
    """Show recent work and continue where you left off"""

    status = UserUtils.get_status()

    if not status.recent_files:
        console.print("[yellow]No recent files found[/yellow]")
        return

    table = Table(title="Recent Work")
    table.add_column("#", style="cyan")
    table.add_column("File", style="white")
    table.add_column("Size", style="green")
    table.add_column("Modified", style="yellow")

    for i, file in enumerate(status.recent_files[:10], 1):
        time_ago = datetime.now() - file['modified']
        if time_ago.days > 0:
            ago = f"{time_ago.days}d ago"
        else:
            hours = time_ago.seconds // 3600
            if hours > 0:
                ago = f"{hours}h ago"
            else:
                ago = f"{time_ago.seconds // 60}m ago"

        table.add_row(
            str(i),
            Path(file['path']).name,
            f"{file['size_mb']:.1f}MB",
            ago
        )

    console.print(table)

    if typer.confirm("\nContinue with most recent?"):
        most_recent = Path(status.recent_files[0]['path'])
        console.print(f"Working with: {most_recent}")
        # Could launch interactive session here


@app.command()
def estimate(
    file_path: Path = typer.Argument(..., help="Media file"),
    operation: str = typer.Argument(..., help="Operation: export/effect/upload/transcribe")
):
    """Estimate processing time"""

    estimate = UserUtils.estimate_time(file_path, operation)
    size_mb = file_path.stat().st_size / (1024 * 1024)

    console.print(f"File: {file_path.name} ({size_mb:.1f}MB)")
    console.print(f"Operation: {operation}")
    console.print(f"[yellow]Estimated time: {estimate}[/yellow]")


@app.command()
def batch(
    pattern: str = typer.Argument(..., help="File pattern: 'today', 'gopro', '*.mp4'"),
    operation: str = typer.Argument(..., help="Operation to perform"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o"),
    parallel: int = typer.Option(4, "--parallel", "-p", help="Parallel jobs")
):
    """Batch process files using parallel processing"""

    from datetime import datetime
    from studioflow.core.batch_processor import BatchProcessor, BatchResult

    files = []

    # Smart pattern matching
    if pattern == "today":
        # Find files from today
        cutoff = datetime.now().replace(hour=0, minute=0, second=0)
        for file in Path.cwd().rglob("*.mp4"):
            if datetime.fromtimestamp(file.stat().st_mtime) > cutoff:
                files.append(file)

    elif pattern == "gopro":
        # Find GoPro files
        for file in Path.cwd().rglob("*GH*.mp4"):
            files.append(file)

    else:
        # Use as glob pattern
        files = list(Path.cwd().rglob(pattern))

    if not files:
        console.print(f"[yellow]No files match '{pattern}'[/yellow]")
        return

    console.print(f"[cyan]Found {len(files)} file(s) to process[/cyan]\n")

    if not output_dir:
        output_dir = Path.cwd() / "batch_output"
    output_dir.mkdir(exist_ok=True)

    # Define operation function for BatchProcessor
    def batch_operation(file: Path, **kwargs) -> BatchResult:
        import time
        start = time.time()
        
        try:
            op = kwargs.get('operation')
            out_dir = kwargs.get('output_dir')
            
            if op == "normalize":
                output = out_dir / f"{file.stem}_norm{file.suffix}"
                result = FFmpegProcessor.normalize_audio(file, output)
                return BatchResult(
                    file=file,
                    success=result.success,
                    output=output if result.success else None,
                    error=result.error_message if not result.success else None,
                    duration=time.time() - start
                )
            elif op == "compress":
                output = out_dir / f"{file.stem}_compressed{file.suffix}"
                result = FFmpegProcessor.export_for_platform(file, "youtube", output)
                return BatchResult(
                    file=file,
                    success=result.success,
                    output=output if result.success else None,
                    error=result.error_message if not result.success else None,
                    duration=time.time() - start
                )
            elif op in SimpleEffects.EFFECTS:
                output = out_dir / f"{file.stem}_{op}{file.suffix}"
                result = SimpleEffects.apply_effect(file, op, output)
                return BatchResult(
                    file=file,
                    success=result.success if hasattr(result, 'success') else True,
                    output=output,
                    error=None,
                    duration=time.time() - start
                )
            else:
                return BatchResult(
                    file=file,
                    success=False,
                    error=f"Unknown operation: {op}",
                    duration=time.time() - start
                )
        except Exception as e:
            return BatchResult(
                file=file,
                success=False,
                error=str(e),
                duration=time.time() - start
            )

    # Process files using BatchProcessor
    processor = BatchProcessor(max_workers=parallel)
    results = processor.process(
        files,
        batch_operation,
        operation_name=f"Batch {operation}",
        operation=operation,
        output_dir=output_dir
    )

    # Display summary
    summary = processor.get_summary()
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Output directory: {output_dir}")
    console.print(f"  Successful: [green]{summary['successful']}[/green]")
    console.print(f"  Failed: [red]{summary['failed']}[/red]")
    console.print(f"  Success rate: {summary['success_rate']*100:.1f}%")
    
    if summary['failed'] > 0:
        console.print(f"\n[yellow]Failed files:[/yellow]")
        for result in results:
            if not result.success:
                console.print(f"  ✗ {result.file.name}: {result.error}")


if __name__ == "__main__":
    app()