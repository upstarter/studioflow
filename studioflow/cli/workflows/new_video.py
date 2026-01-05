"""
New Video Workflow - The Main Automation
Handles the complete workflow from project creation to ready-to-edit
"""

from pathlib import Path
from typing import Optional
import os
import subprocess

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from studioflow.core.project import Project, ProjectResult
from studioflow.core.config import get_config, Platform
from studioflow.core.state import StateManager
from studioflow.core.media import MediaImporter, MediaScanner


console = Console()


def create_workflow(
    name: str,
    template: str = "youtube",
    import_path: Optional[Path] = None,
    platform: str = "youtube",
    interactive: bool = False
) -> ProjectResult:
    """
    Complete workflow for creating a new video project.

    This orchestrates:
    1. Project creation with template
    2. Media import and organization
    3. DaVinci Resolve project setup
    4. Platform-specific optimization
    """
    state = StateManager()
    config = get_config()

    try:
        # Interactive mode - ask for details
        if interactive:
            name, template, import_path, platform = _interactive_setup(name)

        # Step 1: Create project structure
        console.print(f"\n[bold]Creating project:[/bold] {name}")
        project = Project(name)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            # Create project
            task = progress.add_task("Creating project structure...", total=None)
            result = project.create(
                template=template,
                platform=Platform(platform)
            )

            if not result.success:
                console.print(f"[red]Failed to create project: {result.error}[/red]")
                return result

            progress.update(task, completed=True)

            # Step 2: Import media if provided
            if import_path and import_path.exists():
                task = progress.add_task("Importing media...", total=None)
                media_stats = _import_media(project, import_path)

                console.print(f"  [green]✓[/green] Imported {media_stats['total_files']} files")
                progress.update(task, completed=True)

            # Step 3: Check Resolve (but don't block on it)
            if config.resolve.enabled:
                task = progress.add_task("Checking DaVinci Resolve...", total=None)

                if _is_resolve_running():
                    # Only try if Resolve is already running
                    resolve_result = _setup_resolve_project(project)
                    if resolve_result['success']:
                        console.print(f"  [green]✓[/green] DaVinci Resolve project created")
                    else:
                        console.print(f"  [yellow]![/yellow] Resolve project will need manual setup")
                else:
                    console.print(f"  [yellow]![/yellow] Resolve not running - use 'sf resolve sync' later")

                progress.update(task, completed=True)

            # Step 4: Platform-specific setup
            task = progress.add_task(f"Configuring for {platform}...", total=None)
            _setup_platform(project, platform)
            progress.update(task, completed=True)

        # Update state
        state.current_project = name
        state.add_recent_project(name)

        # Show summary
        _show_summary(project, result)

        return result

    except KeyboardInterrupt:
        console.print("\n[yellow]Workflow cancelled by user[/yellow]")
        return ProjectResult(success=False, error="Cancelled by user")

    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        return ProjectResult(success=False, error=str(e))


def _interactive_setup(name: str) -> tuple:
    """Interactive setup wizard"""
    console.print("\n[bold cyan]New Video Project Setup[/bold cyan]\n")

    # Get project name if not provided
    if not name:
        name = Prompt.ask("Project name")

    # Select template
    templates = ["youtube", "vlog", "tutorial", "shorts", "multicam", "custom"]
    console.print("\nAvailable templates:")
    for i, tmpl in enumerate(templates, 1):
        console.print(f"  {i}. {tmpl}")

    template_idx = Prompt.ask(
        "Select template",
        default="1",
        choices=[str(i) for i in range(1, len(templates) + 1)]
    )
    template = templates[int(template_idx) - 1]

    # Ask for media import
    import_path = None
    if Confirm.ask("\nImport media now?", default=False):
        path_str = Prompt.ask("Media location (SD card or folder)")
        import_path = Path(path_str)

        if not import_path.exists():
            console.print(f"[yellow]Path does not exist: {import_path}[/yellow]")
            import_path = None

    # Select platform
    platforms = ["youtube", "instagram", "tiktok", "vimeo", "all"]
    console.print("\nTarget platform:")
    for i, plat in enumerate(platforms, 1):
        console.print(f"  {i}. {plat}")

    platform_idx = Prompt.ask(
        "Select platform",
        default="1",
        choices=[str(i) for i in range(1, len(platforms) + 1)]
    )
    platform = platforms[int(platform_idx) - 1]

    return name, template, import_path, platform


def _import_media(project: Project, import_path: Path) -> dict:
    """Import media with smart organization"""
    scanner = MediaScanner()
    files = scanner.scan(import_path)

    if not files:
        return {"total_files": 0, "total_size": 0}

    importer = MediaImporter(project)
    stats = {"total_files": 0, "total_size": 0}

    for file_info in files:
        result = importer.import_file(file_info)
        if result['imported']:
            stats['total_files'] += 1
            stats['total_size'] += file_info['size']

    return stats


def _is_resolve_running() -> bool:
    """Check if DaVinci Resolve is currently running"""
    try:
        # Quick check if Resolve process is running
        result = subprocess.run(
            ["pgrep", "-f", "resolve"],
            capture_output=True,
            timeout=1
        )

        # Also check if we can connect to the API
        if result.returncode == 0:
            config = get_config()
            api_path = config.resolve.api_path or config.resolve.install_path / "Developer" / "Scripting"
            if api_path.exists():
                import sys
                sys.path.insert(0, str(api_path / "Modules"))
                import DaVinciResolveScript as dvr
                resolve = dvr.scriptapp("Resolve")
                return resolve is not None
    except:
        pass

    return False


def _setup_resolve_project(project: Project) -> dict:
    """Setup DaVinci Resolve project (only if Resolve is running)"""
    try:
        # Import Resolve API
        config = get_config()
        import sys
        api_path = config.resolve.api_path or config.resolve.install_path / "Developer" / "Scripting"
        sys.path.insert(0, str(api_path / "Modules"))

        import DaVinciResolveScript as dvr

        # Get Resolve instance (don't try to start it)
        resolve = dvr.scriptapp("Resolve")
        if not resolve:
            return {"success": False, "error": "Could not connect to DaVinci Resolve"}

        # Create project
        pm = resolve.GetProjectManager()
        new_project = pm.CreateProject(project.name)

        if not new_project:
            return {"success": False, "error": "Failed to create Resolve project"}

        # Set project settings
        new_project.SetSetting("timelineFrameRate", str(project.metadata.framerate))
        new_project.SetSetting("timelineResolutionWidth", project.metadata.resolution.split("x")[0])
        new_project.SetSetting("timelineResolutionHeight", project.metadata.resolution.split("x")[1])

        # Import media if exists
        media_pool = new_project.GetMediaPool()
        media_folder = project.path / "01_MEDIA"

        if media_folder.exists():
            media_files = list(media_folder.rglob("*.mp4")) + list(media_folder.rglob("*.mov"))
            if media_files:
                media_pool.ImportMedia([str(f) for f in media_files])

        return {"success": True, "project": new_project}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _setup_platform(project: Project, platform: str):
    """Configure project for specific platform"""
    platform_configs = {
        "youtube": {
            "resolution": "3840x2160",
            "framerate": 29.97,
            "aspect": "16:9",
            "folders": ["Thumbnails", "Descriptions", "Tags"]
        },
        "instagram": {
            "resolution": "1080x1920",
            "framerate": 30,
            "aspect": "9:16",
            "folders": ["Covers", "Captions", "Hashtags"]
        },
        "tiktok": {
            "resolution": "1080x1920",
            "framerate": 30,
            "aspect": "9:16",
            "folders": ["Hooks", "Captions", "Sounds"]
        }
    }

    if platform in platform_configs:
        config = platform_configs[platform]

        # Create platform-specific folders
        for folder in config.get("folders", []):
            (project.path / folder).mkdir(exist_ok=True)

        # Update project metadata
        project.metadata.resolution = config["resolution"]
        project.metadata.framerate = config["framerate"]
        project.save_metadata()


def _show_summary(project: Project, result: ProjectResult):
    """Show project creation summary"""
    summary = f"""
[bold green]✅ Project Created Successfully![/bold green]

📁 Project: [cyan]{project.name}[/cyan]
📍 Location: {project.path}
🎬 Template: {project.metadata.template}
📺 Platform: {project.metadata.platform}
🎞️ Resolution: {project.metadata.resolution} @ {project.metadata.framerate}fps

[bold]Next Steps:[/bold]
1. Import more media: [cyan]sf import /path/to/media[/cyan]
2. Open in Resolve: [cyan]sf edit[/cyan]
3. Publish when ready: [cyan]sf publish --platform {project.metadata.platform}[/cyan]

💡 Tip: Use [cyan]sf status[/cyan] to check project details anytime
"""

    console.print(Panel(summary, title="Project Ready", border_style="green"))