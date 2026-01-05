"""
Robust FFmpeg processor with quality of life features
Handles errors gracefully, provides helpful feedback, and includes smart defaults
"""

import subprocess
import json
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Import GPU utils (lazy import to avoid circular dependencies)
try:
    from studioflow.core.gpu_utils import get_gpu_detector
except ImportError:
    # Fallback if gpu_utils not available
    def get_gpu_detector():
        class DummyGPU:
            def get_video_encoder(self):
                return ("libx264", "fast")
        return DummyGPU()


class VideoQuality(Enum):
    """Common quality presets for quick selection"""
    ULTRA = {"crf": "16", "preset": "slower"}  # Best quality, slow
    HIGH = {"crf": "18", "preset": "slow"}     # YouTube recommended
    MEDIUM = {"crf": "23", "preset": "medium"}  # Good balance
    LOW = {"crf": "28", "preset": "fast"}      # Fast, smaller files
    DRAFT = {"crf": "32", "preset": "ultrafast"} # Preview only


@dataclass
class ProcessResult:
    """Result from FFmpeg operation with helpful context"""
    success: bool
    output_path: Optional[Path] = None
    error_message: str = ""
    suggestion: str = ""
    duration: float = 0.0
    file_size_mb: float = 0.0


class FFmpegProcessor:
    """Robust video operations with error recovery and smart defaults"""

    @staticmethod
    def check_ffmpeg() -> bool:
        """Verify FFmpeg is installed and accessible"""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  FFmpeg not found. Install with: sudo apt install ffmpeg")
            return False

    @staticmethod
    def get_media_info(file_path: Path) -> Dict:
        """Get comprehensive media information with error handling"""
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-show_format",
            "-show_error",
            str(file_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)

            # Add convenience fields
            if "format" in info:
                info["duration_seconds"] = float(info["format"].get("duration", 0))
                info["size_mb"] = int(info["format"].get("size", 0)) / (1024 * 1024)
                info["bitrate_kbps"] = int(info["format"].get("bit_rate", 0)) / 1000

            # Extract video/audio stream info
            for stream in info.get("streams", []):
                if stream["codec_type"] == "video":
                    info["video_codec"] = stream.get("codec_name", "unknown")
                    info["resolution"] = f"{stream.get('width', 0)}x{stream.get('height', 0)}"
                    info["fps"] = eval(stream.get("r_frame_rate", "0/1"))
                elif stream["codec_type"] == "audio":
                    info["audio_codec"] = stream.get("codec_name", "unknown")
                    info["sample_rate"] = stream.get("sample_rate", 0)
                    info["channels"] = stream.get("channels", 0)

            return info
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            return {"error": str(e), "suggestion": "File may be corrupted. Try: ffmpeg -i file.mp4 -c copy fixed.mp4"}

    @staticmethod
    def cut_video(input_file: Path, output_file: Path,
                 start_time: float, duration: float,
                 reencode: bool = False) -> ProcessResult:
        """Cut a segment from video with smart keyframe handling"""
        start = time.time()

        if not input_file.exists():
            return ProcessResult(False, error_message=f"Input file not found: {input_file}")

        # Use fast seek for cutting (may be slightly inaccurate at boundaries)
        # For precise cuts, use reencode=True
        if reencode:
            # Use GPU acceleration if available
            gpu = get_gpu_detector()
            encoder, preset = gpu.get_video_encoder()
            
            cmd = [
                "ffmpeg", "-i", str(input_file),
                "-ss", str(start_time),
                "-t", str(duration),
                "-c:v", encoder,
            ]
            
            # GPU encoders use different preset syntax
            if encoder.startswith("h264_nvenc"):
                cmd.extend(["-preset", preset, "-cq", "23"])  # CQ = constant quality
            elif encoder.startswith("h264_amf"):
                cmd.extend(["-quality", preset, "-rc", "vbr_peak", "-qmin", "18", "-qmax", "28"])
            elif encoder.startswith("h264_qsv"):
                cmd.extend(["-preset", preset, "-global_quality", "23"])
            else:
                # CPU fallback
                cmd.extend(["-preset", preset, "-crf", "23"])
            
            cmd.extend(["-c:a", "aac", "-y", str(output_file)])
        else:
            # Fast copy mode - seeks to nearest keyframe
            cmd = [
                "ffmpeg",
                "-ss", str(start_time),  # Seek before input for speed
                "-i", str(input_file),
                "-t", str(duration),
                "-c", "copy",  # No re-encoding
                "-avoid_negative_ts", "make_zero",  # Fix timestamp issues
                "-y", str(output_file)
            ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Get output file info
            size_mb = output_file.stat().st_size / (1024 * 1024) if output_file.exists() else 0

            return ProcessResult(
                success=True,
                output_path=output_file,
                duration=time.time() - start,
                file_size_mb=size_mb
            )
        except subprocess.CalledProcessError as e:
            suggestion = "Try with reencode=True for precise cuts" if not reencode else "Check if timestamps are within video duration"
            return ProcessResult(
                success=False,
                error_message=e.stderr[:200] if e.stderr else str(e),
                suggestion=suggestion
            )

    @staticmethod
    def concat_videos(input_files: List[Path], output_file: Path,
                     reencode: bool = None) -> ProcessResult:
        """Concatenate videos with automatic format detection"""
        start = time.time()

        # Verify all inputs exist
        missing = [f for f in input_files if not f.exists()]
        if missing:
            return ProcessResult(
                success=False,
                error_message=f"Missing files: {', '.join(str(f) for f in missing)}"
            )

        # Auto-detect if re-encoding needed
        if reencode is None:
            # Check if all videos have same codec/resolution
            formats = []
            for f in input_files:
                info = FFmpegProcessor.get_media_info(f)
                formats.append({
                    "codec": info.get("video_codec"),
                    "resolution": info.get("resolution"),
                    "fps": info.get("fps")
                })

            # If formats differ, need re-encoding
            reencode = len(set(str(f) for f in formats)) > 1

        # Create concat list
        list_file = Path("/tmp") / f"concat_{output_file.stem}.txt"
        try:
            with open(list_file, 'w') as f:
                for file in input_files:
                    f.write(f"file '{file.absolute()}'\n")

            if reencode:
                # Re-encode for compatibility
                cmd = [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(list_file),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "192k",
                    "-y", str(output_file)
                ]
            else:
                # Fast copy mode
                cmd = [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(list_file),
                    "-c", "copy",
                    "-y", str(output_file)
                ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            list_file.unlink(missing_ok=True)

            size_mb = output_file.stat().st_size / (1024 * 1024) if output_file.exists() else 0

            return ProcessResult(
                success=True,
                output_path=output_file,
                duration=time.time() - start,
                file_size_mb=size_mb
            )

        except subprocess.CalledProcessError as e:
            list_file.unlink(missing_ok=True)
            return ProcessResult(
                success=False,
                error_message=e.stderr[:200] if e.stderr else str(e),
                suggestion="Videos may have incompatible formats. Try with reencode=True"
            )
        except Exception as e:
            list_file.unlink(missing_ok=True)
            return ProcessResult(success=False, error_message=str(e))

    @staticmethod
    def export_for_platform(input_file: Path, platform: str, output_file: Path,
                          quality: VideoQuality = VideoQuality.HIGH,
                          two_pass: bool = False) -> ProcessResult:
        """Export video optimized for platform with smart compression"""
        start = time.time()

        if not input_file.exists():
            return ProcessResult(False, error_message=f"Input file not found: {input_file}")

        # Enhanced platform presets with quality options
        presets = {
            "youtube": {
                "vcodec": "libx264",
                "preset": quality.value["preset"],
                "crf": quality.value["crf"],
                "acodec": "aac",
                "abitrate": "320k",
                "pix_fmt": "yuv420p",
                "movflags": "+faststart",
                "format": "mp4"
            },
            "instagram": {
                "vcodec": "libx264",
                "preset": "medium",
                "crf": "23",
                "acodec": "aac",
                "abitrate": "128k",
                "scale": "1080:1080",  # Square for feed
                "max_duration": 60,
                "max_size_mb": 100,
                "format": "mp4"
            },
            "instagram_reel": {
                "vcodec": "libx264",
                "preset": "medium",
                "crf": "23",
                "acodec": "aac",
                "abitrate": "128k",
                "scale": "1080:1920",  # 9:16 for reels
                "max_duration": 90,
                "format": "mp4"
            },
            "tiktok": {
                "vcodec": "libx264",
                "preset": "medium",
                "crf": "23",
                "acodec": "aac",
                "abitrate": "128k",
                "scale": "1080:1920",  # 9:16 vertical
                "max_duration": 180,
                "format": "mp4"
            },
            "twitter": {
                "vcodec": "libx264",
                "preset": "fast",
                "crf": "25",
                "acodec": "aac",
                "abitrate": "128k",
                "max_duration": 140,
                "max_size_mb": 512,
                "format": "mp4"
            }
        }

        if platform not in presets:
            return ProcessResult(
                False,
                error_message=f"Unknown platform: {platform}",
                suggestion=f"Available: {', '.join(presets.keys())}"
            )

        preset = presets[platform]

        # Build command
        cmd = ["ffmpeg", "-i", str(input_file)]

        # Video settings
        cmd.extend(["-c:v", preset["vcodec"]])

        if "preset" in preset:
            cmd.extend(["-preset", preset["preset"]])

        if "crf" in preset:
            cmd.extend(["-crf", preset["crf"]])
        elif "vbitrate" in preset:
            cmd.extend(["-b:v", preset["vbitrate"]])

        # Scale/crop for platform
        if "scale" in preset:
            cmd.extend(["-vf", f"scale={preset['scale']}:force_original_aspect_ratio=decrease,pad={preset['scale']}:(ow-iw)/2:(oh-ih)/2"])

        # Audio settings
        cmd.extend(["-c:a", preset["acodec"], "-b:a", preset["abitrate"]])

        # Platform-specific options
        if "pix_fmt" in preset:
            cmd.extend(["-pix_fmt", preset["pix_fmt"]])

        if "movflags" in preset:
            cmd.extend(["-movflags", preset["movflags"]])

        # Duration limit
        if "max_duration" in preset:
            cmd.extend(["-t", str(preset["max_duration"])])

        # Two-pass encoding for better quality/size ratio
        if two_pass and "crf" not in preset:
            # First pass
            cmd_pass1 = cmd + ["-pass", "1", "-f", "null", "/dev/null"]
            subprocess.run(cmd_pass1, capture_output=True, check=False)

            # Second pass
            cmd.extend(["-pass", "2"])

        cmd.extend(["-y", str(output_file)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Check size constraints
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)

                # Auto-compress if too large
                if "max_size_mb" in preset and size_mb > preset["max_size_mb"]:
                    compressed = FFmpegProcessor._smart_compress(
                        output_file, preset["max_size_mb"]
                    )
                    if compressed.success:
                        return compressed

                return ProcessResult(
                    success=True,
                    output_path=output_file,
                    duration=time.time() - start,
                    file_size_mb=size_mb
                )

        except subprocess.CalledProcessError as e:
            return ProcessResult(
                success=False,
                error_message=e.stderr[:200] if e.stderr else str(e),
                suggestion="Try with different quality setting or check input format"
            )

    @staticmethod
    def _smart_compress(file_path: Path, target_mb: float) -> ProcessResult:
        """Smart compression to reach target size"""
        current_size_mb = file_path.stat().st_size / (1024 * 1024)

        if current_size_mb <= target_mb:
            return ProcessResult(True, output_path=file_path, file_size_mb=current_size_mb)

        # Get video info for smart bitrate calculation
        info = FFmpegProcessor.get_media_info(file_path)
        duration = info.get('duration_seconds', 60)

        # Calculate target bitrate (leave 5% margin for audio/container)
        target_size_bits = target_mb * 1024 * 1024 * 8 * 0.95
        target_video_bitrate = int(target_size_bits / duration - 128000) / 1000  # kbps, minus audio

        temp_file = file_path.parent / f"{file_path.stem}_compressed.mp4"

        # Use 2-pass encoding for better quality at target size
        base_cmd = [
            "ffmpeg", "-i", str(file_path),
            "-c:v", "libx264",
            "-b:v", f"{target_video_bitrate}k",
            "-c:a", "aac", "-b:a", "128k"
        ]

        try:
            # Pass 1
            subprocess.run(
                base_cmd + ["-pass", "1", "-f", "null", "/dev/null"],
                capture_output=True, check=True
            )

            # Pass 2
            subprocess.run(
                base_cmd + ["-pass", "2", "-y", str(temp_file)],
                capture_output=True, check=True
            )

            # Replace original
            shutil.move(str(temp_file), str(file_path))

            new_size_mb = file_path.stat().st_size / (1024 * 1024)

            return ProcessResult(
                success=True,
                output_path=file_path,
                file_size_mb=new_size_mb
            )

        except subprocess.CalledProcessError as e:
            temp_file.unlink(missing_ok=True)
            return ProcessResult(
                success=False,
                error_message="Compression failed",
                suggestion=f"Target bitrate too low ({target_video_bitrate}k). Try reducing duration or quality."
            )

    @staticmethod
    def extract_audio(input_file: Path, output_file: Optional[Path] = None,
                     format: str = "wav") -> ProcessResult:
        """Extract audio with format detection"""
        if not input_file.exists():
            return ProcessResult(False, error_message=f"Input file not found: {input_file}")

        if output_file is None:
            output_file = input_file.with_suffix(f".{format}")

        # Format-specific settings
        if format == "wav":
            cmd = [
                "ffmpeg", "-i", str(input_file),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "48000",
                "-ac", "2",
                "-y", str(output_file)
            ]
        elif format == "mp3":
            cmd = [
                "ffmpeg", "-i", str(input_file),
                "-vn",
                "-acodec", "libmp3lame",
                "-ab", "320k",
                "-y", str(output_file)
            ]
        elif format == "aac":
            cmd = [
                "ffmpeg", "-i", str(input_file),
                "-vn",
                "-acodec", "aac",
                "-ab", "256k",
                "-y", str(output_file)
            ]
        else:
            return ProcessResult(
                False,
                error_message=f"Unsupported format: {format}",
                suggestion="Use 'wav', 'mp3', or 'aac'"
            )

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)
            return ProcessResult(True, output_path=output_file, file_size_mb=size_mb)
        except subprocess.CalledProcessError as e:
            return ProcessResult(False, error_message=str(e))

    @staticmethod
    def add_audio(video_file: Path, audio_file: Path, output_file: Path,
                 mix: bool = False, volume: float = 1.0) -> ProcessResult:
        """Add, replace, or mix audio in video"""
        if not video_file.exists() or not audio_file.exists():
            return ProcessResult(False, error_message="Input files not found")

        if mix:
            # Mix with existing audio
            filter_complex = f"[0:a][1:a]amix=inputs=2:duration=longest[aout]"
            cmd = [
                "ffmpeg",
                "-i", str(video_file),
                "-i", str(audio_file),
                "-filter_complex", filter_complex,
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-y", str(output_file)
            ]
        else:
            # Replace audio, with volume adjustment
            cmd = [
                "ffmpeg",
                "-i", str(video_file),
                "-i", str(audio_file),
                "-c:v", "copy",
                "-map", "0:v:0",
                "-map", "1:a:0"
            ]

            if volume != 1.0:
                cmd.extend(["-af", f"volume={volume}"])

            cmd.extend(["-c:a", "aac", "-y", str(output_file)])

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return ProcessResult(True, output_path=output_file)
        except subprocess.CalledProcessError as e:
            return ProcessResult(
                False,
                error_message=str(e),
                suggestion="Check if audio/video durations match"
            )

    @staticmethod
    def generate_thumbnail(video_file: Path, output_file: Optional[Path] = None,
                         timestamp: float = None, best_frame: bool = False) -> ProcessResult:
        """Generate thumbnail with smart frame selection"""
        if not video_file.exists():
            return ProcessResult(False, error_message=f"Video file not found: {video_file}")

        if output_file is None:
            output_file = video_file.with_suffix(".jpg")

        # Auto-select timestamp if not provided
        if timestamp is None:
            info = FFmpegProcessor.get_media_info(video_file)
            duration = info.get('duration_seconds', 10)
            # Use 10% into the video as default
            timestamp = min(duration * 0.1, 5.0)

        if best_frame:
            # Use scene detection to find best frame
            cmd = [
                "ffmpeg", "-i", str(video_file),
                "-vf", f"select='gte(scene,0.4)',scale=1920:-1",
                "-frames:v", "1",
                "-y", str(output_file)
            ]
        else:
            # Extract specific frame
            cmd = [
                "ffmpeg", "-i", str(video_file),
                "-ss", str(timestamp),
                "-vframes", "1",
                "-vf", "scale=1920:-1",  # HD width, maintain aspect
                "-q:v", "2",  # High quality JPEG
                "-y", str(output_file)
            ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)
            return ProcessResult(True, output_path=output_file, file_size_mb=size_mb)
        except subprocess.CalledProcessError as e:
            return ProcessResult(False, error_message=str(e))

    @staticmethod
    def create_video_from_image(image_file: Path, duration: float,
                              output_file: Path, audio_file: Optional[Path] = None,
                              zoom_pan: bool = False) -> ProcessResult:
        """Create video from image with optional Ken Burns effect"""
        if not image_file.exists():
            return ProcessResult(False, error_message=f"Image file not found: {image_file}")

        cmd = ["ffmpeg"]

        # Add audio input if provided
        if audio_file and audio_file.exists():
            cmd.extend(["-i", str(audio_file)])

        # Image input with duration
        if zoom_pan:
            # Ken Burns effect - slow zoom and pan
            filter = (
                f"scale=8000:-1,"
                f"zoompan=z='min(zoom+0.0015,1.5)':d={int(duration*25)}:s=1920x1080"
            )
            cmd.extend([
                "-loop", "1",
                "-i", str(image_file),
                "-vf", filter,
                "-t", str(duration)
            ])
        else:
            # Static image
            cmd.extend([
                "-loop", "1",
                "-framerate", "25",
                "-i", str(image_file),
                "-t", str(duration),
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
            ])

        # Output settings
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p"
        ])

        if audio_file:
            cmd.extend(["-c:a", "aac", "-shortest"])  # Match shortest input

        cmd.extend(["-y", str(output_file)])

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)
            return ProcessResult(True, output_path=output_file, file_size_mb=size_mb)
        except subprocess.CalledProcessError as e:
            return ProcessResult(False, error_message=str(e))

    # Productivity methods

    @staticmethod
    def batch_process(files: List[Path], operation: str, **kwargs) -> List[ProcessResult]:
        """Process multiple files with same operation"""
        results = []
        for i, file in enumerate(files, 1):
            print(f"Processing {i}/{len(files)}: {file.name}")

            output_suffix = kwargs.pop('output_suffix', f'_{operation}')
            output = file.parent / f"{file.stem}{output_suffix}{file.suffix}"

            if operation == "cut":
                result = FFmpegProcessor.cut_video(file, output, **kwargs)
            elif operation == "export":
                result = FFmpegProcessor.export_for_platform(file, output_file=output, **kwargs)
            elif operation == "thumbnail":
                result = FFmpegProcessor.generate_thumbnail(file, **kwargs)
            else:
                result = ProcessResult(False, error_message=f"Unknown operation: {operation}")

            results.append(result)

            if result.success:
                print(f"  ✓ {result.output_path}")
            else:
                print(f"  ✗ {result.error_message}")

        return results

    @staticmethod
    def auto_cut_silence(input_file: Path, output_file: Path,
                         threshold: float = -30.0, min_silence: float = 0.5) -> ProcessResult:
        """Remove silence from video automatically"""
        if not input_file.exists():
            return ProcessResult(False, error_message=f"Input file not found: {input_file}")

        # Detect silence periods
        detect_cmd = [
            "ffmpeg", "-i", str(input_file),
            "-af", f"silencedetect=n={threshold}dB:d={min_silence}",
            "-f", "null", "-"
        ]

        try:
            result = subprocess.run(detect_cmd, capture_output=True, text=True, check=True)

            # Parse silence detection output
            import re
            silence_pattern = r"silence_start: ([\d.]+).*?silence_end: ([\d.]+)"
            silences = re.findall(silence_pattern, result.stderr)

            if not silences:
                # No silence detected, just copy
                shutil.copy2(input_file, output_file)
                return ProcessResult(True, output_path=output_file)

            # Build complex filter to remove silence
            # This is simplified - real implementation would build segment list
            cmd = [
                "ffmpeg", "-i", str(input_file),
                "-af", f"silenceremove=stop_periods=-1:stop_duration={min_silence}:stop_threshold={threshold}dB",
                "-y", str(output_file)
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)

            return ProcessResult(True, output_path=output_file, file_size_mb=size_mb)

        except subprocess.CalledProcessError as e:
            return ProcessResult(False, error_message=str(e))

    @staticmethod
    def normalize_audio(input_file: Path, output_file: Optional[Path] = None,
                       target_lufs: float = -14.0) -> ProcessResult:
        """Normalize audio to YouTube standard (-14 LUFS) or custom target
        
        Args:
            input_file: Input video file
            output_file: Output file (defaults to {input}_normalized.{ext})
            target_lufs: Target LUFS level (default -14.0 for YouTube)
        """
        if not input_file.exists():
            return ProcessResult(False, error_message=f"Input file not found: {input_file}")

        if output_file is None:
            output_file = input_file.parent / f"{input_file.stem}_normalized{input_file.suffix}"

        # First pass - analyze audio
        analyze_cmd = [
            "ffmpeg", "-i", str(input_file),
            "-af", f"loudnorm=I={target_lufs}:print_format=json",
            "-f", "null", "-"
        ]

        try:
            result = subprocess.run(analyze_cmd, capture_output=True, text=True, check=True)

            # Extract loudnorm stats from stderr
            import re
            json_match = re.search(r'\{[^}]+\}', result.stderr[::-1])  # Search from end
            if json_match:
                stats = json.loads(json_match.group()[::-1])

                # Second pass - apply normalization
                filter = (
                    f"loudnorm=I={target_lufs}:"
                    f"measured_I={stats.get('input_i', -70)}:"
                    f"measured_TP={stats.get('input_tp', -10)}:"
                    f"measured_LRA={stats.get('input_lra', 7)}:"
                    f"measured_thresh={stats.get('input_thresh', -80)}"
                )
            else:
                # Fallback to simple normalization
                filter = f"loudnorm=I={target_lufs}"

            # Apply normalization
            cmd = [
                "ffmpeg", "-i", str(input_file),
                "-af", filter,
                "-c:v", "copy",  # Keep video unchanged
                "-y", str(output_file)
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)

            return ProcessResult(True, output_path=output_file, file_size_mb=size_mb)

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            return ProcessResult(
                False,
                error_message=str(e),
                suggestion="Try simple volume adjustment instead"
            )

    @staticmethod
    def quick_preview(input_file: Path, duration: float = 30,
                     scale: int = 480) -> ProcessResult:
        """Create a quick low-res preview for fast review"""
        if not input_file.exists():
            return ProcessResult(False, error_message=f"Input file not found: {input_file}")

        output_file = input_file.parent / f"{input_file.stem}_preview.mp4"

        # Get middle portion of video
        info = FFmpegProcessor.get_media_info(input_file)
        total_duration = info.get('duration_seconds', duration)
        start = max(0, (total_duration - duration) / 2)

        cmd = [
            "ffmpeg",
            "-ss", str(start),
            "-i", str(input_file),
            "-t", str(duration),
            "-vf", f"scale={scale}:-1",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-c:a", "aac", "-b:a", "96k",
            "-y", str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)
            return ProcessResult(
                True,
                output_path=output_file,
                file_size_mb=size_mb
            )
        except subprocess.CalledProcessError as e:
            return ProcessResult(False, error_message=str(e))

    @staticmethod
    def smart_trim(input_file: Path, output_file: Path,
                  fade_duration: float = 0.5) -> ProcessResult:
        """Trim black frames from start/end with fade"""
        if not input_file.exists():
            return ProcessResult(False, error_message=f"Input file not found: {input_file}")

        # Detect black frames
        detect_cmd = [
            "ffmpeg", "-i", str(input_file),
            "-vf", "blackdetect=d=0.1:pix_th=0.1",
            "-f", "null", "-"
        ]

        try:
            result = subprocess.run(detect_cmd, capture_output=True, text=True, check=True)

            # Parse black frame detection
            import re
            black_pattern = r"black_start:([\d.]+) black_end:([\d.]+)"
            blacks = re.findall(black_pattern, result.stderr)

            # Get video duration
            info = FFmpegProcessor.get_media_info(input_file)
            duration = info.get('duration_seconds', 0)

            # Find trim points
            start = 0
            end = duration

            if blacks:
                # Skip black at start
                for b_start, b_end in blacks:
                    if float(b_start) == 0:
                        start = float(b_end)
                        break

                # Skip black at end
                for b_start, b_end in reversed(blacks):
                    if float(b_end) >= duration - 0.5:
                        end = float(b_start)
                        break

            # Apply trim with fades
            trim_duration = end - start
            cmd = [
                "ffmpeg",
                "-ss", str(start),
                "-i", str(input_file),
                "-t", str(trim_duration),
                "-vf", f"fade=in:0:d={fade_duration},fade=out:st={trim_duration-fade_duration}:d={fade_duration}",
                "-af", f"afade=in:st=0:d={fade_duration},afade=out:st={trim_duration-fade_duration}:d={fade_duration}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                "-c:a", "aac",
                "-y", str(output_file)
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            size_mb = output_file.stat().st_size / (1024 * 1024)

            return ProcessResult(
                True,
                output_path=output_file,
                file_size_mb=size_mb
            )

        except subprocess.CalledProcessError as e:
            return ProcessResult(False, error_message=str(e))