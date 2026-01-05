"""
Media Normalization Service
Ensures all footage is properly normalized for editing workflow:
- Audio: -14 LUFS, PCM format
- Filenames: Clean, consistent naming for audio markers
- Organization: Single footage directory with only normalized files
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from .ffmpeg import FFmpegProcessor, ProcessResult


@dataclass
class NormalizationResult:
    """Result of normalization process"""
    success: bool
    input_file: Path
    output_file: Optional[Path] = None
    error_message: Optional[str] = None
    lufs_before: Optional[float] = None
    lufs_after: Optional[float] = None
    duration: Optional[float] = None


class MediaNormalizer:
    """Normalize media files for consistent editing workflow"""
    
    def __init__(self, target_lufs: float = -14.0, audio_codec: str = "pcm_s16le"):
        """
        Args:
            target_lufs: Target LUFS level (default -14.0 for YouTube)
            audio_codec: Audio codec (default pcm_s16le for PCM 16-bit)
        """
        self.target_lufs = target_lufs
        self.audio_codec = audio_codec
        self.ffmpeg = FFmpegProcessor()
    
    def normalize_video(self, 
                       input_file: Path, 
                       output_file: Optional[Path] = None,
                       normalize_filename: bool = True,
                       output_dir: Optional[Path] = None) -> NormalizationResult:
        """
        Normalize video file: audio to -14 LUFS, PCM audio, clean filename
        
        Args:
            input_file: Input video file
            output_file: Output file path (auto-generated if None)
            normalize_filename: If True, clean up filename for audio markers
        
        Returns:
            NormalizationResult with success status and metadata
        """
        if not input_file.exists():
            return NormalizationResult(
                success=False,
                input_file=input_file,
                error_message=f"Input file not found: {input_file}"
            )
        
        # Generate output filename
        if output_file is None:
            output_file = self._generate_output_filename(input_file, normalize_filename, output_dir)
        
        # Check if already normalized (same output path exists and is recent)
        if output_file.exists() and output_file.stat().st_mtime >= input_file.stat().st_mtime:
            # Check if it's already normalized
            lufs_check = self._check_lufs(output_file)
            if lufs_check and abs(lufs_check - self.target_lufs) < 0.5:
                return NormalizationResult(
                    success=True,
                    input_file=input_file,
                    output_file=output_file,
                    lufs_before=lufs_check,
                    lufs_after=lufs_check
                )
        
        # Get original LUFS
        lufs_before = self._check_lufs(input_file)
        
        # Normalize audio to -14 LUFS with PCM codec
        result = self._normalize_audio_pcm(input_file, output_file, self.target_lufs)
        
        if result.success:
            lufs_after = self._check_lufs(output_file)
            return NormalizationResult(
                success=True,
                input_file=input_file,
                output_file=output_file,
                lufs_before=lufs_before,
                lufs_after=lufs_after
            )
        else:
            return NormalizationResult(
                success=False,
                input_file=input_file,
                error_message=result.error_message
            )
    
    def _normalize_audio_pcm(self, input_file: Path, output_file: Path, target_lufs: float) -> ProcessResult:
        """
        Normalize audio to target LUFS and convert to PCM
        
        Two-pass normalization:
        1. Analyze audio to get loudness stats
        2. Apply normalization with PCM audio codec
        """
        # First pass - analyze audio
        analyze_cmd = [
            "ffmpeg", "-i", str(input_file),
            "-af", f"loudnorm=I={target_lufs}:print_format=json",
            "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(analyze_cmd, capture_output=True, text=True, check=True, timeout=300)
            
            # Extract loudnorm stats from stderr
            json_match = re.search(r'\{[^}]+\}', result.stderr[::-1])
            if json_match:
                stats = json.loads(json_match.group()[::-1])
                
                # Second pass - apply normalization with PCM audio
                filter_str = (
                    f"loudnorm=I={target_lufs}:"
                    f"measured_I={stats.get('input_i', -70)}:"
                    f"measured_TP={stats.get('input_tp', -10)}:"
                    f"measured_LRA={stats.get('input_lra', 7)}:"
                    f"measured_thresh={stats.get('input_thresh', -80)}"
                )
            else:
                # Fallback to simple normalization
                filter_str = f"loudnorm=I={target_lufs}"
            
            # Apply normalization with PCM audio codec
            cmd = [
                "ffmpeg", "-i", str(input_file),
                "-af", filter_str,
                "-c:v", "copy",  # Keep video unchanged
                "-c:a", self.audio_codec,  # PCM audio
                "-ar", "48000",  # 48kHz sample rate (professional standard)
                "-y", str(output_file)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
            
            # Verify output file was created
            if output_file.exists() and output_file.stat().st_size > 0:
                size_mb = output_file.stat().st_size / (1024 * 1024)
                return ProcessResult(
                    success=True,
                    output_path=output_file,
                    file_size_mb=size_mb
                )
            else:
                return ProcessResult(
                    success=False,
                    error_message="Output file was not created or is empty"
                )
                
        except subprocess.TimeoutExpired:
            return ProcessResult(
                success=False,
                error_message="Normalization timed out (>10 minutes)"
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr[:200] if e.stderr else str(e)
            return ProcessResult(
                success=False,
                error_message=f"FFmpeg error: {error_msg}"
            )
        except Exception as e:
            return ProcessResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _check_lufs(self, file_path: Path) -> Optional[float]:
        """Check current LUFS level of file"""
        try:
            cmd = [
                "ffmpeg", "-i", str(file_path),
                "-af", "loudnorm=I=-14:print_format=json",
                "-f", "null", "-"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            json_match = re.search(r'\{[^}]+\}', result.stderr[::-1])
            if json_match:
                stats = json.loads(json_match.group()[::-1])
                return float(stats.get('input_i', -99))
        except:
            pass
        return None
    
    def _generate_output_filename(self, input_file: Path, normalize_filename: bool, output_dir: Optional[Path] = None) -> Path:
        """
        Generate output filename
        
        Rules:
        - Remove _normalized suffix if present (avoid double normalization)
        - Clean up filename for audio markers (remove special chars, normalize spaces)
        - Keep original extension
        - Output to output_dir if provided, else same directory as input
        """
        stem = input_file.stem
        
        # Remove _normalized suffix if present
        if stem.endswith("_normalized"):
            stem = stem[:-11]  # Remove "_normalized"
        
        if normalize_filename:
            # Clean filename for audio markers:
            # - Replace spaces with underscores (standard for audio markers)
            # - Remove special characters that might confuse transcription
            # - Keep alphanumeric, underscores, hyphens, parentheses (for numbered takes)
            # - Preserve parentheses for numbered clips like (1), (2)
            stem = re.sub(r'[^\w\-_()]', '_', stem)
            stem = re.sub(r'_+', '_', stem)  # Collapse multiple underscores
            stem = stem.strip('_')  # Remove leading/trailing underscores
        
        output_path = (output_dir if output_dir else input_file.parent) / f"{stem}{input_file.suffix}"
        return output_path
    
    def normalize_directory(self,
                           input_dir: Path,
                           output_dir: Path,
                           preserve_originals: bool = True,
                           original_dir: Optional[Path] = None) -> Dict[str, List[NormalizationResult]]:
        """
        Normalize all video files in a directory
        
        Args:
            input_dir: Source directory with raw footage
            output_dir: Output directory for normalized files (clean footage directory)
            preserve_originals: If True, copy originals to separate directory
            original_dir: Directory for originals (defaults to output_dir/../00_ORIGINALS)
        
        Returns:
            Dict with 'success' and 'failed' lists of NormalizationResult
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if preserve_originals and original_dir:
            original_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all video files
        video_extensions = ['.mp4', '.mov', '.MP4', '.MOV', '.mxf', '.MXF', '.avi', '.AVI']
        video_files = []
        for ext in video_extensions:
            video_files.extend(input_dir.rglob(f"*{ext}"))
        
        results = {
            'success': [],
            'failed': []
        }
        
        for video_file in video_files:
            # Skip already normalized files
            if "_normalized" in video_file.stem:
                continue
            
            # Generate output filename (clean name, no _normalized suffix)
            output_file = self._generate_output_filename(video_file, normalize_filename=True, output_dir=output_dir)
            
            # Preserve original if requested
            if preserve_originals and original_dir:
                import shutil
                original_copy = original_dir / video_file.name
                if not original_copy.exists():
                    shutil.copy2(video_file, original_copy)
            
            # Normalize
            result = self.normalize_video(video_file, output_file, normalize_filename=True)
            
            if result.success:
                results['success'].append(result)
            else:
                results['failed'].append(result)
        
        return results

