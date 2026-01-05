"""
Eric's specific StudioFlow configuration
Tailored for Sony FX30/ZVE10, DaVinci Resolve, YouTube content
"""

from pathlib import Path
from typing import Dict, Any


class MySetup:
    """Eric's production setup configuration"""

    # Camera Configuration
    CAMERAS = {
        "fx30": {
            "name": "Sony FX30",
            "sensor": "APS-C",
            "color_profile": "S-Log3",
            "color_space": "S-Gamut3.Cine",
            "base_iso": 800,
            "dual_iso": 2500,
            "resolution": "4K DCI (4096x2160)",
            "proxy_codec": "XAVC S-I",
            "file_pattern": "C*.MP4",  # Sony file naming
            "record_format": "XAVC S 4K",
            "bitrate": "200Mbps",
            "audio": "24bit 48kHz"
        },
        "zve10": {
            "name": "Sony ZV-E10",
            "sensor": "APS-C",
            "color_profile": "S-Log2",  # or Picture Profiles
            "resolution": "4K (3840x2160)",
            "file_pattern": "DSC*.MP4",
            "record_format": "XAVC S",
            "bitrate": "100Mbps",
            "focus": "Real-time Eye AF",
            "stabilization": "Active SteadyShot"
        }
    }

    # DaVinci Resolve Configuration
    RESOLVE = {
        "version": "18.6",  # Your version
        "database": "PostgreSQL",
        "project_settings": {
            "timeline_resolution": "3840x2160",  # 4K UHD
            "timeline_framerate": "29.97",  # or 30
            "working_colorspace": "DaVinci Wide Gamut",
            "output_colorspace": "Rec.709-A",
            "gpu_processing": "Metal",  # or CUDA/OpenCL
            "cache_format": "ProRes 422 Proxy"
        },
        "render_presets": {
            "youtube_4k": {
                "format": "QuickTime",
                "codec": "H.264",
                "resolution": "3840x2160",
                "framerate": "original",
                "quality": "Automatic",  # Best quality
                "bitrate": "45000",  # YouTube recommended for 4K
                "profile": "High",
                "audio_codec": "AAC",
                "audio_bitrate": "320"
            },
            "youtube_1080": {
                "format": "QuickTime",
                "codec": "H.264",
                "resolution": "1920x1080",
                "framerate": "original",
                "bitrate": "8000",  # YouTube recommended for 1080p
                "profile": "High",
                "audio_codec": "AAC",
                "audio_bitrate": "320"
            }
        }
    }

    # Color Grading
    COLOR = {
        "primary_lut": "Orange_Teal_Classic.cube",
        "luts": {
            "orange_teal": "/mnt/nas/LUTs/Orange_Teal_Classic.cube",
            "cinematic": "/mnt/nas/LUTs/Cinematic_Film.cube",
            "sony_slog3_rec709": "/mnt/nas/LUTs/Sony_Slog3_to_Rec709.cube",
            "youtube": "/mnt/nas/LUTs/YouTube_Vibrant.cube"
        },
        "color_workflow": [
            "Apply S-Log3 to Rec.709 conversion",
            "Color balance/exposure correction",
            "Apply orange/teal LUT at 75% intensity",
            "Selective color adjustments",
            "Add film grain (optional)"
        ],
        "nodes_template": {
            "node_1": "Input S-Log3",
            "node_2": "Color Space Transform",
            "node_3": "Primary Corrections",
            "node_4": "Orange/Teal LUT",
            "node_5": "Skin Tone Protection",
            "node_6": "Vignette",
            "node_7": "Output"
        }
    }

    # YouTube Specifications
    YOUTUBE = {
        "channel": "YourChannelName",  # Update this
        "content_types": {
            "episode": {
                "duration": "10-20 minutes",
                "resolution": "4K (3840x2160)",
                "framerate": "29.97fps",
                "thumbnail": "1920x1080",
                "format": "16:9"
            },
            "short": {
                "duration": "< 60 seconds",
                "resolution": "1080x1920",  # Vertical
                "framerate": "30fps",
                "format": "9:16"
            }
        },
        "audio": {
            "lufs": -14,  # YouTube's loudness standard
            "true_peak": -1,  # dB
            "sample_rate": 48000,
            "bit_depth": 24,
            "codec": "AAC",
            "bitrate": 320  # kbps
        },
        "upload": {
            "title_template": "Episode {number}: {title}",
            "description_template": """Episode {number} of [Series Name]

{description}

Timestamps:
00:00 Intro
{timestamps}

Equipment:
• Sony FX30 Cinema Camera
• Sony ZV-E10
• DaVinci Resolve Studio

#SonyFX30 #CinematicVideo #ColorGrading""",
            "tags": [
                "Sony FX30",
                "Cinematic",
                "Color Grading",
                "Orange Teal",
                "4K Video"
            ],
            "category": "Film & Animation",  # or your category
            "visibility": "public"
        }
    }

    # File Organization
    STORAGE = {
        "base": Path.home() / "StudioFlow",
        "nas": Path("/mnt/nas"),
        "structure": {
            "episodes": "{base}/Episodes/EP{number:03d}_{name}",
            "shorts": "{base}/Shorts/{date}_{name}",
            "raw": "{project}/01_RAW/{camera}/{date}",
            "proxies": "{project}/02_Proxies",
            "resolve": "{project}/03_Resolve",
            "color": "{project}/04_Color",
            "exports": "{project}/05_Exports",
            "thumbnails": "{project}/06_Thumbnails",
            "uploads": "{project}/07_YouTube"
        },
        "archive_after_days": 30,
        "proxy_after_gb": 100
    }

    # Workflow Automation
    WORKFLOW = {
        "import": {
            "auto_organize": True,
            "verify_checksums": True,
            "create_proxies": True,
            "detect_camera": True,  # Auto-detect FX30 vs ZVE10
            "apply_metadata": True
        },
        "episode_pipeline": [
            "Import from camera cards",
            "Organize by camera and take",
            "Generate proxies (ProRes 422 Proxy)",
            "Create Resolve project from template",
            "Apply base color grade (S-Log3 → Rec.709)",
            "Apply orange/teal LUT",
            "Edit in Resolve",
            "Audio normalization to -14 LUFS",
            "Export at 4K H.264 45Mbps",
            "Generate thumbnail (custom or auto)",
            "Upload to YouTube"
        ],
        "short_pipeline": [
            "Import from ZV-E10",
            "Quick cut to < 60s",
            "Vertical crop (9:16)",
            "Punchy color grade",
            "Text overlays",
            "Export for YouTube Shorts"
        ]
    }

    # Quick Commands (your most used)
    QUICK_COMMANDS = {
        "episode": "sf episode new",
        "import_fx30": "sf import /media/fx30",
        "import_zve10": "sf import /media/zve10",
        "grade": "sf grade orange-teal",
        "export": "sf export youtube-4k",
        "upload": "sf upload episode",
        "check": "sf check lufs"
    }

    # Default Settings
    DEFAULTS = {
        "camera": "fx30",
        "resolution": "3840x2160",
        "framerate": 29.97,
        "color_profile": "S-Log3",
        "lut": "orange_teal",
        "export_preset": "youtube_4k",
        "audio_lufs": -14,
        "auto_normalize": True,
        "auto_backup": True,
        "create_proxies": True,
        "thumbnail_at": "best_scene"  # or specific timecode
    }

    @classmethod
    def get_camera_settings(cls, camera: str) -> Dict[str, Any]:
        """Get specific camera settings"""
        return cls.CAMERAS.get(camera, cls.CAMERAS["fx30"])

    @classmethod
    def get_youtube_spec(cls, content_type: str = "episode") -> Dict[str, Any]:
        """Get YouTube specifications"""
        return cls.YOUTUBE["content_types"].get(content_type, cls.YOUTUBE["content_types"]["episode"])

    @classmethod
    def get_lut_path(cls, name: str = "orange_teal") -> Path:
        """Get LUT file path"""
        lut_path = cls.COLOR["luts"].get(name)
        if lut_path:
            return Path(lut_path)
        return Path(cls.COLOR["luts"]["orange_teal"])

    @classmethod
    def get_episode_path(cls, episode_number: int, name: str) -> Path:
        """Get episode project path"""
        base = cls.STORAGE["base"]
        return base / "Episodes" / f"EP{episode_number:03d}_{name}"

    @classmethod
    def get_export_settings(cls, preset: str = "youtube_4k") -> Dict[str, Any]:
        """Get export settings for Resolve"""
        return cls.RESOLVE["render_presets"].get(preset, cls.RESOLVE["render_presets"]["youtube_4k"])

    @classmethod
    def detect_camera_from_file(cls, file_path: Path) -> str:
        """Detect which camera from file naming"""
        name = file_path.name.upper()
        if name.startswith("C") and "MP4" in name:
            return "fx30"
        elif name.startswith("DSC"):
            return "zve10"
        return "fx30"  # default

    @classmethod
    def get_color_workflow(cls) -> list:
        """Get color grading workflow steps"""
        return cls.COLOR["color_workflow"]

    @classmethod
    def get_youtube_metadata(cls, episode_number: int, title: str, description: str = "") -> Dict[str, Any]:
        """Generate YouTube metadata"""
        return {
            "title": cls.YOUTUBE["upload"]["title_template"].format(
                number=episode_number,
                title=title
            ),
            "description": cls.YOUTUBE["upload"]["description_template"].format(
                number=episode_number,
                description=description,
                timestamps="01:00 Main Content\n05:00 Key Point\n10:00 Conclusion"
            ),
            "tags": cls.YOUTUBE["upload"]["tags"],
            "category": cls.YOUTUBE["upload"]["category"],
            "visibility": cls.YOUTUBE["upload"]["visibility"]
        }