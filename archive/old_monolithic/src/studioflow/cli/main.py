#!/usr/bin/env python3
"""
StudioFlow CLI - Professional video project organization
"""

import os
import click
import yaml
import sys
import json
import time
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.tree import Tree

console = Console()

@click.group()
@click.version_option(version='1.0.0', prog_name='StudioFlow')
def cli():
    """StudioFlow - Professional video project organization made simple"""
    pass

@cli.command()
@click.argument('name')
@click.option('--template', '-t', default='minimal', help='Template: minimal, youtube, client, or custom')
@click.option('--path', '-p', type=click.Path(), help='Where to create project')
@click.option('--add', '-a', multiple=True, help='Add: audio, graphics, vfx, color, cache')
@click.option('--dry-run', is_flag=True, help='Show what would be created')
def create(name: str, template: str, path: Optional[str], add: tuple, dry_run: bool):
    """Create a new video project"""
    
    from ..core.project_creator import ProjectCreator
    
    creator = ProjectCreator()
    
    if dry_run:
        console.print("[yellow]DRY RUN - No files created[/yellow]\n")
        creator.show_structure(name, template, path, add)
    else:
        try:
            project_path = creator.create(name, template, path, add)
            console.print(f"✅ Project created at: [cyan]{project_path}[/cyan]")
        except ValueError as e:
            console.print(f"[red]✗ {e}[/red]")
            raise click.Abort()

@cli.command()
def templates():
    """List available templates"""
    
    table = Table(title="Available Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Directories")
    
    # Built-in templates
    templates = {
        'minimal': ('Just the essentials', 'footage, exports'),
        'youtube': ('YouTube optimized', 'footage, audio, graphics, exports/youtube, exports/shorts'),
        'client': ('Client projects', 'footage, audio, graphics, exports/drafts, exports/final, feedback')
    }
    
    for name, (desc, dirs) in templates.items():
        table.add_row(name, desc, dirs)
    
    # Check for user templates
    user_dir = Path.home() / '.studioflow' / 'templates'
    if user_dir.exists():
        for template_file in user_dir.glob('*.yml'):
            table.add_row(template_file.stem, "Custom template", "...")
    
    console.print(table)

@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
def health(project_path: str):
    """Check health of a video project"""
    
    path = Path(project_path)
    health_file = path / '.studioflow' / 'health' / 'baseline.json'
    
    if not health_file.exists():
        console.print("[yellow]No health baseline found. Creating one now...[/yellow]")
        from ..core.project_creator import ProjectCreator
        creator = ProjectCreator()
        creator._create_health_baseline(path)
    
    # Load baseline
    with open(health_file) as f:
        baseline = json.load(f)
    
    # Check current state
    current = {
        'directories': {},
        'total_size': 0,
        'file_count': 0
    }
    
    issues = []
    
    for item in path.rglob('*'):
        if item.is_file() and '.git' not in str(item):
            current['file_count'] += 1
            current['total_size'] += item.stat().st_size
        elif item.is_dir() and '.git' not in str(item):
            rel_path = str(item.relative_to(path))
            current['directories'][rel_path] = {
                'exists': True,
                'file_count': len(list(item.glob('*')))
            }
    
    # Check for missing directories
    for dir_name in baseline.get('directories', {}):
        if dir_name not in current['directories']:
            issues.append(f"Missing directory: {dir_name}")
    
    # Display results
    table = Table(title=f"Project Health: {path.name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", style="green")
    table.add_column("Current", style="yellow")
    
    table.add_row("Files", str(baseline['file_count']), str(current['file_count']))
    table.add_row("Size", _format_size(baseline['total_size']), _format_size(current['total_size']))
    table.add_row("Directories", str(len(baseline['directories'])), str(len(current['directories'])))
    
    console.print(table)
    
    if issues:
        console.print("\n[red]Issues found:[/red]")
        for issue in issues:
            console.print(f"  • {issue}")
    else:
        console.print("\n[green]✅ Project is healthy![/green]")

@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--name', '-n', help='Snapshot name')
def snapshot(project_path: str, name: Optional[str]):
    """Create a snapshot of project state"""
    
    path = Path(project_path)
    snapshots_dir = path / '.studioflow' / 'snapshots'
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate snapshot name
    if not name:
        name = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    snapshot_data = {
        'name': name,
        'created': datetime.now().isoformat(),
        'files': {},
        'directories': [],
        'total_size': 0,
        'file_count': 0
    }
    
    # Collect file info
    for item in path.rglob('*'):
        if '.git' in str(item) or '.studioflow' in str(item):
            continue
            
        if item.is_file():
            rel_path = str(item.relative_to(path))
            snapshot_data['files'][rel_path] = {
                'size': item.stat().st_size,
                'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            }
            snapshot_data['file_count'] += 1
            snapshot_data['total_size'] += item.stat().st_size
        elif item.is_dir():
            snapshot_data['directories'].append(str(item.relative_to(path)))
    
    # Save snapshot
    snapshot_file = snapshots_dir / f"{name}.json"
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot_data, f, indent=2)
    
    console.print(f"✅ Snapshot created: [cyan]{snapshot_file.name}[/cyan]")
    console.print(f"   Files: {snapshot_data['file_count']}")
    console.print(f"   Size: {_format_size(snapshot_data['total_size'])}")

def _format_size(bytes_size: int) -> str:
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

@cli.command()
@click.option('--init', is_flag=True, help='Initialize configuration')
@click.option('--set', nargs=2, help='Set config value: --set key value')
@click.option('--get', help='Get config value')
@click.option('--edit', is_flag=True, help='Edit config file')
def config(init: bool, set: tuple, get: str, edit: bool):
    """Manage StudioFlow configuration"""
    
    config_path = Path.home() / '.studioflow' / 'config.yml'
    
    if init:
        _init_config()
    elif set:
        key, value = set
        console.print(f"Setting {key} = {value}")
        # TODO: Implement config setting
    elif get:
        console.print(f"Getting {get}")
        # TODO: Implement config getting
    elif edit:
        import subprocess
        editor = os.environ.get('EDITOR', 'nano')
        subprocess.call([editor, str(config_path)])
    else:
        # Show current config
        if config_path.exists():
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
                console.print(yaml.dump(config_data, default_flow_style=False))
        else:
            console.print("[yellow]No configuration found. Run 'studioflow config --init'[/yellow]")

def _init_config():
    """Initialize configuration interactively"""
    config_dir = Path.home() / '.studioflow'
    config_dir.mkdir(exist_ok=True)
    
    console.print("[cyan]StudioFlow Configuration Setup[/cyan]\n")
    
    base_path = Prompt.ask("Where do you store video projects?", default="~/Videos/Projects")
    default_template = Prompt.ask("Default template?", choices=['minimal', 'youtube', 'client'], default='minimal')
    
    config = {
        'storage': {
            'base_path': base_path
        },
        'templates': {
            'default': default_template
        }
    }
    
    config_file = config_dir / 'config.yml'
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    console.print(f"\n✅ Configuration saved to {config_file}")

if __name__ == '__main__':
    cli()