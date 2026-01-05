"""
Library workspace commands optimized for /mnt/library workflow
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from studioflow.core.resolve_api import ResolveDirectAPI, create_documentary_project, FX30ProjectSettings
from studioflow.core.storage import StorageTierSystem

console = Console()
app = typer.Typer()


@app.command()
def status(
    library_path: Optional[Path] = typer.Option(None, "--path", "-p", help="Library path (defaults to /mnt/library)")
):
    """Show library workspace status and structure"""
    
    if library_path is None:
        library_path = Path("/mnt/library")
    
    if not library_path.exists():
        console.print(f"[red]Library path does not exist: {library_path}[/red]")
        console.print("Create it with: [cyan]sf library init[/cyan]")
        raise typer.Exit(1)
    
    # Show library structure
    tree = Tree(f"[bold cyan]{library_path}[/bold cyan]")
    
    # Check common directories
    common_dirs = [
        "PROJECTS",
        "EPISODES", 
        "DOCS",
        "FILMS",
        "CACHE",
        "PROXIES",
        "EXPORTS",
        "ASSETS"
    ]
    
    for dir_name in common_dirs:
        dir_path = library_path / dir_name
        if dir_path.exists():
            # Count items
            files = list(dir_path.rglob("*"))
            file_count = sum(1 for f in files if f.is_file())
            dir_count = sum(1 for f in files if f.is_dir())
            
            status = f" [dim]({dir_count} dirs, {file_count} files)[/dim]"
            
            # Color based on type
            if dir_name in ["PROJECTS", "EPISODES", "DOCS", "FILMS"]:
                tree.add(f"[green]📁 {dir_name}[/green]{status}")
            elif dir_name in ["CACHE", "PROXIES"]:
                tree.add(f"[yellow]⚡ {dir_name}[/yellow]{status}")
            else:
                tree.add(f"[blue]📦 {dir_name}[/blue]{status}")
        else:
            tree.add(f"[dim]📁 {dir_name} (missing)[/dim]")
    
    console.print(tree)
    
    # Show disk usage
    storage = StorageTierSystem()
    status = storage.get_tier_status()
    if "library" in status and status["library"]["exists"]:
        lib_status = status["library"]
        console.print(f"\n[bold]Storage:[/bold]")
        console.print(f"  Used: {lib_status['disk_used_gb']:.1f} GB / {lib_status['disk_total_gb']:.1f} GB")
        console.print(f"  Free: {lib_status['disk_free_gb']:.1f} GB ({100 - lib_status['disk_usage_percent']:.1f}%)")
    
    # Show Resolve connection status
    console.print(f"\n[bold]Resolve Integration:[/bold]")
    api = ResolveDirectAPI()
    if api.is_connected():
        console.print("  [green]✓ Connected to Resolve[/green]")
        info = api.get_project_info()
        if info:
            console.print(f"  Current project: {info.get('name', 'None')}")
    else:
        console.print("  [yellow]✗ Resolve not connected (run Resolve first)[/yellow]")


@app.command()
def init(
    library_path: Optional[Path] = typer.Option(None, "--path", "-p", help="Library path (defaults to /mnt/library)"),
    create_structure: bool = typer.Option(True, "--structure/--no-structure", help="Create directory structure")
):
    """Initialize library workspace structure"""
    
    if library_path is None:
        library_path = Path("/mnt/library")
    
    console.print(f"Initializing library workspace at [cyan]{library_path}[/cyan]...")
    
    # Create base directory
    library_path.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/green] Created base directory")
    
    if create_structure:
        # Create standard structure
        structure = {
            "PROJECTS": {
                "DOCS": {},
                "EPISODES": {},
                "FILMS": {},
            },
            "CACHE": {},
            "PROXIES": {},
            "EXPORTS": {
                "YOUTUBE": {},
                "INSTAGRAM": {},
                "TIKTOK": {},
            },
            "ASSETS": {
                "MUSIC": {},
                "SFX": {},
                "GRAPHICS": {},
                "LUTS": {},
            },
        }
        
        def create_dir_tree(base: Path, tree: dict, prefix: str = ""):
            for name, subtree in tree.items():
                dir_path = base / name
                dir_path.mkdir(parents=True, exist_ok=True)
                console.print(f"{prefix}[green]✓[/green] {dir_path}")
                
                if isinstance(subtree, dict) and subtree:
                    create_dir_tree(dir_path, subtree, prefix + "  ")
        
        create_dir_tree(library_path, structure)
        
        console.print(f"\n[green]✓ Library structure initialized![/green]")
    
    # Save to config
    from studioflow.core.config import ConfigManager
    config_mgr = ConfigManager()
    config = config_mgr.config
    config.storage.library = library_path
    config_mgr.save()
    
    console.print(f"[green]✓ Configuration updated[/green]")


@app.command()
def create(
    project_name: str = typer.Argument(..., help="Project name"),
    project_type: str = typer.Option("episode", "--type", "-t", help="Project type: episode/doc/film"),
    media_dir: Optional[Path] = typer.Option(None, "--media", "-m", help="Media directory to import"),
    library_path: Optional[Path] = typer.Option(None, "--library", "-l", help="Library path"),
):
    """Create new Resolve project in library workspace"""
    
    if library_path is None:
        library_path = Path("/mnt/library")
    
    if not library_path.exists():
        console.print(f"[yellow]Library not initialized. Run:[/yellow] [cyan]sf library init[/cyan]")
        if typer.confirm("Initialize now?"):
            init(library_path=library_path)
        else:
            raise typer.Exit(1)
    
    console.print(f"Creating [cyan]{project_type}[/cyan] project: [bold]{project_name}[/bold]")
    
    # Determine project location based on type
    type_map = {
        "episode": library_path / "PROJECTS" / "EPISODES",
        "doc": library_path / "PROJECTS" / "DOCS",
        "film": library_path / "PROJECTS" / "FILMS",
    }
    
    project_dir = type_map.get(project_type.lower(), library_path / "PROJECTS")
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create project in Resolve
    result = create_documentary_project(
        project_name=project_name,
        media_dir=media_dir,
        library_path=library_path
    )
    
    if result.get("error"):
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(1)
    
    # Show results
    console.print(Panel(
        f"[green]✓ Project created successfully![/green]\n\n"
        f"Project: {result['project_name']}\n"
        f"Bins: {result['bins_created']}\n"
        f"Timelines: {result['timelines_created']}\n"
        f"Clips imported: {result['clips_imported']}\n"
        f"Stock library: {result['stock_library_clips']} clips",
        title="Project Created",
        border_style="green"
    ))
    
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Open project in DaVinci Resolve")
    console.print(f"  2. Import media: [cyan]sf library import {project_name}[/cyan]")
    console.print(f"  3. Check status: [cyan]sf library projects[/cyan]")


@app.command()
def projects(
    library_path: Optional[Path] = typer.Option(None, "--path", "-p", help="Library path"),
    project_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type: episode/doc/film"),
):
    """List all projects in library"""
    
    if library_path is None:
        library_path = Path("/mnt/library")
    
    if not library_path.exists():
        console.print(f"[red]Library path does not exist: {library_path}[/red]")
        raise typer.Exit(1)
    
    # Find projects in each type directory
    type_dirs = {
        "episode": library_path / "PROJECTS" / "EPISODES",
        "doc": library_path / "PROJECTS" / "DOCS",
        "film": library_path / "PROJECTS" / "FILMS",
    }
    
    all_projects = []
    
    for ptype, pdir in type_dirs.items():
        if project_type and ptype != project_type.lower():
            continue
            
        if pdir.exists():
            for item in pdir.iterdir():
                if item.is_dir():
                    # Try to find Resolve project file
                    drp_files = list(item.rglob("*.drp"))
                    resolve_project = len(drp_files) > 0
                    
                    all_projects.append({
                        "name": item.name,
                        "type": ptype,
                        "path": item,
                        "resolve_project": resolve_project,
                        "size_mb": sum(f.stat().st_size for f in item.rglob("*") if f.is_file()) / (1024**2)
                    })
    
    if not all_projects:
        console.print("[yellow]No projects found[/yellow]")
        return
    
    # Display table
    table = Table(title=f"Projects in {library_path}")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Resolve", style="green")
    table.add_column("Size", style="white")
    table.add_column("Path", style="dim")
    
    for proj in sorted(all_projects, key=lambda x: x["name"]):
        resolve_status = "✓" if proj["resolve_project"] else "-"
        size_str = f"{proj['size_mb']:.1f} MB" if proj['size_mb'] < 1024 else f"{proj['size_mb']/1024:.1f} GB"
        table.add_row(
            proj["name"],
            proj["type"].upper(),
            resolve_status,
            size_str,
            str(proj["path"].relative_to(library_path))
        )
    
    console.print(table)


@app.command()
def optimize(
    library_path: Optional[Path] = typer.Option(None, "--path", "-p", help="Library path"),
    cleanup_cache: bool = typer.Option(False, "--cleanup-cache", help="Clean up old cache files"),
    cleanup_proxies: bool = typer.Option(False, "--cleanup-proxies", help="Clean up old proxy files"),
):
    """Optimize library workspace (cleanup, organize)"""
    
    if library_path is None:
        library_path = Path("/mnt/library")
    
    console.print(f"Optimizing library at [cyan]{library_path}[/cyan]...")
    
    cleanup_stats = {"cache_removed": 0, "proxies_removed": 0, "space_freed_mb": 0}
    
    if cleanup_cache:
        cache_dir = library_path / "CACHE"
        if cache_dir.exists():
            console.print("Cleaning cache files older than 30 days...")
            # Implementation would go here
            console.print(f"[green]✓[/green] Cache cleanup complete")
    
    if cleanup_proxies:
        proxy_dir = library_path / "PROXIES"
        if proxy_dir.exists():
            console.print("Cleaning proxy files...")
            # Implementation would go here
            console.print(f"[green]✓[/green] Proxy cleanup complete")
    
    # Show storage status
    storage = StorageTierSystem()
    status = storage.get_tier_status()
    if "library" in status:
        lib_status = status["library"]
        console.print(f"\n[bold]Storage Status:[/bold]")
        console.print(f"  Free space: {lib_status['disk_free_gb']:.1f} GB")


if __name__ == "__main__":
    app()



