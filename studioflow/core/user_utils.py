"""
User-focused utilities for StudioFlow
Practical features for daily use
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import subprocess


@dataclass
class ProjectStatus:
    """Current project and work status"""
    current_project: Optional[Path] = None
    recent_files: List[Dict[str, Any]] = field(default_factory=list)
    active_processes: List[str] = field(default_factory=list)
    disk_usage: Dict[str, float] = field(default_factory=dict)
    last_commands: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """Media quality check results"""
    file_path: Path
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    can_autofix: bool = False


class UserUtils:
    """User-centric utilities"""

    CONFIG_FILE = Path.home() / ".studioflow" / "user_config.json"
    HISTORY_FILE = Path.home() / ".studioflow" / "history.json"
    SNAPSHOTS_DIR = Path.home() / ".studioflow" / "snapshots"

    @classmethod
    def init_user_data(cls):
        """Initialize user data directories"""
        cls.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        cls.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize config if not exists
        if not cls.CONFIG_FILE.exists():
            default_config = {
                "defaults": {
                    "platform": "youtube",
                    "audio_lufs": -16,
                    "video_quality": "high",
                    "auto_normalize": True,
                    "auto_backup": True
                },
                "preferences": {},
                "learned_patterns": {}
            }
            cls.CONFIG_FILE.write_text(json.dumps(default_config, indent=2))

    @classmethod
    def get_status(cls) -> ProjectStatus:
        """Get current work status"""
        from .simple_templates import find_project_root

        status = ProjectStatus()

        # Find current project
        status.current_project = find_project_root()

        # Get recent files (last 24 hours)
        if status.current_project:
            media_dir = status.current_project / "01_MEDIA"
            if media_dir.exists():
                cutoff = datetime.now() - timedelta(hours=24)
                for file in media_dir.rglob("*.mp4"):
                    if file.stat().st_mtime > cutoff.timestamp():
                        status.recent_files.append({
                            "path": str(file),
                            "modified": datetime.fromtimestamp(file.stat().st_mtime),
                            "size_mb": file.stat().st_size / (1024 * 1024)
                        })

        # Check disk space
        if status.current_project:
            disk = shutil.disk_usage(status.current_project)
            status.disk_usage = {
                "free_gb": disk.free / (1024**3),
                "used_gb": disk.used / (1024**3),
                "total_gb": disk.total / (1024**3),
                "percent_used": (disk.used / disk.total) * 100
            }

        # Get last commands from history
        if cls.HISTORY_FILE.exists():
            history = json.loads(cls.HISTORY_FILE.read_text())
            status.last_commands = history.get("commands", [])[-5:]

        return status

    @classmethod
    def snapshot(cls, file_path: Path, label: str = None) -> Path:
        """Create snapshot before destructive operation"""
        if not label:
            label = datetime.now().strftime("%Y%m%d_%H%M%S")

        snapshot_dir = cls.SNAPSHOTS_DIR / file_path.stem / label
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        snapshot_path = snapshot_dir / file_path.name
        shutil.copy2(file_path, snapshot_path)

        # Save metadata
        meta = {
            "original": str(file_path),
            "snapshot": str(snapshot_path),
            "created": datetime.now().isoformat(),
            "label": label
        }
        (snapshot_dir / "metadata.json").write_text(json.dumps(meta, indent=2))

        return snapshot_path

    @classmethod
    def undo(cls, file_path: Path) -> bool:
        """Restore last snapshot"""
        snapshot_dir = cls.SNAPSHOTS_DIR / file_path.stem
        if not snapshot_dir.exists():
            return False

        # Find most recent snapshot
        snapshots = sorted(snapshot_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)

        for snapshot in snapshots:
            if snapshot.is_dir():
                snapshot_file = snapshot / file_path.name
                if snapshot_file.exists():
                    shutil.copy2(snapshot_file, file_path)
                    return True

        return False

    @classmethod
    def quick_preview(cls, file_path: Path, effect: str = None, duration: float = 5.0) -> Path:
        """Generate quick preview"""
        from .ffmpeg import FFmpegProcessor

        preview_path = Path("/tmp") / f"{file_path.stem}_preview.mp4"

        # Get middle 5 seconds
        info = FFmpegProcessor.get_media_info(file_path)
        total_duration = info.get('duration_seconds', 10)
        start = max(0, (total_duration - duration) / 2)

        # Cut preview segment
        result = FFmpegProcessor.cut_video(file_path, preview_path, start, duration)

        if result.success and effect:
            # Apply effect to preview
            from .simple_effects import SimpleEffects
            effect_preview = Path("/tmp") / f"{file_path.stem}_preview_{effect}.mp4"
            effect_result = SimpleEffects.apply_effect(preview_path, effect, effect_preview)
            if effect_result.success:
                return effect_preview

        return preview_path if result.success else None

    @classmethod
    def check_quality(cls, file_path: Path) -> QualityReport:
        """Check media quality and find issues"""
        from .ffmpeg import FFmpegProcessor

        report = QualityReport(file_path=file_path)

        # Get media info
        info = FFmpegProcessor.get_media_info(file_path)

        if "error" in info:
            report.issues.append(f"File error: {info['error']}")
            return report

        # Check video quality
        resolution = info.get("resolution", "0x0")
        width = int(resolution.split("x")[0])
        height = int(resolution.split("x")[1]) if "x" in resolution else 0

        if width < 1920:
            report.warnings.append(f"Low resolution: {resolution} (recommend 1920x1080+)")

        # Check audio levels
        # Run a quick loudness scan
        try:
            cmd = [
                "ffmpeg", "-i", str(file_path),
                "-af", "loudnorm=print_format=json",
                "-f", "null", "-"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            # Parse loudness from stderr (simplified)
            if "input_i" in result.stderr:
                # Extract LUFS value (this is simplified)
                import re
                match = re.search(r'"input_i"\s*:\s*"(-?\d+\.?\d*)"', result.stderr)
                if match:
                    lufs = float(match.group(1))
                    if lufs < -20:
                        report.warnings.append(f"Audio too quiet: {lufs:.1f} LUFS (recommend -16)")
                        report.suggestions.append("Run 'sf fix quiet' to normalize audio")
                        report.can_autofix = True
                    elif lufs > -14:
                        report.warnings.append(f"Audio too loud: {lufs:.1f} LUFS")
        except:
            pass

        # Check for black frames at start/end
        duration = info.get('duration_seconds', 0)
        if duration > 0:
            # Simplified black detection
            cmd = [
                "ffmpeg", "-i", str(file_path),
                "-t", "2",  # Check first 2 seconds
                "-vf", "blackdetect=d=0.1:pix_th=0.1",
                "-f", "null", "-"
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if "black_start:0" in result.stderr:
                    report.warnings.append("Black frames at start")
                    report.suggestions.append("Run 'sf fix black' to auto-trim")
                    report.can_autofix = True
            except:
                pass

        # Check bitrate
        bitrate_kbps = info.get('bitrate_kbps', 0)
        if bitrate_kbps > 50000:
            report.warnings.append(f"Very high bitrate: {bitrate_kbps:.0f} kbps")
            report.suggestions.append("Consider re-encoding for streaming")

        # Check format compatibility
        video_codec = info.get('video_codec', '')
        if video_codec not in ['h264', 'hevc']:
            report.warnings.append(f"Codec may have compatibility issues: {video_codec}")
            report.suggestions.append("Convert to H.264 for maximum compatibility")

        return report

    @classmethod
    def smart_fix(cls, file_path: Path, issue: str) -> Path:
        """Fix common issues automatically"""
        from .ffmpeg import FFmpegProcessor
        from .simple_effects import SimpleEffects

        output = file_path.parent / f"{file_path.stem}_fixed{file_path.suffix}"

        # Create snapshot first
        cls.snapshot(file_path, f"before_fix_{issue}")

        if issue == "quiet" or issue == "audio":
            # Fix quiet audio
            result = FFmpegProcessor.normalize_audio(file_path, output)
            return output if result.success else None

        elif issue == "dark":
            # Fix dark video
            result = SimpleEffects.apply_effect(
                file_path, "brightness", output,
                {"value": 0.2}
            )
            return output if result.success else None

        elif issue == "shaky":
            # Stabilize video
            result = SimpleEffects.apply_effect(
                file_path, "stabilize", output
            )
            return output if result.success else None

        elif issue == "black":
            # Trim black frames
            result = FFmpegProcessor.smart_trim(file_path, output)
            return output if result.success else None

        return None

    @classmethod
    def learn_pattern(cls, action: str, params: Dict):
        """Learn user patterns for smart defaults"""
        cls.init_user_data()

        config = json.loads(cls.CONFIG_FILE.read_text())

        if "learned_patterns" not in config:
            config["learned_patterns"] = {}

        # Track action frequency
        pattern_key = f"{action}_{json.dumps(params, sort_keys=True)}"
        if pattern_key not in config["learned_patterns"]:
            config["learned_patterns"][pattern_key] = {"count": 0, "last_used": None}

        config["learned_patterns"][pattern_key]["count"] += 1
        config["learned_patterns"][pattern_key]["last_used"] = datetime.now().isoformat()

        # Update defaults if pattern is frequent
        if config["learned_patterns"][pattern_key]["count"] > 3:
            if action == "export" and "platform" in params:
                config["defaults"]["platform"] = params["platform"]
            elif action == "audio" and "lufs" in params:
                config["defaults"]["audio_lufs"] = params["lufs"]

        cls.CONFIG_FILE.write_text(json.dumps(config, indent=2))

    @classmethod
    def get_smart_defaults(cls) -> Dict:
        """Get learned defaults"""
        cls.init_user_data()
        config = json.loads(cls.CONFIG_FILE.read_text())
        return config.get("defaults", {})

    @classmethod
    def add_to_history(cls, command: str):
        """Track command history"""
        cls.init_user_data()

        history = {"commands": [], "timestamps": []}
        if cls.HISTORY_FILE.exists():
            history = json.loads(cls.HISTORY_FILE.read_text())

        history["commands"].append(command)
        history["timestamps"].append(datetime.now().isoformat())

        # Keep last 100 commands
        history["commands"] = history["commands"][-100:]
        history["timestamps"] = history["timestamps"][-100:]

        cls.HISTORY_FILE.write_text(json.dumps(history, indent=2))

    @classmethod
    def estimate_time(cls, file_path: Path, operation: str) -> str:
        """Estimate processing time"""
        from .ffmpeg import FFmpegProcessor

        info = FFmpegProcessor.get_media_info(file_path)
        duration = info.get('duration_seconds', 60)
        size_mb = file_path.stat().st_size / (1024 * 1024)

        # Simple estimates based on experience
        estimates = {
            "export": duration * 0.5,  # Usually faster than realtime
            "effect": duration * 0.3,
            "upload": size_mb * 2,  # 2 seconds per MB
            "transcribe": duration * 0.2,
            "normalize": duration * 0.1
        }

        seconds = estimates.get(operation, duration)

        if seconds < 60:
            return f"{seconds:.0f} seconds"
        elif seconds < 3600:
            return f"{seconds/60:.1f} minutes"
        else:
            return f"{seconds/3600:.1f} hours"

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Sanitize filename: remove spaces, parentheses, special chars
        
        Args:
            name: Original filename
            
        Returns:
            Sanitized filename with underscores instead of spaces,
            special characters removed, and multiple underscores collapsed
        """
        import re
        stem = Path(name).stem
        suffix = Path(name).suffix
        stem = stem.replace(' ', '_')
        stem = re.sub(r'[\(\)\[\]\{\}]', '_', stem)
        stem = re.sub(r'_+', '_', stem)
        stem = stem.strip('_')
        return f"{stem}{suffix}"