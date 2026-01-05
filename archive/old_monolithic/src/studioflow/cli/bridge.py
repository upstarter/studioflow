import click
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..integrations.bridge.discovery import WorkflowBridge
from ..core.project import ProjectGenerator

console = Console()

@click.group()
def cli():
    """StudioFlow Bridge - Seamlessly integrate with existing workflows"""
    pass

@cli.command()
@click.argument('existing_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory for analysis report')
def discover(existing_path: str, output: str):
    """
    Discover and analyze existing video production structure.
    This is completely non-invasive - just looks, doesn't touch.
    """
    path = Path(existing_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Analyzing {path.name}...", total=None)
        
        bridge = WorkflowBridge()
        discovery = bridge.discover_existing_structure(path)
        
        progress.update(task, completed=True)
    
    # Display results
    console.print(Panel.fit(
        f"[bold cyan]Workflow Analysis Complete[/bold cyan]\n"
        f"Integration Score: [green]{discovery['integration_score']}/100[/green]",
        title="StudioFlow Bridge"
    ))
    
    # Show detected workflow type
    if discovery['detected_type'] != 'unknown':
        console.print(f"\n🎬 Detected Workflow: [cyan]{discovery['detected_type']}[/cyan]")
    
    # Show discovered assets
    if discovery['assets']['projects']:
        console.print(f"\n📁 Found [green]{len(discovery['assets']['projects'])}[/green] active projects")
    
    if discovery['assets']['stock_footage']:
        total_size = sum(s['size_gb'] for s in discovery['assets']['stock_footage'])
        console.print(f"🎞️  Found [green]{len(discovery['assets']['stock_footage'])}[/green] stock footage libraries ({total_size:.1f} GB)")
    
    # Show workflow patterns
    if discovery['workflow_patterns']:
        console.print("\n[bold]Detected Patterns:[/bold]")
        patterns_by_type = {}
        for pattern in discovery['workflow_patterns']:
            if pattern['type'] not in patterns_by_type:
                patterns_by_type[pattern['type']] = []
            patterns_by_type[pattern['type']].append(pattern)
        
        for ptype, patterns in patterns_by_type.items():
            console.print(f"  • {ptype}: {len(patterns)} location(s)")
    
    # Save output if requested
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(discovery, f, default_flow_style=False)
        console.print(f"\n💾 Analysis saved to: {output_path}")
    
    # Show next steps
    console.print("\n[dim]Next steps:[/dim]")
    console.print(f"  studioflow-bridge integrate {existing_path} MyProject")
    console.print(f"  studioflow-bridge optimize {existing_path}")

@cli.command()
@click.argument('existing_path', type=click.Path(exists=True))
@click.argument('project_name')
@click.option('--location', '-l', default='.', type=click.Path())
@click.option('--mode', '-m', 
              type=click.Choice(['bridge', 'hybrid', 'migrate']),
              default='bridge',
              help='Integration mode: bridge (symlinks), hybrid (mixed), migrate (copy)')
@click.option('--dry-run', is_flag=True, help='Preview changes without applying')
def integrate(existing_path: str, project_name: str, location: str, mode: str, dry_run: bool):
    """
    Create a StudioFlow project that bridges with existing structure.
    Your files stay where they are - we just add intelligence.
    """
    existing = Path(existing_path)
    location_path = Path(location)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # First, discover existing structure
        task = progress.add_task("Discovering existing structure...", total=None)
        bridge = WorkflowBridge()
        discovery = bridge.discover_existing_structure(existing)
        progress.update(task, completed=True)
        
        # Create StudioFlow project
        task = progress.add_task(f"Creating StudioFlow project '{project_name}'...", total=None)
        generator = ProjectGenerator()
        project_path = generator.create_project(
            name=project_name,
            location=location_path,
            template='standard',
            init_git=True
        )
        progress.update(task, completed=True)
        
        # Create bridge configuration
        task = progress.add_task("Creating bridge configuration...", total=None)
        bridge_config = bridge.create_bridge_config(existing, project_path, discovery)
        bridge_config['mode'] = mode
        progress.update(task, completed=True)
        
        # Apply bridge
        task = progress.add_task("Applying bridge..." if not dry_run else "Simulating bridge...", total=None)
        actions = bridge.apply_bridge(bridge_config, dry_run=dry_run)
        progress.update(task, completed=True)
    
    # Show results
    if dry_run:
        console.print("\n[yellow]DRY RUN - No changes made[/yellow]")
    else:
        console.print("\n[green]✓ Integration complete![/green]")
    
    # Display action summary
    successful = sum(1 for a in actions if a.get('status') == 'completed')
    failed = sum(1 for a in actions if a.get('status') == 'failed')
    
    table = Table(title="Bridge Actions")
    table.add_column("Type", style="cyan")
    table.add_column("Source", style="white")
    table.add_column("Status", style="green")
    
    for action in actions[:5]:  # Show first 5
        status_style = "green" if action['status'] == 'completed' else "red"
        table.add_row(
            action['type'],
            Path(action['source']).name,
            f"[{status_style}]{action['status']}[/{status_style}]"
        )
    
    if len(actions) > 5:
        table.add_row("...", f"({len(actions) - 5} more)", "...")
    
    console.print(table)
    
    console.print(f"\n📊 Summary: {successful} successful, {failed} failed")
    
    if not dry_run:
        console.print(f"\n🎉 Your existing workflow at [cyan]{existing}[/cyan]")
        console.print(f"   is now enhanced with StudioFlow at [cyan]{project_path}[/cyan]")
        console.print("\n[dim]Your original files remain untouched and in place.[/dim]")

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def optimize(path: str):
    """
    Analyze existing structure and suggest optimizations.
    Non-invasive analysis that shows how StudioFlow can help.
    """
    existing = Path(path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing for optimizations...", total=None)
        bridge = WorkflowBridge()
        suggestions = bridge.suggest_optimizations(existing)
        progress.update(task, completed=True)
    
    if not suggestions:
        console.print("\n[green]✓[/green] Your workflow is well-organized!")
        return
    
    console.print(Panel.fit(
        f"[bold]Found {len(suggestions)} Optimization Opportunities[/bold]",
        title="StudioFlow Intelligence"
    ))
    
    for i, suggestion in enumerate(suggestions, 1):
        severity_color = {
            'high': 'red',
            'medium': 'yellow',
            'low': 'cyan'
        }.get(suggestion['severity'], 'white')
        
        console.print(f"\n{i}. [{severity_color}]{suggestion['type'].upper()}[/{severity_color}]")
        console.print(f"   {suggestion['message']}")
        console.print(f"   [green]→[/green] {suggestion['action']}")
        
        if 'benefit' in suggestion:
            console.print(f"   [dim]Benefit: {suggestion['benefit']}[/dim]")
        if 'savings' in suggestion:
            console.print(f"   [dim]Savings: {suggestion['savings']}[/dim]")
    
    console.print("\n[dim]Run 'studioflow-bridge integrate' to implement these optimizations[/dim]")

@cli.command()
@click.argument('name')
@click.option('--stock-footage', '-s', multiple=True, help='Stock footage directories')
@click.option('--templates', '-t', multiple=True, help='Project template directories')
@click.option('--archive', '-a', multiple=True, help='Archive directories')
@click.option('--cache', '-c', help='Cache directory')
def profile(name: str, stock_footage, templates, archive, cache):
    """
    Create a reusable workspace profile for your setup.
    Example: NAS-based workflow, cloud hybrid, local SSD setup.
    """
    bridge = WorkflowBridge()
    
    paths = {
        'stock_footage': list(stock_footage),
        'project_templates': list(templates),
        'archive': list(archive),
        'cache': cache or '/tmp/studioflow_cache'
    }
    
    # Detect storage tiers based on paths
    hot_storage = []
    warm_storage = []
    cold_storage = []
    
    for path in list(stock_footage) + list(templates) + list(archive):
        path_lower = path.lower()
        if 'ssd' in path_lower or 'nvme' in path_lower:
            hot_storage.append(path)
        elif 'nas' in path_lower or 'network' in path_lower:
            warm_storage.append(path)
        elif 'archive' in path_lower or 'backup' in path_lower:
            cold_storage.append(path)
    
    paths['hot_storage'] = hot_storage
    paths['warm_storage'] = warm_storage
    paths['cold_storage'] = cold_storage
    
    profile = bridge.create_workspace_profile(name, paths)
    
    console.print(f"[green]✓[/green] Created workspace profile: [cyan]{name}[/cyan]")
    console.print(f"   Saved to: ~/.studioflow/profiles/{name}.yaml")
    
    # Show profile summary
    console.print("\n[bold]Profile Configuration:[/bold]")
    if stock_footage:
        console.print(f"  📦 Stock Footage: {len(stock_footage)} location(s)")
    if templates:
        console.print(f"  📋 Templates: {len(templates)} location(s)")
    if archive:
        console.print(f"  🗄️  Archives: {len(archive)} location(s)")
    
    console.print(f"\n[dim]Use this profile: studioflow-project create MyProject --profile {name}[/dim]")

if __name__ == '__main__':
    cli()