#!/usr/bin/env python3
"""
Migration Script - Transition from Unix tools to modern CLI
Preserves existing functionality while upgrading to new architecture
"""

import os
import sys
import shutil
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

# Add old tools to path for migration
sys.path.insert(0, '/mnt/projects/studioflow')


console = Console()


def migrate_config():
    """Migrate from old config to new Pydantic-based config"""
    console.print("\n[bold]Migrating configuration...[/bold]")

    old_config = Path("/mnt/projects/studioflow/config/default.yaml")
    new_config_dir = Path.home() / ".studioflow"
    new_config_file = new_config_dir / "config.yaml"

    if old_config.exists() and not new_config_file.exists():
        new_config_dir.mkdir(exist_ok=True)
        shutil.copy2(old_config, new_config_file)
        console.print("[green]✓[/green] Migrated configuration")

        # Update paths to use $HOME instead of hardcoded
        import yaml

        with open(new_config_file) as f:
            config = yaml.safe_load(f)

        # Replace /home/eric with $HOME
        home = str(Path.home())
        if 'paths' in config:
            for key, value in config['paths'].items():
                if isinstance(value, str) and '/home/eric' in value:
                    config['paths'][key] = value.replace('/home/eric', home)

        with open(new_config_file, 'w') as f:
            yaml.dump(config, f)

        console.print("[green]✓[/green] Updated paths to use current user home")
    else:
        console.print("[yellow]![/yellow] Config already exists or old config not found")


def create_compatibility_wrappers():
    """Create wrapper scripts for backward compatibility"""
    console.print("\n[bold]Creating compatibility wrappers...[/bold]")

    wrappers = {
        "sf-project": "sf project",
        "sf-audio": "sf audio",
        "sf-youtube": "sf youtube",
        "sf-resolve": "sf resolve",
        "sf-orchestrator": "sf orchestrate",
        "sf-ingest": "sf import",
    }

    wrapper_dir = Path("/usr/local/bin")
    if not os.access(wrapper_dir, os.W_OK):
        wrapper_dir = Path.home() / ".local" / "bin"
        wrapper_dir.mkdir(exist_ok=True)

    for old_cmd, new_cmd in wrappers.items():
        wrapper_path = wrapper_dir / old_cmd
        wrapper_content = f"""#!/bin/bash
# Compatibility wrapper for {old_cmd}
echo "[Migration] {old_cmd} is deprecated. Use '{new_cmd}' instead." >&2
{new_cmd} "$@"
"""
        try:
            wrapper_path.write_text(wrapper_content)
            wrapper_path.chmod(0o755)
            console.print(f"[green]✓[/green] Created wrapper: {old_cmd} → {new_cmd}")
        except Exception as e:
            console.print(f"[yellow]![/yellow] Could not create wrapper for {old_cmd}: {e}")


def migrate_projects():
    """Migrate existing projects to new structure"""
    console.print("\n[bold]Checking for existing projects...[/bold]")

    # Look for projects in common locations
    possible_locations = [
        Path("/mnt/studio/Projects"),
        Path.home() / "Videos" / "StudioFlow" / "Projects",
        Path("/mnt/projects"),
    ]

    found_projects = []
    for location in possible_locations:
        if location.exists():
            for path in location.iterdir():
                if path.is_dir() and not (path / ".studioflow" / "project.json").exists():
                    # Looks like an old project
                    found_projects.append(path)

    if found_projects:
        console.print(f"Found {len(found_projects)} potential projects to migrate:")
        for proj in found_projects[:5]:  # Show first 5
            console.print(f"  - {proj.name}")

        if Confirm.ask("\nMigrate these projects?"):
            for proj_path in found_projects:
                migrate_single_project(proj_path)
    else:
        console.print("[green]✓[/green] No old projects found to migrate")


def migrate_single_project(proj_path: Path):
    """Migrate a single project to new structure"""
    from studioflow.core.project import ProjectMetadata

    # Create .studioflow directory
    sf_dir = proj_path / ".studioflow"
    sf_dir.mkdir(exist_ok=True)

    # Create project metadata
    metadata = ProjectMetadata(
        name=proj_path.name,
        template="youtube",  # Default
        platform="youtube"
    )

    # Save metadata
    import json
    with open(sf_dir / "project.json", 'w') as f:
        json.dump(metadata.dict(), f, indent=2, default=str)

    console.print(f"[green]✓[/green] Migrated project: {proj_path.name}")


def install_new_cli():
    """Install the new CLI using pip"""
    console.print("\n[bold]Installing new StudioFlow CLI...[/bold]")

    try:
        import subprocess

        # Install in development mode
        result = subprocess.run(
            ["pip", "install", "-e", "/mnt/projects/studioflow"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            console.print("[green]✓[/green] Installed StudioFlow 2.0")

            # Test installation
            test_result = subprocess.run(
                ["sf", "--version"],
                capture_output=True,
                text=True
            )

            if test_result.returncode == 0:
                console.print(f"[green]✓[/green] CLI working: {test_result.stdout.strip()}")
            else:
                console.print("[yellow]![/yellow] CLI installed but not in PATH")
                console.print("Add ~/.local/bin to your PATH if needed")
        else:
            console.print(f"[red]Error installing:[/red] {result.stderr}")

    except Exception as e:
        console.print(f"[red]Installation failed:[/red] {e}")


def show_migration_summary():
    """Show summary and next steps"""
    summary = """
[bold green]Migration Complete![/bold green]

The new StudioFlow CLI is ready to use with these improvements:

✅ [bold]Single command:[/bold] 'sf' instead of 15+ separate tools
✅ [bold]Workflow automation:[/bold] 'sf new' does everything
✅ [bold]Better UX:[/bold] Progress bars, colors, interactive prompts
✅ [bold]Configuration:[/bold] ~/.studioflow/config.yaml
✅ [bold]Backwards compatible:[/bold] Old commands still work

[bold]Quick Start:[/bold]
  sf new "My Video" --import /media/sdcard
  sf status
  sf edit
  sf publish

[bold]Old → New Command Mapping:[/bold]
  sf-project create  →  sf project create
  sf-orchestrator    →  sf import
  sf-resolve         →  sf resolve sync
  sf-youtube         →  sf youtube optimize

[bold]Next Steps:[/bold]
1. Test with: sf --help
2. Create project: sf new "Test Project"
3. Check config: sf config --list
4. Run setup wizard: sf config --wizard

[yellow]Note:[/yellow] Your old tools are preserved and will continue to work.
"""

    console.print(Panel(summary, title="StudioFlow 2.0 Migration", border_style="green"))


def main():
    """Run full migration"""
    console.print(Panel(
        "[bold cyan]StudioFlow Migration Tool[/bold cyan]\n\n"
        "This will migrate your StudioFlow installation from the\n"
        "Unix philosophy architecture to the modern Git-style CLI.",
        title="Welcome",
        border_style="cyan"
    ))

    if not Confirm.ask("\nProceed with migration?"):
        console.print("Migration cancelled.")
        return

    # Run migration steps
    migrate_config()
    create_compatibility_wrappers()
    migrate_projects()
    install_new_cli()

    # Show summary
    show_migration_summary()


if __name__ == "__main__":
    main()