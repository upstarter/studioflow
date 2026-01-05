"""
Multicam Color Matching
Handles color matching for multicam workflows (FX30 + ZV-E10)
Uses DaVinci Resolve color management for optimal workflow
"""

from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import subprocess
import json
import tempfile

from studioflow.core.media import MediaFile, MediaScanner


class MulticamColorMatcher:
    """
    Multicam color matching using DaVinci Resolve color management.
    
    Since DaVinci Resolve handles S-Log3 → Rec.709 conversion internally
    via color management, this focuses on:
    1. Resolve project setup with correct color management
    2. Exposure and white balance matching
    """
    
    def __init__(self):
        self.scanner = MediaScanner()
    
    def setup_resolve_color_management(
        self,
        input_color_space: str = "S-Gamut3.Cine/S-Log3",
        timeline_color_space: str = "DaVinci Wide Gamut",
        timeline_gamma: str = "DaVinci Intermediate",
        output_color_space: str = "Rec.709",
        output_gamma: str = "Gamma 2.4"
    ) -> Dict[str, Any]:
        """
        Generate Resolve color management settings.
        
        Returns settings dictionary for Resolve project configuration.
        These settings should be applied via Resolve API or manually.
        """
        return {
            "color_science": "DaVinci YRGB Color Managed",
            "timeline_color_space": timeline_color_space,
            "timeline_gamma": timeline_gamma,
            "output_color_space": output_color_space,
            "output_gamma": output_gamma,
            "input_color_space": input_color_space,  # For both cameras (S-Log3)
            "auto_color_management": True
        }
    
    def detect_sony_profile(self, media_file: MediaFile) -> str:
        """
        Detect Sony picture profile from metadata.
        
        Returns: "slog3", "slog2", "scinetone", "cine2", "rec709", "unknown"
        """
        # Check metadata dict for picture profile
        picture_profile = media_file.metadata.get('picture_profile', '')
        color_mode = media_file.metadata.get('color_mode', '')
        color_trc = media_file.color_trc or ''
        
        profile_str = f"{picture_profile} {color_mode} {color_trc}".upper()
        
        if 'S-LOG3' in profile_str or 'SLOG3' in profile_str:
            return "slog3"
        elif 'S-LOG2' in profile_str or 'SLOG2' in profile_str:
            return "slog2"
        elif 'S-CINETONE' in profile_str or 'SCINETONE' in profile_str:
            return "scinetone"
        elif 'CINE2' in profile_str:
            return "cine2"
        elif 'REC.709' in profile_str or 'REC709' in profile_str:
            return "rec709"
        
        return "unknown"
    
    def match_exposure_white_balance(
        self,
        reference_clip: Path,
        target_clip: Path,
        output_path: Path
    ) -> Dict[str, Any]:
        """
        Match exposure and white balance between two clips.
        
        This is optional pre-processing if matching needs to happen before Resolve.
        Footage is kept in S-Log3 (DaVinci handles conversion).
        
        Args:
            reference_clip: Reference clip (FX30)
            target_clip: Target clip to match (ZV-E10)
            output_path: Output path for matched clip
        
        Returns:
            Dict with success status and correction parameters
        """
        result = {
            "success": False,
            "correction": {},
            "error": None
        }
        
        try:
            # Extract sample frames for analysis
            ref_frame = self._extract_sample_frame(reference_clip)
            target_frame = self._extract_sample_frame(target_clip)
            
            if not ref_frame or not target_frame:
                result["error"] = "Failed to extract sample frames"
                return result
            
            # Calculate exposure and WB corrections
            correction = self._calculate_exposure_wb_correction(ref_frame, target_frame)
            
            # Apply correction via FFmpeg (keep in S-Log3)
            success = self._apply_exposure_wb_correction(
                target_clip,
                output_path,
                correction
            )
            
            result["success"] = success
            result["correction"] = correction
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _extract_sample_frame(self, video_path: Path, timestamp: float = 5.0) -> Optional[Path]:
        """Extract sample frame for color analysis"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                frame_path = Path(tmp.name)
            
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-ss", str(timestamp),
                "-vframes", "1",
                "-y",
                str(frame_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0 and frame_path.exists():
                return frame_path
            return None
        except Exception:
            return None
    
    def _calculate_exposure_wb_correction(
        self,
        ref_frame: Path,
        target_frame: Path
    ) -> Dict[str, float]:
        """
        Calculate exposure and white balance correction parameters.
        
        This is a simplified implementation. In practice, would analyze
        histograms and calculate precise adjustments.
        
        Returns:
            Dict with correction parameters (brightness, contrast, colorbalance)
        """
        # TODO: Implement proper histogram analysis
        # For now, return minimal corrections
        # In production, would:
        # 1. Extract RGB histograms from both frames
        # 2. Calculate brightness/contrast differences
        # 3. Calculate color temperature/tint differences
        # 4. Return adjustment values
        
        return {
            "brightness": 0.0,  # -1.0 to 1.0
            "contrast": 1.0,    # 0.0 to 2.0
            "saturation": 1.0,  # 0.0 to 2.0
            "rs": 0.0,          # Red shadows adjustment
            "gs": 0.0,          # Green shadows adjustment
            "bs": 0.0,          # Blue shadows adjustment
            "rm": 0.0,          # Red midtones adjustment
            "gm": 0.0,          # Green midtones adjustment
            "bm": 0.0,          # Blue midtones adjustment
            "rh": 0.0,          # Red highlights adjustment
            "gh": 0.0,          # Green highlights adjustment
            "bh": 0.0           # Blue highlights adjustment
        }
    
    def _apply_exposure_wb_correction(
        self,
        input_path: Path,
        output_path: Path,
        correction: Dict[str, float]
    ) -> bool:
        """
        Apply exposure and white balance correction via FFmpeg.
        
        Keeps footage in S-Log3 (no conversion LUT - DaVinci handles it).
        """
        try:
            # Build filter chain
            filters = []
            
            # Exposure adjustments
            if correction.get("brightness", 0.0) != 0.0 or correction.get("contrast", 1.0) != 1.0:
                brightness = correction.get("brightness", 0.0)
                contrast = correction.get("contrast", 1.0)
                saturation = correction.get("saturation", 1.0)
                filters.append(f"eq=brightness={brightness}:contrast={contrast}:saturation={saturation}")
            
            # White balance adjustments (colorbalance)
            rs = correction.get("rs", 0.0)
            gs = correction.get("gs", 0.0)
            bs = correction.get("bs", 0.0)
            rm = correction.get("rm", 0.0)
            gm = correction.get("gm", 0.0)
            bm = correction.get("bm", 0.0)
            rh = correction.get("rh", 0.0)
            gh = correction.get("gh", 0.0)
            bh = correction.get("bh", 0.0)
            
            if any([rs, gs, bs, rm, gm, bm, rh, gh, bh]):
                filters.append(
                    f"colorbalance=rs={rs}:gs={gs}:bs={bs}:"
                    f"rm={rm}:gm={gm}:bm={bm}:"
                    f"rh={rh}:gh={gh}:bh={bh}"
                )
            
            # Build FFmpeg command
            cmd = ["ffmpeg", "-i", str(input_path)]
            
            if filters:
                cmd.extend(["-vf", ",".join(filters)])
            
            # Copy audio
            cmd.extend(["-c:a", "copy"])
            
            # Output
            cmd.extend(["-y", str(output_path)])
            
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            return result.returncode == 0
            
        except Exception:
            return False


