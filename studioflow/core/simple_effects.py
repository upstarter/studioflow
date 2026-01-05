"""
Simple but powerful effects system
Direct FFmpeg filters with smart presets
"""

import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

from .ffmpeg import ProcessResult, VideoQuality


@dataclass
class EffectPreset:
    """Effect configuration with sensible defaults"""
    name: str
    filter: str
    description: str
    params: Dict[str, Any]


class SimpleEffects:
    """Simple effects that actually work"""

    # Common effect presets
    EFFECTS = {
        # Basic adjustments
        "fade_in": EffectPreset(
            "fade_in",
            "fade=in:0:d={duration}",
            "Fade in from black",
            {"duration": 1.0}
        ),
        "fade_out": EffectPreset(
            "fade_out",
            "fade=out:st={start}:d={duration}",
            "Fade out to black",
            {"duration": 1.0, "start": None}  # Will calculate
        ),
        "brightness": EffectPreset(
            "brightness",
            "eq=brightness={value}",
            "Adjust brightness (-1.0 to 1.0)",
            {"value": 0.1}
        ),
        "contrast": EffectPreset(
            "contrast",
            "eq=contrast={value}",
            "Adjust contrast (0 to 2.0)",
            {"value": 1.2}
        ),
        "saturation": EffectPreset(
            "saturation",
            "eq=saturation={value}",
            "Adjust saturation (0 to 3.0)",
            {"value": 1.2}
        ),

        # Blur effects
        "blur": EffectPreset(
            "blur",
            "boxblur={amount}",
            "Apply box blur",
            {"amount": "5:1"}
        ),
        "gaussian_blur": EffectPreset(
            "gaussian_blur",
            "gblur=sigma={sigma}",
            "Apply gaussian blur",
            {"sigma": 5}
        ),
        "motion_blur": EffectPreset(
            "motion_blur",
            "tmix=frames={frames}:weights={weights}",
            "Motion blur effect",
            {"frames": 8, "weights": "1 1 1 1 1 1 1 1"}
        ),

        # Sharpening
        "sharpen": EffectPreset(
            "sharpen",
            "unsharp=5:5:{amount}:5:5:0",
            "Sharpen image",
            {"amount": 1.0}
        ),

        # Color effects
        "grayscale": EffectPreset(
            "grayscale",
            "format=gray",
            "Convert to grayscale",
            {}
        ),
        "sepia": EffectPreset(
            "sepia",
            "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
            "Sepia tone effect",
            {}
        ),
        "negative": EffectPreset(
            "negative",
            "negate",
            "Negative/invert colors",
            {}
        ),
        "vintage": EffectPreset(
            "vintage",
            "curves=vintage",
            "Vintage color grading",
            {}
        ),

        # Transform effects
        "flip_h": EffectPreset(
            "flip_h",
            "hflip",
            "Flip horizontally",
            {}
        ),
        "flip_v": EffectPreset(
            "flip_v",
            "vflip",
            "Flip vertically",
            {}
        ),
        "rotate": EffectPreset(
            "rotate",
            "rotate={angle}*PI/180",
            "Rotate video",
            {"angle": 90}
        ),

        # Speed effects
        "speed": EffectPreset(
            "speed",
            "setpts={factor}*PTS",
            "Change playback speed",
            {"factor": 0.5}  # 2x speed
        ),
        "slow_motion": EffectPreset(
            "slow_motion",
            "setpts=2*PTS",
            "2x slow motion",
            {}
        ),
        "timelapse": EffectPreset(
            "timelapse",
            "setpts=0.1*PTS",
            "10x timelapse",
            {}
        ),

        # Stabilization
        "stabilize": EffectPreset(
            "stabilize",
            "vidstabdetect=shakiness=5:accuracy=15:result=/tmp/transform.trf",
            "Video stabilization (2-pass)",
            {}
        ),

        # Noise reduction
        "denoise": EffectPreset(
            "denoise",
            "nlmeans=s={strength}",
            "Reduce noise",
            {"strength": 4.0}
        ),

        # Vignette
        "vignette": EffectPreset(
            "vignette",
            "vignette",
            "Add vignette effect",
            {}
        ),

        # Crop and scale
        "crop": EffectPreset(
            "crop",
            "crop={width}:{height}:{x}:{y}",
            "Crop video",
            {"width": "iw/2", "height": "ih/2", "x": "iw/4", "y": "ih/4"}
        ),
        "scale": EffectPreset(
            "scale",
            "scale={width}:{height}",
            "Scale video",
            {"width": 1280, "height": 720}
        ),
        "letterbox": EffectPreset(
            "letterbox",
            "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",
            "Add letterbox bars",
            {}
        ),
    }

    @staticmethod
    def apply_effect(input_file: Path, effect_name: str, output_file: Optional[Path] = None,
                    params: Optional[Dict] = None) -> ProcessResult:
        """Apply a single effect with smart defaults"""

        if not input_file.exists():
            return ProcessResult(False, error_message=f"Input file not found: {input_file}")

        if effect_name not in SimpleEffects.EFFECTS:
            available = ", ".join(sorted(SimpleEffects.EFFECTS.keys()))
            return ProcessResult(
                False,
                error_message=f"Unknown effect: {effect_name}",
                suggestion=f"Available effects: {available}"
            )

        if output_file is None:
            output_file = input_file.parent / f"{input_file.stem}_{effect_name}{input_file.suffix}"

        effect = SimpleEffects.EFFECTS[effect_name]

        # Merge default params with user params
        effect_params = effect.params.copy()
        if params:
            effect_params.update(params)

        # Special handling for effects that need video info
        if effect_name == "fade_out" and effect_params.get("start") is None:
            # Calculate fade out start time
            from .ffmpeg import FFmpegProcessor
            info = FFmpegProcessor.get_media_info(input_file)
            duration = info.get('duration_seconds', 10)
            effect_params["start"] = duration - effect_params["duration"]

        # Build filter string
        filter_str = effect.filter.format(**effect_params)

        # Build command
        cmd = [
            "ffmpeg", "-i", str(input_file),
            "-vf", filter_str,
            "-c:a", "copy",  # Keep audio unchanged
            "-y", str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)
            return ProcessResult(True, output_path=output_file, file_size_mb=size_mb)
        except subprocess.CalledProcessError as e:
            return ProcessResult(
                False,
                error_message=str(e)[:200],
                suggestion=f"Check parameters for {effect_name}"
            )

    @staticmethod
    def apply_multiple(input_file: Path, effects: List[str], output_file: Optional[Path] = None,
                      params: Optional[Dict[str, Dict]] = None) -> ProcessResult:
        """Apply multiple effects in sequence"""

        if not input_file.exists():
            return ProcessResult(False, error_message=f"Input file not found: {input_file}")

        if output_file is None:
            output_file = input_file.parent / f"{input_file.stem}_effects{input_file.suffix}"

        # Build filter chain
        filters = []
        for effect_name in effects:
            if effect_name not in SimpleEffects.EFFECTS:
                continue

            effect = SimpleEffects.EFFECTS[effect_name]
            effect_params = effect.params.copy()

            # Get params for this effect if provided
            if params and effect_name in params:
                effect_params.update(params[effect_name])

            # Special handling
            if effect_name == "fade_out" and effect_params.get("start") is None:
                from .ffmpeg import FFmpegProcessor
                info = FFmpegProcessor.get_media_info(input_file)
                duration = info.get('duration_seconds', 10)
                effect_params["start"] = duration - effect_params["duration"]

            filters.append(effect.filter.format(**effect_params))

        if not filters:
            return ProcessResult(False, error_message="No valid effects specified")

        # Join filters
        filter_str = ",".join(filters)

        cmd = [
            "ffmpeg", "-i", str(input_file),
            "-vf", filter_str,
            "-c:a", "copy",
            "-y", str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)
            return ProcessResult(
                True,
                output_path=output_file,
                file_size_mb=size_mb
            )
        except subprocess.CalledProcessError as e:
            return ProcessResult(False, error_message=str(e)[:200])

    @staticmethod
    def create_preset(preset_name: str, input_file: Path, output_file: Optional[Path] = None) -> ProcessResult:
        """Apply predefined effect combinations"""

        presets = {
            "cinematic": ["letterbox", "contrast", "vignette", "fade_in", "fade_out"],
            "vintage": ["sepia", "vignette", "contrast"],
            "dramatic": ["contrast", "saturation", "vignette"],
            "clean": ["denoise", "sharpen"],
            "social_media": ["crop", "sharpen", "contrast"],
            "documentary": ["stabilize", "denoise", "contrast"],
        }

        if preset_name not in presets:
            available = ", ".join(sorted(presets.keys()))
            return ProcessResult(
                False,
                error_message=f"Unknown preset: {preset_name}",
                suggestion=f"Available presets: {available}"
            )

        # Apply preset effects
        preset_params = {
            "contrast": {"value": 1.3} if preset_name == "dramatic" else {"value": 1.1},
            "saturation": {"value": 1.4} if preset_name == "dramatic" else {"value": 1.1},
            "crop": {"width": "1080", "height": "1080", "x": "(iw-1080)/2", "y": "(ih-1080)/2"}
        }

        return SimpleEffects.apply_multiple(
            input_file,
            presets[preset_name],
            output_file,
            preset_params
        )

    @staticmethod
    def auto_enhance(input_file: Path, output_file: Optional[Path] = None) -> ProcessResult:
        """Automatically enhance video quality"""

        if output_file is None:
            output_file = input_file.parent / f"{input_file.stem}_enhanced{input_file.suffix}"

        # Auto-enhancement filter chain
        filters = [
            "normalize=blackpt=black:whitept=white:smoothing=50",  # Auto levels
            "eq=contrast=1.1:brightness=0.05:saturation=1.1",  # Subtle enhancement
            "unsharp=5:5:0.5:5:5:0",  # Mild sharpening
        ]

        filter_str = ",".join(filters)

        cmd = [
            "ffmpeg", "-i", str(input_file),
            "-vf", filter_str,
            "-c:a", "copy",
            "-y", str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)
            return ProcessResult(True, output_path=output_file, file_size_mb=size_mb)
        except subprocess.CalledProcessError as e:
            return ProcessResult(False, error_message=str(e)[:200])

    @staticmethod
    def text_overlay(input_file: Path, text: str, output_file: Optional[Path] = None,
                    position: str = "bottom", font_size: int = 48,
                    font_color: str = "white", bg_color: str = "black@0.5") -> ProcessResult:
        """Add text overlay with background"""

        if output_file is None:
            output_file = input_file.parent / f"{input_file.stem}_text{input_file.suffix}"

        # Position mappings
        positions = {
            "top": "x=(w-text_w)/2:y=50",
            "center": "x=(w-text_w)/2:y=(h-text_h)/2",
            "bottom": "x=(w-text_w)/2:y=h-text_h-50",
            "top_left": "x=50:y=50",
            "top_right": "x=w-text_w-50:y=50",
            "bottom_left": "x=50:y=h-text_h-50",
            "bottom_right": "x=w-text_w-50:y=h-text_h-50"
        }

        pos = positions.get(position, positions["bottom"])

        # Build drawtext filter with background box
        filter_str = (
            f"drawtext=text='{text}':"
            f"fontsize={font_size}:"
            f"fontcolor={font_color}:"
            f"box=1:boxcolor={bg_color}:boxborderw=10:"
            f"{pos}"
        )

        # Try to use system font
        filter_str += ":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

        cmd = [
            "ffmpeg", "-i", str(input_file),
            "-vf", filter_str,
            "-c:a", "copy",
            "-y", str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)
            return ProcessResult(True, output_path=output_file, file_size_mb=size_mb)
        except subprocess.CalledProcessError:
            # Try without fontfile specification
            filter_str = (
                f"drawtext=text='{text}':"
                f"fontsize={font_size}:"
                f"fontcolor={font_color}:"
                f"box=1:boxcolor={bg_color}:boxborderw=10:"
                f"{pos}"
            )

            cmd[3] = filter_str  # Update filter

            try:
                subprocess.run(cmd, check=True, capture_output=True)
                size_mb = output_file.stat().st_size / (1024 * 1024)
                return ProcessResult(True, output_path=output_file, file_size_mb=size_mb)
            except subprocess.CalledProcessError as e:
                return ProcessResult(
                    False,
                    error_message=str(e)[:200],
                    suggestion="Check if fonts are installed: apt install fonts-dejavu"
                )