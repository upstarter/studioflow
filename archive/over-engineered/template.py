"""Template management commands"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from studioflow.core.template_definitions import (
    get_template,
    list_templates,
    video_effects_registry,
    script_patterns_registry,
    encoding_profiles_registry,
    project_templates_registry
)
from studioflow.core.templates import ComposableTemplate, TemplateFactory


console = Console()
app = typer.Typer()


@app.command()
def list(
    template_type: Optional[str] = typer.Option(None, "--type", "-t", help="Template type filter"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Category filter"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information")
):
    """
    List all available templates

    Examples:
        sf template list
        sf template list --type video_effect
        sf template list --category youtube
        sf template list --detailed
    """
    templates = list_templates(template_type, category)

    if template_type:
        # Single type view
        _display_single_type(templates, detailed)
    else:
        # All types view
        _display_all_types(templates, detailed)


def _display_single_type(templates: dict, detailed: bool):
    """Display templates for a single type"""
    table = Table(title=f"{templates['type'].replace('_', ' ').title()} Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="yellow")

    if detailed:
        table.add_column("Description", style="white")

    for template_name in templates["templates"]:
        template = get_template(templates["type"], template_name)
        preview = template.preview()

        row = [template_name]

        # Find category
        category = "uncategorized"
        for cat, names in templates.get("categories", {}).items():
            if template_name in names:
                category = cat
                break
        row.append(category)

        if detailed:
            desc = preview.get("metadata", {}).get("description", "No description")
            row.append(desc)

        table.add_row(*row)

    console.print(table)


def _display_all_types(templates: dict, detailed: bool):
    """Display all template types in a tree view"""
    tree = Tree("📋 Available Templates")

    for template_type, template_names in templates.items():
        if template_names:
            type_branch = tree.add(f"[bold cyan]{template_type.replace('_', ' ').title()}[/bold cyan]")

            for name in template_names:
                if detailed:
                    template = get_template(template_type.rstrip('s'), name)
                    preview = template.preview()
                    desc = preview.get("metadata", {}).get("description", "")
                    if desc:
                        type_branch.add(f"[white]{name}[/white] - [dim]{desc}[/dim]")
                    else:
                        type_branch.add(f"[white]{name}[/white]")
                else:
                    type_branch.add(f"[white]{name}[/white]")

    console.print(tree)


@app.command()
def apply(
    template_type: str = typer.Argument(..., help="Template type"),
    template_name: str = typer.Argument(..., help="Template name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path"),
    context_file: Optional[Path] = typer.Option(None, "--context", "-c", help="Context JSON/YAML file"),
    **kwargs: str  # Accept arbitrary key=value pairs
):
    """
    Apply a template with context

    Examples:
        sf template apply video_effect radial_scanner --output overlay.setting
        sf template apply script_pattern retention_optimized --topic "Python Tutorial"
        sf template apply encoding_profile av1_youtube_4k --input video.mp4 --output final.mp4
        sf template apply project youtube_creator --name "My Channel"
    """
    try:
        template = get_template(template_type, template_name)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Build context from various sources
    context = {}

    # Load from file if provided
    if context_file and context_file.exists():
        import json
        import yaml

        with open(context_file) as f:
            if context_file.suffix in ['.yaml', '.yml']:
                context = yaml.safe_load(f)
            else:
                context = json.load(f)

    # Add command-line arguments
    context.update(kwargs)

    # Add output if specified
    if output:
        context["output"] = str(output)

    # Apply template
    console.print(f"\n[bold]Applying template:[/bold] {template_name}")
    result = template.apply(context)

    # Display results based on template type
    if template_type == "video_effect":
        _display_video_effect_result(result)
    elif template_type == "script_pattern":
        _display_script_result(result)
    elif template_type == "encoding_profile":
        _display_encoding_result(result)
    elif template_type == "project":
        _display_project_result(result)

    return result


def _display_video_effect_result(result: dict):
    """Display video effect application result"""
    panel = Panel(
        f"Effect: {result['effect']}\n"
        f"Timeline Position: {result['timeline_position']}\n"
        f"Duration: {result['duration']}\n"
        f"Parameters: {result['parameters']}",
        title="Video Effect Applied",
        border_style="green"
    )
    console.print(panel)


def _display_script_result(result: dict):
    """Display script generation result"""
    console.print(f"\n[bold]Generated Script: {result['title']}[/bold]\n")

    for section in result["sections"]:
        console.print(f"[cyan]{section['name'].upper()}[/cyan] ({section['duration']})")
        console.print(f"  Content: {section['content'][:200]}...")

        if section.get("techniques"):
            console.print(f"  Techniques: {', '.join(section['techniques'])}")
        if section.get("b_roll_suggestions"):
            console.print(f"  B-Roll: {', '.join(section['b_roll_suggestions'])}")
        console.print()

    if result.get("hooks"):
        console.print("[bold]Available Hooks:[/bold]")
        for i, hook in enumerate(result["hooks"][:3], 1):
            console.print(f"  {i}. {hook}")


def _display_encoding_result(result: dict):
    """Display encoding command result"""
    if result.get("two_pass"):
        console.print("\n[bold]Two-Pass Encoding Commands:[/bold]\n")
        console.print("[cyan]Pass 1:[/cyan]")
        console.print(f"  {result['commands'][0]}\n")
        console.print("[cyan]Pass 2:[/cyan]")
        console.print(f"  {result['commands'][1]}")
    else:
        console.print("\n[bold]Encoding Command:[/bold]")
        console.print(f"  {result['command']}")

    console.print(f"\n[dim]Profile: {result['profile']}[/dim]")


def _display_project_result(result: dict):
    """Display project creation result"""
    console.print("\n[green]✓ Project created successfully![/green]\n")

    table = Table(title="Project Structure")
    table.add_column("Type", style="cyan")
    table.add_column("Created", style="white")

    table.add_row("Directories", f"{len(result['directories'])} created")
    table.add_row("Config Files", f"{len(result['files'])} created")

    if result.get("workflows"):
        table.add_row("Workflows", ", ".join(result["workflows"]))

    console.print(table)


@app.command()
def create(
    template_type: str = typer.Argument(..., help="Template type"),
    name: str = typer.Argument(..., help="Template name"),
    config_file: Path = typer.Argument(..., help="Configuration file (YAML/JSON)"),
    register: bool = typer.Option(True, "--register/--no-register", help="Register template")
):
    """
    Create a new template from configuration

    Examples:
        sf template create video_effect my_overlay config.yaml
        sf template create script_pattern viral_hook pattern.json
    """
    if not config_file.exists():
        console.print(f"[red]Configuration file not found: {config_file}[/red]")
        raise typer.Exit(1)

    try:
        # Create template from file
        template = TemplateFactory.from_file(config_file)

        # Register if requested
        if register:
            registries = {
                "video_effect": video_effects_registry,
                "script_pattern": script_patterns_registry,
                "encoding_profile": encoding_profiles_registry,
                "project": project_templates_registry
            }

            registry = registries.get(template_type)
            if registry:
                registry.register(name, type(template))
                console.print(f"[green]✓ Template '{name}' registered successfully[/green]")

        # Preview
        preview = template.preview()
        console.print("\n[bold]Template Preview:[/bold]")
        for key, value in preview.items():
            console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[red]Failed to create template: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def compose(
    name: str = typer.Argument(..., help="Composite template name"),
    components: str = typer.Argument(..., help="Comma-separated component names"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save composition")
):
    """
    Create a composite template from multiple components

    Examples:
        sf template compose my_workflow "script_pattern:retention_optimized,encoding_profile:av1_youtube_4k"
        sf template compose full_production "project:youtube_creator,video_effect:radial_scanner"
    """
    # Parse components
    component_specs = components.split(",")
    component_templates = []

    for spec in component_specs:
        parts = spec.strip().split(":")
        if len(parts) != 2:
            console.print(f"[red]Invalid component spec: {spec}[/red]")
            console.print("[dim]Format: type:name[/dim]")
            raise typer.Exit(1)

        template_type, template_name = parts
        try:
            template = get_template(template_type, template_name)
            component_templates.append(template)
        except Exception as e:
            console.print(f"[red]Failed to load {template_type}:{template_name} - {e}[/red]")
            raise typer.Exit(1)

    # Create composite
    composite = ComposableTemplate(
        name=name,
        components=component_templates,
        metadata={
            "description": f"Composite of {len(component_templates)} templates",
            "components": [c.name for c in component_templates]
        }
    )

    # Preview
    preview = composite.preview()
    console.print(f"\n[bold]Composite Template: {name}[/bold]")
    console.print(f"Components: {len(preview['components'])}")

    for i, comp in enumerate(preview["components"], 1):
        console.print(f"  {i}. {comp.get('name', 'unnamed')} ({comp.get('type', 'unknown')})")

    # Save if requested
    if output:
        import json
        config = {
            "type": "composite",
            "name": name,
            "components": [c.to_dict() for c in component_templates],
            "metadata": composite.metadata
        }
        with open(output, 'w') as f:
            json.dump(config, f, indent=2)
        console.print(f"\n[green]✓ Saved to {output}[/green]")

    return composite


@app.command()
def preview(
    template_type: str = typer.Argument(..., help="Template type"),
    template_name: str = typer.Argument(..., help="Template name")
):
    """
    Preview a template without applying

    Examples:
        sf template preview video_effect radial_scanner
        sf template preview script_pattern retention_optimized
    """
    try:
        template = get_template(template_type, template_name)
        preview = template.preview()

        console.print(Panel(
            f"[bold]Template: {template_name}[/bold]\n"
            f"Type: {template_type}\n\n" +
            "\n".join([f"{k}: {v}" for k, v in preview.items()]),
            title="Template Preview",
            border_style="cyan"
        ))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)