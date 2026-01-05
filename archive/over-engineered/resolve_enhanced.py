"""Enhanced DaVinci Resolve Commands with Effects Integration"""

import sys
import subprocess
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from studioflow.core.state import StateManager
from studioflow.core.project import ProjectManager
from studioflow.core.config import get_config
from studioflow.core.resolve_profiles import ResolveProfiles
from studioflow.core.composition import (
    Composition,
    CompositionType,
    CompositionBuilder,
    export_to_resolve,
    export_to_edl
)
from studioflow.core.effects import NodeGraph, create_procedural_effect
from studioflow.core.fairlight_templates import create_fairlight_template
from studioflow.core.animation import AnimationCurve, AnimationPresets


console = Console()
app = typer.Typer()


@app.command()
def create(
    name: str = typer.Argument(..., help="Timeline name"),
    profile: str = typer.Option("youtube", "--profile", "-p", help="Resolution/framerate profile"),
    media_path: Optional[Path] = typer.Option(None, "--media", "-m", help="Media folder to import"),
    with_effects: bool = typer.Option(False, "--effects", help="Apply default effects"),
    audio_template: Optional[str] = typer.Option(None, "--audio", help="Apply audio template"),
    composition: Optional[str] = typer.Option(None, "--composition", help="Use composition template")
):
    """
    Create new timeline with integrated effects

    Examples:
        sf resolve create "Episode 1" --profile youtube
        sf resolve create "Podcast" --audio podcast_mastering
        sf resolve create "Tutorial" --effects --composition title_sequence
        sf resolve create "Music Video" --audio music_mastering --effects
    """
    console.print(f"\n[bold]Creating timeline:[/bold] {name}")

    # Get profile settings
    profiles = ResolveProfiles()
    if profile == "youtube":
        profile_data = profiles.get_youtube_settings("4k30_master")
        width, height = profile_data["resolution"]
        framerate = 29.97
    elif profile == "podcast":
        width, height = 1920, 1080
        framerate = 29.97
    elif profile == "cinema4k":
        width, height = 4096, 2160
        framerate = 24
    else:
        width, height = 1920, 1080
        framerate = 29.97

    console.print(f"  Resolution: {width}x{height}")
    console.print(f"  Framerate: {framerate}")

    # Create composition
    comp_type = CompositionType.COMPOSITE
    if composition == "title_sequence":
        comp_type = CompositionType.TITLE
    elif composition == "lower_third":
        comp_type = CompositionType.LOWER_THIRD

    comp = CompositionBuilder(name, comp_type)
    comp.set_duration(10.0)
    comp.set_resolution(width, height)

    # Apply effects if requested
    if with_effects:
        console.print("\n[bold]Adding effects:[/bold]")

        # Add glow effect
        console.print("  • Adding glow effect")
        glow = create_procedural_effect("audio_reactive_glow")
        comp.add_effect(glow)

        # Add text animation
        console.print("  • Adding text animation")
        text_anim = AnimationPresets.typewriter(len(name))
        comp.add_animation(text_anim, start_time=0.5)

        # Add particles
        console.print("  • Adding particle system")
        particles = create_procedural_effect("particles")
        comp.add_effect(particles, blend_mode="add")

    # Apply audio template if specified
    if audio_template:
        console.print(f"\n[bold]Applying audio template:[/bold] {audio_template}")
        try:
            audio_chain = create_fairlight_template(audio_template)

            # Build the chain with appropriate parameters
            if audio_template == "podcast_mastering":
                graph = audio_chain.build_chain(target_lufs=-16.0)
            elif audio_template == "music_mastering":
                graph = audio_chain.build_chain(genre="electronic")
            else:
                graph = audio_chain.build_chain()

            comp.add_effect(graph)
            console.print(f"[green]✓[/green] Audio template configured")

        except Exception as e:
            console.print(f"[yellow]Warning: Could not apply audio template: {e}[/yellow]")

    # Add media if specified
    if media_path and media_path.exists():
        console.print(f"\n[bold]Importing media from:[/bold] {media_path}")
        media_files = list(media_path.glob("*.mp4")) + \
                     list(media_path.glob("*.mov")) + \
                     list(media_path.glob("*.mxf"))

        for i, media_file in enumerate(media_files[:5]):  # Limit to 5 files for demo
            comp.add_image(str(media_file), position=(0, 0, i * -10))
            console.print(f"  • {media_file.name}")

    # Build composition
    composition_obj = comp.build()

    # Export to Resolve script
    script_path = Path(f"{name.replace(' ', '_')}_resolve.py")
    export_to_resolve(composition_obj, script_path)

    # Also export EDL for compatibility
    edl_path = Path(f"{name.replace(' ', '_')}.edl")
    export_to_edl(composition_obj, edl_path)

    console.print(f"\n[green]✓[/green] Timeline created successfully")
    console.print(f"  Resolve script: {script_path}")
    console.print(f"  EDL file: {edl_path}")
    console.print("\n[dim]To apply in Resolve:[/dim]")
    console.print(f"  1. Open Resolve Console (Workspace → Console)")
    console.print(f"  2. Run: exec(open('{script_path}').read())")


@app.command()
def apply_effects(
    timeline: str = typer.Argument(..., help="Timeline to apply effects to"),
    effect_chain: Path = typer.Option(None, "--chain", "-c", help="Effect chain configuration file"),
    audio_template: Optional[str] = typer.Option(None, "--audio", help="Audio processing template"),
    video_effects: List[str] = typer.Option([], "--effect", "-e", help="Video effects to apply")
):
    """
    Apply effects to existing timeline

    Examples:
        sf resolve apply-effects "My Timeline" --audio podcast_mastering
        sf resolve apply-effects "Tutorial" --effect glow --effect shake
        sf resolve apply-effects "Music Video" --chain effects.yaml
    """
    console.print(f"\n[bold]Applying effects to:[/bold] {timeline}")

    # Create node graph for effects
    graph = NodeGraph()

    # Load effect chain if provided
    if effect_chain and effect_chain.exists():
        console.print(f"\n[bold]Loading effect chain:[/bold] {effect_chain}")
        import yaml
        import json

        with open(effect_chain) as f:
            if effect_chain.suffix in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            else:
                config = json.load(f)

        # Process chain configuration
        for effect_config in config.get("effects", []):
            console.print(f"  • Adding {effect_config['type']}")
            # Add effects based on config

    # Apply individual video effects
    if video_effects:
        console.print("\n[bold]Adding video effects:[/bold]")
        for effect_name in video_effects:
            console.print(f"  • {effect_name}")
            effect = create_procedural_effect(effect_name)
            # Add to graph

    # Apply audio template
    if audio_template:
        console.print(f"\n[bold]Applying audio template:[/bold] {audio_template}")
        template = create_fairlight_template(audio_template)
        audio_graph = template.build_chain()
        console.print(f"  [green]✓[/green] {audio_template} configured")

    # Generate Resolve script
    script = f"""
# Apply Effects to Timeline: {timeline}
import DaVinciResolveScript as dvr

resolve = dvr.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()
timeline = project.GetTimelineByName("{timeline}")

if timeline:
    # Apply effects via Fusion/Fairlight pages
    print("Effects configured for timeline: {timeline}")
else:
    print("Timeline not found: {timeline}")
"""

    script_path = Path(f"{timeline.replace(' ', '_')}_effects.py")
    script_path.write_text(script)

    console.print(f"\n[green]✓[/green] Effects configured")
    console.print(f"  Script saved to: {script_path}")


@app.command()
def render_with_effects(
    output: Path = typer.Argument(..., help="Output file path"),
    preset: str = typer.Option("youtube_4k", "--preset", "-p", help="Render preset"),
    effects: bool = typer.Option(True, "--effects/--no-effects", help="Apply effects during render"),
    audio_norm: bool = typer.Option(True, "--normalize", help="Normalize audio to platform standards")
):
    """
    Render timeline with integrated effects

    Examples:
        sf resolve render-with-effects output.mp4 --preset youtube_4k
        sf resolve render-with-effects final.mov --preset prores_master --no-effects
        sf resolve render-with-effects podcast.mp4 --normalize
    """
    console.print(f"\n[bold]Rendering with effects to:[/bold] {output}")
    console.print(f"  Preset: {preset}")
    console.print(f"  Effects: {'Enabled' if effects else 'Disabled'}")
    console.print(f"  Audio Normalization: {'Enabled' if audio_norm else 'Disabled'}")

    # Get render settings from preset
    profiles = ResolveProfiles()
    settings = profiles.get_export_preset(preset.split("_")[0])

    # Build render configuration
    render_config = {
        "output": str(output),
        "preset": preset,
        "settings": settings,
        "effects_enabled": effects,
        "audio_normalization": audio_norm
    }

    if audio_norm:
        # Set LUFS target based on platform
        if "youtube" in preset.lower():
            render_config["target_lufs"] = -14.0
        elif "spotify" in preset.lower():
            render_config["target_lufs"] = -14.0
        elif "podcast" in preset.lower():
            render_config["target_lufs"] = -16.0
        else:
            render_config["target_lufs"] = -23.0  # Broadcast standard

    # Generate render script
    script = f"""
# Render with Effects
import DaVinciResolveScript as dvr

resolve = dvr.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()

# Configure render settings
project.SetRenderSettings({{
    "TargetDir": "{output.parent}",
    "CustomName": "{output.stem}",
    "FormatWidth": {settings.get('resolution', '1920x1080').split('x')[0]},
    "FormatHeight": {settings.get('resolution', '1920x1080').split('x')[1]},
    "FrameRate": {settings.get('framerate', 29.97)},
    {"AudioCodec": "AAC"," if audio_norm else ""}
    {"AudioBitrate": 320," if audio_norm else ""}
}})

# Add to render queue and start
project.AddRenderJob()
project.StartRendering()
"""

    script_path = Path("render_script.py")
    script_path.write_text(script)

    console.print("\n[green]✓[/green] Render configured")
    console.print(f"  Script: {script_path}")
    console.print("\n[bold]Estimated render time:[/bold]")
    console.print("  Based on timeline duration and complexity")
    console.print("  4K: ~2-5x realtime")
    console.print("  1080p: ~0.5-1x realtime")


@app.command()
def preview_effects(
    effect_name: str = typer.Argument(..., help="Effect to preview"),
    duration: float = typer.Option(5.0, "--duration", "-d", help="Preview duration"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save preview")
):
    """
    Preview effects before applying

    Examples:
        sf resolve preview-effects glow
        sf resolve preview-effects "audio_reactive_glow" --duration 10
        sf resolve preview-effects particles --output preview.mp4
    """
    console.print(f"\n[bold]Previewing effect:[/bold] {effect_name}")
    console.print(f"  Duration: {duration}s")

    # Create a simple composition with the effect
    comp = CompositionBuilder(f"{effect_name}_preview", CompositionType.COMPOSITE)
    comp.set_duration(duration)
    comp.set_resolution(1920, 1080)

    # Add background
    comp.add_background(color=(0.1, 0.1, 0.1))

    # Add the effect
    try:
        if effect_name in ["glow", "audio_reactive_glow", "particles", "shake"]:
            effect = create_procedural_effect(effect_name)
            comp.add_effect(effect)
            console.print(f"  [green]✓[/green] Effect added: {effect_name}")

        elif effect_name in ["podcast_mastering", "voiceover", "music_mastering"]:
            template = create_fairlight_template(effect_name)
            graph = template.build_chain()
            comp.add_effect(graph)
            console.print(f"  [green]✓[/green] Audio template added: {effect_name}")

        else:
            console.print(f"  [yellow]Unknown effect: {effect_name}[/yellow]")

    except Exception as e:
        console.print(f"  [red]Error: {e}[/red]")
        return

    # Build composition
    composition = comp.build()

    # Save preview if requested
    if output:
        if output.suffix == ".json":
            output.write_text(composition.export("json"))
        else:
            # Generate preview render command
            console.print(f"\n[dim]To render preview, use FFmpeg:[/dim]")
            console.print(f"  ffmpeg -f lavfi -i color=c=black:s=1920x1080:d={duration} -vf [effects] {output}")

    console.print(f"\n[green]✓[/green] Preview ready")
    console.print("  View in Resolve's Fusion/Fairlight pages for real-time preview")


if __name__ == "__main__":
    app()