"""
Export Validation System
Validates video exports for YouTube compliance and quality
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .ffmpeg import FFmpegProcessor


@dataclass
class ValidationResult:
    """Export validation result"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]


class ExportValidator:
    """Validates video exports for platform compliance"""
    
    # YouTube requirements
    YOUTUBE_REQUIREMENTS = {
        "max_file_size_gb": 128,
        "max_duration_hours": 12,
        "min_resolution": (426, 240),
        "max_resolution": (7680, 4320),
        "audio_lufs_target": -14.0,
        "audio_lufs_tolerance": 1.0,
        "audio_true_peak_max": -1.0,
        "supported_codecs": ["h264", "h265", "vp9", "av1"],
        "max_bitrate_mbps": 100,
    }
    
    def validate_youtube(self, video_path: Path) -> Dict[str, Any]:
        """Validate video for YouTube upload"""
        errors = []
        warnings = []
        details = {}
        
        if not video_path.exists():
            return {
                "valid": False,
                "errors": [f"File not found: {video_path}"],
                "warnings": [],
                "details": {}
            }
        
        # Get video info
        info = FFmpegProcessor.get_media_info(video_path)
        
        # Check file size
        file_size_gb = video_path.stat().st_size / (1024**3)
        details["file_size_gb"] = file_size_gb
        
        if file_size_gb > self.YOUTUBE_REQUIREMENTS["max_file_size_gb"]:
            errors.append(f"File too large: {file_size_gb:.1f} GB (max: {self.YOUTUBE_REQUIREMENTS['max_file_size_gb']} GB)")
        elif file_size_gb > 100:
            warnings.append(f"Large file: {file_size_gb:.1f} GB (upload may be slow)")
        
        # Check duration
        duration = info.get("duration_seconds", 0)
        duration_hours = duration / 3600
        details["duration_hours"] = duration_hours
        
        if duration_hours > self.YOUTUBE_REQUIREMENTS["max_duration_hours"]:
            errors.append(f"Video too long: {duration_hours:.1f} hours (max: {self.YOUTUBE_REQUIREMENTS['max_duration_hours']} hours)")
        
        # Check resolution
        resolution = info.get("resolution", "unknown")
        if isinstance(resolution, tuple):
            width, height = resolution
            details["resolution"] = f"{width}x{height}"
            
            min_w, min_h = self.YOUTUBE_REQUIREMENTS["min_resolution"]
            max_w, max_h = self.YOUTUBE_REQUIREMENTS["max_resolution"]
            
            if width < min_w or height < min_h:
                errors.append(f"Resolution too low: {width}x{height} (min: {min_w}x{min_h})")
            elif width > max_w or height > max_h:
                errors.append(f"Resolution too high: {width}x{height} (max: {max_w}x{max_h})")
            
            # Warn about non-standard aspect ratios
            aspect_ratio = width / height
            if aspect_ratio < 1.33 or aspect_ratio > 2.0:
                warnings.append(f"Non-standard aspect ratio: {aspect_ratio:.2f} (YouTube prefers 16:9)")
        else:
            warnings.append(f"Could not determine resolution: {resolution}")
        
        # Check codec
        codec = info.get("video_codec", "").lower()
        details["codec"] = codec
        
        if codec and codec not in self.YOUTUBE_REQUIREMENTS["supported_codecs"]:
            warnings.append(f"Codec '{codec}' may not be optimal (preferred: h264)")
        
        # Check audio levels (LUFS)
        audio_lufs = self._check_audio_levels(video_path)
        if audio_lufs:
            details["audio_lufs"] = audio_lufs
            target = self.YOUTUBE_REQUIREMENTS["audio_lufs_target"]
            tolerance = self.YOUTUBE_REQUIREMENTS["audio_lufs_tolerance"]
            
            if abs(audio_lufs - target) > tolerance:
                if audio_lufs < target - tolerance:
                    warnings.append(f"Audio too quiet: {audio_lufs:.1f} LUFS (target: {target} LUFS) - YouTube will boost")
                else:
                    warnings.append(f"Audio too loud: {audio_lufs:.1f} LUFS (target: {target} LUFS) - YouTube will reduce")
        
        # Check bitrate
        bitrate = info.get("bitrate_kbps", 0)
        if bitrate:
            bitrate_mbps = bitrate / 1000
            details["bitrate_mbps"] = bitrate_mbps
            max_bitrate = self.YOUTUBE_REQUIREMENTS["max_bitrate_mbps"]
            
            if bitrate_mbps > max_bitrate:
                warnings.append(f"Bitrate very high: {bitrate_mbps:.1f} Mbps (max recommended: {max_bitrate} Mbps)")
        
        # Check if file is readable
        try:
            test_cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "json",
                str(video_path)
            ]
            result = subprocess.run(test_cmd, capture_output=True, timeout=10)
            if result.returncode != 0:
                errors.append("File may be corrupted or unreadable")
        except:
            warnings.append("Could not verify file integrity")
        
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "details": details
        }
    
    def _check_audio_levels(self, video_path: Path) -> Optional[float]:
        """Check audio LUFS levels"""
        try:
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
                "-f", "null", "-"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Parse JSON from stderr
            json_match = re.search(r'\{[^}]+\}', result.stderr[::-1])
            if json_match:
                data = json.loads(json_match.group()[::-1])
                return float(data.get("input_i", 0))
        except:
            pass
        
        return None

