"""
Version commands - User-friendly version control
No Git knowledge required!
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from datetime import datetime

from ..core.version_manager import VersionManager

console = Console()

@click.group()
def version():
    """Simple version control for your projects"""
    pass

@version.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--message', '-m', help='Description of what you changed')
def save(project_path: str, message: str):
    """Save current version of your project"""
    
    path = Path(project_path)
    vm = VersionManager(path)
    
    if not message:
        message = Prompt.ask("What did you change?", default="Quick save")
    
    if vm.save_version(message):
        console.print("✅ Version saved successfully!")
        
        # Show recent versions
        versions = vm.get_versions(limit=3)
        if versions:
            console.print("\nRecent versions:")
            for v in versions:
                console.print(f"  • {v['description']} ({v['time']})")
    else:
        console.print("[yellow]No changes to save[/yellow]")

@version.command()
@click.argument('project_path', type=click.Path(exists=True))
def history(project_path: str):
    """View version history"""
    
    path = Path(project_path)
    vm = VersionManager(path)
    
    versions = vm.get_versions(limit=20)
    
    if not versions:
        console.print("[yellow]No version history yet[/yellow]")
        return
    
    table = Table(title=f"Version History: {path.name}")
    table.add_column("ID", style="cyan")
    table.add_column("Description")
    table.add_column("When", style="green")
    
    for v in versions:
        table.add_row(v['id'], v['description'], v['time'])
    
    console.print(table)

@version.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--version-id', help='Version ID to restore (from history)')
def restore(project_path: str, version_id: str):
    """Restore to a previous version"""
    
    path = Path(project_path)
    vm = VersionManager(path)
    
    if not version_id:
        # Show versions and let user choose
        versions = vm.get_versions(limit=10)
        
        console.print("Recent versions:")
        for i, v in enumerate(versions, 1):
            console.print(f"{i}. {v['description']} ({v['time']}) [{v['id']}]")
        
        choice = Prompt.ask("Which version to restore?", choices=[str(i) for i in range(1, len(versions)+1)])
        version_id = versions[int(choice)-1]['full_id']
    
    if Confirm.ask(f"Restore to version {version_id[:8]}?"):
        if vm.restore_version(version_id):
            console.print("✅ Successfully restored!")
        else:
            console.print("[red]Restore failed[/red]")

@version.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.argument('name')
@click.option('--notes', help='Additional notes about this milestone')
def milestone(project_path: str, name: str, notes: str):
    """Mark an important milestone"""
    
    path = Path(project_path)
    vm = VersionManager(path)
    
    if vm.save_milestone(name, notes):
        console.print(f"✅ Milestone saved: [cyan]{name}[/cyan]")
    else:
        console.print("[red]Failed to save milestone[/red]")

@version.command()
@click.argument('project_path', type=click.Path(exists=True))
def compare(project_path: str):
    """Compare current version with previous"""
    
    path = Path(project_path)
    vm = VersionManager(path)
    
    stats = vm.compare_versions()
    
    if stats:
        console.print(f"\n[cyan]Changes since last version:[/cyan]")
        console.print(f"  Files changed: {stats['files_changed']}")
        console.print(f"  Added: [green]+{stats['insertions']}[/green] lines")
        console.print(f"  Removed: [red]-{stats['deletions']}[/red] lines")
        
        if stats['files']:
            console.print("\n[cyan]Modified files:[/cyan]")
            for file in stats['files'][:10]:
                console.print(f"  • {file}")
    else:
        console.print("[yellow]No changes since last version[/yellow]")

@version.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.argument('name')
def alternative(project_path: str, name: str):
    """Create an alternative edit (like 'Director's Cut')"""
    
    path = Path(project_path)
    vm = VersionManager(path)
    
    if vm.create_branch(name):
        console.print(f"✅ Created alternative edit: [cyan]{name}[/cyan]")
        console.print("You can now make different edits without affecting the original")
    else:
        console.print("[red]Failed to create alternative[/red]")

@version.command()
@click.argument('project_path', type=click.Path(exists=True))
def alternatives(project_path: str):
    """List all alternative edits"""
    
    path = Path(project_path)
    vm = VersionManager(path)
    
    alts = vm.list_alternatives()
    
    if alts:
        console.print("[cyan]Alternative edits:[/cyan]")
        for alt in alts:
            console.print(f"  • {alt}")
    else:
        console.print("[yellow]No alternative edits yet[/yellow]")
        console.print("Create one with: studioflow version alternative <project> <name>")