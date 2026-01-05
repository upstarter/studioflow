"""
Fairlight Audio Processing Templates for StudioFlow
Provides ready-to-use audio processing chains and templates
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np

from studioflow.core.effects import (
    NodeGraph, Node, NodeID,
    EQNode, CompressorNode, ReverbNode,
    DelayNode, GateNode, LimiterNode,
    ChorusNode, PhaserNode, FlangerNode,
    SaturatorNode, FilterNode
)


@dataclass
class AudioProfile:
    """Audio processing profile with target specs"""
    name: str
    target_lufs: float
    true_peak: float
    frequency_response: Dict[str, Any]
    dynamics: Dict[str, Any]
    spatial: Dict[str, Any]


class FairlightTemplate:
    """Base class for Fairlight audio templates"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.graph = NodeGraph()
        self.presets = {}

    def build_chain(self) -> NodeGraph:
        """Build the audio processing chain"""
        # Default implementation - subclasses should override
        return self.graph

    def apply_preset(self, preset_name: str) -> None:
        """Apply a named preset to the chain"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            for node_id, params in preset.items():
                if node_id in self.graph.nodes:
                    self.graph.nodes[node_id].parameters.update(params)


class PodcastMasteringTemplate(FairlightTemplate):
    """Professional podcast mastering chain"""

    def __init__(self):
        super().__init__(
            "podcast_mastering",
            "Complete podcast mastering with LUFS targeting"
        )

        self.presets = {
            "spotify": {
                "compressor": {"ratio": 3.0, "threshold": -18.0},
                "limiter": {"ceiling": -1.0, "release": 50.0}
            },
            "youtube": {
                "compressor": {"ratio": 2.5, "threshold": -20.0},
                "limiter": {"ceiling": -1.0, "release": 30.0}
            },
            "apple_podcasts": {
                "compressor": {"ratio": 3.5, "threshold": -16.0},
                "limiter": {"ceiling": -0.5, "release": 40.0}
            }
        }

    def build_chain(self, target_lufs: float = -16.0) -> NodeGraph:
        """Build podcast mastering chain"""

        # Input stage
        input_node = self.graph.add_node(Node())

        # 1. Noise Gate (remove room noise)
        gate = GateNode(
            threshold=-40.0,
            ratio=10.0,
            attack=1.0,
            release=100.0,
            hold=10.0
        )
        gate_id = self.graph.add_node(gate)

        # 2. High-pass filter (remove rumble)
        hp_filter = FilterNode(
            filter_type="highpass",
            frequency=80.0,
            q=0.7,
            gain=0.0
        )
        hp_id = self.graph.add_node(hp_filter)

        # 3. Parametric EQ (voice enhancement)
        eq = EQNode()
        eq.add_band(200, 0.7, -2.0, "bell")    # Reduce muddiness
        eq.add_band(3000, 0.5, 3.0, "bell")    # Presence boost
        eq.add_band(8000, 0.8, 2.0, "shelf")   # Air/brilliance
        eq_id = self.graph.add_node(eq)

        # 4. De-esser (custom frequency compressor)
        deesser = CompressorNode(
            threshold=-20.0,
            ratio=6.0,
            attack=0.5,
            release=10.0,
            knee=2.0,
            frequency_range=(5000, 9000)  # Target sibilance
        )
        deesser_id = self.graph.add_node(deesser)

        # 5. Main Compressor (dynamics control)
        comp = CompressorNode(
            threshold=-18.0,
            ratio=3.0,
            attack=2.0,
            release=40.0,
            knee=2.0,
            makeup_gain=3.0
        )
        comp_id = self.graph.add_node(comp)

        # 6. Multiband Compressor (frequency-specific dynamics)
        mb_comp = MultibandCompressorNode(
            bands=[
                {"freq": 120, "ratio": 2.0, "threshold": -20.0},
                {"freq": 500, "ratio": 2.5, "threshold": -18.0},
                {"freq": 2000, "ratio": 3.0, "threshold": -16.0},
                {"freq": 8000, "ratio": 2.0, "threshold": -18.0}
            ]
        )
        mb_id = self.graph.add_node(mb_comp)

        # 7. Tape Saturation (warmth)
        saturator = SaturatorNode(
            drive=0.3,
            mix=0.2,
            output_gain=0.0,
            saturation_type="tape"
        )
        sat_id = self.graph.add_node(saturator)

        # 8. Limiter (peak control)
        limiter = LimiterNode(
            threshold=target_lufs + 6.0,
            ceiling=-1.0,
            release=30.0,
            lookahead=5.0
        )
        limiter_id = self.graph.add_node(limiter)

        # 9. LUFS Meter (measurement)
        lufs_meter = LUFSMeterNode(
            target=target_lufs,
            integration_time=400  # ms
        )
        meter_id = self.graph.add_node(lufs_meter)

        # Connect the chain
        connections = [
            (input_node, "output", gate_id, "input"),
            (gate_id, "output", hp_id, "input"),
            (hp_id, "output", eq_id, "input"),
            (eq_id, "output", deesser_id, "input"),
            (deesser_id, "output", comp_id, "input"),
            (comp_id, "output", mb_id, "input"),
            (mb_id, "output", sat_id, "input"),
            (sat_id, "output", limiter_id, "input"),
            (limiter_id, "output", meter_id, "input")
        ]

        for conn in connections:
            self.graph.connect(*conn)

        return self.graph


class VoiceOverTemplate(FairlightTemplate):
    """Voice-over processing for narration"""

    def __init__(self):
        super().__init__(
            "voiceover",
            "Professional voice-over processing"
        )

        self.presets = {
            "natural": {
                "eq": {"presence_boost": 2.0, "warmth": 1.0},
                "comp": {"ratio": 2.0, "threshold": -20.0}
            },
            "commercial": {
                "eq": {"presence_boost": 4.0, "bass_boost": 2.0},
                "comp": {"ratio": 4.0, "threshold": -15.0}
            },
            "audiobook": {
                "eq": {"presence_boost": 1.0, "warmth": 2.0},
                "comp": {"ratio": 2.5, "threshold": -18.0}
            }
        }

    def build_chain(self, style: str = "natural") -> NodeGraph:
        """Build voice-over processing chain"""

        # Proximity effect compensation
        proximity = ProximityEffectNode(
            distance=30.0,  # cm from mic
            compensation=0.7
        )

        # Room correction
        room_correction = RoomCorrectionNode(
            room_size="small",
            treatment_level=0.6,
            target_rt60=0.3
        )

        # Voice-optimized EQ
        voice_eq = VoiceEQNode(
            gender="auto",
            clarity=0.6,
            warmth=0.4,
            presence=0.7
        )

        # Breath control
        breath_control = BreathControlNode(
            sensitivity=0.5,
            reduction=0.7,
            preserve_natural=True
        )

        # Add nodes and connect
        proximity_id = self.graph.add_node(proximity)
        room_id = self.graph.add_node(room_correction)
        voice_eq_id = self.graph.add_node(voice_eq)
        breath_id = self.graph.add_node(breath_control)

        # Connect the chain
        self.graph.connect("input", "output", proximity_id, "input")
        self.graph.connect(proximity_id, "output", room_id, "input")
        self.graph.connect(room_id, "output", voice_eq_id, "input")
        self.graph.connect(voice_eq_id, "output", breath_id, "input")

        return self.graph


class MusicMasteringTemplate(FairlightTemplate):
    """Music mastering chain with genre presets"""

    def __init__(self):
        super().__init__(
            "music_mastering",
            "Professional music mastering"
        )

        self.genre_profiles = {
            "electronic": {
                "low_end": {"freq": 50, "boost": 3.0, "tightness": 0.8},
                "high_end": {"freq": 10000, "boost": 2.0, "smoothness": 0.6},
                "compression": {"ratio": 4.0, "attack": 1.0},
                "stereo_width": 1.2
            },
            "rock": {
                "low_end": {"freq": 80, "boost": 2.0, "tightness": 0.6},
                "high_end": {"freq": 8000, "boost": 1.5, "smoothness": 0.4},
                "compression": {"ratio": 3.0, "attack": 5.0},
                "stereo_width": 1.0
            },
            "jazz": {
                "low_end": {"freq": 60, "boost": 1.0, "tightness": 0.3},
                "high_end": {"freq": 12000, "boost": 1.0, "smoothness": 0.8},
                "compression": {"ratio": 2.0, "attack": 10.0},
                "stereo_width": 0.9
            }
        }

    def build_chain(self, genre: str = "electronic") -> NodeGraph:
        """Build music mastering chain"""

        profile = self.genre_profiles.get(genre, self.genre_profiles["electronic"])

        # M/S Processing
        ms_processor = MSProcessorNode()

        # Linear Phase EQ
        linear_eq = LinearPhaseEQNode(
            bands=[
                {"freq": profile["low_end"]["freq"], "gain": profile["low_end"]["boost"]},
                {"freq": 500, "gain": -0.5, "q": 0.7},
                {"freq": profile["high_end"]["freq"], "gain": profile["high_end"]["boost"]}
            ]
        )

        # Multiband Dynamics
        multiband = MultibandDynamicsNode(
            bands=4,
            crossover_freqs=[100, 500, 5000],
            band_settings=[
                {"ratio": 2.0, "threshold": -20, "makeup": 1.0},
                {"ratio": 2.5, "threshold": -18, "makeup": 0.5},
                {"ratio": 3.0, "threshold": -16, "makeup": 0.0},
                {"ratio": 2.0, "threshold": -18, "makeup": 1.0}
            ]
        )

        # Stereo Enhancement
        stereo = StereoEnhancerNode(
            width=profile["stereo_width"],
            bass_mono_freq=120.0,
            correlation_target=0.5
        )

        # Harmonic Exciter
        exciter = HarmonicExciterNode(
            harmonics=[2, 3, 4],
            amounts=[0.1, 0.05, 0.02],
            frequency_range=(2000, 15000)
        )

        # Tape/Analog Emulation
        analog = AnalogEmulationNode(
            tape_saturation=0.3,
            transformer_saturation=0.2,
            console_coloration=0.1
        )

        # Final Limiter
        limiter = AdaptiveLimiterNode(
            target_lufs=-14.0 if genre == "electronic" else -16.0,
            true_peak=-1.0,
            release_curve="adaptive",
            transient_preservation=0.7
        )

        # Build connections
        ms_id = self.graph.add_node(ms_processor)
        eq_id = self.graph.add_node(linear_eq)
        mb_id = self.graph.add_node(multiband)
        stereo_id = self.graph.add_node(stereo)
        exciter_id = self.graph.add_node(exciter)
        analog_id = self.graph.add_node(analog)
        limiter_id = self.graph.add_node(limiter)

        # Connect chain
        self.graph.connect("input", "output", ms_id, "input")
        self.graph.connect(ms_id, "output", eq_id, "input")
        self.graph.connect(eq_id, "output", mb_id, "input")
        self.graph.connect(mb_id, "output", stereo_id, "input")
        self.graph.connect(stereo_id, "output", exciter_id, "input")
        self.graph.connect(exciter_id, "output", analog_id, "input")
        self.graph.connect(analog_id, "output", limiter_id, "input")

        return self.graph


class DialogueCleanupTemplate(FairlightTemplate):
    """Advanced dialogue cleanup and restoration"""

    def __init__(self):
        super().__init__(
            "dialogue_cleanup",
            "AI-powered dialogue restoration"
        )

    def build_chain(self) -> NodeGraph:
        """Build dialogue cleanup chain"""

        # Spectral Noise Reduction
        spectral_nr = SpectralNoiseReductionNode(
            noise_profile="learn",
            reduction_amount=12.0,
            smoothing=0.5,
            preserve_transients=True
        )

        # Wind Noise Removal
        wind_removal = WindNoiseRemovalNode(
            sensitivity=0.6,
            frequency_range=(20, 200),
            adaptive=True
        )

        # Click and Pop Removal
        declick = DeclickNode(
            sensitivity=0.7,
            click_types=["digital", "analog", "surface"],
            interpolation="cubic"
        )

        # Hum Removal (50/60Hz + harmonics)
        dehum = DehumNode(
            base_frequency="auto",  # Detects 50 or 60 Hz
            harmonics=5,
            q_factor=10.0,
            tracking=True
        )

        # Reverb Removal
        dereverb = DereverbNode(
            amount=0.6,
            preserve_direct=0.9,
            frequency_smoothing=0.3
        )

        # Dialogue Isolation (AI-based)
        dialogue_iso = DialogueIsolationNode(
            model="demucs",
            separation_strength=0.8,
            preserve_ambience=0.2
        )

        # Intelligibility Enhancement
        clarity = ClarityEnhancerNode(
            consonant_boost=2.0,
            formant_enhancement=1.5,
            frequency_range=(1000, 4000)
        )

        # Build and connect nodes
        spectral_id = self.graph.add_node(spectral_nr)
        wind_id = self.graph.add_node(wind_removal)
        click_id = self.graph.add_node(declick)
        hum_id = self.graph.add_node(dehum)
        reverb_id = self.graph.add_node(dereverb)
        dialogue_id = self.graph.add_node(dialogue_iso)
        clarity_id = self.graph.add_node(clarity)

        # Connect chain
        self.graph.connect("input", "output", spectral_id, "input")
        self.graph.connect(spectral_id, "output", wind_id, "input")
        self.graph.connect(wind_id, "output", click_id, "input")
        self.graph.connect(click_id, "output", hum_id, "input")
        self.graph.connect(hum_id, "output", reverb_id, "input")
        self.graph.connect(reverb_id, "output", dialogue_id, "input")
        self.graph.connect(dialogue_id, "output", clarity_id, "input")

        return self.graph


class SurroundMixTemplate(FairlightTemplate):
    """5.1/7.1/Atmos surround mixing template"""

    def __init__(self):
        super().__init__(
            "surround_mix",
            "Immersive audio mixing"
        )

    def build_chain(self, format: str = "5.1") -> NodeGraph:
        """Build surround mixing chain"""

        # Surround Panner
        panner = SurroundPannerNode(
            format=format,
            divergence=0.5,
            center_percentage=50.0,
            lfe_send=-10.0
        )

        # Room Simulation
        room = RoomSimulationNode(
            room_type="theater",
            size="medium",
            materials={
                "walls": "acoustic_panel",
                "floor": "carpet",
                "ceiling": "acoustic_tile"
            }
        )

        # Bass Management
        bass_mgmt = BassManagementNode(
            crossover_freq=80.0,
            lfe_gain=10.0,
            phase_alignment=True
        )

        # Surround Compressor
        surround_comp = SurroundCompressorNode(
            link_channels=True,
            preserve_imaging=True,
            center_priority=1.2
        )

        # Format Encoder (Dolby, DTS, etc.)
        encoder = FormatEncoderNode(
            format="dolby_digital_plus",
            bitrate=448,
            dialogue_normalization=-27.0
        )

        return self.graph


class LiveStreamTemplate(FairlightTemplate):
    """Real-time audio processing for live streaming"""

    def __init__(self):
        super().__init__(
            "live_stream",
            "Low-latency streaming audio"
        )

    def build_chain(self) -> NodeGraph:
        """Build live streaming chain"""

        # Real-time Noise Suppression
        noise_supp = RTNoiseSuppressionNode(
            algorithm="rnnoise",
            suppression_level=15.0,
            latency_mode="ultra_low"
        )

        # Automatic Gain Control
        agc = AutoGainControlNode(
            target_level=-18.0,
            max_gain=20.0,
            response_time=100.0,
            noise_gate=-40.0
        )

        # Voice Beautifier
        beautifier = VoiceBeautifierNode(
            smoothing=0.4,
            warmth=0.3,
            clarity=0.6,
            de_harsh=0.5
        )

        # Adaptive Limiter
        limiter = AdaptiveLimiterNode(
            target_lufs=-16.0,
            true_peak=-1.0,
            lookahead=1.0,  # Minimal for low latency
            isr_mode=True    # Intelligent sample rate
        )

        # Stream Encoder
        encoder = StreamEncoderNode(
            codec="opus",
            bitrate=128,
            complexity=5,
            packet_loss_protection=0.3
        )

        return self.graph


# Additional Node implementations for advanced features

class MultibandCompressorNode(Node):
    """Multiband compression node"""

    def __init__(self, bands: List[Dict[str, Any]]):
        super().__init__()
        self.bands = bands

    def process(self, inputs: Dict[str, Any], time: float = 0) -> Dict[str, Any]:
        # Implement multiband compression
        return {"output": inputs.get("input")}


class LUFSMeterNode(Node):
    """LUFS metering node"""

    def __init__(self, target: float, integration_time: float):
        super().__init__()
        self.parameters = {
            "target": target,
            "integration_time": integration_time,
            "current_lufs": 0.0,
            "peak": 0.0
        }

    def process(self, inputs: Dict[str, Any], time: float = 0) -> Dict[str, Any]:
        # Calculate LUFS
        return {
            "output": inputs.get("input"),
            "lufs": self.parameters["current_lufs"],
            "peak": self.parameters["peak"]
        }


class ProximityEffectNode(Node):
    """Compensate for proximity effect in close-mic recording"""

    def __init__(self, distance: float, compensation: float):
        super().__init__()
        self.parameters = {
            "distance": distance,
            "compensation": compensation
        }

    def process(self, inputs: Dict[str, Any], time: float = 0) -> Dict[str, Any]:
        # Apply proximity compensation EQ
        return {"output": inputs.get("input")}


class RoomCorrectionNode(Node):
    """Room acoustics correction"""

    def __init__(self, room_size: str, treatment_level: float, target_rt60: float):
        super().__init__()
        self.parameters = {
            "room_size": room_size,
            "treatment_level": treatment_level,
            "target_rt60": target_rt60
        }


class VoiceEQNode(Node):
    """Intelligent voice-optimized EQ"""

    def __init__(self, gender: str, clarity: float, warmth: float, presence: float):
        super().__init__()
        self.parameters = {
            "gender": gender,
            "clarity": clarity,
            "warmth": warmth,
            "presence": presence
        }


class BreathControlNode(Node):
    """Breath detection and control"""

    def __init__(self, sensitivity: float, reduction: float, preserve_natural: bool):
        super().__init__()
        self.parameters = {
            "sensitivity": sensitivity,
            "reduction": reduction,
            "preserve_natural": preserve_natural
        }


class MSProcessorNode(Node):
    """Mid/Side processing"""

    def process(self, inputs: Dict[str, Any], time: float = 0) -> Dict[str, Any]:
        # Convert stereo to M/S
        return {"mid": inputs.get("input"), "side": inputs.get("input")}


class LinearPhaseEQNode(Node):
    """Linear phase EQ for mastering"""

    def __init__(self, bands: List[Dict[str, Any]]):
        super().__init__()
        self.bands = bands


class MultibandDynamicsNode(Node):
    """Multiband dynamics processor"""

    def __init__(self, bands: int, crossover_freqs: List[float], band_settings: List[Dict]):
        super().__init__()
        self.parameters = {
            "bands": bands,
            "crossover_freqs": crossover_freqs,
            "band_settings": band_settings
        }


class StereoEnhancerNode(Node):
    """Stereo width enhancement"""

    def __init__(self, width: float, bass_mono_freq: float, correlation_target: float):
        super().__init__()
        self.parameters = {
            "width": width,
            "bass_mono_freq": bass_mono_freq,
            "correlation_target": correlation_target
        }


class HarmonicExciterNode(Node):
    """Harmonic excitement generator"""

    def __init__(self, harmonics: List[int], amounts: List[float], frequency_range: Tuple[float, float]):
        super().__init__()
        self.parameters = {
            "harmonics": harmonics,
            "amounts": amounts,
            "frequency_range": frequency_range
        }


class AnalogEmulationNode(Node):
    """Analog hardware emulation"""

    def __init__(self, tape_saturation: float, transformer_saturation: float, console_coloration: float):
        super().__init__()
        self.parameters = {
            "tape_saturation": tape_saturation,
            "transformer_saturation": transformer_saturation,
            "console_coloration": console_coloration
        }


class AdaptiveLimiterNode(LimiterNode):
    """Adaptive limiting with intelligent release"""

    def __init__(self, target_lufs: float, true_peak: float, release_curve: str, transient_preservation: float):
        super().__init__(threshold=target_lufs + 6.0, ceiling=true_peak, release=30.0, lookahead=5.0)
        self.parameters.update({
            "target_lufs": target_lufs,
            "release_curve": release_curve,
            "transient_preservation": transient_preservation
        })


class SpectralNoiseReductionNode(Node):
    """Spectral noise reduction"""

    def __init__(self, noise_profile: str, reduction_amount: float, smoothing: float, preserve_transients: bool):
        super().__init__()
        self.parameters = {
            "noise_profile": noise_profile,
            "reduction_amount": reduction_amount,
            "smoothing": smoothing,
            "preserve_transients": preserve_transients
        }


class WindNoiseRemovalNode(Node):
    """Wind noise removal"""

    def __init__(self, sensitivity: float, frequency_range: Tuple[float, float], adaptive: bool):
        super().__init__()
        self.parameters = {
            "sensitivity": sensitivity,
            "frequency_range": frequency_range,
            "adaptive": adaptive
        }


class DeclickNode(Node):
    """Click and pop removal"""

    def __init__(self, sensitivity: float, click_types: List[str], interpolation: str):
        super().__init__()
        self.parameters = {
            "sensitivity": sensitivity,
            "click_types": click_types,
            "interpolation": interpolation
        }


class DehumNode(Node):
    """Hum and buzz removal"""

    def __init__(self, base_frequency: str, harmonics: int, q_factor: float, tracking: bool):
        super().__init__()
        self.parameters = {
            "base_frequency": base_frequency,
            "harmonics": harmonics,
            "q_factor": q_factor,
            "tracking": tracking
        }


class DereverbNode(Node):
    """Reverb removal"""

    def __init__(self, amount: float, preserve_direct: float, frequency_smoothing: float):
        super().__init__()
        self.parameters = {
            "amount": amount,
            "preserve_direct": preserve_direct,
            "frequency_smoothing": frequency_smoothing
        }


class DialogueIsolationNode(Node):
    """AI-based dialogue isolation"""

    def __init__(self, model: str, separation_strength: float, preserve_ambience: float):
        super().__init__()
        self.parameters = {
            "model": model,
            "separation_strength": separation_strength,
            "preserve_ambience": preserve_ambience
        }


class ClarityEnhancerNode(Node):
    """Speech clarity enhancement"""

    def __init__(self, consonant_boost: float, formant_enhancement: float, frequency_range: Tuple[float, float]):
        super().__init__()
        self.parameters = {
            "consonant_boost": consonant_boost,
            "formant_enhancement": formant_enhancement,
            "frequency_range": frequency_range
        }


class SurroundPannerNode(Node):
    """Surround sound panning"""

    def __init__(self, format: str, divergence: float, center_percentage: float, lfe_send: float):
        super().__init__()
        self.parameters = {
            "format": format,
            "divergence": divergence,
            "center_percentage": center_percentage,
            "lfe_send": lfe_send
        }


class RoomSimulationNode(Node):
    """Acoustic room simulation"""

    def __init__(self, room_type: str, size: str, materials: Dict[str, str]):
        super().__init__()
        self.parameters = {
            "room_type": room_type,
            "size": size,
            "materials": materials
        }


class BassManagementNode(Node):
    """Bass management for surround"""

    def __init__(self, crossover_freq: float, lfe_gain: float, phase_alignment: bool):
        super().__init__()
        self.parameters = {
            "crossover_freq": crossover_freq,
            "lfe_gain": lfe_gain,
            "phase_alignment": phase_alignment
        }


class SurroundCompressorNode(Node):
    """Surround-aware compression"""

    def __init__(self, link_channels: bool, preserve_imaging: bool, center_priority: float):
        super().__init__()
        self.parameters = {
            "link_channels": link_channels,
            "preserve_imaging": preserve_imaging,
            "center_priority": center_priority
        }


class FormatEncoderNode(Node):
    """Audio format encoder"""

    def __init__(self, format: str, bitrate: int, dialogue_normalization: float):
        super().__init__()
        self.parameters = {
            "format": format,
            "bitrate": bitrate,
            "dialogue_normalization": dialogue_normalization
        }


class RTNoiseSuppressionNode(Node):
    """Real-time noise suppression"""

    def __init__(self, algorithm: str, suppression_level: float, latency_mode: str):
        super().__init__()
        self.parameters = {
            "algorithm": algorithm,
            "suppression_level": suppression_level,
            "latency_mode": latency_mode
        }


class AutoGainControlNode(Node):
    """Automatic gain control"""

    def __init__(self, target_level: float, max_gain: float, response_time: float, noise_gate: float):
        super().__init__()
        self.parameters = {
            "target_level": target_level,
            "max_gain": max_gain,
            "response_time": response_time,
            "noise_gate": noise_gate
        }


class VoiceBeautifierNode(Node):
    """Voice beautification"""

    def __init__(self, smoothing: float, warmth: float, clarity: float, de_harsh: float):
        super().__init__()
        self.parameters = {
            "smoothing": smoothing,
            "warmth": warmth,
            "clarity": clarity,
            "de_harsh": de_harsh
        }


class StreamEncoderNode(Node):
    """Streaming audio encoder"""

    def __init__(self, codec: str, bitrate: int, complexity: int, packet_loss_protection: float):
        super().__init__()
        self.parameters = {
            "codec": codec,
            "bitrate": bitrate,
            "complexity": complexity,
            "packet_loss_protection": packet_loss_protection
        }


# Factory function to create templates
def create_fairlight_template(template_type: str, **kwargs) -> FairlightTemplate:
    """Factory to create Fairlight audio templates"""

    templates = {
        "podcast_mastering": PodcastMasteringTemplate,
        "voiceover": VoiceOverTemplate,
        "music_mastering": MusicMasteringTemplate,
        "dialogue_cleanup": DialogueCleanupTemplate,
        "surround_mix": SurroundMixTemplate,
        "live_stream": LiveStreamTemplate
    }

    template_class = templates.get(template_type)
    if not template_class:
        raise ValueError(f"Unknown template type: {template_type}")

    template = template_class()
    graph = template.build_chain(**kwargs)

    return template