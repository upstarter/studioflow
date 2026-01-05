"""
Folder-based scene organization for Sony cameras
Intelligent folder structure detection and workflow optimization
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from .ffmpeg import FFmpegProcessor
from .safe_marking import SafeMarkingAnalysis, SafeMarkingDetector


@dataclass
class FolderAnalysis:
    """Analysis of camera folder contents"""
    folder_path: Path
    folder_number: int
    folder_name: str  # e.g., "101MSDCF"
    clip_count: int
    total_duration: float
    avg_duration: float
    content_type: str  # scene, broll, hero, test
    inferred_purpose: str  # intro, main_content, product_shots, etc.
    priority_score: int  # 1-10, higher = more important
    protected_clips: int = 0
    hero_clips: int = 0
    clips: List[SafeMarkingAnalysis] = field(default_factory=list)
    quality_distribution: Dict[str, int] = field(default_factory=dict)
    shoot_session: Optional[str] = None  # morning, afternoon, etc.


@dataclass
class ShootStructure:
    """Complete shoot organization structure"""
    card_path: Path
    total_folders: int
    total_clips: int
    shoot_date: datetime
    camera_type: str  # fx30, zve10
    folders: List[FolderAnalysis]
    scene_count: int
    broll_folders: int
    hero_folders: int
    recommended_workflow: List[str] = field(default_factory=list)


class FolderIntelligence:
    """AI-powered folder structure analysis and optimization"""

    # Standard folder type mappings
    FOLDER_TYPES = {
        100: {"type": "test", "purpose": "Setup/Tests/Warmup", "priority": 2},
        101: {"type": "scene", "purpose": "Scene 1: Hook/Intro", "priority": 9},
        102: {"type": "scene", "purpose": "Scene 2: Main Content", "priority": 9},
        103: {"type": "scene", "purpose": "Scene 3: Demo/Example", "priority": 8},
        104: {"type": "scene", "purpose": "Scene 4: Conclusion", "priority": 8},
        105: {"type": "broll", "purpose": "B-Roll: Product Shots", "priority": 6},
        106: {"type": "broll", "purpose": "B-Roll: Environment", "priority": 5},
        107: {"type": "broll", "purpose": "B-Roll: Detail Shots", "priority": 5},
        108: {"type": "hero", "purpose": "Hero Takes Only", "priority": 10},
        109: {"type": "backup", "purpose": "Safety/Backup Takes", "priority": 3},
    }

    # Content type classification
    CONTENT_PATTERNS = {
        "talking_head": {"min_duration": 15, "max_clips": 20, "audio_required": True},
        "broll": {"min_duration": 3, "max_duration": 15, "audio_optional": True},
        "demo": {"min_duration": 30, "audio_required": True, "motion_likely": True},
        "intro": {"max_duration": 30, "audio_required": True, "first_folder": True},
        "outro": {"max_duration": 45, "audio_required": True, "last_folder": True}
    }

    def __init__(self):
        self.marking_detector = SafeMarkingDetector()

    def analyze_folder_structure(self, card_path: Path) -> ShootStructure:
        """Analyze complete folder structure from camera card"""

        print(f"📁 Analyzing folder structure: {card_path}")

        # Find all DCIM folders
        dcim_folders = self._find_dcim_folders(card_path)
        if not dcim_folders:
            raise ValueError("No DCIM folder structure found")

        # Analyze each folder
        folder_analyses = []
        for folder_path in dcim_folders:
            analysis = self._analyze_single_folder(folder_path)
            if analysis and analysis.clip_count > 0:  # Only include folders with clips
                folder_analyses.append(analysis)

        # Sort by folder number
        folder_analyses.sort(key=lambda f: f.folder_number)

        # Determine camera type
        camera_type = self._detect_camera_type(folder_analyses)

        # Create shoot structure
        shoot_structure = ShootStructure(
            card_path=card_path,
            total_folders=len(folder_analyses),
            total_clips=sum(f.clip_count for f in folder_analyses),
            shoot_date=self._estimate_shoot_date(folder_analyses),
            camera_type=camera_type,
            folders=folder_analyses,
            scene_count=len([f for f in folder_analyses if f.content_type == "scene"]),
            broll_folders=len([f for f in folder_analyses if f.content_type == "broll"]),
            hero_folders=len([f for f in folder_analyses if f.content_type == "hero"])
        )

        # Generate workflow recommendations
        shoot_structure.recommended_workflow = self._generate_workflow_recommendations(shoot_structure)

        return shoot_structure

    def _find_dcim_folders(self, card_path: Path) -> List[Path]:
        """Find all DCIM folders on card"""
        dcim_folders = []

        # Look for DCIM structure
        dcim_path = card_path / "DCIM"
        if dcim_path.exists():
            # Find numbered folders (100MSDCF, 101MSDCF, etc.)
            for folder in dcim_path.iterdir():
                if folder.is_dir() and re.match(r'\d{3}[A-Z]+', folder.name):
                    dcim_folders.append(folder)
        else:
            # Maybe card root has the folders directly
            for folder in card_path.iterdir():
                if folder.is_dir() and re.match(r'\d{3}[A-Z]+', folder.name):
                    dcim_folders.append(folder)

        return sorted(dcim_folders)

    def _analyze_single_folder(self, folder_path: Path) -> Optional[FolderAnalysis]:
        """Analyze contents of a single folder"""

        # Extract folder number
        folder_name = folder_path.name
        folder_match = re.match(r'(\d{3})', folder_name)
        if not folder_match:
            return None

        folder_number = int(folder_match.group(1))

        # Find all media files
        media_files = []
        for ext in ['*.MP4', '*.MOV', '*.mp4', '*.mov']:
            media_files.extend(folder_path.glob(ext))

        if not media_files:
            return None

        # Analyze markings for each clip
        media_files.sort(key=lambda f: f.name)  # Sort by filename
        clip_analyses = []

        for file_path in media_files:
            # Create basic analysis
            clip_analysis = SafeMarkingAnalysis(file_path=file_path)

            # Check protection
            clip_analysis.is_protected = self.marking_detector._is_file_protected(file_path)

            # Get basic file info
            info = FFmpegProcessor.get_media_info(file_path)
            duration = info.get("duration_seconds", 0)

            clip_analysis.duration = duration
            clip_analyses.append(clip_analysis)

        # Calculate folder statistics
        total_duration = sum(c.duration for c in clip_analyses if hasattr(c, 'duration'))
        avg_duration = total_duration / len(clip_analyses) if clip_analyses else 0
        protected_count = len([c for c in clip_analyses if c.is_protected])

        # Determine content type and purpose
        content_type = self._classify_folder_content_type(folder_number, clip_analyses)
        inferred_purpose = self._infer_folder_purpose(folder_number, clip_analyses, content_type)
        priority_score = self._calculate_folder_priority(folder_number, content_type, protected_count)

        # Quality distribution
        quality_dist = {"high": 0, "medium": 0, "low": 0}
        for clip in clip_analyses:
            if clip.is_protected:
                quality_dist["high"] += 1
            elif hasattr(clip, 'duration') and clip.duration > 10:
                quality_dist["medium"] += 1
            else:
                quality_dist["low"] += 1

        return FolderAnalysis(
            folder_path=folder_path,
            folder_number=folder_number,
            folder_name=folder_name,
            clip_count=len(clip_analyses),
            total_duration=total_duration,
            avg_duration=avg_duration,
            content_type=content_type,
            inferred_purpose=inferred_purpose,
            priority_score=priority_score,
            protected_clips=protected_count,
            clips=clip_analyses,
            quality_distribution=quality_dist
        )

    def _classify_folder_content_type(self, folder_number: int, clips: List[SafeMarkingAnalysis]) -> str:
        """Classify what type of content is in this folder"""

        # Check predefined folder types first
        if folder_number in self.FOLDER_TYPES:
            return self.FOLDER_TYPES[folder_number]["type"]

        # Analyze content characteristics
        if not clips:
            return "empty"

        avg_duration = sum(getattr(c, 'duration', 0) for c in clips) / len(clips)
        protected_ratio = len([c for c in clips if c.is_protected]) / len(clips)

        # Classification logic
        if folder_number >= 108:  # High numbers = curated
            return "hero"
        elif folder_number == 100:  # Default folder
            return "test"
        elif avg_duration < 10 and len(clips) > 10:  # Many short clips
            return "broll"
        elif protected_ratio > 0.5:  # High protection rate = important
            return "scene"
        elif 101 <= folder_number <= 107:  # Standard range
            return "scene"
        else:
            return "mixed"

    def _infer_folder_purpose(self, folder_number: int, clips: List[SafeMarkingAnalysis], content_type: str) -> str:
        """Infer the specific purpose of this folder"""

        # Use predefined purposes
        if folder_number in self.FOLDER_TYPES:
            return self.FOLDER_TYPES[folder_number]["purpose"]

        # Infer from content
        if content_type == "hero":
            return "Curated Best Takes"
        elif content_type == "broll":
            if folder_number == 105:
                return "Product/Subject B-Roll"
            elif folder_number == 106:
                return "Environment B-Roll"
            else:
                return "Supplementary Footage"
        elif content_type == "scene":
            scene_num = folder_number - 100
            return f"Scene {scene_num}: Content"
        elif content_type == "test":
            return "Setup/Testing"
        else:
            return f"Folder {folder_number} Content"

    def _calculate_folder_priority(self, folder_number: int, content_type: str, protected_count: int) -> int:
        """Calculate priority score for folder (1-10)"""

        # Base priority from folder type
        if folder_number in self.FOLDER_TYPES:
            base_priority = self.FOLDER_TYPES[folder_number]["priority"]
        else:
            base_priority = 5  # Default

        # Adjust based on content
        if content_type == "hero":
            base_priority = 10
        elif content_type == "scene":
            base_priority = max(base_priority, 7)
        elif content_type == "test":
            base_priority = min(base_priority, 3)

        # Boost for protected content
        if protected_count > 0:
            base_priority = min(10, base_priority + 1)

        return base_priority

    def _detect_camera_type(self, folder_analyses: List[FolderAnalysis]) -> str:
        """Detect camera type from file patterns"""

        if not folder_analyses:
            return "unknown"

        # Look at first few clips for naming pattern
        for folder in folder_analyses:
            if folder.clips:
                first_clip = folder.clips[0]
                filename = first_clip.file_path.name.upper()

                if filename.startswith("C") and "MP4" in filename:
                    return "fx30"
                elif filename.startswith("DSC"):
                    return "zve10"

        return "unknown"

    def _estimate_shoot_date(self, folder_analyses: List[FolderAnalysis]) -> datetime:
        """Estimate when the shoot happened"""

        if not folder_analyses or not folder_analyses[0].clips:
            return datetime.now()

        # Use creation time of first clip
        first_clip = folder_analyses[0].clips[0]
        return datetime.fromtimestamp(first_clip.file_path.stat().st_ctime)

    def _generate_workflow_recommendations(self, shoot_structure: ShootStructure) -> List[str]:
        """Generate workflow recommendations based on folder structure"""

        recommendations = []

        # Basic import strategy
        if shoot_structure.hero_folders > 0:
            recommendations.append("Import hero folders first for quick preview")

        if shoot_structure.scene_count >= 3:
            recommendations.append("Organize scenes sequentially for story flow")

        if shoot_structure.broll_folders > 0:
            recommendations.append("Use B-roll folders for transitions and cutaways")

        # Quality recommendations
        total_protected = sum(f.protected_clips for f in shoot_structure.folders)
        if total_protected == 0:
            recommendations.append("Consider marking best takes during review")
        elif total_protected > shoot_structure.total_clips * 0.8:
            recommendations.append("High protection rate - be more selective")

        # Folder-specific recommendations
        hero_folder = next((f for f in shoot_structure.folders if f.content_type == "hero"), None)
        if hero_folder and hero_folder.clip_count > 0:
            recommendations.append(f"Hero folder has {hero_folder.clip_count} clips - use for rough cut")

        test_folder = next((f for f in shoot_structure.folders if f.folder_number == 100), None)
        if test_folder and test_folder.clip_count > 10:
            recommendations.append("Many test clips detected - consider cleaning up")

        return recommendations

    def create_resolve_bin_structure(self, shoot_structure: ShootStructure) -> Dict[str, Any]:
        """Create optimal Resolve bin structure from folder analysis"""

        bin_structure = {
            "project_name": f"Episode_{shoot_structure.shoot_date.strftime('%Y%m%d')}",
            "bins": []
        }

        # Create bins from folders
        for folder in sorted(shoot_structure.folders, key=lambda f: f.priority_score, reverse=True):
            if folder.clip_count == 0:
                continue

            # Determine bin icon and color
            if folder.content_type == "hero":
                icon = "⭐"
                color = "gold"
            elif folder.content_type == "scene":
                icon = "🎬"
                color = "blue"
            elif folder.content_type == "broll":
                icon = "🎞️"
                color = "green"
            elif folder.content_type == "test":
                icon = "🧪"
                color = "gray"
            else:
                icon = "📁"
                color = "default"

            bin_data = {
                "name": f"{icon} {folder.inferred_purpose}",
                "color": color,
                "folder_source": folder.folder_name,
                "clip_count": folder.clip_count,
                "total_duration": folder.total_duration,
                "priority": folder.priority_score,
                "clips": []
            }

            # Add clip information
            for clip in folder.clips:
                clip_info = {
                    "file_path": str(clip.file_path),
                    "filename": clip.file_path.name,
                    "is_protected": clip.is_protected,
                    "duration": getattr(clip, 'duration', 0),
                    "recommended_use": self._recommend_clip_use(clip, folder.content_type)
                }
                bin_data["clips"].append(clip_info)

            bin_structure["bins"].append(bin_data)

        return bin_structure

    def _recommend_clip_use(self, clip: SafeMarkingAnalysis, folder_type: str) -> str:
        """Recommend how to use this clip in edit"""

        if clip.is_protected:
            if folder_type == "hero":
                return "primary_timeline"
            elif folder_type == "scene":
                return "main_content"
            else:
                return "backup_option"
        else:
            if folder_type == "broll":
                return "transitions"
            elif folder_type == "test":
                return "skip"
            else:
                return "review_needed"

    def generate_folder_report(self, shoot_structure: ShootStructure) -> str:
        """Generate comprehensive folder analysis report"""

        report = []
        report.append("=== Folder Structure Analysis ===\n")

        # Overview
        report.append(f"📅 Shoot Date: {shoot_structure.shoot_date.strftime('%Y-%m-%d')}")
        report.append(f"📷 Camera: {shoot_structure.camera_type.upper()}")
        report.append(f"📁 Total Folders: {shoot_structure.total_folders}")
        report.append(f"🎬 Total Clips: {shoot_structure.total_clips}")
        report.append(f"⏱️  Total Duration: {sum(f.total_duration for f in shoot_structure.folders)/60:.1f} minutes")

        # Folder breakdown
        report.append(f"\n📊 Content Distribution:")
        report.append(f"🎬 Scene Folders: {shoot_structure.scene_count}")
        report.append(f"🎞️ B-Roll Folders: {shoot_structure.broll_folders}")
        report.append(f"⭐ Hero Folders: {shoot_structure.hero_folders}")

        # Detailed folder analysis
        report.append(f"\n📁 Folder Details:")
        for folder in sorted(shoot_structure.folders, key=lambda f: f.folder_number):
            protected_pct = (folder.protected_clips / folder.clip_count * 100) if folder.clip_count > 0 else 0

            report.append(f"\n{folder.folder_name} - {folder.inferred_purpose}")
            report.append(f"   📊 {folder.clip_count} clips, {folder.total_duration/60:.1f} min")
            report.append(f"   🔒 {folder.protected_clips} protected ({protected_pct:.0f}%)")
            report.append(f"   ⭐ Priority: {folder.priority_score}/10")

        # Recommendations
        if shoot_structure.recommended_workflow:
            report.append(f"\n💡 Workflow Recommendations:")
            for i, rec in enumerate(shoot_structure.recommended_workflow, 1):
                report.append(f"   {i}. {rec}")

        return "\n".join(report)

    def export_folder_mapping(self, shoot_structure: ShootStructure, output_path: Path):
        """Export folder mapping for import tools"""

        mapping = {
            "shoot_info": {
                "date": shoot_structure.shoot_date.isoformat(),
                "camera": shoot_structure.camera_type,
                "total_folders": shoot_structure.total_folders,
                "total_clips": shoot_structure.total_clips
            },
            "folder_mapping": {}
        }

        for folder in shoot_structure.folders:
            mapping["folder_mapping"][folder.folder_name] = {
                "purpose": folder.inferred_purpose,
                "type": folder.content_type,
                "priority": folder.priority_score,
                "clip_count": folder.clip_count,
                "protected_clips": folder.protected_clips,
                "clips": [
                    {
                        "filename": clip.file_path.name,
                        "protected": clip.is_protected,
                        "duration": getattr(clip, 'duration', 0)
                    }
                    for clip in folder.clips
                ]
            }

        output_path.write_text(json.dumps(mapping, indent=2))
        print(f"📄 Folder mapping exported to: {output_path}")