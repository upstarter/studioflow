"""
Sony camera specific functionality
FX30 and ZV-E10 optimized workflows
"""

import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .ffmpeg import FFmpegProcessor, ProcessResult
from .config import get_config


@dataclass
class SonyClip:
    """Sony camera clip metadata"""
    file_path: Path
    camera: str  # "fx30" or "zve10"
    clip_name: str
    date_shot: datetime
    duration: float
    resolution: str
    framerate: float
    color_profile: str
    file_size_gb: float
    take_number: Optional[int] = None
    scene: Optional[str] = None


class SonyMediaHandler:
    """Handle Sony FX30 and ZV-E10 media"""

    @staticmethod
    def detect_sony_media(directory: Path) -> Dict[str, List[SonyClip]]:
        """Detect and organize Sony camera files"""

        clips = {
            "fx30": [],
            "zve10": []
        }

        # Sony FX30 files (C0001.MP4, etc.)
        for file in directory.glob("C*.MP4"):
            clip = SonyMediaHandler._parse_fx30_clip(file)
            if clip:
                clips["fx30"].append(clip)

        # Sony ZV-E10 files (DSC00001.MP4, etc.)
        for file in directory.glob("DSC*.MP4"):
            clip = SonyMediaHandler._parse_zve10_clip(file)
            if clip:
                clips["zve10"].append(clip)

        # Sort by clip number/time
        clips["fx30"].sort(key=lambda x: x.clip_name)
        clips["zve10"].sort(key=lambda x: x.clip_name)

        return clips

    @staticmethod
    def _parse_fx30_clip(file_path: Path) -> Optional[SonyClip]:
        """Parse FX30 clip metadata"""

        info = FFmpegProcessor.get_media_info(file_path)
        if not info:
            return None

        # Extract clip number from filename (C0001.MP4 -> 1)
        clip_name = file_path.stem
        clip_number = int(clip_name[1:]) if clip_name[1:].isdigit() else 0

        return SonyClip(
            file_path=file_path,
            camera="fx30",
            clip_name=clip_name,
            date_shot=datetime.fromtimestamp(file_path.stat().st_mtime),
            duration=info.get("duration_seconds", 0),
            resolution=info.get("resolution", "4096x2160"),
            framerate=info.get("fps", 29.97),
            color_profile="S-Log3",  # FX30 default
            file_size_gb=file_path.stat().st_size / (1024**3),
            take_number=clip_number
        )

    @staticmethod
    def _parse_zve10_clip(file_path: Path) -> Optional[SonyClip]:
        """Parse ZV-E10 clip metadata"""

        info = FFmpegProcessor.get_media_info(file_path)
        if not info:
            return None

        clip_name = file_path.stem

        return SonyClip(
            file_path=file_path,
            camera="zve10",
            clip_name=clip_name,
            date_shot=datetime.fromtimestamp(file_path.stat().st_mtime),
            duration=info.get("duration_seconds", 0),
            resolution=info.get("resolution", "3840x2160"),
            framerate=info.get("fps", 30),
            color_profile="Standard",  # or S-Log2 if set
            file_size_gb=file_path.stat().st_size / (1024**3)
        )

    @staticmethod
    def organize_by_camera(clips: Dict[str, List[SonyClip]], output_dir: Path):
        """Organize clips by camera into folders"""

        for camera, camera_clips in clips.items():
            if not camera_clips:
                continue

            camera_dir = output_dir / camera.upper()
            camera_dir.mkdir(parents=True, exist_ok=True)

            for clip in camera_clips:
                # Create date-based subfolder
                date_folder = clip.date_shot.strftime("%Y%m%d")
                date_dir = camera_dir / date_folder
                date_dir.mkdir(exist_ok=True)

                # Copy or link file
                dest = date_dir / clip.file_path.name
                if not dest.exists():
                    import shutil
                    shutil.copy2(clip.file_path, dest)

    @staticmethod
    def create_proxy_media(clip: SonyClip, proxy_dir: Path) -> Optional[Path]:
        """Create editing proxy for Sony footage"""

        proxy_dir.mkdir(parents=True, exist_ok=True)

        # Use ProRes 422 Proxy for Resolve
        proxy_path = proxy_dir / f"{clip.clip_name}_proxy.mov"

        cmd = [
            "ffmpeg", "-i", str(clip.file_path),
            "-vf", "scale=1920:-1",  # HD proxy
            "-c:v", "prores_ks",
            "-profile:v", "0",  # ProRes 422 Proxy
            "-c:a", "pcm_s16le",
            "-ar", "48000",
            "-y", str(proxy_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return proxy_path
        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def apply_slog3_to_rec709(input_file: Path, output_file: Path) -> ProcessResult:
        """Convert S-Log3 to Rec.709 for viewing"""

        # S-Log3 to Rec.709 conversion
        # This is a simplified version - proper conversion needs a LUT
        cmd = [
            "ffmpeg", "-i", str(input_file),
            "-vf", "lut3d=/mnt/nas/LUTs/Sony_Slog3_to_Rec709.cube",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-c:a", "copy",
            "-y", str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return ProcessResult(
                success=True,
                output_path=output_file,
                file_size_mb=output_file.stat().st_size / (1024**2)
            )
        except subprocess.CalledProcessError as e:
            return ProcessResult(
                success=False,
                error_message=str(e),
                suggestion="Check if LUT file exists at /mnt/nas/LUTs/"
            )

    @staticmethod
    def extract_fx30_metadata(file_path: Path) -> Dict:
        """Extract FX30 specific metadata from file"""

        # FX30 embeds extensive metadata
        cmd = [
            "exiftool", "-j", str(file_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            metadata = json.loads(result.stdout)[0] if result.stdout else {}

            # Extract FX30 specific fields
            fx30_data = {
                "camera_model": metadata.get("Model", "FX30"),
                "lens": metadata.get("LensModel", "Unknown"),
                "iso": metadata.get("ISO", ""),
                "shutter_speed": metadata.get("ShutterSpeed", ""),
                "aperture": metadata.get("FNumber", ""),
                "white_balance": metadata.get("WhiteBalance", ""),
                "picture_profile": metadata.get("PictureProfile", "PP11"),  # S-Log3
                "color_mode": metadata.get("ColorMode", "S-Gamut3.Cine"),
                "focus_mode": metadata.get("FocusMode", ""),
                "stabilization": metadata.get("SteadyShot", "")
            }

            return fx30_data
        except:
            return {}

    @staticmethod
    def generate_camera_report(clips: Dict[str, List[SonyClip]]) -> str:
        """Generate report of imported Sony media"""

        report = []
        report.append("=== Sony Camera Import Report ===\n")

        # FX30 clips
        if clips.get("fx30"):
            report.append(f"\n📹 Sony FX30: {len(clips['fx30'])} clips")
            total_duration = sum(c.duration for c in clips["fx30"])
            total_size = sum(c.file_size_gb for c in clips["fx30"])
            report.append(f"   Duration: {total_duration/60:.1f} minutes")
            report.append(f"   Size: {total_size:.1f} GB")
            report.append(f"   Resolution: 4K DCI (4096x2160)")
            report.append(f"   Color: S-Log3 / S-Gamut3.Cine")

        # ZV-E10 clips
        if clips.get("zve10"):
            report.append(f"\n📹 Sony ZV-E10: {len(clips['zve10'])} clips")
            total_duration = sum(c.duration for c in clips["zve10"])
            total_size = sum(c.file_size_gb for c in clips["zve10"])
            report.append(f"   Duration: {total_duration/60:.1f} minutes")
            report.append(f"   Size: {total_size:.1f} GB")
            report.append(f"   Resolution: 4K (3840x2160)")

        report.append("\n=== Recommended Workflow ===")
        report.append("1. Generate proxies for editing")
        report.append("2. Import to Resolve with S-Log3 color space")
        report.append("3. Apply Sony S-Log3 to Rec.709 LUT")
        report.append("4. Apply orange/teal grade")
        report.append("5. Export at YouTube 4K settings")

        return "\n".join(report)


class SonyToResolve:
    """Sony to DaVinci Resolve workflow"""

    @staticmethod
    def create_timeline_from_sony(clips: List[SonyClip], project_name: str) -> Path:
        """Create Resolve timeline from Sony clips"""

        # Create FCPXML for Resolve import
        root = ET.Element("fcpxml", version="1.9")

        # Add resources
        resources = ET.SubElement(root, "resources")

        # FX30 format (4K DCI)
        fx30_format = ET.SubElement(resources, "format", {
            "id": "fx30_4k",
            "name": "FX30 4K DCI",
            "frameDuration": "1001/30000s",
            "width": "4096",
            "height": "2160",
            "colorSpace": "S-Log3"
        })

        # Add clips to resources
        for i, clip in enumerate(clips):
            asset = ET.SubElement(resources, "asset", {
                "id": f"clip_{i}",
                "src": str(clip.file_path),
                "format": "fx30_4k" if clip.camera == "fx30" else "r1"
            })

        # Create project
        event = ET.SubElement(root, "event", {"name": project_name})
        project = ET.SubElement(event, "project", {"name": project_name})

        # Create sequence
        sequence = ET.SubElement(project, "sequence", {
            "format": "fx30_4k",
            "renderColorSpace": "DaVinci Wide Gamut"
        })

        spine = ET.SubElement(sequence, "spine")

        # Add clips to timeline
        current_time = 0
        for i, clip in enumerate(clips):
            clip_elem = ET.SubElement(spine, "asset-clip", {
                "ref": f"clip_{i}",
                "offset": f"{current_time}s",
                "duration": f"{clip.duration}s",
                "format": "fx30_4k" if clip.camera == "fx30" else "r1"
            })

            # Add color correction metadata
            if clip.camera == "fx30":
                ET.SubElement(clip_elem, "colorCorrection", {
                    "colorSpace": "S-Log3",
                    "targetSpace": "Rec.709"
                })

            current_time += clip.duration

        # Save XML
        output_path = Path(f"{project_name}_timeline.fcpxml")
        tree = ET.ElementTree(root)
        tree.write(str(output_path), encoding="UTF-8", xml_declaration=True)

        return output_path

    @staticmethod
    def apply_orange_teal_grade(video_path: Path, output_path: Path, intensity: float = 0.75) -> ProcessResult:
        """Apply orange/teal color grade"""
        config = get_config()
        # Default LUT path - users can configure in their config
        lut_dir = config.storage.nas / "LUTs" if config.storage.nas else Path.home() / "LUTs"
        lut_path = lut_dir / "orange_teal.cube"

        if not lut_path.exists():
            return ProcessResult(
                success=False,
                error_message=f"LUT not found: {lut_path}",
                suggestion="Check LUT path in my_config.py"
            )

        # Apply LUT with intensity control
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-vf", f"lut3d={lut_path}:interp=tetrahedral",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-c:a", "copy",
            "-y", str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return ProcessResult(
                success=True,
                output_path=output_path,
                file_size_mb=output_path.stat().st_size / (1024**2)
            )
        except subprocess.CalledProcessError as e:
            return ProcessResult(success=False, error_message=str(e))