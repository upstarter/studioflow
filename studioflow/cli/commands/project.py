"""Project Management Commands"""

import typer
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from typing import Optional, List, Dict
from pathlib import Path

from studioflow.core.project import ProjectManager
from studioflow.core.state import StateManager
from studioflow.core.config import get_config
from studioflow.core.archive import (
    analyze_project,
    display_analysis,
    cleanup_project,
    archive_project,
    get_destination_path,
    ARCHIVE_DESTINATIONS,
)


console = Console()
app = typer.Typer()


@app.command()
def create(
    name: str,
    template: str = "youtube",
    platform: str = "youtube"
):
    """Create a new project"""
    manager = ProjectManager()
    result = manager.create_project(name, template=template, platform=platform)

    if result.success:
        console.print(f"[green]✓[/green] Created project: {name}")

        # Set as current
        state = StateManager()
        state.current_project = name
    else:
        console.print(f"[red]Error:[/red] {result.error}")


@app.command()
def list(include_archived: bool = False):
    """List all projects"""
    manager = ProjectManager()
    projects = manager.list_projects(include_archived=include_archived)

    if not projects:
        console.print("No projects found. Create one with [bold]sf new[/bold]")
        return

    table = Table(title="Projects")
    table.add_column("Name", style="cyan")
    table.add_column("Modified")
    table.add_column("Template")
    table.add_column("Status")
    table.add_column("Size")

    for project in projects:
        table.add_row(
            project.name,
            project.metadata.modified_at.strftime("%Y-%m-%d"),
            project.metadata.template,
            project.metadata.status,
            project.metadata.human_size
        )

    console.print(table)


@app.command()
def select(name: str):
    """Select project as current"""
    manager = ProjectManager()
    project = manager.get_project(name)

    if project:
        state = StateManager()
        state.current_project = name
        console.print(f"[green]✓[/green] Selected project: {name}")
    else:
        console.print(f"[red]Project not found:[/red] {name}")


@app.command()
def archive(
    name: Optional[str] = typer.Argument(None, help="Project name or path"),
    destination: str = typer.Option(
        "deepfreeze",
        "--destination", "-d",
        help="Destination: deepfreeze, archive, archive_video, or custom path"
    ),
    project_type: str = typer.Option(
        "DOCS",
        "--type", "-t",
        help="Project type: DOCS, EPISODES, FILMS"
    ),
    analyze_only: bool = typer.Option(
        False,
        "--analyze", "-a",
        help="Only analyze, don't archive"
    ),
    no_cleanup: bool = typer.Option(
        False,
        "--no-cleanup",
        help="Skip cleanup (keep duplicates and cache)"
    ),
    delete_source: bool = typer.Option(
        False,
        "--delete-source",
        help="Delete local copy after successful archive"
    ),
    yes: bool = typer.Option(
        False,
        "--yes", "-y",
        help="Skip confirmation prompts"
    ),
):
    """
    Archive a project with best-practice cleanup.

    Removes duplicates, cache, and junk files before archiving.

    Examples:
        sf project archive DOC001_Mom
        sf project archive DOC001_Mom --destination deepfreeze
        sf project archive DOC001_Mom --analyze  # Just show what would be cleaned
        sf project archive /path/to/project --destination /custom/archive
        sf project archive DOC001_Mom --delete-source  # Remove local after archive
    """
    # Get project path
    if name and Path(name).exists():
        # Direct path provided
        project_path = Path(name)
    else:
        # Try to find project by name
        state = StateManager()
        name = name or state.current_project

        if not name:
            console.print("[red]No project specified[/red]")
            console.print("Usage: sf project archive <name> or sf project archive <path>")
            raise typer.Exit(1)

        manager = ProjectManager()
        project = manager.get_project(name)

        if project:
            project_path = project.path
        else:
            # Try common project locations
            from studioflow.core.config import get_config
            config = get_config()

            search_paths = [
                config.storage.active / name,
                config.storage.docs / name if hasattr(config.storage, 'docs') else None,
                config.storage.episodes / name if hasattr(config.storage, 'episodes') else None,
            ]
            # Add library paths if configured
            if config.storage.studio:
                search_paths.extend([
                    config.storage.studio / "PROJECTS" / "DOCS" / name,
                    config.storage.studio / "PROJECTS" / "EPISODES" / name,
                    config.storage.studio / "PROJECTS" / "FILMS" / name,
                ])

            project_path = None
            for path in search_paths:
                if path and path.exists():
                    project_path = path
                    break

            if not project_path:
                console.print(f"[red]Project not found:[/red] {name}")
                raise typer.Exit(1)

    console.print(f"\n[bold]Project:[/bold] {project_path}")

    # Step 1: Analyze
    analysis = analyze_project(project_path)
    display_analysis(analysis)

    if analyze_only:
        console.print("\n[dim]Use without --analyze to proceed with archive[/dim]")
        return

    # Step 2: Confirm
    if not yes:
        dest_path = get_destination_path(destination, project_type)
        console.print(f"\n[bold]Destination:[/bold] {dest_path / project_path.name}")

        if analysis.potential_savings > 0:
            console.print(f"[bold]Will remove:[/bold] {analysis.human_size(analysis.potential_savings)} of duplicates/cache")

        if delete_source:
            console.print("[yellow]Warning:[/yellow] Local copy will be deleted after archive")

        if not Confirm.ask("\nProceed with archive?"):
            console.print("Cancelled.")
            raise typer.Exit(0)

    # Step 3: Archive
    dest_path = get_destination_path(destination, project_type)

    success = archive_project(
        project_path=project_path,
        destination=dest_path,
        cleanup=not no_cleanup,
        verify=True,
        delete_source=delete_source
    )

    if success:
        console.print(f"\n[green]✓[/green] Archived to: {dest_path / project_path.name}")
    else:
        console.print("\n[red]Archive failed[/red]")
        raise typer.Exit(1)


@app.command()
def cleanup(
    name: Optional[str] = typer.Argument(None, help="Project name or path"),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-n",
        help="Show what would be removed without deleting"
    ),
    no_duplicates: bool = typer.Option(
        False,
        "--no-duplicates",
        help="Skip duplicate removal"
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Skip cache directory removal"
    ),
):
    """
    Clean up a project (remove duplicates, cache, junk).

    Use --dry-run to preview changes without deleting.

    Examples:
        sf project cleanup DOC001_Mom --dry-run
        sf project cleanup DOC001_Mom
        sf project cleanup /path/to/project
    """
    # Get project path (same logic as archive)
    if name and Path(name).exists():
        project_path = Path(name)
    else:
        state = StateManager()
        name = name or state.current_project

        if not name:
            console.print("[red]No project specified[/red]")
            raise typer.Exit(1)

        manager = ProjectManager()
        project = manager.get_project(name)

        if project:
            project_path = project.path
        else:
            console.print(f"[red]Project not found:[/red] {name}")
            raise typer.Exit(1)

    console.print(f"\n[bold]Project:[/bold] {project_path}")

    if dry_run:
        console.print("[yellow]DRY RUN - no files will be deleted[/yellow]\n")

    # Analyze first
    analysis = analyze_project(project_path)
    display_analysis(analysis)

    if analysis.potential_savings == 0:
        console.print("\n[green]Project is already clean![/green]")
        return

    # Cleanup
    stats = cleanup_project(
        project_path,
        remove_duplicates=not no_duplicates,
        remove_cache=not no_cache,
        remove_junk=True,
        dry_run=dry_run
    )

    if not dry_run:
        console.print(f"\n[green]Cleaned up {analysis.human_size(stats['bytes_removed'])}[/green]")


def _discover_projects(library_path: Optional[Path] = None) -> List[Dict]:
    """Discover all projects in library and config paths"""
    if library_path is None:
        from studioflow.core.config import get_config
        config = get_config()
        library_path = config.storage.studio or Path.home() / "Videos" / "StudioFlow" / "Studio"
    
    config = get_config()
    projects = []
    
    # Search paths
    search_paths = [
        library_path / "PROJECTS" / "DOCS" if library_path.exists() else None,
        library_path / "PROJECTS" / "EPISODES" if library_path.exists() else None,
        library_path / "PROJECTS" / "FILMS" if library_path.exists() else None,
        config.storage.active if hasattr(config.storage, 'active') else None,
        config.storage.docs if hasattr(config.storage, 'docs') else None,
        config.storage.episodes if hasattr(config.storage, 'episodes') else None,
    ]
    
    # Find all project directories
    for base_path in search_paths:
        if not base_path or not base_path.exists():
            continue
            
        # Scan for project directories
        for item in base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it looks like a project (has certain files/folders)
                project_files = [
                    item / "01_MEDIA",
                    item / "03_resolve",
                    item / "03_RESOLVE",
                    item / "PROJECT",
                    item / ".studioflow",
                ]
                
                has_project_structure = any(f.exists() for f in project_files)
                
                # Check for Resolve project file
                drp_files = list(item.rglob("*.drp"))
                
                if has_project_structure or drp_files:
                    # Get project metadata
                    try:
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                        
                        # Determine project type
                        if "DOCS" in str(base_path) or "DOC" in item.name.upper():
                            ptype = "doc"
                        elif "EPISODES" in str(base_path) or "EP" in item.name.upper():
                            ptype = "episode"
                        elif "FILMS" in str(base_path) or "FILM" in item.name.upper():
                            ptype = "film"
                        else:
                            ptype = "unknown"
                        
                        projects.append({
                            "name": item.name,
                            "path": item,
                            "type": ptype,
                            "modified": mtime,
                            "size_mb": size / (1024**2),
                            "has_resolve": len(drp_files) > 0,
                            "resolve_files": len(drp_files),
                            "location": str(base_path.relative_to(base_path.parent)) if base_path.parent else str(base_path),
                        })
                    except (OSError, PermissionError):
                        continue
    
    # Sort by modified date (most recent first)
    projects.sort(key=lambda x: x["modified"], reverse=True)
    return projects


@app.command()
def discover(
    library_path: Optional[Path] = typer.Option(None, "--library", "-l", help="Library path to search"),
    type_filter: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type: doc/episode/film"),
    show_paths: bool = typer.Option(False, "--paths", help="Show full paths"),
):
    """Auto-discover all projects in library and configured paths"""
    
    console.print("[bold cyan]Discovering projects...[/bold cyan]\n")
    
    projects = _discover_projects(library_path)
    
    if type_filter:
        projects = [p for p in projects if p["type"] == type_filter.lower()]
    
    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        console.print("\nTry:")
        console.print("  - Creating a project: [cyan]sf project create MyProject[/cyan]")
        console.print("  - Checking library: [cyan]sf library status[/cyan]")
        return
    
    # Display table
    table = Table(title=f"Found {len(projects)} Project(s)")
    table.add_column("Name", style="cyan", width=30)
    table.add_column("Type", style="yellow", width=10)
    table.add_column("Modified", style="white", width=15)
    table.add_column("Size", style="green", width=10)
    table.add_column("Resolve", style="magenta", width=8)
    
    if show_paths:
        table.add_column("Path", style="dim", width=40)
    
    for proj in projects[:50]:  # Limit to 50 for display
        modified_str = proj["modified"].strftime("%Y-%m-%d")
        size_str = f"{proj['size_mb']:.1f} MB" if proj['size_mb'] < 1024 else f"{proj['size_mb']/1024:.1f} GB"
        resolve_str = "✓" if proj["has_resolve"] else "-"
        
        row = [
            proj["name"],
            proj["type"].upper(),
            modified_str,
            size_str,
            resolve_str,
        ]
        
        if show_paths:
            row.append(str(proj["path"]))
        
        table.add_row(*row)
    
    console.print(table)
    
    if len(projects) > 50:
        console.print(f"\n[dim]Showing 50 of {len(projects)} projects. Use filters to narrow results.[/dim]")


@app.command()
def open(
    name: Optional[str] = typer.Argument(None, help="Project name (optional, will prompt if not provided)"),
    library_path: Optional[Path] = typer.Option(None, "--library", "-l", help="Library path"),
):
    """Interactive project picker to open/select a project"""
    
    projects = _discover_projects(library_path)
    
    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        raise typer.Exit(1)
    
    if name:
        # Find exact match
        matches = [p for p in projects if p["name"].lower() == name.lower()]
        if not matches:
            # Try partial match
            matches = [p for p in projects if name.lower() in p["name"].lower()]
        
        if not matches:
            console.print(f"[red]Project not found: {name}[/red]")
            console.print("\n[bold]Available projects:[/bold]")
            for p in projects[:10]:
                console.print(f"  - {p['name']}")
            raise typer.Exit(1)
        
        selected = matches[0]
    else:
        # Interactive selection
        console.print(f"\n[bold]Select a project:[/bold] (showing last {min(20, len(projects))})\n")
        
        # Display options
        for i, proj in enumerate(projects[:20], 1):
            resolve_indicator = "✓" if proj["has_resolve"] else " "
            modified = proj["modified"].strftime("%Y-%m-%d")
            console.print(f"  {i:2d}. [{resolve_indicator}] {proj['name']:30s} ({proj['type']:8s}) {modified}")
        
        try:
            choice = Prompt.ask("\nEnter number or project name", default="1")
            
            # Try number first
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(projects[:20]):
                    selected = projects[idx]
                else:
                    console.print("[red]Invalid selection[/red]")
                    raise typer.Exit(1)
            else:
                # Try name match
                matches = [p for p in projects if choice.lower() in p["name"].lower()]
                if not matches:
                    console.print(f"[red]Project not found: {choice}[/red]")
                    raise typer.Exit(1)
                selected = matches[0]
        except KeyboardInterrupt:
            raise typer.Exit(0)
    
    # Set as current project
    state = StateManager()
    state.current_project = selected["name"]
    
    console.print(Panel(
        f"[green]✓[/green] Selected project: [bold]{selected['name']}[/bold]\n\n"
        f"Path: {selected['path']}\n"
        f"Type: {selected['type'].upper()}\n"
        f"Modified: {selected['modified'].strftime('%Y-%m-%d %H:%M')}\n"
        f"Size: {selected['size_mb']:.1f} MB\n"
        f"Resolve: {'✓' if selected['has_resolve'] else '✗'}",
        title="Project Selected",
        border_style="green"
    ))
    
    # Suggest next actions
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  - Open in Resolve: [cyan]sf resolve sync[/cyan]")
    console.print(f"  - View status: [cyan]sf project status[/cyan]")
    console.print(f"  - Open folder: [cyan]cd {selected['path']}[/cyan]")


@app.command()
def recent(
    count: int = typer.Option(10, "--count", "-n", help="Number of recent projects to show"),
):
    """Show recently modified projects"""
    
    projects = _discover_projects()
    recent_projects = projects[:count]
    
    if not recent_projects:
        console.print("[yellow]No projects found[/yellow]")
        return
    
    table = Table(title=f"Recent {len(recent_projects)} Projects")
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="cyan", width=30)
    table.add_column("Type", style="yellow", width=10)
    table.add_column("Modified", style="white", width=20)
    table.add_column("Size", style="green", width=12)
    table.add_column("Actions", style="dim", width=20)
    
    state = StateManager()
    current = state.current_project
    
    for i, proj in enumerate(recent_projects, 1):
        modified = proj["modified"].strftime("%Y-%m-%d %H:%M")
        size_str = f"{proj['size_mb']:.1f} MB" if proj['size_mb'] < 1024 else f"{proj['size_mb']/1024:.1f} GB"
        
        is_current = "← current" if proj["name"] == current else ""
        
        table.add_row(
            str(i),
            proj["name"],
            proj["type"].upper(),
            modified,
            size_str,
            is_current,
        )
    
    console.print(table)
    
    console.print(f"\n[dim]Open project: [cyan]sf project open <name>[/cyan][/dim]")
    console.print(f"[dim]Select current: [cyan]sf project open[/cyan][/dim]")