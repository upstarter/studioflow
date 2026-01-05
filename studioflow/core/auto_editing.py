"""
Auto-Editing System for YouTube Episodes
Intelligent automation for Resolve project setup, bin organization, and timeline creation
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import timedelta
import subprocess

from .resolve_api import ResolveDirectAPI
from .transcription import TranscriptionService
from .media import MediaScanner
from .ffmpeg import FFmpegProcessor
from .config import get_config


@dataclass
class SmartBin:
    """Smart bin configuration"""
    name: str
    description: str
    rules: List[Dict[str, Any]]
    clips: List[Path] = field(default_factory=list)


@dataclass
class Chapter:
    """Chapter marker"""
    timestamp: float
    title: str
    description: Optional[str] = None
    color: str = "Yellow"  # Resolve marker colors


@dataclass
class AutoEditConfig:
    """Configuration for auto-editing"""
    project_name: str
    footage_path: Path
    transcript_path: Optional[Path] = None
    template: str = "youtube_episode"
    library_path: Optional[Path] = None
    
    # Smart bin settings
    create_smart_bins: bool = True
    create_power_bins: bool = True
    
    # Timeline settings
    create_timeline: bool = True
    hook_duration: float = 10.0  # seconds
    min_chapter_length: float = 60.0  # seconds
    
    # Music settings
    auto_add_music: bool = False
    music_path: Optional[Path] = None


class AutoEditingEngine:
    """Intelligent auto-editing system for YouTube episodes"""
    
    # Smart bin definitions
    SMART_BINS = {
        "A_ROLL_TALKING_HEAD": {
            "description": "Person speaking directly to camera",
            "rules": [
                {"type": "duration_min", "value": 30},
                {"type": "has_face", "value": True},
                {"type": "has_speech", "value": True},
            ]
        },
        "A_ROLL_DIALOGUE": {
            "description": "Conversations and interviews",
            "rules": [
                {"type": "duration_min", "value": 15},
                {"type": "has_speech", "value": True},
                {"type": "has_multiple_speakers", "value": True},
            ]
        },
        "B_ROLL_PRODUCT": {
            "description": "Product shots and demonstrations",
            "rules": [
                {"type": "duration_min", "value": 10},
                {"type": "duration_max", "value": 60},
                {"type": "no_faces", "value": True},
            ]
        },
        "B_ROLL_DEMONSTRATION": {
            "description": "Screen recordings and demos",
            "rules": [
                {"type": "is_screen_recording", "value": True},
            ]
        },
        "B_ROLL_B_ROLL": {
            "description": "Generic B-roll footage",
            "rules": [
                {"type": "duration_min", "value": 10},
                {"type": "duration_max", "value": 90},
                {"type": "no_faces", "value": True},
            ]
        },
        "AUDIO_ONLY": {
            "description": "Good audio, visual not important",
            "rules": [
                {"type": "audio_quality_min", "value": 0.7},
                {"type": "visual_quality_max", "value": 0.5},
            ]
        },
        "REJECTS": {
            "description": "Test clips, corrupted files, unusable footage",
            "rules": [
                {"type": "duration_max", "value": 3},  # Very short = test clip
                {"type": "has_corruption", "value": True},
            ]
        },
    }
    
    # Power bin asset locations - now uses /mnt/nas/Media
    # Loaded lazily to avoid circular import issues
    _power_bin_sources = None

    @classmethod
    def get_power_bin_sources(cls) -> Optional[Dict[str, Dict[str, Path]]]:
        """Get power bin sources lazily (returns None if not configured)"""
        if cls._power_bin_sources is None:
            from .power_bins_config import PowerBinsConfig
            cls._power_bin_sources = PowerBinsConfig.get_structure()  # Can be None
        return cls._power_bin_sources
    
    def __init__(self, config: AutoEditConfig):
        self.config = config
        
        # Set library_path from config if not provided
        if self.config.library_path is None:
            cfg = get_config()
            self.config.library_path = cfg.storage.studio or cfg.storage.active or Path.home() / "Videos" / "StudioFlow" / "Studio"
        
        self.resolve_api = ResolveDirectAPI()
        self.transcription_service = TranscriptionService()
        self.scanner = MediaScanner()
        
    def process_episode(self) -> Dict[str, Any]:
        """Complete auto-editing workflow"""
        results = {
            "smart_bins": {},
            "power_bins": {},
            "chapters": [],
            "timeline": None,
            "success": False,
        }
        
        # 1. Analyze footage
        print("📹 Analyzing footage...")
        media_files = self._analyze_footage()
        
        # 2. Create smart bins
        if self.config.create_smart_bins:
            print("📁 Creating smart bins...")
            results["smart_bins"] = self.create_smart_bins(media_files)
        
        # 3. Create power bins
        if self.config.create_power_bins:
            print("⚡ Setting up power bins...")
            power_bins_result = self.setup_power_bins()
            if power_bins_result.get("error") != "Power Bins not configured":
                results["power_bins"] = power_bins_result
            else:
                results["power_bins"] = {"skipped": True, "reason": "Power Bins not configured (no NAS/library assets)"}
        
        # 4. Generate chapters
        if self.config.transcript_path:
            print("📖 Generating chapters...")
            results["chapters"] = self.generate_chapters_from_transcript()
        
        # 5. Create timeline
        if self.config.create_timeline:
            print("🎬 Creating timeline...")
            results["timeline"] = self.create_smart_timeline(media_files, results["chapters"])
        
        results["success"] = True
        return results
    
    def _analyze_footage(self) -> List[Dict[str, Any]]:
        """Analyze all footage files"""
        media_files = []
        
        # Scan for media
        scanned = self.scanner.scan(self.config.footage_path)
        
        for item in scanned:
            # Get media info
            info = FFmpegProcessor.get_media_info(item.path)
            
            media_files.append({
                "path": item.path,
                "duration": info.get("duration_seconds", 0),
                "resolution": info.get("resolution", "unknown"),
                "fps": info.get("fps", 30),
                "size_mb": item.size / (1024**2),
                "has_audio": info.get("has_audio", False),
                "has_video": info.get("has_video", False),
                # These would be detected by analysis
                "has_face": False,  # TODO: Add face detection
                "has_speech": False,  # TODO: Add speech detection
                "content_type": self._guess_content_type(item.path, info),
            })
        
        return media_files
    
    def _guess_content_type(self, path: Path, info: Dict) -> str:
        """Guess content type from filename and metadata"""
        name_lower = path.name.lower()
        
        # Screen recording detection
        if any(term in name_lower for term in ["screen", "capture", "recording", "demo"]):
            return "screen_recording"
        
        # Product shot detection
        if any(term in name_lower for term in ["product", "unbox", "review"]):
            return "product"
        
        # Duration-based guessing
        duration = info.get("duration_seconds", 0)
        if duration < 5:
            return "test_clip"
        elif duration < 30:
            return "broll"
        else:
            return "aroll"
    
    def create_smart_bins(self, media_files: List[Dict]) -> Dict[str, Any]:
        """Create smart bins and organize clips"""
        if not self.resolve_api.is_connected():
            return {"error": "Resolve not connected"}
        
        # Ensure project exists
        if not self.resolve_api.project:
            success = self.resolve_api.create_project(
                self.config.project_name,
                library_path=self.config.library_path
            )
            if not success:
                return {"error": "Failed to create Resolve project"}
        
        media_pool = self.resolve_api.media_pool
        root = media_pool.GetRootFolder()
        
        # Create smart bin structure
        bins_created = {}
        clips_organized = {}
        
        # Create 01_SMART_BINS folder
        smart_bins_folder = self.resolve_api.media_pool.AddSubFolder(root, "01_SMART_BINS")
        if not smart_bins_folder:
            return {"error": "Failed to create smart bins folder"}
        
        # Create each smart bin
        for bin_name, bin_config in self.SMART_BINS.items():
            bin_folder = self.resolve_api.media_pool.AddSubFolder(smart_bins_folder, bin_name)
            if bin_folder:
                bins_created[bin_name] = bin_folder
            
            # Organize clips into bin
            matching_clips = self._match_clips_to_bin(media_files, bin_name, bin_config["rules"])
            clips_organized[bin_name] = len(matching_clips)
            
            # Import matching clips
            if matching_clips:
                self.resolve_api.media_pool.SetCurrentFolder(bin_folder)
                clip_paths = [str(clip["path"]) for clip in matching_clips]
                imported = self.resolve_api.media_pool.ImportMedia(clip_paths)
                if imported:
                    print(f"  ✓ {bin_name}: {len(imported)} clips")
        
        # Reset to root
        self.resolve_api.media_pool.SetCurrentFolder(root)
        
        return {
            "bins_created": len(bins_created),
            "clips_organized": clips_organized,
            "total_clips": len(media_files),
        }
    
    def _match_clips_to_bin(self, clips: List[Dict], bin_name: str, rules: List[Dict]) -> List[Dict]:
        """Match clips to smart bin based on rules"""
        matching = []
        
        for clip in clips:
            matches = True
            
            for rule in rules:
                rule_type = rule["type"]
                rule_value = rule["value"]
                
                if rule_type == "duration_min" and clip["duration"] < rule_value:
                    matches = False
                elif rule_type == "duration_max" and clip["duration"] > rule_value:
                    matches = False
                elif rule_type == "has_face" and clip.get("has_face") != rule_value:
                    matches = False
                elif rule_type == "has_speech" and clip.get("has_speech") != rule_value:
                    matches = False
                elif rule_type == "no_faces" and clip.get("has_face") == True:
                    matches = False
                elif rule_type == "is_screen_recording" and clip["content_type"] != "screen_recording":
                    matches = False
                # Add more rule types as needed
            
            if matches:
                matching.append(clip)
        
        return matching
    
    def setup_power_bins(self) -> Dict[str, Any]:
        """Create and populate Power Bins (optional feature - requires NAS or library assets)"""
        if not self.resolve_api.is_connected():
            return {"error": "Resolve not connected"}
        
        # Check if Power Bins is available
        from .power_bins_config import PowerBinsConfig
        if not PowerBinsConfig.is_available():
            return {"error": "Power Bins not configured", "message": "Configure storage.nas or storage.studio in ~/.studioflow/config.yaml"}
        
        # Use existing stock library function as base
        result = self.resolve_api.setup_stock_library()
        
        # Additionally, create power bin structure from library assets
        media_pool = self.resolve_api.media_pool
        root = media_pool.GetRootFolder()
        
        # Check if _POWER_BINS exists, if not create it
        subfolders = root.GetSubFolderList()
        power_bins_folder = None
        
        for folder in subfolders:
            if folder.GetName() == "_POWER_BINS":
                power_bins_folder = folder
                break
        
        if not power_bins_folder:
            power_bins_folder = self.resolve_api.media_pool.AddSubFolder(root, "_POWER_BINS")
        
        if not power_bins_folder:
            return {"error": "Failed to create power bins folder"}
        
        assets_imported = {}
        
        # Get power bin sources (will be None if not available)
        power_bin_sources = self.get_power_bin_sources()
        if power_bin_sources is None:
            return {"error": "Power Bins not configured", "message": "No media library found"}
        
        # Create power bin structure from library
        for category, subcategories in power_bin_sources.items():
            cat_folder = self.resolve_api.media_pool.AddSubFolder(power_bins_folder, category)
            
            if cat_folder:
                for subcat_name, source_path in subcategories.items():
                    source = Path(source_path) if not isinstance(source_path, Path) else source_path
                    
                    if source.exists():
                        subcat_folder = self.resolve_api.media_pool.AddSubFolder(cat_folder, subcat_name)
                        
                        if subcat_folder:
                            # Find media files using category-specific extensions
                            media_files = []
                            extensions = PowerBinsConfig.get_extensions(category)
                            for ext in extensions:
                                media_files.extend(source.glob(ext))
                                media_files.extend(source.glob(ext.upper()))
                            
                            if media_files:
                                self.resolve_api.media_pool.SetCurrentFolder(subcat_folder)
                                imported = self.resolve_api.media_pool.ImportMedia([str(f) for f in media_files])
                                
                                if imported:
                                    count = len(imported) if imported else 0
                                    assets_imported[f"{category}/{subcat_name}"] = count
                                    print(f"  ✓ {category}/{subcat_name}: {count} assets")
                    else:
                        # Path doesn't exist - still create bin for future use
                        subcat_folder = self.resolve_api.media_pool.AddSubFolder(cat_folder, subcat_name)
                        assets_imported[f"{category}/{subcat_name}"] = 0
                        print(f"  ⚠ {category}/{subcat_name}: path not found ({source})")
        
        # Reset to root
        self.resolve_api.media_pool.SetCurrentFolder(root)
        
        return {
            "stock_library_clips": result,
            "power_bins_assets": assets_imported,
            "total_assets": sum(assets_imported.values()),
        }
    
    def generate_chapters_from_transcript(self) -> List[Chapter]:
        """Generate chapters from transcript file"""
        if not self.config.transcript_path or not self.config.transcript_path.exists():
            return []
        
        chapters = []
        
        # Load transcript
        if self.config.transcript_path.suffix == ".json":
            with open(self.config.transcript_path) as f:
                transcript_data = json.load(f)
                segments = transcript_data.get("segments", [])
        elif self.config.transcript_path.suffix == ".srt":
            # Parse SRT
            segments = self._parse_srt(self.config.transcript_path)
        else:
            return []
        
        # Simple chapter detection: topic changes, pauses, keywords
        current_chapter = None
        chapter_keywords = ["intro", "introduction", "overview", "feature", "demo", "conclusion", "outro", "summary"]
        
        for segment in segments:
            text = segment.get("text", "").lower()
            start = segment.get("start", 0)
            
            # Check for chapter keywords
            is_chapter_start = any(keyword in text for keyword in chapter_keywords)
            
            # Check for topic change (simple heuristic: long pause or keyword)
            is_topic_change = False
            if current_chapter:
                prev_end = current_chapter.timestamp
                pause_duration = start - prev_end
                is_topic_change = pause_duration > 3.0  # 3 second pause
            
            if is_chapter_start or is_topic_change:
                # Finalize previous chapter
                if current_chapter:
                    # Check minimum duration
                    duration = start - current_chapter.timestamp
                    if duration >= self.config.min_chapter_length:
                        chapters.append(current_chapter)
                
                # Start new chapter
                title = self._generate_chapter_title(text)
                current_chapter = Chapter(
                    timestamp=start,
                    title=title,
                    description=segment.get("text", "")[:100]
                )
        
        # Add final chapter
        if current_chapter and segments:
            last_segment = segments[-1]
            duration = last_segment.get("end", 0) - current_chapter.timestamp
            if duration >= self.config.min_chapter_length:
                chapters.append(current_chapter)
        
        # Ensure first chapter starts at 0
        if chapters and chapters[0].timestamp > 0:
            chapters.insert(0, Chapter(
                timestamp=0.0,
                title="Introduction",
                color="Red"
            ))
        
        return chapters
    
    def _parse_srt(self, srt_path: Path) -> List[Dict]:
        """Parse SRT file to segments"""
        segments = []
        content = srt_path.read_text()
        
        # Simple SRT parser
        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            start_str = match[1]
            end_str = match[2]
            text = match[3].strip().replace('\n', ' ')
            
            # Convert timecode to seconds
            start = self._srt_timecode_to_seconds(start_str)
            end = self._srt_timecode_to_seconds(end_str)
            
            segments.append({
                "start": start,
                "end": end,
                "text": text
            })
        
        return segments
    
    def _srt_timecode_to_seconds(self, timecode: str) -> float:
        """Convert SRT timecode to seconds"""
        time_parts = timecode.replace(',', ':').split(':')
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = int(time_parts[2])
        millis = int(time_parts[3])
        return hours * 3600 + minutes * 60 + seconds + millis / 1000.0
    
    def _generate_chapter_title(self, text: str) -> str:
        """Generate chapter title from text"""
        # Take first 50 characters, clean up
        title = text[:50].strip()
        
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        
        # Remove filler words at start
        fillers = ["so", "um", "uh", "well", "okay", "ok"]
        words = title.split()
        if words and words[0].lower() in fillers:
            words = words[1:]
        title = " ".join(words)
        
        return title if title else "Chapter"
    
    def create_smart_timeline(
        self,
        media_files: List[Dict],
        chapters: List[Chapter],
        aroll_clips: Optional[List[Path]] = None,
        broll_clips: Optional[List[Path]] = None,
        music_track: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Create intelligent timeline assembly with B-roll and music"""
        if not self.resolve_api.is_connected():
            return {"error": "Resolve not connected"}
        
        # Use timeline automation for advanced features
        from .timeline_automation import TimelineAutomation
        
        timeline_automation = TimelineAutomation(self.resolve_api)
        
        # Convert media files to paths
        if not aroll_clips:
            aroll_clips = [Path(f["path"]) for f in media_files if f.get("content_type") in ["aroll", "talking_head"]]
        
        if not broll_clips:
            broll_clips = [Path(f["path"]) for f in media_files if f.get("content_type") in ["broll", "product", "screen_recording"]]
        
        # Select hook clips
        hook_clips = [Path(f["path"]) for f in media_files[:3] if f.get("duration", 0) < 15]
        
        # Create timeline
        result = timeline_automation.create_smart_assembly(
            timeline_name="01_AUTO_ASSEMBLY",
            aroll_clips=aroll_clips,
            broll_clips=broll_clips,
            music_track=music_track,
            hook_clips=hook_clips,
            style="youtube"
        )
        
        # Add chapter markers if timeline was created
        if result.get("success") and chapters:
            timeline = self.resolve_api.media_pool.GetTimelineByName("01_AUTO_ASSEMBLY")
            if timeline:
                self._add_chapter_markers(timeline, chapters)
        
        return result
    
    def _add_chapter_markers(self, timeline, chapters: List[Chapter]):
        """Add chapter markers to timeline"""
        # Resolve API for markers
        for chapter in chapters:
            # Convert timestamp to frames (assuming 30fps)
            frame = int(chapter.timestamp * 30)
            
            # Add marker
            # Note: Resolve API marker functions vary by version
            # This is a conceptual implementation
            try:
                timeline.AddMarker(frame, chapter.color, chapter.title, chapter.description or "", 1)
            except:
                # Fallback: marker might not be available in all Resolve versions
                print(f"  Note: Could not add marker at {chapter.timestamp}s - {chapter.title}")
    
    def _format_youtube_timestamp(self, seconds: float) -> str:
        """Format timestamp for YouTube chapters (MM:SS or HH:MM:SS)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

