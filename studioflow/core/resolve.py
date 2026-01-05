"""
DaVinci Resolve integration for professional editing
Simplified but powerful API
"""

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import timedelta
import json


@dataclass
class TimelineClip:
    """Clip on timeline"""
    file_path: Path
    start_time: float  # Timeline position
    duration: float
    in_point: float = 0  # Clip in point
    out_point: Optional[float] = None  # Clip out point
    track: int = 1
    effects: List[str] = None


@dataclass
class ResolveProject:
    """Resolve project configuration"""
    name: str
    resolution: str = "1920x1080"
    framerate: float = 30.0
    clips: List[TimelineClip] = None
    color_grade: Optional[str] = None
    output_preset: str = "YouTube"


class ResolveIntegration:
    """Simplified DaVinci Resolve integration"""

    # Common Resolve paths
    RESOLVE_PATHS = {
        "linux": "/opt/resolve/bin/resolve",
        "mac": "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/MacOS/Resolve",
        "windows": "C:/Program Files/Blackmagic Design/DaVinci Resolve/Resolve.exe"
    }

    # Professional presets
    EXPORT_PRESETS = {
        "YouTube_4K": {
            "format": "mp4",
            "codec": "h264",
            "resolution": "3840x2160",
            "bitrate": 45000,
            "audio_codec": "aac",
            "audio_bitrate": 320
        },
        "YouTube": {
            "format": "mp4",
            "codec": "h264",
            "resolution": "1920x1080",
            "bitrate": 8000,
            "audio_codec": "aac",
            "audio_bitrate": 320
        },
        "ProRes_422": {
            "format": "mov",
            "codec": "prores",
            "profile": "422",
            "resolution": "1920x1080",
            "audio_codec": "pcm_s16le"
        },
        "ProRes_4444": {
            "format": "mov",
            "codec": "prores",
            "profile": "4444",
            "resolution": "3840x2160",
            "audio_codec": "pcm_s24le"
        },
        "DNxHD": {
            "format": "mxf",
            "codec": "dnxhd",
            "resolution": "1920x1080",
            "bitrate": 175000,
            "audio_codec": "pcm_s16le"
        },
        "Cinema_DCP": {
            "format": "dcp",
            "codec": "jpeg2000",
            "resolution": "2048x1080",
            "bitrate": 250000,
            "color_space": "xyz"
        }
    }

    # Color grading LUTs
    COLOR_GRADES = {
        "cinematic": "Cinematic_Warm.cube",
        "hollywood": "Hollywood_Orange_Teal.cube",
        "vintage": "Vintage_Film.cube",
        "noir": "Black_White_Contrast.cube",
        "documentary": "Natural_Enhanced.cube",
        "commercial": "Clean_Vibrant.cube"
    }

    @staticmethod
    def check_resolve() -> bool:
        """Check if Resolve is installed"""
        import platform

        system = platform.system().lower()
        if system == "darwin":
            system = "mac"
        elif system == "windows":
            system = "windows"
        else:
            system = "linux"

        resolve_path = ResolveIntegration.RESOLVE_PATHS.get(system)
        if resolve_path and Path(resolve_path).exists():
            return True
        return False

    @staticmethod
    def create_timeline_xml(project: ResolveProject, output_path: Path) -> bool:
        """Create FCPXML for Resolve import"""

        # Create FCPXML structure
        root = ET.Element("fcpxml", version="1.9")

        # Resources section
        resources = ET.SubElement(root, "resources")

        # Add format
        format_elem = ET.SubElement(resources, "format", {
            "id": "r1",
            "name": f"FFVideoFormat{project.resolution}p{project.framerate}",
            "frameDuration": f"{1}/{int(project.framerate)}s",
            "width": project.resolution.split('x')[0],
            "height": project.resolution.split('x')[1]
        })

        # Add media assets
        for i, clip in enumerate(project.clips or []):
            asset = ET.SubElement(resources, "asset", {
                "id": f"asset_{i}",
                "src": str(clip.file_path.absolute()),
                "format": "r1"
            })

        # Create event/project
        event = ET.SubElement(root, "event", {"name": project.name})
        timeline_elem = ET.SubElement(event, "project", {"name": project.name})

        # Create sequence
        sequence = ET.SubElement(timeline_elem, "sequence", {
            "format": "r1",
            "duration": f"{sum(c.duration for c in project.clips or [])}s"
        })

        # Create spine (main timeline)
        spine = ET.SubElement(sequence, "spine")

        # Add clips to timeline
        for i, clip in enumerate(project.clips or []):
            clip_elem = ET.SubElement(spine, "asset-clip", {
                "ref": f"asset_{i}",
                "offset": f"{clip.start_time}s",
                "duration": f"{clip.duration}s",
                "start": f"{clip.in_point}s"
            })

            # Add effects if any
            if clip.effects:
                for effect in clip.effects:
                    ResolveIntegration._add_effect_to_clip(clip_elem, effect)

        # Write XML
        tree = ET.ElementTree(root)
        tree.write(str(output_path), encoding="UTF-8", xml_declaration=True)
        return True

    @staticmethod
    def _add_effect_to_clip(clip_elem: ET.Element, effect: str):
        """Add effect to clip in XML"""

        effect_mappings = {
            "fade_in": {"filter": "fadeIn", "duration": "1s"},
            "fade_out": {"filter": "fadeOut", "duration": "1s"},
            "blur": {"filter": "gaussianBlur", "amount": "20"},
            "sharpen": {"filter": "sharpen", "amount": "0.5"},
            "stabilize": {"filter": "stabilization", "method": "automatic"},
            "speed_2x": {"filter": "retiming", "rate": "2.0"},
            "reverse": {"filter": "retiming", "rate": "-1.0"}
        }

        if effect in effect_mappings:
            filter_data = effect_mappings[effect]
            filter_elem = ET.SubElement(clip_elem, "filter-video", {
                "ref": filter_data["filter"],
                "name": effect
            })

            # Add parameters
            for key, value in filter_data.items():
                if key != "filter":
                    param = ET.SubElement(filter_elem, "param", {
                        "name": key,
                        "value": value
                    })

    @staticmethod
    def create_edit_script(project: ResolveProject) -> str:
        """Create Python script for Resolve's scripting API"""

        script = f"""#!/usr/bin/env python
# DaVinci Resolve Edit Script
# Generated by StudioFlow

import DaVinciResolveScript as dvr

# Get Resolve instance
resolve = dvr.scriptapp("Resolve")
projectManager = resolve.GetProjectManager()

# Create new project
project = projectManager.CreateProject("{project.name}")
if not project:
    project = projectManager.LoadProject("{project.name}")

# Get media pool and timeline
mediaPool = project.GetMediaPool()
rootFolder = mediaPool.GetRootFolder()

# Set project settings
project.SetSetting("timelineResolutionWidth", "{project.resolution.split('x')[0]}")
project.SetSetting("timelineResolutionHeight", "{project.resolution.split('x')[1]}")
project.SetSetting("timelineFrameRate", "{project.framerate}")

# Import clips
clips = []
"""

        # Add clip imports
        for clip in project.clips or []:
            script += f"""
clip = mediaPool.ImportMedia(["{clip.file_path.absolute()}"])[0]
clips.append(clip)
"""

        # Create timeline
        script += f"""
# Create timeline
timeline = mediaPool.CreateTimelineFromClips("{project.name}", clips)

# Apply color grade if specified
if "{project.color_grade}":
    # Apply LUT to timeline
    timeline.ApplyGradeFromDRX("{project.color_grade}")

# Set up for export
project.SetRenderSettings({{
    "SelectAllFrames": True,
    "TargetDir": "/exports",
    "CustomName": "{project.name}_export",
    "FormatWidth": {project.resolution.split('x')[0]},
    "FormatHeight": {project.resolution.split('x')[1]},
    "FrameRate": {project.framerate}
}})

print("Project created successfully!")
"""
        return script

    @staticmethod
    def apply_color_grade(video_path: Path, grade: str, output_path: Path) -> bool:
        """Apply color grade using LUT"""

        lut_file = ResolveIntegration.COLOR_GRADES.get(grade)
        if not lut_file:
            return False

        # Use FFmpeg with LUT (fallback when Resolve not available)
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-vf", f"lut3d={lut_file}",
            "-c:a", "copy",
            "-y", str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def create_proxy_media(video_path: Path, proxy_dir: Path) -> Path:
        """Create proxy media for faster editing"""

        proxy_dir.mkdir(parents=True, exist_ok=True)
        proxy_path = proxy_dir / f"{video_path.stem}_proxy.mp4"

        # Create low-res proxy
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-vf", "scale=960:-1",  # Half resolution
            "-c:v", "libx264",
            "-preset", "superfast",
            "-crf", "25",
            "-c:a", "aac", "-b:a", "128k",
            "-y", str(proxy_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return proxy_path
        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def create_multicam_sync(clips: List[Path], output_path: Path,
                            sync_method: str = "audio") -> bool:
        """Sync multiple camera angles"""

        if sync_method == "audio":
            # Use audio waveform matching
            # This is simplified - real implementation would use audio fingerprinting

            # For now, just stack videos (simplified)
            filter_complex = ""
            for i in range(len(clips)):
                row = i // 2
                col = i % 2
                filter_complex += f"[{i}:v]scale=960:540,setpts=PTS-STARTPTS[v{i}];"

            # Create grid
            if len(clips) == 2:
                filter_complex += "[v0][v1]hstack=inputs=2[out]"
            elif len(clips) == 4:
                filter_complex += "[v0][v1]hstack=inputs=2[top];[v2][v3]hstack=inputs=2[bot];[top][bot]vstack=inputs=2[out]"
            else:
                filter_complex += "[v0]copy[out]"

            cmd = ["ffmpeg"]
            for clip in clips:
                cmd.extend(["-i", str(clip)])

            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-map", "0:a",  # Use first audio
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                "-y", str(output_path)
            ])

            try:
                subprocess.run(cmd, check=True, capture_output=True)
                return True
            except subprocess.CalledProcessError:
                return False

        return False

    @staticmethod
    def export_edl(project: ResolveProject, output_path: Path):
        """Export Edit Decision List"""

        edl_content = f"TITLE: {project.name}\n"
        edl_content += f"FCM: NON-DROP FRAME\n\n"

        for i, clip in enumerate(project.clips or [], 1):
            # EDL format: edit# reel# channel operation [duration] [src_in] [src_out] [rec_in] [rec_out]
            tc_in = ResolveIntegration._seconds_to_timecode(clip.in_point, project.framerate)
            tc_out = ResolveIntegration._seconds_to_timecode(
                clip.in_point + clip.duration, project.framerate
            )
            tc_rec_in = ResolveIntegration._seconds_to_timecode(clip.start_time, project.framerate)
            tc_rec_out = ResolveIntegration._seconds_to_timecode(
                clip.start_time + clip.duration, project.framerate
            )

            edl_content += f"{i:03d}  {clip.file_path.stem}  V  C  "
            edl_content += f"{tc_in} {tc_out} {tc_rec_in} {tc_rec_out}\n"
            edl_content += f"* FROM CLIP NAME: {clip.file_path.name}\n\n"

        output_path.write_text(edl_content)

    @staticmethod
    def _seconds_to_timecode(seconds: float, fps: float) -> str:
        """Convert seconds to timecode"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        frames = int((seconds % 1) * fps)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"

    @staticmethod
    def generate_dailies(media_dir: Path, output_dir: Path,
                        burn_in_tc: bool = True) -> List[Path]:
        """Generate dailies with burned-in timecode"""

        output_dir.mkdir(parents=True, exist_ok=True)
        dailies = []

        for video_file in media_dir.glob("*.mp4"):
            daily_path = output_dir / f"{video_file.stem}_daily.mp4"

            if burn_in_tc:
                # Add timecode overlay
                cmd = [
                    "ffmpeg", "-i", str(video_file),
                    "-vf", "drawtext=text='%{pts\\:hms}':x=10:y=10:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5",
                    "-c:a", "copy",
                    "-y", str(daily_path)
                ]
            else:
                # Just copy
                cmd = [
                    "ffmpeg", "-i", str(video_file),
                    "-c", "copy",
                    "-y", str(daily_path)
                ]

            try:
                subprocess.run(cmd, check=True, capture_output=True)
                dailies.append(daily_path)
            except subprocess.CalledProcessError:
                continue

        return dailies