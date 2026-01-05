import click
import os
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.project import ProjectGenerator
from ..core.health import HealthMonitor

console = Console()

@click.group()
def cli():
    """StudioFlow Project Management CLI"""
    pass

@cli.command()
@click.argument('name')
@click.option('--template', '-t', default='standard', 
              type=click.Choice(['standard', 'youtube', 'commercial', 'documentary']),
              help='Project template to use')
@click.option('--location', '-l', default='.', 
              type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Location to create the project')
@click.option('--no-git', is_flag=True, help='Skip git initialization')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing project')
@click.option('--profile', '-p', help='Use a workspace profile')
@click.option('--bridge', '-b', type=click.Path(exists=True), 
              help='Bridge with existing directory structure')
def create(name: str, template: str, location: str, no_git: bool, force: bool, 
           profile: Optional[str], bridge: Optional[str]):
    """Create a new video project structure"""
    project_path = Path(location) / name
    
    if project_path.exists() and not force:
        console.print(f"[red]Error:[/red] Project '{name}' already exists at {project_path}")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Creating project '{name}'...", total=None)
        
        try:
            generator = ProjectGenerator()
            project_path, report = generator.create_project(
                name=name,
                location=Path(location),
                template=template,
                init_git=not no_git,
                force=force
            )
            
            if not report['success']:
                progress.update(task, completed=True)
                console.print(f"[red]Error creating project:[/red] {report.get('error', 'Unknown error')}")
                if 'suggestion' in report:
                    console.print(f"[yellow]Suggestion:[/yellow] {report['suggestion']}")
                sys.exit(1)
            
            project = project_path
            
            # Load and apply profile if specified
            if profile:
                import yaml
                profile_path = Path.home() / '.studioflow' / 'profiles' / f'{profile}.yaml'
                if profile_path.exists():
                    with open(profile_path, 'r') as f:
                        profile_data = yaml.safe_load(f)
                    console.print(f"[cyan]Applied profile:[/cyan] {profile}")
                else:
                    console.print(f"[yellow]Warning:[/yellow] Profile '{profile}' not found")
            
            # Create bridge if specified
            if bridge:
                from ..integrations.bridge.discovery import WorkflowBridge
                bridge_path = Path(bridge)
                wb = WorkflowBridge()
                discovery = wb.discover_existing_structure(bridge_path)
                bridge_config = wb.create_bridge_config(bridge_path, project, discovery)
                actions = wb.apply_bridge(bridge_config)
                console.print(f"[green]✓[/green] Bridged with: {bridge_path}")
                console.print(f"  Created {len(actions)} connections")
            
            progress.update(task, completed=True)
            console.print(f"[green]✓[/green] Project created successfully at: {project}")
            
            if not no_git:
                console.print(f"[green]✓[/green] Git repository initialized")
            
            console.print(f"[cyan]Next steps:[/cyan]")
            console.print(f"  cd {project}")
            console.print(f"  studioflow-project health .")
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error creating project:[/red] {e}")
            sys.exit(1)

@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed health information')
def health(project_path: str, verbose: bool):
    """Check project health and integrity"""
    path = Path(project_path)
    
    if not (path / '.studioflow').exists():
        console.print(f"[red]Error:[/red] Not a StudioFlow project: {path}")
        sys.exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Checking project health...", total=None)
        
        try:
            monitor = HealthMonitor(path)
            report = monitor.check_health(verbose=verbose)
            
            progress.update(task, completed=True)
            
            if report['status'] == 'healthy':
                console.print(f"[green]✓[/green] Project is healthy")
            elif report['status'] == 'warning':
                console.print(f"[yellow]⚠[/yellow] Project has warnings")
            else:
                console.print(f"[red]✗[/red] Project has errors")
            
            if verbose or report['status'] != 'healthy':
                console.print("\n[bold]Health Report:[/bold]")
                for issue in report.get('issues', []):
                    level = issue['level']
                    if level == 'error':
                        console.print(f"  [red]✗[/red] {issue['message']}")
                    elif level == 'warning':
                        console.print(f"  [yellow]⚠[/yellow] {issue['message']}")
                    else:
                        console.print(f"  [cyan]ℹ[/cyan] {issue['message']}")
            
            console.print(f"\n[dim]Last checked: {report['timestamp']}[/dim]")
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error checking health:[/red] {e}")
            sys.exit(1)

@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--name', '-n', help='Snapshot name/description')
def snapshot(project_path: str, name: Optional[str]):
    """Create a project snapshot for backup/restore"""
    path = Path(project_path)
    
    if not (path / '.studioflow').exists():
        console.print(f"[red]Error:[/red] Not a StudioFlow project: {path}")
        sys.exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating snapshot...", total=None)
        
        try:
            monitor = HealthMonitor(path)
            snapshot_file = monitor.create_snapshot(name=name)
            
            progress.update(task, completed=True)
            console.print(f"[green]✓[/green] Snapshot created: {snapshot_file}")
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error creating snapshot:[/red] {e}")
            sys.exit(1)

if __name__ == '__main__':
    cli()