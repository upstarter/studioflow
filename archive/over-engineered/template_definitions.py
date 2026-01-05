"""
Template definitions and registrations for StudioFlow
This module registers all available templates using the abstract template system
"""

from pathlib import Path
from typing import Dict, Any

from studioflow.core.templates import (
    TemplateRegistry,
    VideoEffectTemplate,
    ScriptPatternTemplate,
    EncodingProfileTemplate,
    ProjectTemplate,
    ComposableTemplate
)


# Initialize registries for different template types
video_effects_registry = TemplateRegistry[VideoEffectTemplate]()
script_patterns_registry = TemplateRegistry[ScriptPatternTemplate]()
encoding_profiles_registry = TemplateRegistry[EncodingProfileTemplate]()
project_templates_registry = TemplateRegistry[ProjectTemplate]()


def register_default_templates():
    """Register all default templates from NAS and built-in definitions"""

    # ============= VIDEO EFFECT TEMPLATES =============

    # HUD Overlays from NAS
    nas_scripts_path = Path("/mnt/nas/Archive/Projects/Scripts")

    if nas_scripts_path.exists():
        # Register HUD templates
        hud_templates = [
            ("radial_scanner", "CAH_HUD_RadialScanner.setting", "hud"),
            ("stinger_title", "CAH_Stinger_Title.setting", "transitions"),
            ("stinger_outro", "CAH_Stinger_Outro.setting", "transitions")
        ]

        for name, filename, category in hud_templates:
            effect_file = nas_scripts_path / filename
            if effect_file.exists():
                video_effects_registry.register(
                    name,
                    lambda n=name, f=effect_file: VideoEffectTemplate(
                        name=n,
                        effect_file=f,
                        parameters={
                            "glow_intensity": 1.0,
                            "flicker_amount": 0.3,
                            "color_preset": "cyan"
                        },
                        metadata={
                            "description": f"Iron Man style {n.replace('_', ' ').title()} overlay",
                            "author": "Creator AI Studio",
                            "version": "1.0"
                        }
                    ),
                    category=category
                )

    # Generic video effect template creator
    video_effects_registry.register(
        "custom_overlay",
        lambda name="custom_overlay": VideoEffectTemplate(
            name=name,
            effect_file=Path("custom.setting"),
            parameters={"opacity": 1.0, "blend_mode": "add"},
            metadata={"description": "Custom video overlay"}
        ),
        category="custom"
    )

    # ============= SCRIPT PATTERN TEMPLATES =============

    # Retention-optimized patterns
    script_patterns_registry.register(
        "retention_optimized",
        lambda: ScriptPatternTemplate(
            name="retention_optimized",
            structure={
                "intro": {
                    "duration": "0-15s",
                    "template": "Hook: {bold_claim}",
                    "techniques": ["cold_open", "striking_visual"],
                    "b_roll": ["product_shot", "result_preview"]
                },
                "tension": {
                    "duration": "15-45s",
                    "template": "Problem: {pain_point} - Stakes: {consequence}",
                    "techniques": ["agitate_problem", "build_curiosity"],
                    "b_roll": ["problem_demonstration", "comparison"]
                },
                "payoff": {
                    "duration": "45-120s",
                    "template": "Solution: {solution} - Proof: {demonstration}",
                    "techniques": ["reveal_method", "show_results"],
                    "b_roll": ["side_by_side", "benchmark", "visual_proof"]
                },
                "body": {
                    "duration": "2-8min",
                    "template": "Teach: {concept}\nShow: {demonstration}\nTell: {takeaway}",
                    "techniques": ["pattern_interrupts", "mini_loops"],
                    "b_roll": ["screen_recording", "cutaway", "meme_insert"]
                },
                "outro": {
                    "duration": "20-30s",
                    "template": "Recap: {value_delivered}\nNext: {teaser}",
                    "techniques": ["cta_stack", "end_screen"],
                    "b_roll": ["related_videos", "subscribe_animation"]
                }
            },
            hooks=[
                "This {topic} trick will change everything",
                "Nobody talks about this {topic} secret",
                "I discovered something about {topic} that shocked me",
                "99% of people get {topic} wrong. Here's why.",
                "What if I told you {topic} could {benefit}?"
            ],
            metadata={
                "description": "Maximizes retention with psychological triggers",
                "retention_target": "50%+ average view duration",
                "ctr_target": "7-10%"
            }
        ),
        category="viral"
    )

    # Tutorial pattern
    script_patterns_registry.register(
        "tutorial",
        lambda: ScriptPatternTemplate(
            name="tutorial",
            structure={
                "intro": {
                    "duration": "0-10s",
                    "template": "Learn {topic} in {duration}",
                    "techniques": ["set_expectations", "preview_outcome"]
                },
                "body": {
                    "duration": "3-10min",
                    "template": "Step {number}: {instruction}",
                    "techniques": ["numbered_steps", "visual_aids"]
                },
                "outro": {
                    "duration": "15-20s",
                    "template": "You learned: {summary}",
                    "techniques": ["recap", "next_steps"]
                }
            },
            metadata={"description": "Clear educational structure"}
        ),
        category="educational"
    )

    # ============= ENCODING PROFILE TEMPLATES =============

    # AV1 profiles
    encoding_profiles_registry.register(
        "av1_youtube_4k",
        lambda: EncodingProfileTemplate(
            name="av1_youtube_4k",
            codec="libsvtav1",
            settings={
                "preset": "6",
                "crf": "24",
                "pix_fmt": "yuv420p10le",
                "bitrate": "45M",
                "maxrate": "60M",
                "bufsize": "120M",
                "g": "240",
                "threads": "10",
                "svtav1-params": "tune=0",
                "color_primaries": "bt709",
                "color_trc": "bt709",
                "colorspace": "bt709",
                "color_range": "tv"
            },
            two_pass=False,
            metadata={
                "description": "Optimized for YouTube 4K with AV1 codec",
                "quality": "high",
                "compatibility": "modern_browsers"
            }
        ),
        category="youtube"
    )

    # H.264 fallback
    encoding_profiles_registry.register(
        "h264_universal",
        lambda: EncodingProfileTemplate(
            name="h264_universal",
            codec="libx264",
            settings={
                "preset": "slow",
                "crf": "18",
                "pix_fmt": "yuv420p",
                "bitrate": "12M",
                "maxrate": "16M",
                "bufsize": "32M",
                "profile:v": "high",
                "level": "4.2"
            },
            two_pass=True,
            metadata={
                "description": "Universal compatibility H.264",
                "quality": "high",
                "compatibility": "all_devices"
            }
        ),
        category="universal"
    )

    # Mezzanine/intermediate
    encoding_profiles_registry.register(
        "dnxhr_mezzanine",
        lambda: EncodingProfileTemplate(
            name="dnxhr_mezzanine",
            codec="dnxhd",
            settings={
                "profile:v": "dnxhr_hqx",
                "pix_fmt": "yuv422p10le",
                "auto_bitrate": True
            },
            two_pass=False,
            metadata={
                "description": "High-quality intermediate for further processing",
                "quality": "lossless",
                "use_case": "editing"
            }
        ),
        category="intermediate"
    )

    encoding_profiles_registry.register(
        "prores_master",
        lambda: EncodingProfileTemplate(
            name="prores_master",
            codec="prores_ks",
            settings={
                "profile:v": "3",  # ProRes 422 HQ
                "pix_fmt": "yuv422p10le",
                "auto_bitrate": True
            },
            two_pass=False,
            metadata={
                "description": "ProRes master for archival",
                "quality": "master",
                "use_case": "archival"
            }
        ),
        category="master"
    )

    # ============= PROJECT TEMPLATES =============

    # YouTube creator project
    project_templates_registry.register(
        "youtube_creator",
        lambda: ProjectTemplate(
            name="youtube_creator",
            structure={
                "directories": [
                    "01_MEDIA/A-Roll",
                    "01_MEDIA/B-Roll",
                    "01_MEDIA/Music",
                    "01_MEDIA/SFX",
                    "02_PROJECT/Resolve",
                    "02_PROJECT/Assets",
                    "03_EXPORTS/Drafts",
                    "03_EXPORTS/Final",
                    "03_EXPORTS/Thumbnails",
                    "04_DOCUMENTS/Scripts",
                    "04_DOCUMENTS/Notes"
                ],
                "configs": {
                    "project.yaml": {
                        "name": "{name}",
                        "type": "youtube",
                        "resolution": "3840x2160",
                        "framerate": 29.97,
                        "audio": {
                            "sample_rate": 48000,
                            "target_lufs": -14.0,
                            "true_peak": -1.0
                        },
                        "color": {
                            "space": "Rec.709",
                            "gamma": "2.4"
                        }
                    },
                    ".studioflow": {
                        "template": "youtube_creator",
                        "version": "1.0",
                        "created": "{timestamp}"
                    }
                }
            },
            workflows=["import", "organize", "edit", "optimize", "publish"],
            metadata={
                "description": "Complete YouTube production setup",
                "includes": ["4K timeline", "LUFS audio", "folder structure"]
            }
        ),
        category="video"
    )

    # Podcast project
    project_templates_registry.register(
        "podcast",
        lambda: ProjectTemplate(
            name="podcast",
            structure={
                "directories": [
                    "01_RECORDINGS/Raw",
                    "01_RECORDINGS/Processed",
                    "02_TRANSCRIPTS",
                    "03_EXPORTS/Episodes",
                    "03_EXPORTS/Clips",
                    "04_ASSETS/Intro",
                    "04_ASSETS/Outro",
                    "04_ASSETS/Music"
                ],
                "configs": {
                    "project.yaml": {
                        "name": "{name}",
                        "type": "podcast",
                        "audio": {
                            "sample_rate": 48000,
                            "bit_depth": 24,
                            "channels": 2,
                            "target_lufs": -16.0
                        }
                    }
                }
            },
            workflows=["record", "transcribe", "edit", "distribute"],
            metadata={
                "description": "Podcast production setup",
                "includes": ["transcription", "audio mastering"]
            }
        ),
        category="audio"
    )


def get_template(template_type: str, name: str) -> Any:
    """Get a template instance by type and name"""
    registries = {
        "video_effect": video_effects_registry,
        "script_pattern": script_patterns_registry,
        "encoding_profile": encoding_profiles_registry,
        "project": project_templates_registry
    }

    registry = registries.get(template_type)
    if not registry:
        raise ValueError(f"Unknown template type: {template_type}")

    template = registry.get(name)
    if not template:
        template = registry.create(name)

    return template


def list_templates(template_type: str = None, category: str = None) -> Dict[str, Any]:
    """List available templates"""
    if template_type:
        registries = {
            "video_effect": video_effects_registry,
            "script_pattern": script_patterns_registry,
            "encoding_profile": encoding_profiles_registry,
            "project": project_templates_registry
        }
        registry = registries.get(template_type)
        if registry:
            return {
                "type": template_type,
                "templates": registry.list_templates(category),
                "categories": registry.list_categories()
            }
    else:
        # Return all types
        return {
            "video_effects": video_effects_registry.list_templates(category),
            "script_patterns": script_patterns_registry.list_templates(category),
            "encoding_profiles": encoding_profiles_registry.list_templates(category),
            "project_templates": project_templates_registry.list_templates(category)
        }


# Register templates on module import
register_default_templates()