"""
Safe Marking Detection for Sony Cameras
Detects protected clips marked on camera (hero takes, important footage)
"""

import os
import stat
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class SafeMarkingAnalysis:
    """Analysis of a single clip's marking status"""
    file_path: Path
    is_protected: bool = False
    duration: float = 0.0
    file_size: int = 0
    marking_method: Optional[str] = None  # "file_attribute", "filename", "metadata"


class SafeMarkingDetector:
    """Detect protected/safe-marked clips from Sony cameras"""
    
    def __init__(self):
        self.protected_count = 0
        self.total_count = 0
    
    def _is_file_protected(self, file_path: Path) -> bool:
        """
        Check if file is marked as protected
        
        Sony cameras mark protected clips by setting the file's read-only attribute
        or by other filesystem flags. This checks multiple methods.
        """
        if not file_path.exists():
            return False
        
        # Method 1: Check file permissions (read-only = protected on some systems)
        file_stat = file_path.stat()
        is_readonly = not (file_stat.st_mode & stat.S_IWRITE)
        
        # Method 2: Check if file has "protected" in metadata/attributes
        # On Linux, we can check extended attributes
        try:
            # Check for user.immutable or similar attributes
            import xattr
            attrs = xattr.listxattr(str(file_path))
            if any('protected' in attr.lower() or 'immutable' in attr.lower() for attr in attrs):
                return True
        except (ImportError, OSError):
            # xattr not available or not supported, skip
            pass
        
        # Method 3: Check filename patterns (some workflows use naming)
        filename_lower = file_path.name.lower()
        if any(marker in filename_lower for marker in ['_prot', '_safe', '_hero', '_keep']):
            return True
        
        # Method 4: Read-only flag (common on Windows/Mac)
        if is_readonly:
            return True
        
        return False
    
    def analyze_clip(self, file_path: Path) -> SafeMarkingAnalysis:
        """Analyze a single clip for marking status"""
        analysis = SafeMarkingAnalysis(file_path=file_path)
        analysis.is_protected = self._is_file_protected(file_path)
        
        # Get file size
        try:
            analysis.file_size = file_path.stat().st_size
        except OSError:
            analysis.file_size = 0
        
        # Determine marking method
        if analysis.is_protected:
            if not (file_path.stat().st_mode & stat.S_IWRITE):
                analysis.marking_method = "file_attribute"
            elif any(marker in file_path.name.lower() for marker in ['_prot', '_safe', '_hero']):
                analysis.marking_method = "filename"
            else:
                analysis.marking_method = "metadata"
        
        return analysis
    
    def analyze_folder(self, folder_path: Path) -> List[SafeMarkingAnalysis]:
        """Analyze all clips in a folder"""
        analyses = []
        
        # Find video files
        video_extensions = ['.mp4', '.mov', '.MP4', '.MOV', '.mxf', '.MXF']
        for ext in video_extensions:
            for file_path in folder_path.glob(f'*{ext}'):
                analysis = self.analyze_clip(file_path)
                analyses.append(analysis)
                self.total_count += 1
                if analysis.is_protected:
                    self.protected_count += 1
        
        return analyses
    
    def get_statistics(self) -> Dict[str, int]:
        """Get marking statistics"""
        return {
            "total_clips": self.total_count,
            "protected_clips": self.protected_count,
            "unprotected_clips": self.total_count - self.protected_count,
            "protection_rate": (self.protected_count / self.total_count * 100) if self.total_count > 0 else 0
        }


class SafeMarkingWorkflow:
    """Workflow for processing safe marking on camera cards"""
    
    def __init__(self):
        self.detector = SafeMarkingDetector()
    
    def process_card(self, card_path: Path) -> Dict[str, any]:
        """
        Process entire camera card for safe markings
        
        Returns:
            Dictionary with protected_clips, hero_clips, good_clips lists
        """
        card_path = Path(card_path)
        
        if not card_path.exists():
            return {
                "protected_clips": 0,
                "hero_clips": [],
                "good_clips": [],
                "error": "Card path does not exist"
            }
        
        # Find all video files recursively
        all_clips = []
        video_extensions = ['.mp4', '.mov', '.MP4', '.MOV']
        
        for ext in video_extensions:
            all_clips.extend(card_path.rglob(f'*{ext}'))
        
        # Analyze each clip
        protected_clips = []
        hero_clips = []
        good_clips = []
        
        for clip_path in all_clips:
            analysis = self.detector.analyze_clip(clip_path)
            
            if analysis.is_protected:
                protected_clips.append(clip_path)
                # Hero clips are typically in folder 108 or have specific naming
                if '108' in str(clip_path) or 'hero' in clip_path.name.lower():
                    hero_clips.append(clip_path)
            else:
                # Good clips are unprotected but might still be usable
                good_clips.append(clip_path)
        
        return {
            "protected_clips": len(protected_clips),
            "hero_clips": [str(p) for p in hero_clips],
            "good_clips": [str(p) for p in good_clips],
            "all_protected": [str(p) for p in protected_clips],
            "statistics": self.detector.get_statistics()
        }
    
    def mark_clip(self, file_path: Path, protected: bool = True) -> bool:
        """
        Mark or unmark a clip as protected
        
        Args:
            file_path: Path to clip
            protected: True to mark as protected, False to unmark
        
        Returns:
            True if successful
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False
            
            # Set read-only attribute
            current_mode = file_path.stat().st_mode
            if protected:
                # Remove write permission
                new_mode = current_mode & ~stat.S_IWRITE
            else:
                # Add write permission
                new_mode = current_mode | stat.S_IWRITE
            
            file_path.chmod(new_mode)
            return True
        except OSError:
            return False


