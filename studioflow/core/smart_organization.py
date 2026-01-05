"""
Smart Media Organization
Intelligent tagging, categorization, and search
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .media import MediaScanner, MediaFile, ClipCategory
from .transcription import TranscriptionService
from .ffmpeg import FFmpegProcessor


@dataclass
class MediaTag:
    """Media tag"""
    name: str
    confidence: float = 1.0
    source: str = "manual"  # manual, auto, ai


@dataclass
class SmartMediaFile:
    """Enhanced media file with smart tags and metadata"""
    path: Path
    duration: float
    tags: List[MediaTag] = field(default_factory=list)
    category: Optional[ClipCategory] = None
    content_type: str = "unknown"
    quality_score: float = 0.0
    transcript: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SmartMediaOrganizer:
    """Intelligent media organization with auto-tagging and search"""
    
    def __init__(self):
        self.scanner = MediaScanner()
        self.transcription_service = TranscriptionService()
    
    def organize_with_tags(
        self,
        media_dir: Path,
        auto_tag: bool = True,
        transcribe: bool = False
    ) -> List[SmartMediaFile]:
        """Organize media with automatic tagging"""
        
        # Scan media
        files = self.scanner.scan(media_dir)
        smart_files = []
        
        for file in files:
            smart_file = SmartMediaFile(
                path=file.path,
                duration=file.duration or 0.0,
                category=file.category
            )
            
            # Auto-tagging
            if auto_tag:
                tags = self._auto_tag_file(file)
                smart_file.tags = tags
                smart_file.content_type = self._detect_content_type(file, tags)
                smart_file.quality_score = self._score_quality(file)
            
            # Transcription (for search)
            if transcribe and file.type.value == "video":
                result = self.transcription_service.transcribe(file.path, model="base")
                if result.get("success"):
                    smart_file.transcript = result.get("text", "")
                    smart_file.metadata["transcript_path"] = result.get("output_files", {}).get("json")
            
            smart_files.append(smart_file)
        
        # Save metadata
        self._save_metadata(media_dir, smart_files)
        
        return smart_files
    
    def _auto_tag_file(self, file: MediaFile) -> List[MediaTag]:
        """Automatically tag a file based on analysis"""
        tags = []
        
        # Duration-based tags
        if file.duration:
            if file.duration < 5:
                tags.append(MediaTag("test_clip", 0.9, "auto"))
            elif file.duration > 60:
                tags.append(MediaTag("long_clip", 0.8, "auto"))
        
        # Filename-based tags
        name_lower = file.path.name.lower()
        
        if "test" in name_lower or "clip" in name_lower:
            tags.append(MediaTag("test", 0.7, "auto"))
        
        if any(word in name_lower for word in ["screen", "capture", "recording"]):
            tags.append(MediaTag("screen_recording", 0.9, "auto"))
        
        if any(word in name_lower for word in ["product", "unbox", "review"]):
            tags.append(MediaTag("product", 0.8, "auto"))
        
        if any(word in name_lower for word in ["talking", "head", "interview"]):
            tags.append(MediaTag("talking_head", 0.8, "auto"))
        
        if any(word in name_lower for word in ["broll", "b-roll", "b_roll"]):
            tags.append(MediaTag("broll", 0.9, "auto"))
        
        # Camera-based tags
        if "fx30" in name_lower:
            tags.append(MediaTag("fx30", 0.9, "auto"))
        elif "zve10" in name_lower or "zv-e10" in name_lower:
            tags.append(MediaTag("zve10", 0.9, "auto"))
        
        return tags
    
    def _detect_content_type(self, file: MediaFile, tags: List[MediaTag]) -> str:
        """Detect content type from file and tags"""
        tag_names = [t.name for t in tags]
        
        if "talking_head" in tag_names:
            return "talking_head"
        elif "screen_recording" in tag_names:
            return "screen_recording"
        elif "product" in tag_names:
            return "product"
        elif "broll" in tag_names:
            return "broll"
        elif file.duration and file.duration < 10:
            return "broll"
        else:
            return "aroll"
    
    def _score_quality(self, file: MediaFile) -> float:
        """Score file quality (0-100)"""
        score = 50.0  # Base score
        
        # Duration factor
        if file.duration:
            if 10 < file.duration < 120:
                score += 10
            elif file.duration < 5:
                score -= 20  # Test clips
        
        # Resolution factor
        if file.resolution:
            width, height = file.resolution
            if width >= 3840:
                score += 15
            elif width >= 1920:
                score += 10
        
        # Framerate factor
        if file.framerate:
            if file.framerate >= 24:
                score += 5
        
        return min(100, max(0, score))
    
    def _save_metadata(self, media_dir: Path, files: List[SmartMediaFile]):
        """Save metadata for search and organization"""
        metadata_file = media_dir / ".studioflow_metadata.json"
        
        metadata = {
            "generated": datetime.now().isoformat(),
            "files": [
                {
                    "path": str(f.path),
                    "tags": [t.name for t in f.tags],
                    "category": f.category.value if f.category else None,
                    "content_type": f.content_type,
                    "quality_score": f.quality_score,
                    "duration": f.duration,
                    "has_transcript": f.transcript is not None,
                }
                for f in files
            ]
        }
        
        metadata_file.write_text(json.dumps(metadata, indent=2))
    
    def search(
        self,
        media_dir: Path,
        query: str,
        search_transcripts: bool = True
    ) -> List[SmartMediaFile]:
        """Search media by tags, filename, or transcript"""
        
        # Load metadata
        metadata_file = media_dir / ".studioflow_metadata.json"
        if not metadata_file.exists():
            # Generate metadata first
            files = self.organize_with_tags(media_dir, auto_tag=True)
        else:
            # Load from metadata
            data = json.loads(metadata_file.read_text())
            files = []
            for item in data.get("files", []):
                file_path = Path(item["path"])
                if file_path.exists():
                    files.append(SmartMediaFile(
                        path=file_path,
                        duration=item.get("duration", 0),
                        tags=[MediaTag(t) for t in item.get("tags", [])],
                        content_type=item.get("content_type", "unknown"),
                        quality_score=item.get("quality_score", 0)
                    ))
        
        query_lower = query.lower()
        results = []
        
        for file in files:
            match_score = 0.0
            
            # Search filename
            if query_lower in file.path.name.lower():
                match_score += 0.8
            
            # Search tags
            for tag in file.tags:
                if query_lower in tag.name.lower():
                    match_score += 0.6
            
            # Search transcript
            if search_transcripts and file.transcript:
                if query_lower in file.transcript.lower():
                    match_score += 0.9
            
            # Search content type
            if query_lower in file.content_type.lower():
                match_score += 0.5
            
            if match_score > 0:
                file.metadata["match_score"] = match_score
                results.append(file)
        
        # Sort by match score
        results.sort(key=lambda f: f.metadata.get("match_score", 0), reverse=True)
        
        return results


