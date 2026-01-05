"""
Power Bins Management Commands
Manage Power Bins structure and sync with NAS media library (configurable)
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from studioflow.core.power_bins_config import PowerBinsConfig
from studioflow.core.resolve_api import ResolveDirectAPI

console = Console()
app = typer.Typer()


@app.command()
def validate():
    """Validate Power Bins structure on NAS"""
    
    if not PowerBinsConfig.is_available():
        console.print(Panel.fit(
            "[yellow]Power Bins is not configured[/yellow]\n\n"
            "Power Bins is an optional feature for organizing stock footage.\n"
            "To enable it, configure one of these in ~/.studioflow/config.yaml:\n\n"
            "[cyan]Option 1: NAS (recommended for shared storage)[/cyan]\n"
            "  storage:\n"
            "    nas: /path/to/your/nas\n\n"
            "[cyan]Option 2: Local library assets[/cyan]\n"
            "  storage:\n"
            "    library: /path/to/your/library\n"
            "  (Will use library/Assets if it exists)",
            title="Power Bins Not Configured",
            border_style="yellow"
        ))
        return
    
    base_path = PowerBinsConfig.get_base_path()
    
    console.print(Panel.fit(
        "[bold cyan]Validating Power Bins Structure[/bold cyan]\n"
        f"Base Path: {base_path}",
        title="Power Bins Validation",
        border_style="cyan"
    ))
    
    results = PowerBinsConfig.validate_structure()
    
    if not results.get("base_exists"):
        console.print(f"\n[red]❌ Base path does not exist:[/red] {base_path}")
        console.print("\n[yellow]Please ensure the path exists or configure it in ~/.studioflow/config.yaml[/yellow]")
        return
    
    console.print(f"\n[green]✓ Base path exists[/green]\n")
    
    # Show structure validation
    table = Table(title="Power Bins Structure", box=box.ROUNDED)
    table.add_column("Category", style="cyan", width=20)
    table.add_column("Subcategory", style="white", width=25)
    table.add_column("Path", style="dim", width=40)
    table.add_column("Status", width=12)
    
    structure = PowerBinsConfig.get_structure()
    all_exist = True
    
    for category, subcategories in structure.items():
        category_row_span = len(subcategories)
        first_subcat = True
        
        for subcat_name, subcat_path in subcategories.items():
            exists = results.get(f"{category}/{subcat_name}", False)
            status_icon = "✓" if exists else "✗"
            status_text = "[green]Exists[/green]" if exists else "[yellow]Missing[/yellow]"
            
            if not exists:
                all_exist = False
            
            cat_display = category if first_subcat else ""
            table.add_row(
                cat_display,
                subcat_name,
                str(subcat_path),
                f"{status_icon} {status_text}"
            )
            first_subcat = False
    
    console.print(table)
    
    if all_exist:
        console.print("\n[green]✓ All Power Bins paths exist and are ready![/green]")
    else:
        console.print("\n[yellow]⚠ Some paths are missing - create them for optimal workflow[/yellow]")
        console.print("\n[cyan]Suggested command:[/cyan]")
        console.print("  sf power-bins create-structure")


@app.command()
def create_structure():
    """Create recommended Power Bins directory structure"""
    
    if not PowerBinsConfig.is_available():
        console.print("[yellow]Power Bins is not configured. Configure storage.nas or storage.library first.[/yellow]")
        return
    
    base_path = PowerBinsConfig.get_base_path()
    
    console.print(Panel.fit(
        "[bold cyan]Creating Power Bins Directory Structure[/bold cyan]\n"
        f"Base Path: {base_path}",
        title="Power Bins Setup",
        border_style="cyan"
    ))
    
    if not base_path.exists():
        console.print(f"\n[red]❌ Base path does not exist:[/red] {base_path}")
        console.print("\n[yellow]Please ensure the path exists or configure it in ~/.studioflow/config.yaml[/yellow]")
        return
    
    structure = PowerBinsConfig.get_structure()
    created = []
    skipped = []
    
    for category, subcategories in structure.items():
        for subcat_name, subcat_path in subcategories.items():
            if subcat_path.exists():
                skipped.append(subcat_path)
            else:
                try:
                    subcat_path.mkdir(parents=True, exist_ok=True)
                    created.append(subcat_path)
                    console.print(f"[green]✓ Created:[/green] {subcat_path}")
                except Exception as e:
                    console.print(f"[red]✗ Failed:[/red] {subcat_path} - {e}")
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Created: {len(created)} directories")
    console.print(f"  Already existed: {len(skipped)} directories")
    
    if created:
        console.print(f"\n[green]✓ Directory structure created successfully![/green]")
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("  1. Add your media files to the created directories")
        console.print("  2. Run: sf power-bins sync")
    else:
        console.print(f"\n[cyan]✓ All directories already exist[/cyan]")


@app.command()
def sync():
    """Sync Power Bins with Resolve project"""
    
    console.print("[cyan]Syncing Power Bins with Resolve...[/cyan]\n")
    
    resolve_api = ResolveDirectAPI()
    
    if not resolve_api.is_connected():
        console.print("[red]Resolve not connected - please start Resolve first[/red]")
        return
    
    # Use auto_editing's setup_power_bins
    from studioflow.core.auto_editing import AutoEditingEngine, AutoEditConfig
    
    config = AutoEditConfig(
        project_name="temp",  # Will use current project
        footage_path=Path("/tmp"),
        create_power_bins=True
    )
    
    engine = AutoEditingEngine(config)
    engine.resolve_api = resolve_api
    
    result = engine.setup_power_bins()
    
    if result.get("error"):
        console.print(f"[red]Error:[/red] {result['error']}")
        return
    
    total = result.get("total_assets", 0)
    power_bins = result.get("power_bins_assets", {})
    
    console.print(f"\n[green]✓ Synced {total} assets to Power Bins[/green]\n")
    
    # Show breakdown
    if power_bins:
        table = Table(title="Imported Assets", box=box.SIMPLE)
        table.add_column("Category", style="cyan")
        table.add_column("Assets", style="green")
        
        for path, count in sorted(power_bins.items()):
            if count > 0:
                table.add_row(path, str(count))
        
        console.print(table)
    
    console.print("\n[yellow]💡 Tip:[/yellow] Drag '_POWER_BINS' to Power Bins in Resolve for persistence across all projects")


@app.command()
def show_structure():
    """Show recommended Power Bins structure"""
    
    if not PowerBinsConfig.is_available():
        console.print("[yellow]Power Bins is not configured. This command shows the structure that would be created if configured.[/yellow]\n")
        # Show structure anyway using a placeholder
        base_path = Path("/path/to/media")
    else:
        base_path = PowerBinsConfig.get_base_path()
    
    console.print(Panel.fit(
        "[bold cyan]Recommended Power Bins Structure[/bold cyan]\n"
        f"Base: {base_path}",
        title="Power Bins Structure",
        border_style="cyan"
    ))
    
    structure = PowerBinsConfig.get_structure()
    if structure is None:
        # Show example structure
        from studioflow.core.power_bins_config import PowerBinsConfig
        # Temporarily set a dummy base to show structure
        console.print("\n[yellow]Example structure (configure Power Bins to use):[/yellow]\n")
        structure = {
            "MUSIC": {"INTRO": base_path / "Audio" / "Music" / "Intro", "BACKGROUND": base_path / "Audio" / "Music" / "Background"},
            "SFX": {"SWISHES": base_path / "Audio" / "SFX" / "Swishes"},
            "GRAPHICS": {"LOWER_THIRDS": base_path / "Graphics" / "Lower_Thirds"},
        }
    
    from rich.tree import Tree
    tree = Tree(f"[bold]{base_path}[/bold]")
    
    for category, subcategories in structure.items():
        cat_branch = tree.add(f"[cyan]{category}/[/cyan]")
        for subcat_name, subcat_path in subcategories.items():
            exists = "✓" if subcat_path.exists() else "✗"
            color = "green" if subcat_path.exists() else "yellow"
            cat_branch.add(f"[{color}]{exists}[/{color}] {subcat_name}")
    
    console.print("\n")
    console.print(tree)
    console.print("\n[dim]✓ = exists, ✗ = missing[/dim]")


if __name__ == "__main__":
    app()


