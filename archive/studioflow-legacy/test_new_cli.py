#!/usr/bin/env python3
"""
Test Script for New StudioFlow CLI
Verifies the new architecture is working correctly
"""

import sys
import subprocess
from pathlib import Path

# Add to path for testing before install
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table


console = Console()


def test_imports():
    """Test that all modules import correctly"""
    console.print("\n[bold]Testing imports...[/bold]")

    try:
        # Core modules
        from studioflow import __version__
        console.print(f"[green]✓[/green] StudioFlow version: {__version__}")

        from studioflow.core.config import Config, ConfigManager
        console.print("[green]✓[/green] Config system imported")

        from studioflow.core.project import Project, ProjectManager
        console.print("[green]✓[/green] Project system imported")

        from studioflow.core.media import MediaScanner, MediaImporter
        console.print("[green]✓[/green] Media system imported")

        from studioflow.core.state import StateManager
        console.print("[green]✓[/green] State manager imported")

        # CLI modules
        from studioflow.cli.main import app
        console.print("[green]✓[/green] CLI app imported")

        from studioflow.cli.workflows.new_video import create_workflow
        console.print("[green]✓[/green] Workflows imported")

        return True

    except ImportError as e:
        console.print(f"[red]✗[/red] Import error: {e}")
        return False


def test_config():
    """Test configuration system"""
    console.print("\n[bold]Testing configuration...[/bold]")

    try:
        from studioflow.core.config import ConfigManager

        manager = ConfigManager()
        config = manager.config

        # Check basic settings
        console.print(f"  User: {config.user_name}")
        console.print(f"  Storage paths configured: {len(dict(config.storage))}")
        console.print(f"  Media extensions: {len(config.media.extensions)}")

        console.print("[green]✓[/green] Configuration system working")
        return True

    except Exception as e:
        console.print(f"[red]✗[/red] Config error: {e}")
        return False


def test_project_creation():
    """Test project creation"""
    console.print("\n[bold]Testing project creation...[/bold]")

    try:
        from studioflow.core.project import Project
        import tempfile

        # Create test project in temp directory
        with tempfile.TemporaryDirectory() as tmp:
            project = Project("Test_Project", Path(tmp) / "Test_Project")
            result = project.create(template="youtube")

            if result.success:
                console.print("[green]✓[/green] Project creation working")
                console.print(f"  Created at: {result.project_path}")

                # Check structure
                expected_dirs = ["01_MEDIA", "02_AUDIO", ".studioflow"]
                for dir_name in expected_dirs:
                    if (result.project_path / dir_name).exists():
                        console.print(f"  [green]✓[/green] {dir_name} created")

                return True
            else:
                console.print(f"[red]✗[/red] Project creation failed: {result.error}")
                return False

    except Exception as e:
        console.print(f"[red]✗[/red] Project error: {e}")
        return False


def test_cli_help():
    """Test CLI help command"""
    console.print("\n[bold]Testing CLI interface...[/bold]")

    try:
        # Run the CLI module directly
        result = subprocess.run(
            [sys.executable, "-m", "studioflow.cli.main", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        if "StudioFlow - Automated Video Production Pipeline" in result.stdout:
            console.print("[green]✓[/green] CLI help working")

            # Count available commands
            commands = ["new", "import", "edit", "publish", "status", "config"]
            found = sum(1 for cmd in commands if cmd in result.stdout)
            console.print(f"  Found {found}/{len(commands)} main commands")

            return True
        else:
            console.print("[red]✗[/red] CLI help not working properly")
            console.print(f"  stdout: {result.stdout[:200]}")
            console.print(f"  stderr: {result.stderr[:200]}")
            return False

    except Exception as e:
        console.print(f"[red]✗[/red] CLI error: {e}")
        return False


def show_results(results):
    """Show test results summary"""
    table = Table(title="\nTest Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status")

    for name, passed in results.items():
        status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        table.add_row(name, status)

    console.print(table)

    total = len(results)
    passed = sum(results.values())

    if passed == total:
        console.print(f"\n[bold green]All tests passed! ({passed}/{total})[/bold green]")
        console.print("\n✅ StudioFlow 2.0 is ready to use!")
        console.print("Run: [bold]python migrate.py[/bold] to complete migration")
    else:
        console.print(f"\n[bold yellow]Some tests failed ({passed}/{total})[/bold yellow]")
        console.print("Please check the errors above")


def main():
    """Run all tests"""
    console.print("[bold cyan]StudioFlow 2.0 Architecture Test[/bold cyan]")

    results = {
        "Imports": test_imports(),
        "Configuration": test_config(),
        "Project Creation": test_project_creation(),
        "CLI Interface": test_cli_help(),
    }

    show_results(results)


if __name__ == "__main__":
    main()