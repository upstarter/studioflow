"""
Advanced DaVinci Resolve AI Integration
Intelligent project management and automation
"""

import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import re

from .ffmpeg import FFmpegProcessor
from .sony import SonyClip, SonyMediaHandler


@dataclass
class MediaAnalysis:
    """Detailed media analysis results"""
    file_path: Path
    camera_type: str  # fx30, zve10, unknown
    shot_type: str  # wide, medium, close, extreme_close, broll
    quality_score: float  # 0-100
    technical_issues: List[str] = field(default_factory=list)
    content_type: str = ""  # talking_head, action, static, establishing
    scene_number: Optional[int] = None
    take_number: Optional[int] = None
    has_speech: bool = False
    faces_detected: int = 0
    is_shaky: bool = False
    exposure_rating: str = "normal"  # under, normal, over
    audio_level: str = "normal"  # silent, quiet, normal, loud
    best_thumbnail_time: Optional[float] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SmartBin:
    """Intelligent bin structure"""
    name: str
    icon: str  # emoji for visual organization
    description: str
    filter_rules: Dict[str, Any]
    clips: List[MediaAnalysis] = field(default_factory=list)
    sub_bins: List['SmartBin'] = field(default_factory=list)


@dataclass
class RenderJob:
    """Render queue job"""
    name: str
    preset: str
    priority: int  # 1 = highest
    timeline: str
    output_path: Path
    settings: Dict[str, Any]
    status: str = "queued"  # queued, rendering, complete, failed
    progress: float = 0.0
    estimated_time: Optional[float] = None


class ResolveProjectAI:
    """Smart Resolve project orchestrator"""

    def __init__(self):
        self.media_analyses = []
        self.project_settings = {}
        self.bins = []
        self.render_queue = []

    def auto_setup_project(self, media_dir: Path, project_name: str = None) -> Dict:
        """Intelligently setup complete Resolve project"""

        print("🧠 Analyzing media for intelligent project setup...")

        # 1. Deep media analysis
        self.media_analyses = self.analyze_media_characteristics(media_dir)

        # 2. Determine optimal project settings
        self.project_settings = self.determine_project_settings()

        # 3. Create intelligent bin structure
        self.bins = self.create_intelligent_bins()

        # 4. Generate project name if not provided
        if not project_name:
            project_name = self.generate_project_name()

        # 5. Create Resolve project
        project_path = self.create_resolve_project(project_name)

        # 6. Setup color management
        self.setup_color_management()

        # 7. Import and organize media
        self.import_and_organize_media()

        # 8. Create smart timelines
        timelines = self.create_smart_timelines()

        return {
            "project_name": project_name,
            "project_path": project_path,
            "media_count": len(self.media_analyses),
            "settings": self.project_settings,
            "bins": len(self.bins),
            "timelines": timelines
        }

    def analyze_media_characteristics(self, media_dir: Path) -> List[MediaAnalysis]:
        """Deep analysis of all media files"""

        analyses = []
        # Match both uppercase and lowercase extensions
        media_files = []
        for ext in ["*.mp4", "*.MP4", "*.mov", "*.MOV", "*.mxf", "*.MXF", "*.avi", "*.AVI"]:
            media_files.extend(media_dir.rglob(ext))

        for file in media_files:
            print(f"  Analyzing: {file.name}")

            analysis = MediaAnalysis(
                file_path=file,
                camera_type=self.detect_camera_type(file),
                shot_type=self.analyze_shot_type(file),
                quality_score=self.calculate_quality_score(file),
                technical_issues=self.detect_technical_issues(file),
                content_type=self.classify_content_type(file),
                scene_number=self.extract_scene_number(file),
                take_number=self.extract_take_number(file),
                has_speech=self.detect_speech(file),
                faces_detected=self.count_faces(file),
                is_shaky=self.detect_shake(file),
                exposure_rating=self.analyze_exposure(file),
                audio_level=self.analyze_audio_level(file),
                best_thumbnail_time=self.find_best_thumbnail_moment(file),
                duration=self.get_duration(file)
            )

            analyses.append(analysis)

        return analyses

    def detect_camera_type(self, file: Path) -> str:
        """Detect camera from file naming and metadata"""
        name = file.name.upper()
        if name.startswith("C") and "MP4" in name:
            return "fx30"
        elif name.startswith("DSC"):
            return "zve10"
        return "unknown"

    def analyze_shot_type(self, file: Path) -> str:
        """Analyze framing/shot type using FFmpeg analysis"""
        # Simplified - would use scene detection in real implementation
        info = FFmpegProcessor.get_media_info(file)
        resolution = info.get("resolution", "")

        # Basic heuristics (would use ML in production)
        if "4096" in resolution:
            return "wide"  # DCI 4K usually for wide shots

        face_count = self.count_faces(file)
        if face_count == 1:
            return "close"
        elif face_count > 1:
            return "medium"

        return "broll"

    def calculate_quality_score(self, file: Path) -> float:
        """
        Calculate overall quality score (fallback metric)
        
        Note: This is a fallback metric when audio markers are not available.
        Audio markers (via RoughCutEngine) take precedence for clip ordering and selection.
        Priority: 1) Audio markers, 2) quality_score (this method), 3) File-based sorting
        """
        score = 100.0

        # Check technical aspects
        if self.detect_shake(file):
            score -= 20

        exposure = self.analyze_exposure(file)
        if exposure == "under":
            score -= 15
        elif exposure == "over":
            score -= 10

        audio = self.analyze_audio_level(file)
        if audio == "silent":
            score -= 30
        elif audio == "quiet":
            score -= 10
        elif audio == "loud":
            score -= 5

        return max(0, score)

    def detect_technical_issues(self, file: Path) -> List[str]:
        """Detect technical problems"""
        issues = []

        if self.detect_shake(file):
            issues.append("shaky")

        exposure = self.analyze_exposure(file)
        if exposure != "normal":
            issues.append(f"exposure_{exposure}")

        audio = self.analyze_audio_level(file)
        if audio != "normal":
            issues.append(f"audio_{audio}")

        # Check for black frames
        if self.has_black_frames(file):
            issues.append("black_frames")

        return issues

    def classify_content_type(self, file: Path) -> str:
        """
        Classify content type from filename only
        
        DEPRECATED: Complex detection removed. Will be replaced by audio marker "type" commands.
        Now only does basic filename prefix detection as minimal fallback.
        """
        # TODO: Replace with audio marker "type" commands (camera, screen, broll)
        # Minimal filename-based fallback only
        name_lower = file.name.lower()
        if "screen" in name_lower or "scrn" in name_lower:
            return "screen_recording"
        elif "broll" in name_lower or "b-roll" in name_lower:
            return "broll"
        elif "cam" in name_lower:
            return "talking_head"
        return "unknown"

    def extract_scene_number(self, file: Path) -> Optional[int]:
        """
        Extract scene number from filename
        
        DEPRECATED: Will be replaced by audio marker "naming" commands.
        Returns None for now - scene/organization will come from audio markers.
        """
        # TODO: Replace with audio marker-based segment naming
        return None

    def extract_take_number(self, file: Path) -> Optional[int]:
        """
        Extract take number from filename (basic only)
        
        Simplified - removed Sony-specific logic. Take numbering will primarily
        come from audio marker "take" commands (or deprecated "order" commands).
        """
        # Basic filename pattern only (no camera-specific logic)
        match = re.search(r'take[_-]?(\d+)', file.name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def detect_speech(self, file: Path) -> bool:
        """Detect if file contains speech"""
        # Use FFmpeg to analyze audio
        cmd = [
            "ffmpeg", "-i", str(file),
            "-af", "silencedetect=n=-30dB:d=0.5",
            "-f", "null", "-"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            # If there are non-silent parts, likely has speech
            return "silence_end" in result.stderr
        except:
            return False

    def count_faces(self, file: Path) -> int:
        """Count faces in video (simplified)"""
        # In production, would use OpenCV or ML model
        # For now, return 0 or make educated guess
        if "interview" in file.name.lower() or "talking" in file.name.lower():
            return 1
        return 0

    def detect_shake(self, file: Path) -> bool:
        """Detect if footage is shaky"""
        # Would use motion vector analysis in production
        return "handheld" in file.name.lower()

    def analyze_exposure(self, file: Path) -> str:
        """Analyze exposure levels"""
        # Simplified - would analyze histogram in production
        return "normal"

    def analyze_audio_level(self, file: Path) -> str:
        """Analyze audio levels"""
        cmd = [
            "ffmpeg", "-i", str(file),
            "-af", "volumedetect",
            "-f", "null", "-"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            # Parse mean volume
            if "mean_volume" in result.stderr:
                match = re.search(r'mean_volume:\s*([-\d.]+)', result.stderr)
                if match:
                    mean_db = float(match.group(1))
                    if mean_db < -40:
                        return "silent"
                    elif mean_db < -25:
                        return "quiet"
                    elif mean_db > -10:
                        return "loud"
            return "normal"
        except:
            return "normal"

    def find_best_thumbnail_moment(self, file: Path) -> Optional[float]:
        """Find best moment for thumbnail"""
        # Would use scene detection and composition analysis
        info = FFmpegProcessor.get_media_info(file)
        duration = info.get("duration_seconds", 10)

        # Use golden ratio for now
        return duration * 0.382

    def get_duration(self, file: Path) -> float:
        """Get file duration"""
        info = FFmpegProcessor.get_media_info(file)
        return info.get("duration_seconds", 0)

    def detect_motion(self, file: Path) -> bool:
        """Detect if video has significant motion"""
        return "action" in file.name.lower() or "move" in file.name.lower()

    def has_black_frames(self, file: Path) -> bool:
        """Check for black frames at start/end"""
        # Simplified check
        return False

    def determine_project_settings(self) -> Dict:
        """Determine optimal project settings from media analysis"""

        # Analyze all media to find best settings
        resolutions = []
        framerates = []
        cameras = defaultdict(int)

        for analysis in self.media_analyses:
            info = FFmpegProcessor.get_media_info(analysis.file_path)
            resolutions.append(info.get("resolution", "1920x1080"))
            framerates.append(info.get("fps", 30))
            cameras[analysis.camera_type] += 1

        # Find most common/highest quality settings
        primary_camera = max(cameras, key=cameras.get) if cameras else "fx30"

        # Determine resolution (use highest)
        if "4096x2160" in resolutions or "3840x2160" in resolutions:
            resolution = "3840x2160"  # 4K UHD
            timeline_resolution = "3840x2160"
        else:
            resolution = "1920x1080"
            timeline_resolution = "1920x1080"

        # Determine framerate (use most common)
        framerate = max(set(framerates), key=framerates.count) if framerates else 29.97

        return {
            "name": f"EP_{datetime.now().strftime('%Y%m%d')}",
            "resolution": resolution,
            "timeline_resolution": timeline_resolution,
            "framerate": framerate,
            "color_science": "DaVinci YRGB Color Managed",
            "working_colorspace": "DaVinci Wide Gamut",
            "timeline_colorspace": "Rec.709-A",
            "primary_camera": primary_camera,
            "gpu_processing": "Metal",  # or CUDA based on system
            "cache_format": "ProRes 422 Proxy",
            "optimized_media": True,
            "proxy_mode": "Half Resolution"
        }

    def create_intelligent_bins(self) -> List[SmartBin]:
        """Create smart bin structure"""

        bins = []

        # Main camera bins
        fx30_bin = SmartBin(
            name="FX30 - A Camera",
            icon="🎥",
            description="Sony FX30 footage (S-Log3)",
            filter_rules={"camera_type": "fx30"}
        )

        zve10_bin = SmartBin(
            name="ZV-E10 - B Camera",
            icon="📹",
            description="Sony ZV-E10 footage",
            filter_rules={"camera_type": "zve10"}
        )

        # Quality-based bins
        hero_bin = SmartBin(
            name="Hero Shots",
            icon="⭐",
            description="Best quality shots",
            filter_rules={"quality_score": {"$gte": 85}}
        )

        fix_needed_bin = SmartBin(
            name="Needs Fixing",
            icon="⚠️",
            description="Shots with technical issues",
            filter_rules={"technical_issues": {"$exists": True, "$ne": []}}
        )

        # Content-based bins
        talking_head_bin = SmartBin(
            name="Talking Head",
            icon="🗣️",
            description="Interview/presentation shots",
            filter_rules={"content_type": "talking_head"}
        )

        broll_bin = SmartBin(
            name="B-Roll",
            icon="🎬",
            description="Supplementary footage",
            filter_rules={"content_type": "broll"}
        )

        # Organize clips into bins
        for analysis in self.media_analyses:
            # Camera bins
            if analysis.camera_type == "fx30":
                fx30_bin.clips.append(analysis)
            elif analysis.camera_type == "zve10":
                zve10_bin.clips.append(analysis)

            # Quality bins
            if analysis.quality_score >= 85:
                hero_bin.clips.append(analysis)
            if analysis.technical_issues:
                fix_needed_bin.clips.append(analysis)

            # Content bins
            if analysis.content_type == "talking_head":
                talking_head_bin.clips.append(analysis)
            elif analysis.content_type == "broll":
                broll_bin.clips.append(analysis)

        # TODO: Create scene-based organization from audio marker "naming" commands
        # Scene-based sub-bins removed - will be organized by marker segments when implemented

        bins.extend([fx30_bin, zve10_bin, hero_bin, fix_needed_bin, talking_head_bin, broll_bin])

        return bins

    def generate_project_name(self) -> str:
        """Generate intelligent project name"""
        # Base it on date and primary content
        date = datetime.now().strftime("%Y%m%d")

        # Analyze content to determine type
        content_types = [a.content_type for a in self.media_analyses]
        primary_content = max(set(content_types), key=content_types.count) if content_types else "project"

        # Check for episode number in filenames
        ep_match = None
        for analysis in self.media_analyses:
            match = re.search(r'ep[_-]?(\d+)', analysis.file_path.name, re.IGNORECASE)
            if match:
                ep_match = match.group(1)
                break

        if ep_match:
            return f"EP{ep_match.zfill(3)}_{date}"
        else:
            return f"{primary_content}_{date}"

    def create_resolve_project(self, project_name: str) -> Path:
        """Create actual Resolve project"""
        # Create project structure
        project_path = Path.home() / "StudioFlow" / "ResolveProjects" / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        # Create DRB (Resolve project) structure
        (project_path / "MediaFiles").mkdir(exist_ok=True)
        (project_path / "CacheFiles").mkdir(exist_ok=True)
        (project_path / "ProxyMedia").mkdir(exist_ok=True)
        (project_path / "RenderCache").mkdir(exist_ok=True)

        # Save project settings
        settings_file = project_path / "project_settings.json"
        settings_file.write_text(json.dumps(self.project_settings, indent=2))

        # Generate project file (would use Resolve API in production)
        self.generate_project_file(project_path, project_name)

        return project_path

    def generate_project_file(self, project_path: Path, project_name: str):
        """Generate Resolve project file"""
        # Create FCPXML for import
        root = ET.Element("fcpxml", version="1.9")

        # Add resources
        resources = ET.SubElement(root, "resources")

        # Define format based on settings
        format_elem = ET.SubElement(resources, "format", {
            "id": "r1",
            "name": "HD",
            "frameDuration": f"1001/{int(self.project_settings['framerate'] * 1000)}s",
            "width": self.project_settings['resolution'].split('x')[0],
            "height": self.project_settings['resolution'].split('x')[1],
            "colorSpace": "rec709"
        })

        # Add all media as assets
        for i, analysis in enumerate(self.media_analyses):
            asset = ET.SubElement(resources, "asset", {
                "id": f"asset_{i}",
                "name": analysis.file_path.stem,
                "src": str(analysis.file_path),
                "format": "r1"
            })

            # Add metadata
            if analysis.metadata:
                metadata = ET.SubElement(asset, "metadata")
                for key, value in analysis.metadata.items():
                    ET.SubElement(metadata, "md", {"key": key, "value": str(value)})

        # Create event and project
        event = ET.SubElement(root, "event", {"name": project_name})
        project = ET.SubElement(event, "project", {"name": project_name})

        # Save FCPXML
        fcpxml_path = project_path / f"{project_name}.fcpxml"
        tree = ET.ElementTree(root)
        tree.write(str(fcpxml_path), encoding="UTF-8", xml_declaration=True)

    def setup_color_management(self):
        """Setup color management pipeline"""
        # This would be done via Resolve API
        self.color_settings = {
            "color_science": "DaVinci YRGB Color Managed",
            "timeline_working_luminance": "100 nits",
            "timeline_working_colorspace": "DaVinci Wide Gamut",
            "output_colorspace": "Rec.709-A",

            # Camera-specific input transforms
            "input_transforms": {
                "fx30": {
                    "colorspace": "S-Log3/S-Gamut3.Cine",
                    "gamma": "S-Log3"
                },
                "zve10": {
                    "colorspace": "S-Log2/S-Gamut",
                    "gamma": "S-Log2"
                }
            },

            # Node structure template
            "node_template": {
                "node_01": "CST Input",
                "node_02": "Primary Balance",
                "node_03": "Shot Match",
                "node_04": "Orange/Teal LUT",
                "node_05": "Secondary Corrections",
                "node_06": "Output Transform"
            }
        }

    def import_and_organize_media(self):
        """Import media with intelligent organization"""
        print("📁 Organizing media into smart bins...")

        # Report bin structure
        for bin in self.bins:
            print(f"  {bin.icon} {bin.name}: {len(bin.clips)} clips")
            for sub_bin in bin.sub_bins:
                print(f"    └─ {sub_bin.icon} {sub_bin.name}: {len(sub_bin.clips)} clips")

    def create_smart_timelines(self) -> List[Dict]:
        """Create intelligent timelines"""
        timelines = []

        # Main edit timeline
        main_timeline = self.create_rough_cut_timeline()
        timelines.append(main_timeline)

        # Selects timeline (best shots only)
        selects_timeline = self.create_selects_timeline()
        timelines.append(selects_timeline)

        # Social media cuts
        social_timelines = self.create_social_timelines()
        timelines.extend(social_timelines)

        return timelines

    def create_rough_cut_timeline(self) -> Dict:
        """
        Create intelligent rough cut timeline (clip-level coordination)
        
        Note: This method works at the clip level (MediaAnalysis objects).
        Audio marker integration happens at the segment level via RoughCutEngine
        (used by `sf rough-cut` command), which processes markers within clips.
        
        This method provides a clip-level view. For marker-based rough cuts,
        use RoughCutEngine which handles segment-level marker processing.
        """
        return {
            "name": "Rough Cut",
            "type": "rough_cut",
            "clips": self.media_analyses,
            "duration": sum(c.duration for c in self.media_analyses)
        }

    def create_selects_timeline(self) -> Dict:
        """
        Create timeline of best shots (clip-level filtering)
        
        Note: This method works at the clip level using quality_score as a fallback.
        Audio markers ("best"/"select" commands) are processed at the segment level
        via RoughCutEngine. For marker-based selects, use RoughCutEngine.
        
        Quality score is used here as a fallback when markers are not available.
        Priority: 1) Audio markers (RoughCutEngine), 2) quality_score (this method)
        """
        # Filter by quality_score as fallback (markers handled by RoughCutEngine)
        selects = [a for a in self.media_analyses if a.quality_score >= 85]
        if not selects:
            selects = self.media_analyses  # Fallback: all clips if none meet threshold
        
        return {
            "name": "Selects",
            "type": "selects",
            "clips": selects,
            "duration": sum(c.duration for c in selects)
        }

    def create_social_timelines(self) -> List[Dict]:
        """
        Create social media optimized timelines (clip-level filtering)
        
        Note: Uses quality_score as fallback. Audio markers are processed at segment
        level via RoughCutEngine. Quality score used here when markers unavailable.
        """
        timelines = []

        # YouTube Short (vertical, <60s)
        # Quality score used as fallback (markers handled by RoughCutEngine)
        short_clips = [a for a in self.media_analyses if a.duration < 15 and a.quality_score > 70]
        if short_clips:
            timelines.append({
                "name": "YouTube Short",
                "type": "youtube_short",
                "clips": short_clips[:4],  # 4 clips ~15s each
                "duration": min(60, sum(c.duration for c in short_clips[:4])),
                "aspect": "9:16"
            })

        # Highlight reel (best moments)
        # Quality score used as fallback (markers handled by RoughCutEngine)
        highlights = [a for a in self.media_analyses if a.content_type in ["action", "talking_head"] and a.quality_score > 75]
        if highlights:
            timelines.append({
                "name": "Highlight Reel",
                "type": "highlights",
                "clips": highlights[:10],
                "duration": sum(c.duration for c in highlights[:10]),
                "aspect": "16:9"
            })

        return timelines