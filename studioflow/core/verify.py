"""
File verification and integrity checking for StudioFlow
Simple, reliable, with auto-repair capabilities
"""

import hashlib
import shutil
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import subprocess


@dataclass
class VerificationResult:
    """Enhanced verification result with repair info"""
    valid: bool
    file_path: Path
    error: Optional[str] = None
    repaired: bool = False
    hash: Optional[str] = None
    size_bytes: int = 0


class FileVerifier:
    """Robust file verification with auto-repair"""

    @staticmethod
    def calculate_hash(file_path: Path) -> Optional[str]:
        """Calculate SHA256 hash of file"""
        if not file_path.exists():
            return None

        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return None

    @staticmethod
    def verify_media_file(file_path: Path, auto_repair: bool = True) -> Tuple[bool, Optional[str]]:
        """Verify media file with optional auto-repair"""

        if not file_path.exists():
            return False, "File does not exist"

        # Check file size
        size = file_path.stat().st_size
        if size == 0:
            return False, "Empty file"

        # Use ffprobe to verify
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1",
            str(file_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                if auto_repair:
                    # Try to repair
                    if FileVerifier._repair_media_file(file_path):
                        # Re-verify after repair
                        re_check = subprocess.run(cmd, capture_output=True, timeout=10)
                        if re_check.returncode == 0:
                            return True, "Repaired successfully"

                return False, "File appears corrupted"

            if "codec_type=" not in result.stdout:
                return False, "No valid streams found"

            return True, None

        except subprocess.TimeoutExpired:
            return False, "File verification timed out"
        except Exception as e:
            return False, f"Verification error: {str(e)}"

    @staticmethod
    def _repair_media_file(file_path: Path) -> bool:
        """Attempt to repair corrupted media file"""
        backup = file_path.with_suffix(file_path.suffix + ".backup")
        repaired = file_path.with_suffix(file_path.suffix + ".repaired")

        try:
            # Create backup
            shutil.copy2(file_path, backup)

            # Try to repair with FFmpeg (re-mux)
            cmd = [
                "ffmpeg",
                "-err_detect", "ignore_err",
                "-i", str(file_path),
                "-c", "copy",
                "-y", str(repaired)
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=60)

            if result.returncode == 0 and repaired.exists():
                # Replace original with repaired
                shutil.move(str(repaired), str(file_path))
                backup.unlink(missing_ok=True)
                return True

            # Cleanup on failure
            repaired.unlink(missing_ok=True)
            backup.unlink(missing_ok=True)
            return False

        except Exception:
            repaired.unlink(missing_ok=True)
            backup.unlink(missing_ok=True)
            return False

    @staticmethod
    def compare_files(file1: Path, file2: Path, quick: bool = False) -> bool:
        """Compare two files by hash"""
        if not file1.exists() or not file2.exists():
            return False

        # Quick check: file size
        if file1.stat().st_size != file2.stat().st_size:
            return False

        if quick:
            return True  # Size match is good enough

        # Deep check: hash
        hash1 = FileVerifier.calculate_hash(file1)
        hash2 = FileVerifier.calculate_hash(file2)
        return hash1 == hash2 and hash1 is not None

    @staticmethod
    def safe_copy(source: Path, destination: Path, verify: bool = True) -> VerificationResult:
        """Copy file with verification"""
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

            if verify and not FileVerifier.compare_files(source, destination):
                destination.unlink(missing_ok=True)
                return VerificationResult(
                    False, destination,
                    error="Copy verification failed"
                )

            return VerificationResult(
                True, destination,
                hash=FileVerifier.calculate_hash(destination),
                size_bytes=destination.stat().st_size
            )

        except Exception as e:
            destination.unlink(missing_ok=True)
            return VerificationResult(False, destination, error=str(e))

    @staticmethod
    def check_disk_space(path: Path, required_gb: float = 1.0) -> Tuple[bool, float]:
        """Check available disk space"""
        try:
            stats = shutil.disk_usage(path if path.is_dir() else path.parent)
            available_gb = stats.free / (1024 ** 3)
            return available_gb >= required_gb, available_gb
        except Exception:
            return False, 0.0

    @staticmethod
    def create_manifest(directory: Path) -> Dict[str, Any]:
        """Create integrity manifest for directory"""
        manifest = {
            "created": datetime.now().isoformat(),
            "directory": str(directory),
            "files": {}
        }

        media_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.mp3', '.wav', '.jpg', '.png'}

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in media_extensions:
                rel_path = str(file_path.relative_to(directory))
                manifest["files"][rel_path] = {
                    "hash": FileVerifier.calculate_hash(file_path),
                    "size": file_path.stat().st_size
                }

        manifest_path = directory / ".studioflow_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return manifest