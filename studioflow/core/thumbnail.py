"""
Thumbnail Generator Stub
"""

from pathlib import Path
from typing import Optional


class ThumbnailGenerator:
    """Generate thumbnails for video projects"""

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path

    def generate(self, video_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """Generate thumbnail from video"""
        # Stub - implement with ffmpeg later
        return None

    def generate_batch(self, video_paths: list) -> list:
        """Generate thumbnails for multiple videos"""
        return []
