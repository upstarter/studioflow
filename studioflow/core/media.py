"""
Media Management - Smart Import and Organization
Handles media scanning, categorization, and import with modern patterns
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
import hashlib
import shutil
import subprocess
import concurrent.futures
from enum import Enum
import json

from rich.progress import Progress, BarColumn, TimeRemainingColumn
from rich.console import Console

from studioflow.core.config import get_config


console = Console()


class MediaType(str, Enum):
    """Media type classification"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    PROJECT = "project"
    OTHER = "other"


class ClipCategory(str, Enum):
    """Clip categorization"""
    A_ROLL = "A_ROLL"
    B_ROLL = "B_ROLL"
    TEST_CLIP = "TEST_CLIP"
    TIMELAPSE = "TIMELAPSE"
    SLOW_MOTION = "SLOW_MOTION"
    INTERVIEW = "INTERVIEW"
    SCREEN_RECORDING = "SCREEN_RECORDING"
    DRONE = "DRONE"
    UNKNOWN = "UNKNOWN"


@dataclass
class MediaFile:
    """Media file information with comprehensive metadata"""
    path: Path
    size: int
    type: MediaType
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    framerate: Optional[float] = None
    codec: Optional[str] = None
    category: Optional[ClipCategory] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Audio metadata
    audio_codec: Optional[str] = None
    audio_sample_rate: Optional[int] = None
    audio_channels: Optional[int] = None
    audio_bitrate: Optional[int] = None
    audio_language: Optional[str] = None
    
    # Format metadata
    container_format: Optional[str] = None
    video_bitrate: Optional[int] = None
    total_bitrate: Optional[int] = None
    creation_time: Optional[datetime] = None
    
    # Color/Technical metadata
    color_space: Optional[str] = None
    color_primaries: Optional[str] = None
    color_trc: Optional[str] = None  # Transfer characteristics
    pixel_format: Optional[str] = None
    bit_depth: Optional[int] = None
    aspect_ratio: Optional[float] = None
    rotation: Optional[int] = None
    
    # Timecode
    timecode: Optional[str] = None
    
    # Camera metadata
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    encoder: Optional[str] = None
    
    # Qualitative content metadata (from analysis)
    scene_count: Optional[int] = None
    face_count: Optional[int] = None
    has_speech: Optional[bool] = None
    exposure_rating: Optional[str] = None  # under, normal, over
    shake_detected: Optional[bool] = None
    best_thumbnail_time: Optional[float] = None

    @property
    def human_size(self) -> str:
        """Human-readable file size"""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class MediaScanner:
    """Scans directories for media files"""

    def __init__(self):
        self.config = get_config()
        self.video_extensions = set(self.config.media.extensions)
        self.audio_extensions = set(self.config.media.audio_extensions)
        self.image_extensions = set(self.config.media.image_extensions)

    def scan(self, path: Path, recursive: bool = True, parallel: bool = True, max_workers: int = 4) -> List[MediaFile]:
        """
        Scan path for media files with optional parallel metadata extraction
        
        Args:
            path: Directory to scan
            recursive: Scan subdirectories recursively
            parallel: Use parallel processing for metadata extraction (default: True)
            max_workers: Maximum number of parallel workers (default: 4)
        
        Returns:
            List of MediaFile objects
        """
        if not path.exists():
            return []

        # First pass: discover all media files (fast, no metadata extraction)
        files = []
        pattern = "**/*" if recursive else "*"

        for file_path in path.glob(pattern):
            if file_path.is_file():
                # Don't extract metadata yet - will do in parallel or sequential pass
                media_file = self._analyze_file(file_path, extract_metadata=False)
                if media_file:
                    files.append(media_file)

        # Second pass: extract metadata in parallel (for video files)
        video_files = [f for f in files if f.type == MediaType.VIDEO]
        
        if parallel and video_files and len(video_files) > 1:
            # Use ThreadPoolExecutor for parallel metadata extraction
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all metadata extraction tasks
                futures = {executor.submit(self._get_video_metadata, f): f for f in video_files}
                
                # Wait for all to complete (results are stored in media_file objects)
                for future in concurrent.futures.as_completed(futures):
                    media_file = futures[future]
                    try:
                        future.result()  # Wait for completion, exception if failed
                    except Exception:
                        pass  # Metadata extraction is optional, continue on error
                
                # Categorize clips after metadata is extracted
                for media_file in video_files:
                    if media_file.duration:  # Only categorize if metadata was extracted
                        media_file.category = self._categorize_clip(media_file)
        else:
            # Sequential processing (backward compatible)
            for media_file in video_files:
                self._get_video_metadata(media_file)
                if media_file.duration:
                    media_file.category = self._categorize_clip(media_file)

        return files

    def _analyze_file(self, path: Path, extract_metadata: bool = False) -> Optional[MediaFile]:
        """
        Analyze a single file
        
        Args:
            path: File path to analyze
            extract_metadata: If True, extract metadata immediately (for sequential mode)
        """
        ext = path.suffix.lower()

        # Determine media type
        if ext in self.video_extensions:
            media_type = MediaType.VIDEO
        elif ext in self.audio_extensions:
            media_type = MediaType.AUDIO
        elif ext in self.image_extensions:
            media_type = MediaType.IMAGE
        else:
            return None  # Skip non-media files

        # Create basic media file
        media_file = MediaFile(
            path=path,
            size=path.stat().st_size,
            type=media_type
        )

        # Get detailed metadata for videos (only if extract_metadata=True, for backward compatibility)
        if extract_metadata and media_type == MediaType.VIDEO:
            self._get_video_metadata(media_file)
            if media_file.duration:
                media_file.category = self._categorize_clip(media_file)

        return media_file

    def _get_video_metadata(self, media_file: MediaFile):
        """Get comprehensive video metadata using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-print_format', 'json',
                '-show_format',          # Format/container info
                '-show_streams',         # All streams (video + audio)
                '-show_chapters',        # Chapter information
                str(media_file.path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                data = json.loads(result.stdout)

                # Extract format metadata
                if 'format' in data:
                    format_info = data['format']
                    
                    # Container format
                    format_name = format_info.get('format_name', '')
                    if format_name:
                        media_file.container_format = format_name.split(',')[0]
                    
                    # Bitrate
                    bit_rate = format_info.get('bit_rate')
                    if bit_rate:
                        media_file.total_bitrate = int(bit_rate)
                    
                    # Creation time from tags
                    tags = format_info.get('tags', {})
                    if 'creation_time' in tags:
                        try:
                            from dateutil.parser import parse
                            media_file.creation_time = parse(tags['creation_time'])
                        except (ImportError, ValueError):
                            pass
                    
                    # Timecode
                    if 'timecode' in tags:
                        media_file.timecode = tags['timecode']
                    
                    # Camera metadata from tags
                    media_file.encoder = tags.get('encoder') or tags.get('encoded_by')
                    media_file.camera_make = tags.get('make') or tags.get('manufacturer')
                    media_file.camera_model = tags.get('model')

                # Extract stream metadata
                video_stream = None
                audio_streams = []

                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                    elif stream.get('codec_type') == 'audio':
                        audio_streams.append(stream)

                # Video stream metadata
                if video_stream:
                    # Resolution
                    if 'width' in video_stream and 'height' in video_stream:
                        media_file.resolution = (video_stream['width'], video_stream['height'])
                        
                        # Aspect ratio
                        if video_stream['width'] > 0 and video_stream['height'] > 0:
                            media_file.aspect_ratio = video_stream['width'] / video_stream['height']
                    
                    # Framerate
                    if 'r_frame_rate' in video_stream:
                        parts = video_stream['r_frame_rate'].split('/')
                        if len(parts) == 2 and int(parts[1]) != 0:
                            media_file.framerate = int(parts[0]) / int(parts[1])
                    
                    # Codec
                    media_file.codec = video_stream.get('codec_name')
                    
                    # Video bitrate
                    bit_rate = video_stream.get('bit_rate')
                    if bit_rate:
                        media_file.video_bitrate = int(bit_rate)
                    
                    # Color information (critical for multicam matching)
                    media_file.color_space = video_stream.get('color_space')
                    media_file.color_primaries = video_stream.get('color_primaries')
                    media_file.color_trc = video_stream.get('color_trc')
                    media_file.pixel_format = video_stream.get('pix_fmt')
                    
                    # Bit depth (from pixel format)
                    pix_fmt = video_stream.get('pix_fmt', '')
                    if '10' in pix_fmt or '12' in pix_fmt:
                        media_file.bit_depth = 10 if '10' in pix_fmt else 12
                    elif '16' in pix_fmt:
                        media_file.bit_depth = 16
                    else:
                        media_file.bit_depth = 8
                    
                    # Rotation
                    rotation = video_stream.get('tags', {}).get('rotate')
                    if rotation:
                        try:
                            media_file.rotation = int(rotation)
                        except (ValueError, TypeError):
                            pass
                    
                    # Duration (prefer video stream, fallback to format)
                    if 'duration' in video_stream:
                        try:
                            media_file.duration = float(video_stream['duration'])
                        except (ValueError, TypeError):
                            pass
                    elif 'format' in data and 'duration' in data['format']:
                        try:
                            media_file.duration = float(data['format']['duration'])
                        except (ValueError, TypeError):
                            pass

                # Audio stream metadata (first audio stream)
                if audio_streams:
                    audio = audio_streams[0]  # Primary audio stream
                    media_file.audio_codec = audio.get('codec_name')
                    
                    sample_rate = audio.get('sample_rate')
                    if sample_rate:
                        try:
                            media_file.audio_sample_rate = int(sample_rate)
                        except (ValueError, TypeError):
                            pass
                    
                    channels = audio.get('channels')
                    if channels:
                        try:
                            media_file.audio_channels = int(channels)
                        except (ValueError, TypeError):
                            pass
                    
                    bit_rate = audio.get('bit_rate')
                    if bit_rate:
                        try:
                            media_file.audio_bitrate = int(bit_rate)
                        except (ValueError, TypeError):
                            pass
                    
                    # Audio language
                    lang = audio.get('tags', {}).get('language')
                    if lang:
                        media_file.audio_language = lang

                # Store raw metadata for advanced usage
                media_file.metadata = {
                    'format': data.get('format', {}),
                    'streams': data.get('streams', []),
                    'chapters': data.get('chapters', [])
                }
                
                # Get camera-specific metadata (optional exiftool)
                self._get_camera_metadata(media_file)
                
                # Fast content analysis (during scan)
                self._analyze_content_fast(media_file)

        except Exception:
            pass  # Metadata extraction is optional

    def _analyze_content_fast(self, media_file: MediaFile):
        """Fast content analysis during scan"""
        if media_file.type != MediaType.VIDEO:
            return
        
        # Speech detection (fast)
        media_file.has_speech = self._detect_speech_fast(media_file.path)
        
        # Basic exposure check
        media_file.exposure_rating = self._check_exposure_fast(media_file.path)
        
        # Face count (heuristic - can be enhanced later)
        media_file.face_count = self._count_faces_fast(media_file.path)

    def _detect_speech_fast(self, file_path: Path) -> bool:
        """Detect if file contains speech using FFmpeg silencedetect"""
        try:
            cmd = [
                "ffmpeg",
                "-i", str(file_path),
                "-af", "silencedetect=n=-30dB:d=0.5",
                "-f", "null",
                "-"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            # If there are non-silent parts, likely has speech
            return "silence_end" in result.stderr
        except Exception:
            return False

    def _check_exposure_fast(self, file_path: Path) -> str:
        """Basic exposure check (simplified - returns 'normal' for now)"""
        # TODO: Implement histogram analysis for exposure rating
        # For now, return 'normal' - can be enhanced with FFmpeg histogram analysis
        return "normal"

    def _count_faces_fast(self, file_path: Path) -> int:
        """Fast face count (heuristic-based for now)"""
        # TODO: Implement lightweight face detection model or use filename patterns
        # For now, return 0 - can be enhanced with OpenCV or lightweight ML model
        name_lower = file_path.name.lower()
        if "interview" in name_lower or "talking" in name_lower:
            return 1
        return 0

    def _get_camera_metadata(self, media_file: MediaFile):
        """Get camera-specific metadata using exiftool (if available)"""
        if media_file.type != MediaType.VIDEO:
            return

        try:
            # Check if exiftool is available
            subprocess.run(['exiftool', '-ver'], capture_output=True, check=True, timeout=2)

            cmd = ['exiftool', '-j', '-q', str(media_file.path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                exif_data = json.loads(result.stdout)[0] if result.stdout else {}

                # Camera metadata
                if 'Make' in exif_data:
                    media_file.camera_make = exif_data['Make']
                if 'Model' in exif_data:
                    media_file.camera_model = exif_data['Model']

                # Sony-specific (FX30/ZV-E10)
                if 'PictureProfile' in exif_data:
                    media_file.metadata['picture_profile'] = exif_data['PictureProfile']
                if 'ColorMode' in exif_data:
                    media_file.metadata['color_mode'] = exif_data['ColorMode']
                if 'ISO' in exif_data:
                    media_file.metadata['iso'] = exif_data['ISO']
                if 'WhiteBalance' in exif_data:
                    media_file.metadata['white_balance'] = exif_data['WhiteBalance']
                if 'ShutterSpeed' in exif_data:
                    media_file.metadata['shutter_speed'] = exif_data['ShutterSpeed']
                if 'FNumber' in exif_data:
                    media_file.metadata['aperture'] = exif_data['FNumber']
                if 'LensModel' in exif_data:
                    media_file.metadata['lens'] = exif_data['LensModel']
                if 'SteadyShot' in exif_data:
                    media_file.metadata['stabilization'] = exif_data['SteadyShot']

        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            # exiftool not available, skip
            pass
        except Exception:
            pass

    def _categorize_clip(self, media_file: MediaFile) -> ClipCategory:
        """Categorize video clip based on metadata"""
        if not media_file.duration:
            return ClipCategory.UNKNOWN

        config = self.config.media
        duration = media_file.duration

        # Check filename patterns
        name_lower = media_file.path.stem.lower()

        if 'test' in name_lower or 'check' in name_lower:
            return ClipCategory.TEST_CLIP

        if 'drone' in name_lower or 'dji' in name_lower:
            return ClipCategory.DRONE

        if 'screen' in name_lower or 'recording' in name_lower:
            return ClipCategory.SCREEN_RECORDING

        if 'interview' in name_lower:
            return ClipCategory.INTERVIEW

        if 'timelapse' in name_lower or 'tl' in name_lower:
            return ClipCategory.TIMELAPSE

        # Duration-based categorization
        if duration <= config.test_clip_max:
            return ClipCategory.TEST_CLIP

        if config.b_roll_min <= duration <= config.b_roll_max:
            return ClipCategory.B_ROLL

        if duration >= config.a_roll_min:
            return ClipCategory.A_ROLL

        # Check framerate for slow motion
        if media_file.framerate and media_file.framerate >= 60:
            return ClipCategory.SLOW_MOTION

        return ClipCategory.B_ROLL  # Default


class MediaImporter:
    """Handles media import with deduplication and organization"""

    def __init__(self, project):
        self.project = project
        self.config = get_config()
        self.imported_files = set()
        self._load_import_history()

    def _load_import_history(self):
        """Load import history to prevent duplicates"""
        history_file = self.project.path / ".studioflow" / "import_history.txt"
        if history_file.exists():
            self.imported_files = set(history_file.read_text().splitlines())

    def _save_import_history(self):
        """Save import history"""
        history_file = self.project.path / ".studioflow" / "import_history.txt"
        history_file.parent.mkdir(exist_ok=True)
        history_file.write_text("\n".join(sorted(self.imported_files)))

    def import_from_path(self, source_path: Path, organize: bool = True) -> Dict[str, Any]:
        """Import media from a path"""
        scanner = MediaScanner()
        files = scanner.scan(source_path)

        if not files:
            return {"total_files": 0, "total_size": 0, "skipped": 0}

        stats = {
            "total_files": 0,
            "total_size": 0,
            "skipped": 0,
            "by_category": {}
        }

        # Import with progress
        with Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
            console=console
        ) as progress:

            task = progress.add_task(
                f"Importing {len(files)} files...",
                total=len(files)
            )

            # Use thread pool for parallel copy
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = []

                for media_file in files:
                    future = executor.submit(
                        self.import_file,
                        media_file,
                        organize
                    )
                    futures.append((future, media_file))

                for future, media_file in futures:
                    result = future.result()

                    if result['imported']:
                        stats['total_files'] += 1
                        stats['total_size'] += media_file.size

                        # Track by category
                        cat = str(media_file.category or "UNKNOWN")
                        stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
                    else:
                        stats['skipped'] += 1

                    progress.advance(task)

        self._save_import_history()
        return stats

    def import_file(self, media_file: MediaFile, organize: bool = True, normalize: bool = True) -> Dict[str, Any]:
        """
        Import a single media file
        
        Args:
            media_file: Media file to import
            organize: Whether to organize into subdirectories
            normalize: Whether to normalize audio (-14 LUFS, PCM codec, clean filename)
        """
        # Check for duplicates
        checksum = self._get_checksum(media_file.path)

        if checksum in self.imported_files:
            return {"imported": False, "reason": "duplicate"}

        # Determine destination
        if organize:
            dest_path = self._get_organized_path(media_file)
        else:
            dest_path = self.project.path / "01_MEDIA" / media_file.path.name

        # Create destination directory
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Normalize video files on import (audio to -14 LUFS, PCM codec, clean filename)
            # For non-video files or if normalize=False, just copy
            video_extensions = {'.mp4', '.mov', '.MP4', '.MOV', '.mxf', '.MXF', '.avi', '.AVI'}
            is_video = media_file.path.suffix in video_extensions
            
            if normalize and is_video:
                from .media_normalizer import MediaNormalizer
                normalizer = MediaNormalizer(target_lufs=-14.0)
                result = normalizer.normalize_video(
                    input_file=media_file.path,
                    output_file=dest_path,
                    normalize_filename=True,
                    output_dir=dest_path.parent
                )
                
                if result.success:
                    # Record import
                    self.imported_files.add(checksum)
                    return {
                        "imported": True,
                        "destination": result.output_file,
                        "checksum": checksum,
                        "normalized": True
                    }
                else:
                    # Normalization failed, fall back to copy
                    # Note: console may not be available in all contexts
                    try:
                        from rich.console import Console
                        console = Console()
                        console.print(f"[yellow]Warning: Normalization failed for {media_file.path.name}, copying original: {result.error_message}[/yellow]")
                    except:
                        pass
                    shutil.copy2(media_file.path, dest_path)
            else:
                # Copy file (preserve metadata) - non-video files or normalize=False
                shutil.copy2(media_file.path, dest_path)

            # Record import
            self.imported_files.add(checksum)

            return {
                "imported": True,
                "destination": dest_path,
                "checksum": checksum,
                "normalized": normalize and is_video
            }

        except Exception as e:
            return {
                "imported": False,
                "reason": str(e)
            }

    def _get_checksum(self, path: Path) -> str:
        """Calculate file checksum for deduplication"""
        # Use size + name for quick check (full hash is slow for large files)
        stat = path.stat()
        unique_str = f"{path.name}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(unique_str.encode()).hexdigest()

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for shell compatibility.
        Replaces spaces, parentheses, and special chars with underscores.
        """
        import re
        # Get stem and suffix
        path = Path(filename)
        stem = path.stem
        suffix = path.suffix

        # Replace problematic characters
        # Spaces → underscores
        stem = stem.replace(' ', '_')
        # Parentheses and brackets → underscores
        stem = re.sub(r'[\(\)\[\]\{\}]', '_', stem)
        # Multiple underscores → single
        stem = re.sub(r'_+', '_', stem)
        # Remove leading/trailing underscores
        stem = stem.strip('_')

        return f"{stem}{suffix}"

    def _get_organized_path(self, media_file: MediaFile) -> Path:
        """Get organized destination path based on category"""
        base = self.project.path / "01_MEDIA"

        # Organize by category
        if media_file.category:
            category_folder = base / media_file.category.value
        else:
            category_folder = base / "UNSORTED"

        # Add date subfolder
        date_str = datetime.now().strftime("%Y%m%d")
        dest_folder = category_folder / date_str

        # Sanitize filename for shell compatibility
        clean_name = self._sanitize_filename(media_file.path.name)

        # Generate unique filename if needed
        dest_path = dest_folder / clean_name
        if dest_path.exists():
            # Add number suffix
            stem = Path(clean_name).stem
            suffix = Path(clean_name).suffix
            for i in range(1, 100):
                new_name = f"{stem}_{i}{suffix}"
                dest_path = dest_folder / new_name
                if not dest_path.exists():
                    break

        return dest_path