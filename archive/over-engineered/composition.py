"""
Effect Chain Composition System for StudioFlow
Combines templates, effects, and animations into reusable compositions
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import json
import yaml
from abc import ABC, abstractmethod

from studioflow.core.templates import Template, ComposableTemplate
from studioflow.core.effects import NodeGraph, Node, NodeID
from studioflow.core.animation import AnimationClip, AnimationController
from studioflow.core.fairlight_templates import FairlightTemplate


class CompositionType(Enum):
    """Types of compositions"""
    VIDEO_EFFECT = "video_effect"
    AUDIO_EFFECT = "audio_effect"
    TRANSITION = "transition"
    TITLE = "title"
    LOWER_THIRD = "lower_third"
    COLOR_GRADE = "color_grade"
    MOTION_GRAPHIC = "motion_graphic"
    COMPOSITE = "composite"


@dataclass
class CompositionLayer:
    """Single layer in a composition"""
    name: str
    type: str  # effect, animation, template, media
    content: Any  # Node, AnimationClip, Template, or media path
    blend_mode: str = "normal"
    opacity: float = 1.0
    transform: Dict[str, Any] = field(default_factory=lambda: {
        "position": [0, 0, 0],
        "rotation": [0, 0, 0],
        "scale": [1, 1, 1]
    })
    timing: Dict[str, float] = field(default_factory=lambda: {
        "start": 0,
        "duration": -1,  # -1 means full composition duration
        "offset": 0
    })
    enabled: bool = True
    locked: bool = False
    parent: Optional[str] = None  # Parent layer name for hierarchical transforms


class EffectChain:
    """Chain of effects to be applied sequentially"""

    def __init__(self, name: str):
        self.name = name
        self.effects: List[Union[Node, Template]] = []
        self.bypassed: List[bool] = []
        self.parameters: Dict[str, Dict[str, Any]] = {}

    def add_effect(self, effect: Union[Node, Template], bypass: bool = False):
        """Add effect to chain"""
        self.effects.append(effect)
        self.bypassed.append(bypass)

    def remove_effect(self, index: int):
        """Remove effect from chain"""
        if 0 <= index < len(self.effects):
            del self.effects[index]
            del self.bypassed[index]

    def set_bypass(self, index: int, bypass: bool):
        """Set bypass state for effect"""
        if 0 <= index < len(self.bypassed):
            self.bypassed[index] = bypass

    def set_parameter(self, effect_index: int, param_name: str, value: Any):
        """Set parameter for specific effect"""
        if 0 <= effect_index < len(self.effects):
            effect_key = f"effect_{effect_index}"
            if effect_key not in self.parameters:
                self.parameters[effect_key] = {}
            self.parameters[effect_key][param_name] = value

    def process(self, input_data: Any, time: float = 0) -> Any:
        """Process input through effect chain"""
        result = input_data

        for i, effect in enumerate(self.effects):
            if not self.bypassed[i]:
                effect_key = f"effect_{i}"
                params = self.parameters.get(effect_key, {})

                if isinstance(effect, Node):
                    # Apply node parameters
                    for param, value in params.items():
                        if hasattr(effect, 'parameters'):
                            effect.parameters[param] = value

                    result = effect.process({"input": result}, time).get("output", result)

                elif isinstance(effect, Template):
                    # Apply template with context
                    context = {"input": result, "time": time, **params}
                    result = effect.apply(context)

        return result


class Composition:
    """Main composition class combining layers, effects, and animations"""

    def __init__(self, name: str, composition_type: CompositionType,
                 duration: float = 10.0, resolution: Tuple[int, int] = (1920, 1080)):
        self.name = name
        self.type = composition_type
        self.duration = duration
        self.resolution = resolution
        self.framerate = 29.97
        self.layers: List[CompositionLayer] = []
        self.effect_chains: Dict[str, EffectChain] = {}
        self.animations: Dict[str, AnimationController] = {}
        self.metadata: Dict[str, Any] = {}
        self.markers: List[Tuple[float, str, str]] = []  # time, name, comment
        self.cache: Dict[str, Any] = {}

    def add_layer(self, layer: CompositionLayer) -> int:
        """Add layer to composition"""
        self.layers.append(layer)
        return len(self.layers) - 1

    def remove_layer(self, index: int):
        """Remove layer from composition"""
        if 0 <= index < len(self.layers):
            del self.layers[index]

    def reorder_layers(self, from_index: int, to_index: int):
        """Reorder layers"""
        if 0 <= from_index < len(self.layers) and 0 <= to_index < len(self.layers):
            layer = self.layers.pop(from_index)
            self.layers.insert(to_index, layer)

    def add_effect_chain(self, name: str, chain: EffectChain):
        """Add named effect chain"""
        self.effect_chains[name] = chain

    def add_animation(self, name: str, controller: AnimationController):
        """Add animation controller"""
        self.animations[name] = controller

    def add_marker(self, time: float, name: str, comment: str = ""):
        """Add timeline marker"""
        self.markers.append((time, name, comment))
        self.markers.sort(key=lambda m: m[0])

    def evaluate(self, time: float, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate composition at given time"""
        if context is None:
            context = {}

        # Check cache
        cache_key = f"{time}_{hash(frozenset(context.items()))}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = {
            "layers": [],
            "audio": None,
            "metadata": self.metadata.copy()
        }

        # Update animations
        for anim_name, controller in self.animations.items():
            anim_result = controller.update(time)
            context[f"anim_{anim_name}"] = anim_result

        # Process layers
        for layer in self.layers:
            if not layer.enabled:
                continue

            # Check timing
            if layer.timing["start"] <= time:
                if layer.timing["duration"] < 0 or \
                   time < layer.timing["start"] + layer.timing["duration"]:

                    layer_result = self._process_layer(layer, time, context)
                    result["layers"].append(layer_result)

        # Apply post-processing effect chains
        for chain_name, chain in self.effect_chains.items():
            if chain_name.startswith("post_"):
                result = chain.process(result, time)

        # Cache result
        self.cache[cache_key] = result

        return result

    def _process_layer(self, layer: CompositionLayer, time: float,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual layer"""
        layer_time = time - layer.timing["start"] + layer.timing["offset"]

        result = {
            "name": layer.name,
            "type": layer.type,
            "blend_mode": layer.blend_mode,
            "opacity": layer.opacity,
            "transform": layer.transform.copy()
        }

        # Apply parent transform if exists
        if layer.parent:
            parent_layer = next((l for l in self.layers if l.name == layer.parent), None)
            if parent_layer:
                result["transform"] = self._combine_transforms(
                    parent_layer.transform,
                    layer.transform
                )

        # Process content based on type
        if layer.type == "effect":
            if isinstance(layer.content, Node):
                result["output"] = layer.content.process({"time": layer_time}, layer_time)
            elif isinstance(layer.content, NodeGraph):
                result["output"] = layer.content.process({"time": layer_time}, layer_time)

        elif layer.type == "animation":
            if isinstance(layer.content, AnimationClip):
                result["output"] = layer.content.evaluate(layer_time, context)

        elif layer.type == "template":
            if isinstance(layer.content, Template):
                template_context = {**context, "time": layer_time}
                result["output"] = layer.content.apply(template_context)

        elif layer.type == "media":
            result["source"] = layer.content  # Path to media file
            result["time_offset"] = layer_time

        return result

    def _combine_transforms(self, parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        """Combine parent and child transforms"""
        combined = {}

        # Add positions
        combined["position"] = [
            parent["position"][i] + child["position"][i]
            for i in range(3)
        ]

        # Add rotations
        combined["rotation"] = [
            parent["rotation"][i] + child["rotation"][i]
            for i in range(3)
        ]

        # Multiply scales
        combined["scale"] = [
            parent["scale"][i] * child["scale"][i]
            for i in range(3)
        ]

        return combined

    def export(self, format: str = "json") -> str:
        """Export composition to JSON or YAML"""
        data = {
            "name": self.name,
            "type": self.type.value,
            "duration": self.duration,
            "resolution": self.resolution,
            "framerate": self.framerate,
            "layers": [self._layer_to_dict(l) for l in self.layers],
            "metadata": self.metadata,
            "markers": [{"time": m[0], "name": m[1], "comment": m[2]} for m in self.markers]
        }

        if format == "json":
            return json.dumps(data, indent=2)
        elif format == "yaml":
            return yaml.dump(data, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _layer_to_dict(self, layer: CompositionLayer) -> Dict[str, Any]:
        """Convert layer to dictionary"""
        return {
            "name": layer.name,
            "type": layer.type,
            "blend_mode": layer.blend_mode,
            "opacity": layer.opacity,
            "transform": layer.transform,
            "timing": layer.timing,
            "enabled": layer.enabled,
            "locked": layer.locked,
            "parent": layer.parent
        }

    @classmethod
    def from_file(cls, file_path: Path) -> "Composition":
        """Load composition from file"""
        with open(file_path) as f:
            if file_path.suffix == ".json":
                data = json.load(f)
            elif file_path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

        comp = cls(
            name=data["name"],
            composition_type=CompositionType(data["type"]),
            duration=data.get("duration", 10.0),
            resolution=tuple(data.get("resolution", [1920, 1080]))
        )

        comp.framerate = data.get("framerate", 29.97)
        comp.metadata = data.get("metadata", {})

        # Load layers
        for layer_data in data.get("layers", []):
            layer = CompositionLayer(
                name=layer_data["name"],
                type=layer_data["type"],
                content=None,  # Content needs to be loaded separately
                blend_mode=layer_data.get("blend_mode", "normal"),
                opacity=layer_data.get("opacity", 1.0),
                transform=layer_data.get("transform", {}),
                timing=layer_data.get("timing", {}),
                enabled=layer_data.get("enabled", True),
                locked=layer_data.get("locked", False),
                parent=layer_data.get("parent")
            )
            comp.add_layer(layer)

        # Load markers
        for marker_data in data.get("markers", []):
            comp.add_marker(
                marker_data["time"],
                marker_data["name"],
                marker_data.get("comment", "")
            )

        return comp


class CompositionPresets:
    """Library of composition presets"""

    @staticmethod
    def title_sequence() -> Composition:
        """Create title sequence composition"""
        comp = Composition("Title Sequence", CompositionType.TITLE, duration=5.0)

        # Background layer
        bg_layer = CompositionLayer(
            name="background",
            type="effect",
            content=None,  # Would be a gradient or solid color node
            opacity=1.0
        )
        comp.add_layer(bg_layer)

        # Title text layer
        title_layer = CompositionLayer(
            name="title",
            type="effect",
            content=None,  # Would be a text node
            blend_mode="normal",
            transform={"position": [0, 0, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1]},
            timing={"start": 0.5, "duration": 4.0, "offset": 0}
        )
        comp.add_layer(title_layer)

        # Subtitle layer
        subtitle_layer = CompositionLayer(
            name="subtitle",
            type="effect",
            content=None,  # Would be another text node
            opacity=0.8,
            transform={"position": [0, -50, 0], "rotation": [0, 0, 0], "scale": [0.8, 0.8, 1]},
            timing={"start": 1.0, "duration": 3.5, "offset": 0}
        )
        comp.add_layer(subtitle_layer)

        return comp

    @staticmethod
    def lower_third() -> Composition:
        """Create lower third composition"""
        comp = Composition("Lower Third", CompositionType.LOWER_THIRD, duration=10.0)

        # Background bar
        bg_bar = CompositionLayer(
            name="background_bar",
            type="effect",
            content=None,  # Would be a rectangle shape node
            blend_mode="normal",
            opacity=0.9,
            transform={"position": [-300, -200, 0], "rotation": [0, 0, 0], "scale": [1, 0.15, 1]}
        )
        comp.add_layer(bg_bar)

        # Name text
        name_layer = CompositionLayer(
            name="name_text",
            type="effect",
            content=None,  # Would be a text node
            transform={"position": [-280, -190, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1]},
            parent="background_bar"
        )
        comp.add_layer(name_layer)

        # Title text
        title_layer = CompositionLayer(
            name="title_text",
            type="effect",
            content=None,  # Would be a text node
            opacity=0.8,
            transform={"position": [-280, -210, 0], "rotation": [0, 0, 0], "scale": [0.8, 0.8, 1]},
            parent="background_bar"
        )
        comp.add_layer(title_layer)

        return comp

    @staticmethod
    def transition_wipe() -> Composition:
        """Create wipe transition composition"""
        comp = Composition("Wipe Transition", CompositionType.TRANSITION, duration=1.0)

        # Wipe mask layer
        wipe_layer = CompositionLayer(
            name="wipe_mask",
            type="effect",
            content=None,  # Would be a gradient wipe node
            blend_mode="multiply",
            timing={"start": 0, "duration": 1.0, "offset": 0}
        )
        comp.add_layer(wipe_layer)

        return comp

    @staticmethod
    def motion_graphic() -> Composition:
        """Create motion graphic composition"""
        comp = Composition("Motion Graphic", CompositionType.MOTION_GRAPHIC, duration=10.0)

        # Animated background
        bg_layer = CompositionLayer(
            name="animated_bg",
            type="animation",
            content=None,  # Would be an AnimationClip
            blend_mode="normal"
        )
        comp.add_layer(bg_layer)

        # Particle system
        particles_layer = CompositionLayer(
            name="particles",
            type="effect",
            content=None,  # Would be a particle system node
            blend_mode="add",
            opacity=0.5
        )
        comp.add_layer(particles_layer)

        # Logo
        logo_layer = CompositionLayer(
            name="logo",
            type="media",
            content="logo.png",
            transform={"position": [0, 0, 10], "rotation": [0, 0, 0], "scale": [1, 1, 1]}
        )
        comp.add_layer(logo_layer)

        # Text elements
        for i in range(3):
            text_layer = CompositionLayer(
                name=f"text_{i}",
                type="effect",
                content=None,  # Would be text nodes
                timing={"start": i * 2, "duration": 3.0, "offset": 0}
            )
            comp.add_layer(text_layer)

        return comp


class CompositionBuilder:
    """Builder pattern for creating complex compositions"""

    def __init__(self, name: str, composition_type: CompositionType):
        self.composition = Composition(name, composition_type)
        self.current_time = 0

    def set_duration(self, duration: float) -> "CompositionBuilder":
        """Set composition duration"""
        self.composition.duration = duration
        return self

    def set_resolution(self, width: int, height: int) -> "CompositionBuilder":
        """Set composition resolution"""
        self.composition.resolution = (width, height)
        return self

    def add_background(self, color: Optional[Tuple[float, float, float]] = None,
                       gradient: Optional[Dict[str, Any]] = None) -> "CompositionBuilder":
        """Add background layer"""
        bg_layer = CompositionLayer(
            name="background",
            type="effect",
            content={"color": color, "gradient": gradient},
            timing={"start": 0, "duration": self.composition.duration, "offset": 0}
        )
        self.composition.add_layer(bg_layer)
        return self

    def add_text(self, text: str, position: Tuple[float, float, float] = (0, 0, 0),
                font_size: float = 24, duration: float = -1) -> "CompositionBuilder":
        """Add text layer"""
        text_layer = CompositionLayer(
            name=f"text_{len(self.composition.layers)}",
            type="effect",
            content={"text": text, "font_size": font_size},
            transform={"position": list(position), "rotation": [0, 0, 0], "scale": [1, 1, 1]},
            timing={"start": self.current_time, "duration": duration, "offset": 0}
        )
        self.composition.add_layer(text_layer)
        return self

    def add_image(self, path: str, position: Tuple[float, float, float] = (0, 0, 0),
                 scale: float = 1.0) -> "CompositionBuilder":
        """Add image layer"""
        img_layer = CompositionLayer(
            name=f"image_{len(self.composition.layers)}",
            type="media",
            content=path,
            transform={
                "position": list(position),
                "rotation": [0, 0, 0],
                "scale": [scale, scale, 1]
            }
        )
        self.composition.add_layer(img_layer)
        return self

    def add_effect(self, effect: Union[Node, EffectChain],
                  blend_mode: str = "normal") -> "CompositionBuilder":
        """Add effect layer"""
        effect_layer = CompositionLayer(
            name=f"effect_{len(self.composition.layers)}",
            type="effect",
            content=effect,
            blend_mode=blend_mode
        )
        self.composition.add_layer(effect_layer)
        return self

    def add_animation(self, animation: AnimationClip,
                     start_time: float = None) -> "CompositionBuilder":
        """Add animation layer"""
        if start_time is None:
            start_time = self.current_time

        anim_layer = CompositionLayer(
            name=f"animation_{len(self.composition.layers)}",
            type="animation",
            content=animation,
            timing={"start": start_time, "duration": animation.duration, "offset": 0}
        )
        self.composition.add_layer(anim_layer)
        return self

    def add_transition(self, transition_type: str,
                      duration: float = 1.0) -> "CompositionBuilder":
        """Add transition at current time"""
        # Implementation would add appropriate transition effect
        self.current_time += duration
        return self

    def seek(self, time: float) -> "CompositionBuilder":
        """Set current time position"""
        self.current_time = time
        return self

    def build(self) -> Composition:
        """Build and return the composition"""
        return self.composition


# Export functions
def export_to_resolve(composition: Composition, output_path: Path) -> bool:
    """Export composition to DaVinci Resolve format"""
    # Generate Resolve Python API script
    script = f"""
#!/usr/bin/env python3
# Generated by StudioFlow
# Composition: {composition.name}

import DaVinciResolveScript as dvr

resolve = dvr.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()
timeline = project.GetCurrentTimeline()

# Set timeline properties
timeline.SetSetting("timelineFrameRate", "{composition.framerate}")
timeline.SetSetting("timelineResolutionWidth", "{composition.resolution[0]}")
timeline.SetSetting("timelineResolutionHeight", "{composition.resolution[1]}")

# Add layers as tracks
"""

    for i, layer in enumerate(composition.layers):
        script += f"""
# Layer {i}: {layer.name}
track = timeline.AddTrack("video")
"""

    output_path.write_text(script)
    return True


def export_to_edl(composition: Composition, output_path: Path) -> bool:
    """Export composition to EDL format"""
    # Generate EDL file for timeline exchange
    edl_content = f"""TITLE: {composition.name}
FCM: NON-DROP FRAME

"""

    for i, layer in enumerate(composition.layers, 1):
        # Format: edit_number reel_name channel trans duration source_in source_out record_in record_out
        start = layer.timing["start"]
        duration = layer.timing["duration"] if layer.timing["duration"] > 0 else composition.duration

        edl_content += f"{i:03d}  {layer.name[:8]:<8} V     C        "
        edl_content += f"{start:011.2f} {start+duration:011.2f} "
        edl_content += f"{start:011.2f} {start+duration:011.2f}\n"
        edl_content += f"* FROM CLIP NAME: {layer.name}\n\n"

    output_path.write_text(edl_content)
    return True


def export_to_fcpxml(composition: Composition, output_path: Path) -> bool:
    """Export composition to Final Cut Pro XML"""
    # Generate FCPXML for Final Cut Pro
    import xml.etree.ElementTree as ET

    # Create FCPXML structure
    fcpxml = ET.Element("fcpxml", version="1.9")
    resources = ET.SubElement(fcpxml, "resources")
    library = ET.SubElement(fcpxml, "library")
    event = ET.SubElement(library, "event", name=composition.name)
    project = ET.SubElement(event, "project", name=composition.name)
    sequence = ET.SubElement(project, "sequence",
                            duration=f"{composition.duration}s",
                            format=f"r{int(composition.framerate)}")
    spine = ET.SubElement(sequence, "spine")

    # Add layers as clips
    for layer in composition.layers:
        if layer.enabled:
            clip = ET.SubElement(spine, "clip",
                                name=layer.name,
                                offset=f"{layer.timing['start']}s",
                                duration=f"{layer.timing['duration']}s")

    # Write XML
    tree = ET.ElementTree(fcpxml)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)
    return True