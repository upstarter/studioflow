"""DaVinci Resolve Commands"""

import sys
import subprocess
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from studioflow.core.state import StateManager
from studioflow.core.project import ProjectManager
from studioflow.core.config import get_config
from studioflow.core.resolve_profiles import ResolveProfiles


console = Console()
app = typer.Typer()


def check_resolve_running() -> bool:
    """Check if DaVinci Resolve is running"""
    try:
        result = subprocess.run(["pgrep", "-f", "resolve"], capture_output=True, timeout=1)
        return result.returncode == 0
    except:
        return False


def get_resolve_api():
    """Get DaVinci Resolve API instance"""
    config = get_config()
    api_path = config.resolve.api_path or config.resolve.install_path / "Developer" / "Scripting"

    if not api_path.exists():
        return None, "DaVinci Resolve API not found"

    sys.path.insert(0, str(api_path / "Modules"))

    try:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp("Resolve")
        if not resolve:
            return None, "Could not connect to Resolve (is it running?)"
        return resolve, None
    except ImportError as e:
        return None, f"Failed to import Resolve API: {e}"


@app.command()
def sync(project_name: Optional[str] = None):
    """Sync project with DaVinci Resolve"""
    state = StateManager()
    name = project_name or state.current_project

    if not name:
        console.print("[red]No project specified. Use --project or select one first[/red]")
        return

    # Get project
    manager = ProjectManager()
    project = manager.get_project(name)

    if not project:
        console.print(f"[red]Project not found: {name}[/red]")
        return

    with Progress(console=console) as progress:
        # Check if Resolve is running
        task = progress.add_task("Checking DaVinci Resolve...", total=3)

        if not check_resolve_running():
            console.print("[yellow]DaVinci Resolve is not running[/yellow]")
            console.print("\nWould you like to:")
            console.print("  1. Start Resolve now")
            console.print("  2. Skip Resolve sync")
            return

        progress.update(task, advance=1, description="Connecting to Resolve API...")

        # Get Resolve API
        resolve, error = get_resolve_api()
        if not resolve:
            console.print(f"[red]Error: {error}[/red]")
            return

        progress.update(task, advance=1, description="Creating/updating project...")

        # Create or get project
        pm = resolve.GetProjectManager()

        # Check if project exists
        existing_project = None
        for proj in pm.GetProjectListInCurrentFolder():
            if proj == project.name:
                existing_project = pm.LoadProject(proj)
                break

        if existing_project:
            console.print(f"[green]✓[/green] Loaded existing Resolve project: {project.name}")
            resolve_project = existing_project
        else:
            resolve_project = pm.CreateProject(project.name)
            if resolve_project:
                console.print(f"[green]✓[/green] Created new Resolve project: {project.name}")
            else:
                console.print(f"[red]Failed to create Resolve project[/red]")
                return

        # Set project settings
        resolve_project.SetSetting("timelineFrameRate", str(project.metadata.framerate))
        res_parts = project.metadata.resolution.split("x")
        resolve_project.SetSetting("timelineResolutionWidth", res_parts[0])
        resolve_project.SetSetting("timelineResolutionHeight", res_parts[1])

        progress.update(task, advance=1, description="Importing media...")

        # Import media
        media_pool = resolve_project.GetMediaPool()
        media_folder = project.path / "01_MEDIA"

        if media_folder.exists():
            media_files = list(media_folder.rglob("*.mp4")) + \
                         list(media_folder.rglob("*.mov")) + \
                         list(media_folder.rglob("*.mxf"))

            if media_files:
                imported = media_pool.ImportMedia([str(f) for f in media_files])
                console.print(f"  [green]✓[/green] Imported {len(media_files)} media files")

    console.print(Panel(
        f"[green]✓[/green] Resolve sync complete!\n\n"
        f"Project '{project.name}' is ready in DaVinci Resolve",
        title="Sync Complete",
        border_style="green"
    ))


@app.command()
def start():
    """Start DaVinci Resolve"""
    config = get_config()
    resolve_bin = config.resolve.install_path / "bin" / "resolve"

    if not resolve_bin.exists():
        console.print(f"[red]DaVinci Resolve not found at: {resolve_bin}[/red]")
        return

    console.print("Starting DaVinci Resolve...")
    subprocess.Popen(
        [str(resolve_bin)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    console.print("[green]✓[/green] DaVinci Resolve is starting (this may take 10-30 seconds)")
    console.print("\nOnce Resolve is open, run: [bold]sf resolve sync[/bold]")


@app.command()
def status():
    """Check DaVinci Resolve status"""
    config = get_config()

    # Check if installed
    resolve_bin = config.resolve.install_path / "bin" / "resolve"
    if resolve_bin.exists():
        console.print(f"[green]✓[/green] Resolve installed at: {config.resolve.install_path}")
    else:
        console.print(f"[red]✗[/red] Resolve not found at: {config.resolve.install_path}")
        return

    # Check if running
    if check_resolve_running():
        console.print("[green]✓[/green] Resolve is running")

        # Try to connect
        resolve, error = get_resolve_api()
        if resolve:
            console.print("[green]✓[/green] API connection successful")

            # Show current project
            pm = resolve.GetProjectManager()
            current = pm.GetCurrentProject()
            if current:
                console.print(f"  Current project: {current.GetName()}")
        else:
            console.print(f"[yellow]![/yellow] API connection failed: {error}")
    else:
        console.print("[yellow]✗[/yellow] Resolve is not running")
        console.print("\nRun: [bold]sf resolve start[/bold] to launch Resolve")


@app.command()
def export(
    input_file: Path = typer.Argument(..., help="Video file to export"),
    preset: str = typer.Option("youtube_4k", "--preset", "-p", help="Export preset"),
    platform: str = typer.Option(None, "--platform", help="Target platform (overrides preset)"),
    show_command: bool = typer.Option(False, "--show-command", help="Show FFmpeg command")
):
    """
    Generate optimized export settings

    Examples:
        sf resolve export video.mp4 --preset youtube_4k
        sf resolve export render.mov --platform instagram
        sf resolve export final.mp4 --show-command
    """
    if not input_file.exists():
        console.print(f"[red]File not found: {input_file}[/red]")
        raise typer.Exit(1)

    # Get preset based on platform if specified
    if platform:
        preset_map = {
            "youtube": "youtube_4k",
            "instagram": "instagram_reel",
            "tiktok": "tiktok",
            "master": "prores_master"
        }
        preset = preset_map.get(platform, "youtube_4k")

    # Get export settings
    settings = ResolveProfiles.get_export_preset(platform or preset.replace("_", " ").split()[0])

    # Display export settings
    console.print(f"\n[bold]Export Settings for {preset}:[/bold]\n")

    table = Table(show_header=False)
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="white")

    for key, value in settings.items():
        if key not in ["optimize_for"]:
            display_key = key.replace("_", " ").title()
            display_value = str(value)
            if "bitrate" in key and isinstance(value, (int, float)):
                display_value = f"{value:,} kbps"
            table.add_row(display_key, display_value)

    console.print(table)

    # Generate FFmpeg command if requested
    if show_command:
        command = ResolveProfiles.generate_export_command(input_file, preset)
        console.print("\n[bold]FFmpeg Command:[/bold]")
        console.print(Panel(command, title="Export Command"))

    # Show strategy
    console.print("\n[bold]Export Strategy:[/bold]")
    strategy = ResolveProfiles.get_multi_export_strategy()
    for tier in strategy[:3]:  # Show top 3 tiers
        console.print(f"  • {tier['description']}")

    return settings


@app.command()
def profiles(
    profile_type: str = typer.Argument("all", help="Profile type: youtube/fx30/export/all"),
    details: bool = typer.Option(False, "--details", "-d", help="Show detailed settings")
):
    """
    Show DaVinci Resolve optimization profiles

    Examples:
        sf resolve profiles
        sf resolve profiles youtube
        sf resolve profiles fx30 --details
    """
    if profile_type == "all" or profile_type == "youtube":
        console.print("\n[bold cyan]YouTube Quality Profiles:[/bold cyan]\n")

        for quality_name, settings in ResolveProfiles.YOUTUBE_QUALITY_MATRIX.items():
            console.print(f"[bold]{quality_name}:[/bold]")
            console.print(f"  Resolution: {settings['resolution'][0]}x{settings['resolution'][1]}")
            console.print(f"  Bitrate: {settings['target_bitrate']} Mbps")
            if 'codec_trigger' in settings:
                console.print(f"  Codec: {settings['codec_trigger']}")
            if 'strategy' in settings:
                console.print(f"  Strategy: [dim]{settings['strategy']}[/dim]\n")

    if profile_type == "all" or profile_type == "fx30":
        console.print("\n[bold cyan]FX30 Camera Profiles:[/bold cyan]\n")

        for profile_name, settings in ResolveProfiles.FX30_PROFILES.items():
            console.print(f"[bold]{profile_name}:[/bold]")
            console.print(f"  {settings['description']}")
            console.print(f"  Color Space: {settings['input_color_space']} → {settings['output_color_space']}")
            if details:
                console.print(f"  Recommended for: {', '.join(settings.get('recommended_for', []))}")
            console.print()

    if profile_type == "all" or profile_type == "export":
        console.print("\n[bold cyan]Export Presets:[/bold cyan]\n")

        table = Table(title="Platform Export Presets")
        table.add_column("Preset", style="cyan")
        table.add_column("Resolution", style="white")
        table.add_column("Bitrate", style="green")
        table.add_column("Format", style="yellow")

        for preset_name, settings in ResolveProfiles.EXPORT_PRESETS.items():
            bitrate = settings.get("target_bitrate", "N/A")
            if isinstance(bitrate, int):
                bitrate = f"{bitrate//1000} Mbps"
            table.add_row(
                preset_name,
                settings.get("resolution", "source"),
                bitrate,
                settings.get("format", "N/A")
            )

        console.print(table)

    # Show workflow tips
    if details:
        console.print("\n[bold]Color Workflow Tips:[/bold]")
        tips = ResolveProfiles.get_color_workflow_tips()
        for tip_name, tip_text in tips.items():
            console.print(f"  • {tip_name}: {tip_text}")


@app.command()
def optimize(
    project_name: Optional[str] = typer.Option(None, "--project", "-p", help="Project name"),
    quality: str = typer.Option("4k30_master", "--quality", "-q", help="Quality preset"),
    camera: str = typer.Option("fx30", "--camera", "-c", help="Camera type")
):
    """
    Get optimized settings for your project

    Examples:
        sf resolve optimize
        sf resolve optimize --quality 4k30_master
        sf resolve optimize --camera fx30
    """
    state = StateManager()
    name = project_name or state.current_project

    console.print(f"\n[bold]Optimization Settings for: {name or 'Generic Project'}[/bold]\n")

    # YouTube settings
    yt_settings = ResolveProfiles.get_youtube_settings(quality)
    console.print("[bold cyan]YouTube Export Settings:[/bold cyan]")
    console.print(f"  Resolution: {yt_settings['resolution'][0]}x{yt_settings['resolution'][1]}")
    console.print(f"  Target Bitrate: {yt_settings['target_bitrate']} Mbps")
    console.print(f"  Max Bitrate: {yt_settings['max_bitrate']} Mbps")
    console.print(f"  Audio Target: {yt_settings['audio_lufs']} LUFS")
    console.print(f"  [dim]{yt_settings['strategy']}[/dim]\n")

    # Camera profile
    if camera == "fx30":
        console.print("[bold cyan]FX30 Camera Workflow:[/bold cyan]")
        console.print("  1. S-Cinetone: Use scinetone_rec709 profile for quick turnaround")
        console.print("  2. S-Log3: Use slog3_workflow for maximum grading flexibility")
        console.print("  3. Apply provided LUTs at 50-70% intensity")
        console.print("  4. Target -14 LUFS for YouTube\n")

    # Multi-tier strategy
    console.print("[bold cyan]Recommended Export Strategy:[/bold cyan]")
    strategy = ResolveProfiles.get_multi_export_strategy()
    for i, tier in enumerate(strategy, 1):
        if i <= 3:  # Show top 3
            console.print(f"  {i}. {tier['description']}")
            console.print(f"     Preset: {tier['preset']}")

    return {
        "youtube_settings": yt_settings,
        "export_strategy": strategy
    }