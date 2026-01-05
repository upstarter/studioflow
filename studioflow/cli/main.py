#!/usr/bin/env python3
"""
StudioFlow CLI - Main Entry Point
Modern Git-style CLI for video production workflows
"""

from typing import Optional, Annotated
from pathlib import Path
import sys
import os

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel
from rich.prompt import Confirm

from studioflow import __version__
from studioflow.cli.commands import simple
from studioflow.cli.commands import professional
from studioflow.cli.commands import user
from studioflow.cli.commands import resolve_magic
from studioflow.cli.commands import project
from studioflow.cli.commands import library
from studioflow.cli.commands import auto_edit
from studioflow.cli.commands import workflow
from studioflow.cli.commands import dashboard
from studioflow.cli.commands import batch_ops
from studioflow.cli.commands import quick_actions
from studioflow.cli.commands import export as export_cmd
from studioflow.cli.commands import media_org
from studioflow.cli.commands import power_bins
from studioflow.cli.commands import rough_cut_cmd
from studioflow.cli.commands import normalize
from studioflow.cli.commands import background
from studioflow.cli.setup_wizard import run_setup
from studioflow.cli.workflows import new_video
from studioflow.core.config import Config, ConfigManager
from studioflow.core.state import StateManager

# Initialize Rich console for beautiful output
console = Console()

# Create main Typer app
app = typer.Typer(
    name="sf",
    help="StudioFlow - Automated Video Production Pipeline",
    no_args_is_help=False,  # We'll handle help display ourselves
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,  # We'll handle our own errors
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Add simplified commands directly to main app
for command in [
    simple.new, simple.import_media, simple.cut, simple.concat,
    simple.export, simple.effect, simple.audio, simple.thumbnail,
    simple.transcribe, simple.upload, simple.info,
    simple.episode, simple.doc, simple.film
]:
    app.command()(command)

# Add professional commands
for command in [
    professional.resolve_check, professional.resolve_timeline, professional.resolve_proxy,
    professional.resolve_multicam, professional.resolve_grade,
    professional.node_pipeline, professional.node_composite,
    professional.workflow_create, professional.workflow_run, professional.workflow_watch,
    professional.workflow_list, professional.workflow_status,
    professional.preset
]:
    app.command()(command)

# Add user-focused commands
for command in [
    user.status, user.check, user.fix, user.preview,
    user.snapshot, user.undo, user.quick, user.typical,
    user.recent, user.estimate, user.batch
]:
    app.command()(command)

# Note: Eric's commands have been moved:
# - check_lufs, fix_lufs -> normalize.check_lufs, normalize.fix_lufs
# - sanitize_names -> user_utils.sanitize_filename (utility function)
# - Other commands archived to archive/user-specific/eric_commands.py

# Add Resolve Magic commands
for command in [
    resolve_magic.magic, resolve_magic.auto_project,
    resolve_magic.smart_bins, resolve_magic.analyze
]:
    app.command()(command)

# Add smart rough-cut command (replaces old rough_cut with transcript-aware version)
app.command(name="rough-cut")(rough_cut_cmd.rough_cut)

# Add project subcommand group (create, list, select, archive, cleanup)
app.add_typer(project.app, name="project", help="Project management commands")

# Add library workspace subcommand group
app.add_typer(library.app, name="library", help="Library workspace management")

# Add auto-editing subcommand group (intelligent automation for YouTube episodes)
app.add_typer(auto_edit.app, name="auto-edit", help="Auto-editing: smart bins, chapters, timeline automation")

# Add complete workflow subcommand group
app.add_typer(workflow.app, name="workflow", help="Complete workflows: episode, import, publish")

# Add dashboard subcommand group
app.add_typer(dashboard.app, name="dashboard", help="Project health dashboard and status")

# Add batch operations subcommand group
app.add_typer(batch_ops.app, name="batch", help="Batch processing: transcribe, trim, thumbnails")

# Add quick actions command
app.command()(quick_actions.menu)

# Add export commands
app.add_typer(export_cmd.app, name="export", help="Export with validation")

# Add media organization commands
app.add_typer(media_org.app, name="media-org", help="Smart media organization and search")

# Add power bins commands
app.add_typer(power_bins.app, name="power-bins", help="Manage Power Bins structure and sync")

# Add normalization commands
app.add_typer(normalize.app, name="normalize", help="Normalize footage: audio to -14 LUFS, PCM codec, clean filenames")

# Add background services commands
app.add_typer(background.app, name="background", help="Background services: auto-transcription, auto-rough-cut")

# State manager for tracking context
state = StateManager()


@app.command()
def new(
    name: Annotated[str, typer.Argument(help="Project name")],
    template: Annotated[Optional[str], typer.Option("-t", "--template", help="Project template")] = "youtube",
    import_path: Annotated[Optional[Path], typer.Option("-i", "--import", help="Import media from path")] = None,
    platform: Annotated[Optional[str], typer.Option("-p", "--platform", help="Target platform")] = "youtube",
    interactive: Annotated[bool, typer.Option("-I", "--interactive", help="Interactive mode")] = False,
):
    """
    Create a new video project with full workflow automation.

    This is the primary workflow command that handles everything:
    - Creates project structure
    - Imports media (if provided)
    - Sets up Resolve project
    - Configures platform optimization

    Examples:
        sf new "My Tutorial"
        sf new "Product Review" --import /media/sdcard
        sf new "Vlog Episode 5" --template vlog --platform instagram
    """
    with console.status(f"Creating project [bold cyan]{name}[/bold cyan]..."):
        result = new_video.create_workflow(
            name=name,
            template=template,
            import_path=import_path,
            platform=platform,
            interactive=interactive,
        )

    if result.success:
        console.print(Panel.fit(
            f"✅ Project [bold green]{name}[/bold green] created successfully!\n\n"
            f"📁 Location: {result.project_path}\n"
            f"🎬 Next: Open DaVinci Resolve or run [bold]sf edit[/bold]",
            title="Project Ready",
            border_style="green"
        ))
    else:
        console.print(f"[bold red]Error:[/bold red] {result.error}")
        raise typer.Exit(1)


@app.command("import")
def import_media(
    path: Annotated[Path, typer.Argument(help="Path to media source")],
    project_name: Annotated[Optional[str], typer.Option("-p", "--project", help="Target project")] = None,
    organize: Annotated[bool, typer.Option("-o", "--organize", help="Auto-organize by type")] = True,
):
    """
    Import media from SD card, folder, or device.

    Smart import that:
    - Detects media type (A-roll, B-roll, etc)
    - Organizes by date/type
    - Checks for duplicates
    - Shows progress with speed
    """
    from studioflow.core.project import ProjectManager
    from studioflow.core.media import MediaScanner, MediaImporter

    project_name = project_name or state.current_project
    if not project_name:
        console.print("[red]No project selected. Use --project or 'sf project select'[/red]")
        raise typer.Exit(1)

    # Check path exists
    if not path.exists():
        console.print(f"[red]Path does not exist: {path}[/red]")
        raise typer.Exit(1)

    # Get project
    manager = ProjectManager()
    proj = manager.get_project(project_name)
    if not proj:
        console.print(f"[red]Project not found: {project_name}[/red]")
        raise typer.Exit(1)

    # Scan for media
    with console.status("Scanning for media files..."):
        scanner = MediaScanner()
        files = scanner.scan(path)

    if not files:
        console.print(f"No media files found in {path}")
        return

    # Show what we found
    console.print(f"Found [cyan]{len(files)}[/cyan] media files:")
    by_type = {}
    total_size = 0
    for f in files:
        by_type[f.type.value] = by_type.get(f.type.value, 0) + 1
        total_size += f.size

    for media_type, count in by_type.items():
        console.print(f"  {media_type}: {count} files")

    # Convert size to human readable
    size_gb = total_size / (1024**3)
    console.print(f"  Total size: {size_gb:.2f} GB")

    # Import with progress
    console.print(f"\nImporting to [cyan]{project_name}[/cyan]...")

    importer = MediaImporter(proj)
    stats = importer.import_from_path(path, organize=organize)

    # Show results
    console.print(f"\n[green]✓ Import complete![/green]")
    console.print(f"  Files imported: {stats['total_files']}")
    console.print(f"  Files skipped (duplicates): {stats['skipped']}")

    if stats.get('by_category'):
        console.print("\n  Organized by category:")
        for cat, count in stats['by_category'].items():
            console.print(f"    {cat}: {count}")

    # Update and save project metadata
    proj.metadata.media_count += stats['total_files']
    proj.metadata.total_size_bytes += stats['total_size']
    proj.save_metadata()

    console.print(f"\nRun [cyan]sf status[/cyan] to see project details")


@app.command()
def edit(
    project: Annotated[Optional[str], typer.Option("-p", "--project", help="Project to edit")] = None,
):
    """Open project in DaVinci Resolve."""
    project_name = project or state.current_project
    if not project_name:
        console.print("[red]No project selected[/red]")
        raise typer.Exit(1)

    # Just run resolve sync - it will handle everything
    console.print(f"Syncing [cyan]{project_name}[/cyan] with DaVinci Resolve...")
    from studioflow.cli.commands.resolve import sync as resolve_sync
    resolve_sync(project_name)


# Note: publish is now a subcommand group, not a single command
# Use: sf publish youtube, sf publish instagram, etc.


@app.command()
def status():
    """Show current project status and statistics."""
    if not state.current_project:
        console.print("No active project. Use [bold]sf new[/bold] or [bold]sf project select[/bold]")
        return

    # Create status table
    table = Table(title=f"Project: {state.current_project}", show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    from studioflow.core.project import ProjectManager
    manager = ProjectManager()
    proj = manager.get_project(state.current_project)

    if proj:
        table.add_row("Location", str(proj.path))
        table.add_row("Created", proj.metadata.created_at.strftime("%Y-%m-%d %H:%M"))
        table.add_row("Media Files", str(proj.metadata.media_count))
        table.add_row("Total Size", proj.metadata.human_size)
        table.add_row("Template", proj.metadata.template)
        table.add_row("Platform", str(proj.metadata.platform))

        console.print(table)
    else:
        console.print(f"[red]Project not found: {state.current_project}[/red]")


@app.command()
def config(
    set_: Annotated[Optional[str], typer.Option("--set", help="Set config value (key=value)")] = None,
    get: Annotated[Optional[str], typer.Option("--get", help="Get config value")] = None,
    list_: Annotated[bool, typer.Option("--list", help="List all config")] = False,
    edit: Annotated[bool, typer.Option("--edit", help="Edit config file")] = False,
):
    """Manage StudioFlow configuration."""
    cfg = ConfigManager()

    if set_:
        key, value = set_.split("=", 1)
        cfg.set(key, value)
        console.print(f"[green]✓[/green] Set {key} = {value}")

    elif get:
        value = cfg.get(get)
        console.print(f"{get} = {value}")

    elif list_:
        table = Table(title="Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        for key, value in cfg.all().items():
            table.add_row(key, str(value))

        console.print(table)

    elif edit:
        import subprocess
        import os
        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, cfg.config_file])


@app.command()
def setup():
    """Run interactive setup wizard"""
    run_setup()


@app.command()
def quickstart(
    workflow: Optional[str] = typer.Option(None, "--workflow", "-w", help="Workflow type")
):
    """
    Interactive quick start guide

    Examples:
        sf quickstart                    # Interactive workflow selection
        sf quickstart --workflow youtube  # YouTube workflow guide
        sf quickstart --workflow podcast  # Podcast workflow guide
    """
    from studioflow.cli.quickstart import run_quickstart
    run_quickstart(workflow)


@app.command()
def version():
    """Show version information."""
    console.print(f"StudioFlow v{__version__}")


@app.command()
def completion(
    shell: Annotated[str, typer.Argument(help="Shell type (bash, zsh, fish)")] = "bash",
    install: Annotated[bool, typer.Option("--install", help="Install completions")] = False
):
    """
    Generate or install shell completions.
    """
    from typer.completion import get_completion

    completion_script = get_completion(shell=shell)

    if install:
        # Determine where to install
        if shell == "bash":
            completion_dir = Path.home() / ".local/share/bash-completion/completions"
        elif shell == "zsh":
            completion_dir = Path.home() / ".zfunc"
        elif shell == "fish":
            completion_dir = Path.home() / ".config/fish/completions"
        else:
            console.print(f"[red]Unsupported shell: {shell}[/red]")
            return

        completion_dir.mkdir(parents=True, exist_ok=True)
        completion_file = completion_dir / "sf"
        if shell == "fish":
            completion_file = completion_file.with_suffix(".fish")

        completion_file.write_text(completion_script)
        console.print(f"[green]✓[/green] Installed {shell} completions to {completion_file}")
        console.print(f"\nRestart your shell or run: source ~/.{shell}rc")
    else:
        # Just print the completion script
        console.print(completion_script)


@app.command()
def commands(
    category: Optional[str] = typer.Argument(None, help="Show commands by category (essential, media, resolve, advanced)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive command browser"),
):
    """Browse available commands by category."""
    if interactive:
        _interactive_command_browser()
        return
    
    categories = {
        "essential": {
            "description": "Most commonly used commands",
            "commands": [
                ("new", "Create a new video project"),
                ("import", "Import media from SD card or folder"),
                ("edit", "Open project in DaVinci Resolve"),
                ("status", "Show current project status"),
                ("transcribe", "Transcribe video/audio"),
                ("publish", "Publish video to platform"),
            ]
        },
        "media": {
            "description": "Media operations and processing",
            "commands": [
                ("import", "Import media files"),
                ("transcribe", "Transcribe audio/video"),
                ("cut", "Cut segments from video"),
                ("concat", "Concatenate videos"),
                ("export", "Export with validation"),
                ("media scan", "Scan for media files"),
                ("media organize", "Organize media files"),
            ]
        },
        "resolve": {
            "description": "DaVinci Resolve integration",
            "commands": [
                ("resolve sync", "Sync project with Resolve"),
                ("resolve start", "Start DaVinci Resolve"),
                ("resolve status", "Check Resolve status"),
                ("resolve export", "Export from Resolve"),
                ("resolve-magic", "Auto-create Resolve project"),
            ]
        },
        "advanced": {
            "description": "Advanced and professional features",
            "commands": [
                ("resolve-timeline", "Create timeline from clips"),
                ("resolve-proxy", "Generate proxy media"),
                ("node-pipeline", "Create effects pipeline"),
                ("workflow-create", "Create custom workflow"),
                ("workflow-run", "Run workflow"),
            ]
        }
    }
    
    if category:
        if category not in categories:
            console.print(f"[red]Unknown category: {category}[/red]")
            console.print(f"Available: {', '.join(categories.keys())}")
            return
        
        cat = categories[category]
        console.print(f"\n[bold cyan]{category.upper()}[/bold cyan] - {cat['description']}\n")
        for cmd, desc in cat["commands"]:
            console.print(f"  [cyan]{cmd:25}[/cyan] {desc}")
    else:
        console.print("[bold]Available command categories:[/bold]\n")
        for cat_name, cat_info in categories.items():
            console.print(f"  [cyan]{cat_name:15}[/cyan] {cat_info['description']}")
        console.print("\n[dim]Use: sf commands <category> to see commands in that category[/dim]")
        console.print("[dim]Use: sf commands --interactive for interactive browser[/dim]")


def _interactive_command_browser():
    """Interactive command browser"""
    from rich.prompt import Prompt
    from rich.table import Table
    
    categories = {
        "1": ("Essential Commands", [
            ("new", "Create a new video project"),
            ("import", "Import media from SD card or folder"),
            ("edit", "Open project in DaVinci Resolve"),
            ("status", "Show current project status"),
            ("transcribe", "Transcribe video/audio"),
            ("publish", "Publish video to platform"),
        ]),
        "2": ("Media Operations", [
            ("import", "Import media files"),
            ("transcribe", "Transcribe audio/video"),
            ("cut", "Cut segments from video"),
            ("concat", "Concatenate videos"),
            ("export", "Export with validation"),
        ]),
        "3": ("Resolve Integration", [
            ("resolve sync", "Sync project with Resolve"),
            ("resolve start", "Start DaVinci Resolve"),
            ("resolve-magic", "Auto-create Resolve project"),
        ]),
        "4": ("Advanced Features", [
            ("resolve-timeline", "Create timeline from clips"),
            ("workflow-create", "Create custom workflow"),
            ("node-pipeline", "Create effects pipeline"),
        ]),
    }
    
    while True:
        console.print("\n[bold cyan]Command Browser[/bold cyan]\n")
        for key, (name, _) in categories.items():
            console.print(f"  {key}. {name}")
        console.print("  0. Exit")
        
        choice = Prompt.ask("\nSelect category", choices=["0", "1", "2", "3", "4"], default="0")
        
        if choice == "0":
            break
        
        name, commands = categories[choice]
        table = Table(title=name, show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan", width=25)
        table.add_column("Description", style="white")
        
        for cmd, desc in commands:
            table.add_row(cmd, desc)
        
        console.print()
        console.print(table)
        console.print("\n[dim]Run: sf <command> --help for detailed help[/dim]")


@app.command()
def help(command: Optional[str] = typer.Argument(None, help="Command to get help for")):
    """Show help for commands."""
    from rich.markdown import Markdown

    if not command:
        # Show main help
        console.print("[bold cyan]StudioFlow - Automated Video Production Pipeline[/bold cyan]\n")
        console.print("[bold]Usage:[/bold] sf [COMMAND] [OPTIONS]\n")

        # Main commands
        console.print("[bold yellow]Main Commands:[/bold yellow]")
        commands = [
            ("new", "Create a new video project"),
            ("import", "Import media from SD card or folder"),
            ("edit", "Open project in DaVinci Resolve"),
            ("publish", "Publish video to platform"),
            ("status", "Show current project status"),
            ("help", "Show help for commands"),
        ]
        for cmd, desc in commands:
            console.print(f"  [cyan]{cmd:12}[/cyan] {desc}")

        console.print("\n[bold yellow]Management Commands:[/bold yellow]")
        subcommands = [
            ("project", "Project management (create, list, select)"),
            ("media", "Media operations (scan, organize)"),
            ("resolve", "DaVinci Resolve (sync, start, status)"),
            ("youtube", "YouTube tools (optimize, upload)"),
            ("publish", "Export and publish to platforms"),
            ("thumbnail", "Generate thumbnails with templates"),
            ("multicam", "Multi-camera synchronization"),
            ("config", "Configuration management"),
        ]
        for cmd, desc in subcommands:
            console.print(f"  [cyan]{cmd:12}[/cyan] {desc}")

        console.print("\n[bold]Examples:[/bold]")
        console.print("  sf new \"My Video\"              # Create new project")
        console.print("  sf import /media/sdcard        # Import media")
        console.print("  sf resolve sync                # Sync with Resolve")
        console.print("  sf help new                    # Get help for 'new' command")

        console.print("\nFor help on a specific command: [bold]sf help [cyan]<command>[/cyan][/bold]")
        return

    # Command-specific help
    help_text = {
        "thumbnail": {
            "usage": "sf thumbnail <subcommand>",
            "desc": "Generate YouTube thumbnails with templates",
            "subcommands": [
                ("generate", "Create a single thumbnail"),
                ("batch", "Generate multiple templates"),
                ("templates", "List available templates"),
                ("preview", "Show project thumbnails"),
            ],
            "examples": [
                'sf thumbnail generate --text "MY VIDEO" --template viral',
                'sf thumbnail batch --templates "viral,modern,tutorial"',
                "sf thumbnail templates",
            ]
        },
        "multicam": {
            "usage": "sf multicam <subcommand>",
            "desc": "Synchronize multiple camera angles",
            "subcommands": [
                ("sync", "Sync cameras by audio or timecode"),
                ("create-sequence", "Create multicam sequence"),
                ("analyze", "Check sync compatibility"),
            ],
            "examples": [
                "sf multicam sync --method audio",
                "sf multicam create-sequence --layout side_by_side",
                "sf multicam analyze",
            ]
        },
        "publish": {
            "usage": "sf publish <platform>",
            "desc": "Export video for different platforms",
            "subcommands": [
                ("youtube", "Optimize for YouTube"),
                ("instagram", "Optimize for Instagram"),
                ("tiktok", "Optimize for TikTok"),
                ("all", "Export for all platforms"),
            ],
            "examples": [
                "sf publish youtube --title \"My Video\"",
                "sf publish instagram --post-type reels",
                "sf publish all",
            ]
        },
        "new": {
            "usage": "sf new <name> [OPTIONS]",
            "desc": "Create a new video project with complete workflow automation",
            "options": [
                ("-t, --template", "Project template (youtube, vlog, tutorial, shorts, multicam)"),
                ("-i, --import", "Import media from path after creation"),
                ("-p, --platform", "Target platform (youtube, instagram, tiktok)"),
                ("-I, --interactive", "Interactive mode with prompts"),
            ],
            "examples": [
                'sf new "My Tutorial"',
                'sf new "Product Review" --template youtube --import /media/sdcard',
                'sf new "Vlog Episode 5" -t vlog -p instagram',
            ]
        },
        "import": {
            "usage": "sf import <path> [OPTIONS]",
            "desc": "Import media from SD card, folder, or device with smart organization",
            "options": [
                ("-p, --project", "Target project (default: current)"),
                ("-o, --organize", "Auto-organize by type (default: true)"),
            ],
            "examples": [
                "sf import /media/sdcard",
                "sf import ~/Downloads/footage --project \"My Video\"",
                "sf import /path/to/camera --no-organize",
            ]
        },
        "status": {
            "usage": "sf status",
            "desc": "Show current project status with media statistics and settings",
            "options": [],
            "examples": [
                "sf status",
            ]
        },
        "edit": {
            "usage": "sf edit [OPTIONS]",
            "desc": "Open project in DaVinci Resolve (creates project if needed)",
            "options": [
                ("-p, --project", "Project to edit (default: current)"),
            ],
            "examples": [
                "sf edit",
                "sf edit --project \"My Video\"",
            ]
        },
        "project": {
            "usage": "sf project <subcommand>",
            "desc": "Project management commands",
            "subcommands": [
                ("create", "Create a new project"),
                ("list", "List all projects"),
                ("select", "Select project as current"),
                ("archive", "Archive a project"),
            ],
            "examples": [
                "sf project list",
                "sf project select \"My Video\"",
                "sf project archive \"Old Project\"",
            ]
        },
        "resolve": {
            "usage": "sf resolve <subcommand>",
            "desc": "DaVinci Resolve integration commands",
            "subcommands": [
                ("sync", "Sync project with Resolve"),
                ("start", "Start DaVinci Resolve"),
                ("status", "Check Resolve status"),
            ],
            "examples": [
                "sf resolve sync",
                "sf resolve start",
                "sf resolve status",
            ]
        },
        "config": {
            "usage": "sf config [OPTIONS]",
            "desc": "Manage StudioFlow configuration",
            "options": [
                ("--set", "Set config value (key=value)"),
                ("--get", "Get config value"),
                ("--list", "List all configuration"),
                ("--edit", "Edit config file in editor"),
            ],
            "examples": [
                "sf config --list",
                "sf config --set storage.active=/my/projects",
                "sf config --get resolve.install_path",
                "sf config --edit",
            ]
        },
    }

    if command not in help_text:
        console.print(f"[red]No help available for command: {command}[/red]")
        console.print(f"\nAvailable commands: {', '.join(help_text.keys())}")
        return

    info = help_text[command]

    # Display help
    console.print(f"[bold cyan]{command.upper()}[/bold cyan]\n")
    console.print(f"[bold]Description:[/bold] {info['desc']}\n")
    console.print(f"[bold]Usage:[/bold] {info['usage']}\n")

    if info.get('options'):
        console.print("[bold]Options:[/bold]")
        for opt, desc in info['options']:
            console.print(f"  [green]{opt:20}[/green] {desc}")
        console.print()

    if info.get('subcommands'):
        console.print("[bold]Subcommands:[/bold]")
        for cmd, desc in info['subcommands']:
            console.print(f"  [cyan]{cmd:12}[/cyan] {desc}")
        console.print()

    if info.get('examples'):
        console.print("[bold]Examples:[/bold]")
        for example in info['examples']:
            console.print(f"  {example}")
        console.print()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version", "-v", help="Show version")] = False,
    all: Annotated[bool, typer.Option("--all", "-a", help="Show all commands (including advanced)")] = False,
):
    """
    StudioFlow - Automated Video Production Pipeline

    A modern CLI for content creators that automates the entire
    video production workflow from import to upload.

    🚀 First time? Run: sf setup

    Quick Start:
        sf new "My Video" --import /media/sdcard
        sf edit
        sf publish --platform youtube

    For help on any command:
        sf COMMAND --help
    """
    if version:
        console.print(f"StudioFlow v{__version__}")
        raise typer.Exit()

    # Show help if no command provided
    # ctx.invoked_subcommand will be None when no subcommand is invoked
    if ctx.invoked_subcommand is None:
        # Check if user wants to see all commands
        if all:
            # Show full help with all commands
            console.print(ctx.get_help())
        else:
            # Default: show simplified help with only essential commands
            _show_simplified_help()
        
        raise typer.Exit()  # Exit after showing help


def _show_simplified_help():
    """Show simplified help with only essential commands"""
    from rich.panel import Panel
    from rich.columns import Columns
    
    console.print(Panel.fit(
        "[bold cyan]StudioFlow[/bold cyan] - Automated Video Production Pipeline\n\n"
        "[dim]Showing essential commands. Use [bold]sf --all[/bold] to see all commands.[/dim]",
        title="Quick Help",
        border_style="cyan"
    ))
    
    console.print("\n[bold yellow]📋 Essential Commands:[/bold yellow]\n")
    
    essential = [
        ("[cyan]new[/cyan] \"Name\"", "Create a new video project"),
        ("[cyan]import[/cyan] <path>", "Import media from SD card or folder"),
        ("[cyan]edit[/cyan]", "Open project in DaVinci Resolve"),
        ("[cyan]status[/cyan]", "Show current project status"),
        ("[cyan]transcribe[/cyan] <file>", "Transcribe video/audio"),
        ("[cyan]publish[/cyan] <platform>", "Publish video to platform"),
    ]
    
    for cmd, desc in essential:
        console.print(f"  {cmd:30} {desc}")
    
    console.print("\n[bold yellow]🔧 Common Subcommands:[/bold yellow]\n")
    
    subcommands = [
        ("[cyan]project[/cyan]", "Project management (list, select, archive)"),
        ("[cyan]media[/cyan]", "Media operations (scan, organize)"),
        ("[cyan]resolve[/cyan]", "DaVinci Resolve integration"),
        ("[cyan]youtube[/cyan]", "YouTube tools (titles, optimize, upload)"),
        ("[cyan]auto-edit[/cyan]", "Auto-editing (smart bins, chapters)"),
    ]
    
    for cmd, desc in subcommands:
        console.print(f"  {cmd:30} {desc}")
    
    console.print("\n[bold yellow]🚀 Getting Started:[/bold yellow]\n")
    
    getting_started = [
        ("[cyan]setup[/cyan]", "Run interactive setup wizard"),
        ("[cyan]quickstart[/cyan]", "Interactive quick start guide"),
        ("[cyan]menu[/cyan]", "Quick actions menu"),
        ("[cyan]help[/cyan] <command>", "Get help for a specific command"),
    ]
    
    for cmd, desc in getting_started:
        console.print(f"  {cmd:30} {desc}")
    
    console.print("\n[dim]💡 Tip: Run [bold]sf --all[/bold] to see all available commands[/dim]")
    console.print("[dim]💡 Tip: Run [bold]sf help <command>[/bold] for detailed help[/dim]\n")


def run():
    """Entry point for the CLI."""
    # Check if this is first run
    config_file = Path.home() / ".config" / "studioflow" / "config.yaml"

    if not config_file.exists() and len(sys.argv) > 1:
        # First run detected, but user is trying to run a command
        if sys.argv[1] not in ["setup", "--help", "-h", "--version", "--all", "-a"]:
            console.print("\n[yellow]⚠ First-time setup required![/yellow]")
            console.print("StudioFlow needs to be configured before use.\n")

            if Confirm.ask("Run setup wizard now?", default=True):
                run_setup()
                console.print("\n[green]Setup complete! Now running your command...\n[/green]")
            else:
                console.print("\n[dim]Run 'sf setup' when you're ready to configure StudioFlow[/dim]")
                sys.exit(0)

    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    run()