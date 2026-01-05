"""
DaVinci Resolve optimization profiles
Ported from sf-resolve for YouTube quality and FX30 camera workflows
"""

from typing import Dict, Any, List
from pathlib import Path


class ResolveProfiles:
    """DaVinci Resolve optimization profiles for maximum YouTube quality"""

    # YouTube quality matrix based on 2024-2025 codec research
    YOUTUBE_QUALITY_MATRIX = {
        "4k30_master": {
            "resolution": (3840, 2160),
            "fps": 29.97,
            "codec_trigger": "Always VP9/AV1",  # 4K always gets premium codec
            "target_bitrate": 45,  # Mbps - YouTube's VP9 efficiency point
            "max_bitrate": 68,     # Mbps - Beyond this is wasted
            "buffer_size": 136,    # 2x max for quality spikes
            "color_depth": "10bit", # Reduces banding
            "chroma": "4:2:0",     # YouTube doesn't preserve 4:2:2
            "audio_lufs": -14.0,   # YouTube's exact target
            "true_peak": -1.0,     # Prevent clipping
            "strategy": "Upload at 4K even if source is 1080p for VP9 assignment"
        },
        "1440p30_fallback": {
            "resolution": (2560, 1440),
            "fps": 29.97,
            "codec_trigger": "VP9 with views OR high bitrate",
            "target_bitrate": 24,
            "max_bitrate": 30,
            "buffer_size": 60,
            "color_depth": "10bit",
            "chroma": "4:2:0",
            "audio_lufs": -14.0,
            "true_peak": -1.0,
            "strategy": "Good middle ground for 1080p content"
        },
        "1080p30_proxy": {
            "resolution": (1920, 1080),
            "fps": 29.97,
            "codec_trigger": "Usually AVC (needs high views for VP9)",
            "target_bitrate": 12,
            "max_bitrate": 16,
            "buffer_size": 32,
            "color_depth": "8bit",
            "chroma": "4:2:0",
            "audio_lufs": -14.0,
            "true_peak": -1.0,
            "strategy": "Only for quick previews, not final upload"
        },
        "shorts_vertical": {
            "resolution": (1080, 1920),  # Vertical 9:16
            "fps": 30,
            "target_bitrate": 20,
            "max_bitrate": 25,
            "buffer_size": 50,
            "color_depth": "8bit",
            "chroma": "4:2:0",
            "audio_lufs": -14.0,
            "true_peak": -1.0,
            "strategy": "Optimized for YouTube Shorts and Instagram Reels"
        }
    }

    # FX30 Camera Pipeline (Sony Cinema Line)
    FX30_PROFILES = {
        "scinetone_rec709": {
            "description": "S-Cinetone - Ready to use, minor adjustments",
            "input_color_space": "Rec.709",
            "input_gamma": "Rec.709",
            "timeline_color_space": "Rec.709",
            "timeline_gamma": "Rec.709",
            "output_color_space": "Rec.709",
            "output_gamma": "Rec.709",
            "nodes": [
                {"type": "Primary", "contrast": 1.05, "saturation": 1.08},
                {"type": "Curves", "adjustments": "slight_s_curve"}
            ],
            "recommended_for": ["vlogs", "interviews", "quick turnaround"]
        },
        "slog3_workflow": {
            "description": "S-Log3 - Maximum flexibility, needs grading",
            "input_color_space": "S-Gamut3.Cine",
            "input_gamma": "S-Log3",
            "timeline_color_space": "DaVinci Wide Gamut",
            "timeline_gamma": "DaVinci Intermediate",
            "output_color_space": "Rec.709",
            "output_gamma": "Rec.709",
            "lut_options": [
                "fx30_neutral.cube",
                "fx30_utopia.cube",
                "fx30_moody.cube"
            ],
            "nodes": [
                {"type": "CST", "purpose": "Input to Working"},
                {"type": "LUT", "purpose": "Base look"},
                {"type": "Primary", "purpose": "Fine tuning"},
                {"type": "CST", "purpose": "Working to Output"}
            ],
            "recommended_for": ["cinematic", "color critical", "high-end production"]
        },
        "hlg_hdr": {
            "description": "HLG - HDR delivery for compatible displays",
            "input_color_space": "Rec.2020",
            "input_gamma": "HLG",
            "timeline_color_space": "Rec.2020",
            "timeline_gamma": "HLG",
            "output_color_space": "Rec.2020",
            "output_gamma": "HLG",
            "nodes": [
                {"type": "Primary", "purpose": "Minimal adjustment"},
                {"type": "HDR_Tools", "purpose": "Tone mapping"}
            ],
            "recommended_for": ["hdr_content", "future_proof", "premium_delivery"]
        }
    }

    # Export presets for different platforms
    EXPORT_PRESETS = {
        "youtube_4k": {
            "format": "H.264",
            "codec": "H.264",
            "resolution": "3840x2160",
            "framerate": "29.97",
            "bitrate_mode": "VBR",
            "target_bitrate": 45000,
            "max_bitrate": 68000,
            "audio_codec": "AAC",
            "audio_bitrate": 320,
            "audio_sample_rate": 48000,
            "container": "MP4",
            "optimize_for": "streaming"
        },
        "youtube_1080p": {
            "format": "H.264",
            "codec": "H.264",
            "resolution": "1920x1080",
            "framerate": "29.97",
            "bitrate_mode": "VBR",
            "target_bitrate": 12000,
            "max_bitrate": 16000,
            "audio_codec": "AAC",
            "audio_bitrate": 256,
            "audio_sample_rate": 48000,
            "container": "MP4",
            "optimize_for": "streaming"
        },
        "instagram_reel": {
            "format": "H.264",
            "codec": "H.264",
            "resolution": "1080x1920",  # Vertical
            "framerate": "30",
            "bitrate_mode": "CBR",
            "target_bitrate": 20000,
            "audio_codec": "AAC",
            "audio_bitrate": 256,
            "audio_sample_rate": 44100,
            "container": "MP4",
            "duration_limit": 90,  # seconds
            "optimize_for": "mobile"
        },
        "tiktok": {
            "format": "H.264",
            "codec": "H.264",
            "resolution": "1080x1920",  # Vertical
            "framerate": "30",
            "bitrate_mode": "VBR",
            "target_bitrate": 15000,
            "max_bitrate": 20000,
            "audio_codec": "AAC",
            "audio_bitrate": 256,
            "audio_sample_rate": 44100,
            "container": "MP4",
            "duration_limit": 180,  # 3 minutes max
            "optimize_for": "mobile"
        },
        "prores_master": {
            "format": "ProRes",
            "codec": "ProRes 422 HQ",
            "resolution": "source",
            "framerate": "source",
            "color_depth": "10bit",
            "audio_codec": "PCM",
            "audio_bitrate": "uncompressed",
            "audio_sample_rate": 48000,
            "container": "MOV",
            "optimize_for": "archival"
        }
    }

    # Multi-tier export strategy
    EXPORT_STRATEGY = {
        "tier1_upload": {
            "description": "Primary upload - Highest quality for YouTube VP9",
            "preset": "youtube_4k",
            "purpose": "Main platform upload",
            "priority": 1
        },
        "tier2_backup": {
            "description": "Fallback quality - Good balance",
            "preset": "youtube_1080p",
            "purpose": "Quick preview, backup upload",
            "priority": 2
        },
        "tier3_social": {
            "description": "Social media versions",
            "presets": ["instagram_reel", "tiktok"],
            "purpose": "Cross-platform distribution",
            "priority": 3
        },
        "tier4_master": {
            "description": "Archival master",
            "preset": "prores_master",
            "purpose": "Future re-exports, archival",
            "priority": 4
        }
    }

    @classmethod
    def get_youtube_settings(cls, quality: str = "4k30_master") -> Dict[str, Any]:
        """Get optimized YouTube export settings"""
        return cls.YOUTUBE_QUALITY_MATRIX.get(quality, cls.YOUTUBE_QUALITY_MATRIX["4k30_master"])

    @classmethod
    def get_fx30_profile(cls, profile: str = "scinetone_rec709") -> Dict[str, Any]:
        """Get FX30 camera color workflow"""
        return cls.FX30_PROFILES.get(profile, cls.FX30_PROFILES["scinetone_rec709"])

    @classmethod
    def get_export_preset(cls, platform: str = "youtube") -> Dict[str, Any]:
        """Get export preset for specific platform"""
        preset_map = {
            "youtube": "youtube_4k",
            "instagram": "instagram_reel",
            "tiktok": "tiktok",
            "master": "prores_master"
        }
        preset_name = preset_map.get(platform, "youtube_4k")
        return cls.EXPORT_PRESETS.get(preset_name)

    @classmethod
    def get_multi_export_strategy(cls) -> List[Dict[str, Any]]:
        """Get complete multi-tier export strategy"""
        strategy = []
        for tier_name, tier_config in cls.EXPORT_STRATEGY.items():
            if isinstance(tier_config.get("presets"), list):
                for preset_name in tier_config["presets"]:
                    preset = cls.EXPORT_PRESETS.get(preset_name, {})
                    strategy.append({
                        "tier": tier_name,
                        "description": tier_config["description"],
                        "preset": preset_name,
                        "settings": preset,
                        "priority": tier_config["priority"]
                    })
            else:
                preset_name = tier_config.get("preset")
                preset = cls.EXPORT_PRESETS.get(preset_name, {})
                strategy.append({
                    "tier": tier_name,
                    "description": tier_config["description"],
                    "preset": preset_name,
                    "settings": preset,
                    "priority": tier_config["priority"]
                })

        return sorted(strategy, key=lambda x: x["priority"])

    @classmethod
    def generate_export_command(cls, input_file: Path, preset: str = "youtube_4k") -> str:
        """Generate FFmpeg export command based on preset"""
        settings = cls.EXPORT_PRESETS.get(preset, cls.EXPORT_PRESETS["youtube_4k"])

        output_file = input_file.parent / f"{input_file.stem}_{preset}{input_file.suffix}"

        # Build FFmpeg command
        cmd_parts = ["ffmpeg", "-i", str(input_file)]

        # Video codec settings
        if settings["codec"] == "H.264":
            cmd_parts.extend(["-c:v", "libx264"])
            cmd_parts.extend(["-preset", "slow"])  # Better quality
            cmd_parts.extend(["-crf", "18"])  # High quality

        elif settings["codec"].startswith("ProRes"):
            cmd_parts.extend(["-c:v", "prores_ks"])
            cmd_parts.extend(["-profile:v", "3"])  # ProRes 422 HQ

        # Resolution
        if settings["resolution"] != "source":
            cmd_parts.extend(["-s", settings["resolution"]])

        # Framerate
        if settings["framerate"] != "source":
            cmd_parts.extend(["-r", settings["framerate"]])

        # Bitrate
        if "target_bitrate" in settings:
            cmd_parts.extend(["-b:v", f"{settings['target_bitrate']}k"])
        if "max_bitrate" in settings:
            cmd_parts.extend(["-maxrate", f"{settings['max_bitrate']}k"])
            cmd_parts.extend(["-bufsize", f"{settings['max_bitrate'] * 2}k"])

        # Audio settings
        if settings["audio_codec"] == "AAC":
            cmd_parts.extend(["-c:a", "aac"])
            cmd_parts.extend(["-b:a", f"{settings['audio_bitrate']}k"])
        elif settings["audio_codec"] == "PCM":
            cmd_parts.extend(["-c:a", "pcm_s16le"])

        cmd_parts.extend(["-ar", str(settings["audio_sample_rate"])])

        # Output file
        cmd_parts.append(str(output_file))

        return " ".join(cmd_parts)

    @classmethod
    def get_color_workflow_tips(cls) -> Dict[str, str]:
        """Get color grading workflow tips"""
        return {
            "fx30_slog3": "Use CST nodes for proper color space conversion. Apply LUT at 50-70% intensity.",
            "fx30_scinetone": "Minimal grading needed. Slight contrast and saturation boost recommended.",
            "youtube_upload": "Ensure Rec.709 output. YouTube will handle HDR metadata if present.",
            "instagram": "Boost contrast and saturation by 10-15% for mobile viewing.",
            "multi_platform": "Create adjustment layers for platform-specific looks.",
            "audio": "Target -14 LUFS for YouTube, -16 LUFS for other platforms."
        }