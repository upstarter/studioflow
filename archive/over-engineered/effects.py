"""Effects management commands"""

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import json
import yaml

from studioflow.core.effects import (
    NodeGraph,
    TextPlusNode,
    GlowNode,
    ShakeNode,
    ParticlesNode,
    EQNode,
    CompressorNode,
    ReverbNode,
    DelayNode,
    ParameterAnimation,
    DataBinding,
    create_procedural_effect
)
from studioflow.core.composition import (
    Composition,
    CompositionType,
    CompositionLayer,
    EffectChain,
    CompositionBuilder
)
from studioflow.core.animation import (
    AnimationClip,
    AnimationCurve,
    AnimationLayer,
    InterpolationType,
    WaveAnimator,
    NoiseAnimator,
    ParticleAnimator
)
from studioflow.core.fairlight_templates import (
    create_fairlight_template,
    PodcastMasteringTemplate,
    VoiceOverTemplate,
    MusicMasteringTemplate
)

console = Console()
app = typer.Typer()


@app.command()
def list(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    effect_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type (fusion/fairlight/animation)")
):
    """
    List available effects and processors

    Examples:
        sf effects list
        sf effects list --type fusion
        sf effects list --category audio
    """
    table = Table(title="Available Effects")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Category", style="green")
    table.add_column("Description", style="white")

    # Fusion effects
    if not effect_type or effect_type == "fusion":
        fusion_effects = [
            ("text_plus", "fusion", "text", "Advanced text generator with animation"),
            ("glow", "fusion", "stylize", "Glow effect with customizable parameters"),
            ("shake", "fusion", "distort", "Camera shake simulation"),
            ("particles", "fusion", "generate", "Particle system generator"),
            ("radial_scanner", "fusion", "overlay", "HUD radial scanner effect"),
        ]
        for effect in fusion_effects:
            if not category or category in effect[2]:
                table.add_row(*effect)

    # Fairlight effects
    if not effect_type or effect_type == "fairlight":
        fairlight_effects = [
            ("eq", "fairlight", "audio", "Parametric equalizer"),
            ("compressor", "fairlight", "audio", "Dynamic range compressor"),
            ("reverb", "fairlight", "audio", "Reverb processor"),
            ("delay", "fairlight", "audio", "Delay/echo effect"),
            ("podcast_mastering", "fairlight", "template", "Complete podcast mastering chain"),
            ("voiceover", "fairlight", "template", "Voice-over processing"),
        ]
        for effect in fairlight_effects:
            if not category or category in effect[2]:
                table.add_row(*effect)

    # Animation effects
    if not effect_type or effect_type == "animation":
        animation_effects = [
            ("wave", "animation", "procedural", "Wave-based animation"),
            ("noise", "animation", "procedural", "Noise-based animation"),
            ("particles", "animation", "procedural", "Particle system animation"),
            ("bounce", "animation", "preset", "Bounce animation preset"),
            ("typewriter", "animation", "preset", "Typewriter text reveal"),
        ]
        for effect in animation_effects:
            if not category or category in effect[2]:
                table.add_row(*effect)

    console.print(table)


@app.command()
def apply(
    effect_name: str = typer.Argument(..., help="Effect name to apply"),
    input_file: Path = typer.Argument(..., help="Input media file"),
    output_file: Path = typer.Argument(..., help="Output file"),
    parameters: Optional[str] = typer.Option(None, "--params", "-p", help="Parameters as JSON string"),
    preset: Optional[str] = typer.Option(None, "--preset", help="Use preset configuration")
):
    """
    Apply an effect to media

    Examples:
        sf effects apply glow input.mp4 output.mp4 --params '{"intensity": 2.0}'
        sf effects apply podcast_mastering audio.wav mastered.wav --preset spotify
        sf effects apply text_plus video.mp4 titled.mp4 --params '{"text": "My Title"}'
    """
    if not input_file.exists():
        console.print(f"[red]Input file not found: {input_file}[/red]")
        raise typer.Exit(1)

    # Parse parameters
    params = json.loads(parameters) if parameters else {}

    console.print(f"\n[bold]Applying effect:[/bold] {effect_name}")
    console.print(f"Input: {input_file}")
    console.print(f"Output: {output_file}")

    try:
        # Create appropriate effect based on name
        if effect_name == "glow":
            graph = NodeGraph()
            glow = graph.add_node(GlowNode())
            glow.parameters.update(params)
            console.print("[green]✓[/green] Glow effect configured")

        elif effect_name == "text_plus":
            graph = NodeGraph()
            text = graph.add_node(TextPlusNode(text=params.get("text", "Text")))
            text.parameters.update(params)
            console.print("[green]✓[/green] Text overlay configured")

        elif effect_name == "shake":
            graph = NodeGraph()
            shake = graph.add_node(ShakeNode())
            shake.parameters.update(params)
            console.print("[green]✓[/green] Shake effect configured")

        elif effect_name == "particles":
            graph = NodeGraph()
            particles = graph.add_node(ParticlesNode())
            particles.parameters.update(params)
            console.print("[green]✓[/green] Particle system configured")

        elif effect_name in ["podcast_mastering", "voiceover", "music_mastering"]:
            template = create_fairlight_template(effect_name, **params)
            if preset:
                template.apply_preset(preset)
            console.print(f"[green]✓[/green] {effect_name} template configured")

        else:
            console.print(f"[red]Unknown effect: {effect_name}[/red]")
            raise typer.Exit(1)

        # In a real implementation, this would apply the effect using FFmpeg or Resolve API
        console.print("\n[yellow]Note: Effect application via FFmpeg/Resolve API not yet implemented[/yellow]")
        console.print("Effect configuration has been prepared for processing")

    except Exception as e:
        console.print(f"[red]Error applying effect: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def chain(
    config_file: Path = typer.Argument(..., help="Effect chain configuration file (JSON/YAML)"),
    input_file: Path = typer.Argument(..., help="Input media file"),
    output_file: Path = typer.Argument(..., help="Output file")
):
    """
    Apply a chain of effects from configuration

    Examples:
        sf effects chain effects.yaml input.mp4 output.mp4
        sf effects chain mastering.json podcast.wav final.wav
    """
    if not config_file.exists():
        console.print(f"[red]Config file not found: {config_file}[/red]")
        raise typer.Exit(1)

    if not input_file.exists():
        console.print(f"[red]Input file not found: {input_file}[/red]")
        raise typer.Exit(1)

    # Load configuration
    with open(config_file) as f:
        if config_file.suffix in ['.yaml', '.yml']:
            config = yaml.safe_load(f)
        else:
            config = json.load(f)

    console.print(f"\n[bold]Loading effect chain:[/bold] {config.get('name', 'Unnamed')}")

    # Create effect chain
    chain = EffectChain(config.get('name', 'chain'))

    # Add effects from config
    for effect_config in config.get('effects', []):
        effect_type = effect_config.get('type')
        params = effect_config.get('parameters', {})
        bypass = effect_config.get('bypass', False)

        console.print(f"  Adding: {effect_type} {'[dim](bypassed)[/dim]' if bypass else ''}")

        # Create appropriate effect
        # In real implementation, this would create actual effect nodes
        chain.add_effect(None, bypass)  # Placeholder

    console.print(f"\n[green]✓[/green] Effect chain loaded with {len(chain.effects)} effects")
    console.print("\n[yellow]Note: Chain processing via FFmpeg/Resolve API not yet implemented[/yellow]")


@app.command()
def compose(
    name: str = typer.Argument(..., help="Composition name"),
    duration: float = typer.Option(10.0, "--duration", "-d", help="Duration in seconds"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save composition to file"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Use composition template")
):
    """
    Create a new composition with effects

    Examples:
        sf effects compose "My Intro" --duration 5 --output intro.json
        sf effects compose "Title Card" --template lower_third
        sf effects compose "Transition" --duration 1 --template wipe
    """
    console.print(f"\n[bold]Creating composition:[/bold] {name}")

    # Create composition based on template
    if template == "lower_third":
        comp = CompositionBuilder(name, CompositionType.LOWER_THIRD)
        comp.set_duration(duration)
        comp.add_background(color=(0, 0, 0))
        comp.add_text("Name", position=(-300, -200, 0), font_size=32)
        comp.add_text("Title", position=(-300, -230, 0), font_size=24)
        composition = comp.build()
        console.print("[green]✓[/green] Lower third composition created")

    elif template == "title":
        comp = CompositionBuilder(name, CompositionType.TITLE)
        comp.set_duration(duration)
        comp.add_background(gradient={"type": "radial"})
        comp.add_text("TITLE", position=(0, 0, 0), font_size=72)
        composition = comp.build()
        console.print("[green]✓[/green] Title composition created")

    elif template == "wipe":
        comp = CompositionBuilder(name, CompositionType.TRANSITION)
        comp.set_duration(duration)
        composition = comp.build()
        console.print("[green]✓[/green] Wipe transition created")

    else:
        comp = CompositionBuilder(name, CompositionType.COMPOSITE)
        comp.set_duration(duration)
        composition = comp.build()
        console.print("[green]✓[/green] Blank composition created")

    # Display composition info
    console.print(f"  Duration: {composition.duration}s")
    console.print(f"  Resolution: {composition.resolution[0]}x{composition.resolution[1]}")
    console.print(f"  Layers: {len(composition.layers)}")

    # Save if requested
    if output:
        comp_data = composition.export(format="json" if output.suffix == ".json" else "yaml")
        output.write_text(comp_data)
        console.print(f"\n[green]✓[/green] Saved to: {output}")


@app.command()
def animate(
    property_name: str = typer.Argument(..., help="Property to animate"),
    start_value: float = typer.Argument(..., help="Start value"),
    end_value: float = typer.Argument(..., help="End value"),
    duration: float = typer.Option(1.0, "--duration", "-d", help="Animation duration"),
    curve: str = typer.Option("linear", "--curve", "-c", help="Interpolation curve"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save animation to file")
):
    """
    Create animation curves

    Examples:
        sf effects animate opacity 0 1 --duration 2 --curve ease_in_out
        sf effects animate position_x -100 100 --duration 5 --curve bounce
        sf effects animate scale 0.5 1.5 --curve elastic --output zoom.json
    """
    # Map curve names to interpolation types
    curve_map = {
        "linear": InterpolationType.LINEAR,
        "ease_in": InterpolationType.EASE_IN,
        "ease_out": InterpolationType.EASE_OUT,
        "ease_in_out": InterpolationType.EASE_IN_OUT,
        "bounce": InterpolationType.BOUNCE,
        "elastic": InterpolationType.ELASTIC,
        "back": InterpolationType.BACK,
        "circular": InterpolationType.CIRCULAR,
        "exponential": InterpolationType.EXPONENTIAL,
        "sine": InterpolationType.SINE
    }

    interp = curve_map.get(curve, InterpolationType.LINEAR)

    console.print(f"\n[bold]Creating animation:[/bold] {property_name}")
    console.print(f"  Range: {start_value} → {end_value}")
    console.print(f"  Duration: {duration}s")
    console.print(f"  Curve: {curve}")

    # Create animation curve
    anim_curve = AnimationCurve(property_name)
    anim_curve.add_keyframe(0, start_value, interp)
    anim_curve.add_keyframe(duration, end_value, InterpolationType.LINEAR)

    # Preview values
    console.print("\n[bold]Preview:[/bold]")
    for t in [0, 0.25, 0.5, 0.75, 1.0]:
        time = t * duration
        value = anim_curve.evaluate(time)
        console.print(f"  t={time:.2f}s: {value:.2f}")

    # Save if requested
    if output:
        anim_data = {
            "name": property_name,
            "keyframes": [
                {"time": 0, "value": start_value, "interpolation": curve},
                {"time": duration, "value": end_value, "interpolation": "linear"}
            ]
        }
        with open(output, 'w') as f:
            json.dump(anim_data, f, indent=2)
        console.print(f"\n[green]✓[/green] Saved to: {output}")


@app.command()
def preview(
    effect_name: str = typer.Argument(..., help="Effect to preview"),
    parameters: Optional[str] = typer.Option(None, "--params", "-p", help="Parameters as JSON")
):
    """
    Preview effect parameters and behavior

    Examples:
        sf effects preview glow
        sf effects preview podcast_mastering --params '{"target_lufs": -16}'
        sf effects preview particles
    """
    params = json.loads(parameters) if parameters else {}

    console.print(f"\n[bold]Effect Preview:[/bold] {effect_name}\n")

    if effect_name == "glow":
        panel = Panel(
            f"[bold]Glow Effect[/bold]\n\n"
            f"Parameters:\n"
            f"  • intensity: {params.get('intensity', 1.0)}\n"
            f"  • threshold: {params.get('threshold', 0.9)}\n"
            f"  • radius: {params.get('radius', 20)}\n"
            f"  • color: {params.get('color', [1, 1, 1])}\n\n"
            f"Description:\n"
            f"  Adds a glowing halo around bright areas.\n"
            f"  Useful for titles, highlights, and sci-fi effects.",
            border_style="cyan"
        )
        console.print(panel)

    elif effect_name == "podcast_mastering":
        panel = Panel(
            f"[bold]Podcast Mastering Chain[/bold]\n\n"
            f"Processing stages:\n"
            f"  1. Noise Gate (-40dB)\n"
            f"  2. High-pass Filter (80Hz)\n"
            f"  3. Parametric EQ (voice enhancement)\n"
            f"  4. De-esser (5-9kHz)\n"
            f"  5. Compressor (3:1 @ -18dB)\n"
            f"  6. Multiband Compressor\n"
            f"  7. Tape Saturation\n"
            f"  8. Limiter (-1dB ceiling)\n"
            f"  9. LUFS Meter (target: {params.get('target_lufs', -16)})\n\n"
            f"Presets: spotify, youtube, apple_podcasts",
            border_style="green"
        )
        console.print(panel)

    elif effect_name == "particles":
        panel = Panel(
            f"[bold]Particle System[/bold]\n\n"
            f"Parameters:\n"
            f"  • num_particles: {params.get('num_particles', 100)}\n"
            f"  • emission_rate: {params.get('emission_rate', 10)}/s\n"
            f"  • lifetime: {params.get('lifetime', 2.0)}s\n"
            f"  • gravity: {params.get('gravity', -9.8)}\n"
            f"  • spread: {params.get('spread', 45)}°\n\n"
            f"Description:\n"
            f"  Generates animated particle effects.\n"
            f"  Can be used for snow, rain, sparks, magic effects.",
            border_style="yellow"
        )
        console.print(panel)

    else:
        console.print(f"[yellow]Preview not available for: {effect_name}[/yellow]")


@app.command()
def benchmark(
    effect_name: str = typer.Argument(..., help="Effect to benchmark"),
    iterations: int = typer.Option(100, "--iterations", "-i", help="Number of iterations")
):
    """
    Benchmark effect performance

    Examples:
        sf effects benchmark glow --iterations 1000
        sf effects benchmark particles --iterations 100
    """
    import time

    console.print(f"\n[bold]Benchmarking:[/bold] {effect_name}")
    console.print(f"Iterations: {iterations}")

    # Create effect
    if effect_name == "glow":
        graph = NodeGraph()
        effect = graph.add_node(GlowNode())
    elif effect_name == "particles":
        effect = ParticleAnimator()
    else:
        console.print(f"[red]Cannot benchmark: {effect_name}[/red]")
        raise typer.Exit(1)

    # Run benchmark
    start = time.time()

    for i in track(range(iterations), description="Processing..."):
        if hasattr(effect, 'process'):
            effect.process({"input": None}, i / 30.0)
        elif hasattr(effect, 'generate'):
            effect.generate(i / 30.0, 1.0)

    elapsed = time.time() - start

    # Display results
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Total time: {elapsed:.3f}s")
    console.print(f"  Per iteration: {(elapsed/iterations)*1000:.2f}ms")
    console.print(f"  FPS equivalent: {iterations/elapsed:.1f}")


if __name__ == "__main__":
    app()