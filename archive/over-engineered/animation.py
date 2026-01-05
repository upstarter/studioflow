"""
Procedural Animation System for StudioFlow
Provides keyframe animation, procedural generation, and expression-based animation
"""

from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
import random
from pathlib import Path
import numpy as np
from abc import ABC, abstractmethod


class InterpolationType(Enum):
    """Animation interpolation types"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    CUBIC = "cubic"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    BACK = "back"
    CIRCULAR = "circular"
    EXPONENTIAL = "exponential"
    SINE = "sine"
    HOLD = "hold"
    CUSTOM = "custom"


@dataclass
class Keyframe:
    """Single keyframe in animation"""
    time: float
    value: Any
    interpolation: InterpolationType = InterpolationType.LINEAR
    tension: float = 0.0
    bias: float = 0.0
    continuity: float = 0.0
    handle_in: Optional[Tuple[float, float]] = None
    handle_out: Optional[Tuple[float, float]] = None


@dataclass
class AnimationCurve:
    """Animation curve with keyframes"""
    name: str
    keyframes: List[Keyframe] = field(default_factory=list)
    pre_infinity: str = "constant"  # constant, linear, cycle, cycle_offset, oscillate
    post_infinity: str = "constant"
    expression: Optional[str] = None

    def add_keyframe(self, time: float, value: Any, interpolation: InterpolationType = InterpolationType.LINEAR):
        """Add a keyframe to the curve"""
        kf = Keyframe(time, value, interpolation)
        self.keyframes.append(kf)
        self.keyframes.sort(key=lambda k: k.time)
        return kf

    def evaluate(self, time: float, context: Dict[str, Any] = None) -> Any:
        """Evaluate curve at given time"""
        if self.expression:
            return self._evaluate_expression(time, context)

        if not self.keyframes:
            return None

        # Handle pre/post infinity
        if time < self.keyframes[0].time:
            return self._handle_pre_infinity(time)
        if time > self.keyframes[-1].time:
            return self._handle_post_infinity(time)

        # Find surrounding keyframes
        for i in range(len(self.keyframes) - 1):
            if self.keyframes[i].time <= time <= self.keyframes[i + 1].time:
                return self._interpolate(
                    self.keyframes[i],
                    self.keyframes[i + 1],
                    time
                )

        return self.keyframes[-1].value

    def _interpolate(self, kf1: Keyframe, kf2: Keyframe, time: float) -> Any:
        """Interpolate between two keyframes"""
        t = (time - kf1.time) / (kf2.time - kf1.time) if kf2.time != kf1.time else 0

        if kf1.interpolation == InterpolationType.HOLD:
            return kf1.value

        # Get interpolation function
        interp_func = self._get_interpolation_function(kf1.interpolation)
        t = interp_func(t)

        # Interpolate based on value type
        if isinstance(kf1.value, (int, float)):
            return kf1.value + (kf2.value - kf1.value) * t
        elif isinstance(kf1.value, (list, tuple)):
            return [
                kf1.value[i] + (kf2.value[i] - kf1.value[i]) * t
                for i in range(len(kf1.value))
            ]
        elif isinstance(kf1.value, dict):
            return {
                key: kf1.value[key] + (kf2.value[key] - kf1.value[key]) * t
                for key in kf1.value if key in kf2.value
            }
        else:
            return kf1.value if t < 0.5 else kf2.value

    def _get_interpolation_function(self, interp_type: InterpolationType) -> Callable[[float], float]:
        """Get interpolation function for type"""
        functions = {
            InterpolationType.LINEAR: lambda t: t,
            InterpolationType.EASE_IN: lambda t: t * t,
            InterpolationType.EASE_OUT: lambda t: t * (2 - t),
            InterpolationType.EASE_IN_OUT: lambda t: t * t * (3 - 2 * t),
            InterpolationType.CUBIC: lambda t: t * t * t,
            InterpolationType.BOUNCE: self._bounce_ease,
            InterpolationType.ELASTIC: self._elastic_ease,
            InterpolationType.BACK: lambda t: t * t * (2.7 * t - 1.7),
            InterpolationType.CIRCULAR: lambda t: 1 - math.sqrt(1 - t * t),
            InterpolationType.EXPONENTIAL: lambda t: 0 if t == 0 else 2 ** (10 * (t - 1)),
            InterpolationType.SINE: lambda t: 1 - math.cos(t * math.pi / 2)
        }
        return functions.get(interp_type, lambda t: t)

    def _bounce_ease(self, t: float) -> float:
        """Bounce easing function"""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375

    def _elastic_ease(self, t: float) -> float:
        """Elastic easing function"""
        if t == 0 or t == 1:
            return t
        p = 0.3
        s = p / 4
        return -(2 ** (10 * (t - 1)) * math.sin((t - 1 - s) * (2 * math.pi) / p))

    def _evaluate_expression(self, time: float, context: Dict[str, Any]) -> Any:
        """Evaluate mathematical expression"""
        # Safe evaluation context
        safe_dict = {
            "t": time,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "abs": abs,
            "min": min,
            "max": max,
            "sqrt": math.sqrt,
            "pow": pow,
            "pi": math.pi,
            "e": math.e,
            "random": random.random,
            "noise": lambda x: self._perlin_noise(x)
        }

        if context:
            safe_dict.update(context)

        try:
            return eval(self.expression, {"__builtins__": {}}, safe_dict)
        except Exception:
            return 0

    def _perlin_noise(self, x: float) -> float:
        """Simple Perlin noise implementation"""
        # Simplified noise function
        return math.sin(x * 0.1) * math.cos(x * 0.05) * 0.5 + 0.5

    def _handle_pre_infinity(self, time: float) -> Any:
        """Handle time before first keyframe"""
        if self.pre_infinity == "constant":
            return self.keyframes[0].value
        elif self.pre_infinity == "linear":
            if len(self.keyframes) >= 2:
                slope = (self.keyframes[1].value - self.keyframes[0].value) / \
                       (self.keyframes[1].time - self.keyframes[0].time)
                return self.keyframes[0].value - slope * (self.keyframes[0].time - time)
        elif self.pre_infinity == "cycle":
            duration = self.keyframes[-1].time - self.keyframes[0].time
            if duration > 0:
                normalized_time = self.keyframes[0].time + (time % duration)
                return self.evaluate(normalized_time)
        return self.keyframes[0].value

    def _handle_post_infinity(self, time: float) -> Any:
        """Handle time after last keyframe"""
        if self.post_infinity == "constant":
            return self.keyframes[-1].value
        elif self.post_infinity == "linear":
            if len(self.keyframes) >= 2:
                slope = (self.keyframes[-1].value - self.keyframes[-2].value) / \
                       (self.keyframes[-1].time - self.keyframes[-2].time)
                return self.keyframes[-1].value + slope * (time - self.keyframes[-1].time)
        elif self.post_infinity == "cycle":
            duration = self.keyframes[-1].time - self.keyframes[0].time
            if duration > 0:
                offset = time - self.keyframes[-1].time
                normalized_time = self.keyframes[0].time + (offset % duration)
                return self.evaluate(normalized_time)
        return self.keyframes[-1].value


class AnimationLayer:
    """Layer for compositing multiple animations"""

    def __init__(self, name: str, blend_mode: str = "normal", opacity: float = 1.0):
        self.name = name
        self.blend_mode = blend_mode
        self.opacity = opacity
        self.curves: Dict[str, AnimationCurve] = {}
        self.enabled = True
        self.solo = False
        self.muted = False

    def add_curve(self, property_name: str, curve: AnimationCurve):
        """Add animation curve for property"""
        self.curves[property_name] = curve

    def evaluate(self, time: float, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate all curves at given time"""
        if self.muted or not self.enabled:
            return {}

        result = {}
        for prop, curve in self.curves.items():
            result[prop] = curve.evaluate(time, context)

        return result


class AnimationClip:
    """Container for animation data"""

    def __init__(self, name: str, duration: float):
        self.name = name
        self.duration = duration
        self.layers: List[AnimationLayer] = []
        self.markers: List[Tuple[float, str]] = []
        self.events: List[Tuple[float, Callable]] = []

    def add_layer(self, layer: AnimationLayer):
        """Add animation layer"""
        self.layers.append(layer)

    def add_marker(self, time: float, label: str):
        """Add named marker"""
        self.markers.append((time, label))
        self.markers.sort(key=lambda m: m[0])

    def add_event(self, time: float, callback: Callable):
        """Add timed event callback"""
        self.events.append((time, callback))
        self.events.sort(key=lambda e: e[0])

    def evaluate(self, time: float, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate all layers at given time"""
        result = {}

        # Process solo layers first
        solo_layers = [l for l in self.layers if l.solo and l.enabled]
        if solo_layers:
            for layer in solo_layers:
                layer_result = layer.evaluate(time, context)
                result = self._blend_results(result, layer_result, layer.blend_mode, layer.opacity)
        else:
            # Process all enabled layers
            for layer in self.layers:
                if layer.enabled and not layer.muted:
                    layer_result = layer.evaluate(time, context)
                    result = self._blend_results(result, layer_result, layer.blend_mode, layer.opacity)

        # Trigger events
        for event_time, callback in self.events:
            if abs(time - event_time) < 0.01:  # Within threshold
                callback(time, result)

        return result

    def _blend_results(self, base: Dict[str, Any], layer: Dict[str, Any],
                       mode: str, opacity: float) -> Dict[str, Any]:
        """Blend layer results based on mode"""
        result = base.copy()

        for key, value in layer.items():
            if key not in result:
                result[key] = value * opacity if isinstance(value, (int, float)) else value
            else:
                if mode == "normal":
                    result[key] = self._lerp(result[key], value, opacity)
                elif mode == "add":
                    result[key] = result[key] + value * opacity
                elif mode == "multiply":
                    result[key] = result[key] * (1 + (value - 1) * opacity)
                elif mode == "screen":
                    result[key] = 1 - (1 - result[key]) * (1 - value * opacity)
                elif mode == "overlay":
                    if result[key] < 0.5:
                        result[key] = 2 * result[key] * value * opacity
                    else:
                        result[key] = 1 - 2 * (1 - result[key]) * (1 - value * opacity)

        return result

    def _lerp(self, a: Any, b: Any, t: float) -> Any:
        """Linear interpolation"""
        if isinstance(a, (int, float)):
            return a + (b - a) * t
        return b if t > 0.5 else a


class ProceduralAnimator(ABC):
    """Base class for procedural animators"""

    def __init__(self, name: str):
        self.name = name
        self.parameters: Dict[str, Any] = {}

    @abstractmethod
    def generate(self, time: float, duration: float) -> Dict[str, Any]:
        """Generate animation values"""
        pass


class WaveAnimator(ProceduralAnimator):
    """Wave-based procedural animation"""

    def __init__(self, name: str = "wave"):
        super().__init__(name)
        self.parameters = {
            "amplitude": 1.0,
            "frequency": 1.0,
            "phase": 0.0,
            "offset": 0.0,
            "wave_type": "sine"  # sine, square, triangle, sawtooth
        }

    def generate(self, time: float, duration: float) -> Dict[str, Any]:
        """Generate wave animation"""
        amp = self.parameters["amplitude"]
        freq = self.parameters["frequency"]
        phase = self.parameters["phase"]
        offset = self.parameters["offset"]
        wave_type = self.parameters["wave_type"]

        t = time * freq + phase

        if wave_type == "sine":
            value = math.sin(t * 2 * math.pi) * amp + offset
        elif wave_type == "square":
            value = (1 if math.sin(t * 2 * math.pi) > 0 else -1) * amp + offset
        elif wave_type == "triangle":
            value = (2 * abs(2 * (t - math.floor(t + 0.5))) - 1) * amp + offset
        elif wave_type == "sawtooth":
            value = (2 * (t - math.floor(t)) - 1) * amp + offset
        else:
            value = offset

        return {"value": value}


class NoiseAnimator(ProceduralAnimator):
    """Noise-based procedural animation"""

    def __init__(self, name: str = "noise"):
        super().__init__(name)
        self.parameters = {
            "amplitude": 1.0,
            "frequency": 1.0,
            "octaves": 3,
            "persistence": 0.5,
            "seed": 42,
            "noise_type": "perlin"  # perlin, simplex, worley
        }

    def generate(self, time: float, duration: float) -> Dict[str, Any]:
        """Generate noise animation"""
        amp = self.parameters["amplitude"]
        freq = self.parameters["frequency"]
        octaves = self.parameters["octaves"]
        persistence = self.parameters["persistence"]

        value = 0
        max_value = 0
        amplitude = 1

        for i in range(octaves):
            value += self._noise(time * freq * (2 ** i)) * amplitude
            max_value += amplitude
            amplitude *= persistence

        value = (value / max_value) * amp

        return {"value": value}

    def _noise(self, x: float) -> float:
        """Simple noise function"""
        # Simplified implementation
        return math.sin(x * 12.9898) * math.cos(x * 78.233) * 0.5 + 0.5


class PhysicsAnimator(ProceduralAnimator):
    """Physics-based procedural animation"""

    def __init__(self, name: str = "physics"):
        super().__init__(name)
        self.parameters = {
            "gravity": -9.8,
            "mass": 1.0,
            "damping": 0.1,
            "stiffness": 10.0,
            "initial_velocity": [0, 0, 0],
            "initial_position": [0, 0, 0]
        }
        self.state = {
            "position": [0, 0, 0],
            "velocity": [0, 0, 0],
            "acceleration": [0, 0, 0]
        }

    def generate(self, time: float, duration: float) -> Dict[str, Any]:
        """Generate physics-based animation"""
        dt = 1.0 / 30.0  # Assume 30 fps

        # Spring force
        k = self.parameters["stiffness"]
        c = self.parameters["damping"]
        m = self.parameters["mass"]

        # Calculate forces
        spring_force = [-k * p for p in self.state["position"]]
        damping_force = [-c * v for v in self.state["velocity"]]
        gravity_force = [0, self.parameters["gravity"] * m, 0]

        # Total force
        total_force = [
            spring_force[i] + damping_force[i] + gravity_force[i]
            for i in range(3)
        ]

        # Update acceleration
        self.state["acceleration"] = [f / m for f in total_force]

        # Update velocity and position
        for i in range(3):
            self.state["velocity"][i] += self.state["acceleration"][i] * dt
            self.state["position"][i] += self.state["velocity"][i] * dt

        return {
            "position": self.state["position"].copy(),
            "velocity": self.state["velocity"].copy()
        }


class ParticleAnimator(ProceduralAnimator):
    """Particle system animator"""

    def __init__(self, name: str = "particles"):
        super().__init__(name)
        self.parameters = {
            "num_particles": 100,
            "emission_rate": 10,
            "lifetime": 2.0,
            "start_size": 1.0,
            "end_size": 0.1,
            "start_speed": 5.0,
            "spread_angle": 45.0,
            "gravity": -9.8,
            "wind": [0, 0, 0]
        }
        self.particles: List[Dict[str, Any]] = []

    def generate(self, time: float, duration: float) -> Dict[str, Any]:
        """Generate particle animation"""
        dt = 1.0 / 30.0

        # Emit new particles
        emission_rate = self.parameters["emission_rate"]
        num_to_emit = int(emission_rate * dt)

        for _ in range(num_to_emit):
            if len(self.particles) < self.parameters["num_particles"]:
                self._emit_particle(time)

        # Update existing particles
        alive_particles = []
        for particle in self.particles:
            particle["age"] += dt

            if particle["age"] < particle["lifetime"]:
                # Update physics
                particle["velocity"][1] += self.parameters["gravity"] * dt

                # Apply wind
                for i in range(3):
                    particle["velocity"][i] += self.parameters["wind"][i] * dt

                # Update position
                for i in range(3):
                    particle["position"][i] += particle["velocity"][i] * dt

                # Update size
                t = particle["age"] / particle["lifetime"]
                particle["size"] = self._lerp(
                    self.parameters["start_size"],
                    self.parameters["end_size"],
                    t
                )

                alive_particles.append(particle)

        self.particles = alive_particles

        return {
            "particles": [
                {
                    "position": p["position"],
                    "size": p["size"],
                    "age": p["age"],
                    "lifetime": p["lifetime"]
                }
                for p in self.particles
            ]
        }

    def _emit_particle(self, time: float):
        """Emit a new particle"""
        angle = random.uniform(-self.parameters["spread_angle"], self.parameters["spread_angle"])
        angle_rad = math.radians(angle)

        speed = self.parameters["start_speed"] * random.uniform(0.8, 1.2)

        particle = {
            "position": [0, 0, 0],
            "velocity": [
                speed * math.sin(angle_rad),
                speed * math.cos(angle_rad),
                random.uniform(-1, 1) * speed * 0.1
            ],
            "size": self.parameters["start_size"],
            "age": 0,
            "lifetime": self.parameters["lifetime"] * random.uniform(0.8, 1.2),
            "birth_time": time
        }

        self.particles.append(particle)

    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation"""
        return a + (b - a) * t


class AnimationMixer:
    """Mix multiple animation clips"""

    def __init__(self):
        self.clips: Dict[str, AnimationClip] = {}
        self.weights: Dict[str, float] = {}
        self.transitions: List[Dict[str, Any]] = []

    def add_clip(self, clip: AnimationClip, weight: float = 1.0):
        """Add animation clip"""
        self.clips[clip.name] = clip
        self.weights[clip.name] = weight

    def set_weight(self, clip_name: str, weight: float):
        """Set clip weight"""
        if clip_name in self.weights:
            self.weights[clip_name] = weight

    def add_transition(self, from_clip: str, to_clip: str, duration: float,
                      curve: InterpolationType = InterpolationType.LINEAR):
        """Add transition between clips"""
        self.transitions.append({
            "from": from_clip,
            "to": to_clip,
            "duration": duration,
            "curve": curve,
            "start_time": None,
            "active": False
        })

    def evaluate(self, time: float, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate mixed animation"""
        result = {}

        # Update transitions
        for transition in self.transitions:
            if transition["active"]:
                if transition["start_time"] is None:
                    transition["start_time"] = time

                t = (time - transition["start_time"]) / transition["duration"]
                if t >= 1.0:
                    t = 1.0
                    transition["active"] = False

                # Interpolate weights
                from_weight = 1.0 - t
                to_weight = t

                self.weights[transition["from"]] = from_weight
                self.weights[transition["to"]] = to_weight

        # Mix clips
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            for clip_name, clip in self.clips.items():
                if clip_name in self.weights and self.weights[clip_name] > 0:
                    weight = self.weights[clip_name] / total_weight
                    clip_result = clip.evaluate(time, context)

                    for key, value in clip_result.items():
                        if key not in result:
                            result[key] = value * weight if isinstance(value, (int, float)) else value
                        else:
                            if isinstance(value, (int, float)):
                                result[key] += value * weight
                            else:
                                result[key] = value if weight > 0.5 else result[key]

        return result


class AnimationController:
    """High-level animation controller"""

    def __init__(self):
        self.clips: Dict[str, AnimationClip] = {}
        self.procedural_animators: Dict[str, ProceduralAnimator] = {}
        self.mixer = AnimationMixer()
        self.current_time = 0
        self.playback_speed = 1.0
        self.is_playing = False
        self.loop = False

    def add_clip(self, clip: AnimationClip):
        """Add animation clip"""
        self.clips[clip.name] = clip
        self.mixer.add_clip(clip)

    def add_procedural(self, animator: ProceduralAnimator):
        """Add procedural animator"""
        self.procedural_animators[animator.name] = animator

    def play(self, clip_name: Optional[str] = None):
        """Play animation"""
        self.is_playing = True
        if clip_name and clip_name in self.clips:
            self.mixer.set_weight(clip_name, 1.0)

    def stop(self):
        """Stop animation"""
        self.is_playing = False

    def update(self, delta_time: float) -> Dict[str, Any]:
        """Update animation state"""
        if not self.is_playing:
            return {}

        self.current_time += delta_time * self.playback_speed

        # Get base animation from clips
        result = self.mixer.evaluate(self.current_time)

        # Layer procedural animations
        for name, animator in self.procedural_animators.items():
            proc_result = animator.generate(self.current_time, 0)
            for key, value in proc_result.items():
                proc_key = f"{name}_{key}"
                result[proc_key] = value

        return result

    def seek(self, time: float):
        """Seek to specific time"""
        self.current_time = time

    def set_speed(self, speed: float):
        """Set playback speed"""
        self.playback_speed = speed


# Animation preset library
class AnimationPresets:
    """Library of animation presets"""

    @staticmethod
    def bounce_in() -> AnimationCurve:
        """Bounce in animation"""
        curve = AnimationCurve("bounce_in")
        curve.add_keyframe(0, 0, InterpolationType.BOUNCE)
        curve.add_keyframe(1, 1, InterpolationType.LINEAR)
        return curve

    @staticmethod
    def fade_in() -> AnimationCurve:
        """Fade in animation"""
        curve = AnimationCurve("fade_in")
        curve.add_keyframe(0, 0, InterpolationType.EASE_IN_OUT)
        curve.add_keyframe(1, 1, InterpolationType.LINEAR)
        return curve

    @staticmethod
    def shake() -> AnimationCurve:
        """Shake animation"""
        curve = AnimationCurve("shake")
        curve.expression = "sin(t * 50) * 0.1 * (1 - t)"
        return curve

    @staticmethod
    def pulse() -> AnimationCurve:
        """Pulse animation"""
        curve = AnimationCurve("pulse")
        curve.expression = "1 + sin(t * 2 * pi) * 0.1"
        return curve

    @staticmethod
    def typewriter(text_length: int) -> AnimationCurve:
        """Typewriter text animation"""
        curve = AnimationCurve("typewriter")
        for i in range(text_length + 1):
            curve.add_keyframe(i * 0.1, i, InterpolationType.HOLD)
        return curve

    @staticmethod
    def orbit(radius: float = 100, speed: float = 1) -> Dict[str, AnimationCurve]:
        """Orbital motion animation"""
        curves = {}

        x_curve = AnimationCurve("orbit_x")
        x_curve.expression = f"{radius} * cos(t * {speed} * 2 * pi)"

        y_curve = AnimationCurve("orbit_y")
        y_curve.expression = f"{radius} * sin(t * {speed} * 2 * pi)"

        curves["x"] = x_curve
        curves["y"] = y_curve

        return curves