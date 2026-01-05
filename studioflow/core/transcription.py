"""
Transcription module - Whisper AI integration
Ported from sf-audio for accurate video/audio transcription
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class TranscriptionService:
    """Whisper AI transcription with multi-format output"""
    
    # Class-level model cache to avoid reloading models
    _model_cache = {}

    def __init__(self):
        self.whisper_available = self._check_whisper()

    def _check_whisper(self) -> bool:
        """Check if Whisper is installed"""
        try:
            import whisper
            return True
        except ImportError:
            return False

    def transcribe(self,
                   audio_path: Path,
                   model: str = "base",
                   language: str = "auto",
                   output_formats: List[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio/video using Whisper AI

        Args:
            audio_path: Path to audio/video file
            model: Whisper model size (tiny, base, small, medium, large)
            language: Language code or "auto" for detection
            output_formats: List of formats to generate (srt, vtt, txt, json)

        Returns:
            Dict with transcription results and file paths
        """
        if not self.whisper_available:
            # Fall back to whisper CLI if available
            return self._transcribe_cli(audio_path, model, language, output_formats)

        try:
            import whisper
            from studioflow.core.gpu_utils import get_gpu_detector

            # Get device (GPU if available)
            gpu = get_gpu_detector()
            device = gpu.get_whisper_device()
            
            # Use cached model if available (saves memory and load time)
            cache_key = (model, device)
            if cache_key not in self._model_cache:
                model_obj = whisper.load_model(model, device=device)
                self._model_cache[cache_key] = model_obj
            else:
                model_obj = self._model_cache[cache_key]

            # Transcribe
            # Enable word_timestamps if JSON output is requested (needed for audio markers)
            word_timestamps = "json" in output_formats if output_formats else False
            options = {
                "language": None if language == "auto" else language,
                "task": "transcribe",
                "verbose": False,
                "fp16": device == "cuda",  # Use FP16 on GPU for speed, FP32 on CPU for accuracy
                "word_timestamps": word_timestamps
            }

            result = model_obj.transcribe(str(audio_path), **options)

            # Generate output files
            output_dir = audio_path.parent
            output_base = audio_path.stem
            output_formats = output_formats or ["srt", "vtt", "txt", "json"]

            output_files = {}

            if "txt" in output_formats:
                txt_file = output_dir / f"{output_base}.txt"
                txt_file.write_text(result["text"].strip())
                output_files["txt"] = txt_file

            if "srt" in output_formats:
                srt_file = output_dir / f"{output_base}.srt"
                self._write_srt(srt_file, result["segments"])
                output_files["srt"] = srt_file

            if "vtt" in output_formats:
                vtt_file = output_dir / f"{output_base}.vtt"
                self._write_vtt(vtt_file, result["segments"])
                output_files["vtt"] = vtt_file

            if "json" in output_formats:
                json_file = output_dir / f"{output_base}_transcript.json"
                # Flatten words from segments for audio marker detection
                all_words = []
                for seg in result.get("segments", []):
                    words = seg.get("words", [])
                    # Ensure words have required fields
                    for word in words:
                        if isinstance(word, dict) and "word" in word:
                            all_words.append({
                                "word": word["word"].strip(),
                                "start": word.get("start", seg["start"]),
                                "end": word.get("end", seg["end"])
                            })
                
                json_data = {
                    "text": result["text"].strip(),
                    "language": result.get("language", "unknown"),
                    "duration": result["segments"][-1]["end"] if result["segments"] else 0,
                    "words": all_words,  # Flattened word list for marker detection
                    "segments": [
                        {
                            "id": i,
                            "start": seg["start"],
                            "end": seg["end"],
                            "text": seg["text"].strip(),
                            "words": seg.get("words", [])
                        }
                        for i, seg in enumerate(result["segments"])
                    ]
                }
                with open(json_file, "w") as f:
                    json.dump(json_data, f, indent=2)
                output_files["json"] = json_file

            return {
                "success": True,
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "duration": result["segments"][-1]["end"] if result["segments"] else 0,
                "segments": len(result["segments"]),
                "output_files": output_files
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _transcribe_cli(self, audio_path: Path, model: str, language: str, output_formats: List[str]) -> Dict[str, Any]:
        """Fallback to whisper CLI if Python module not available"""
        try:
            output_dir = audio_path.parent

            # Build whisper command
            cmd = [
                "whisper",
                str(audio_path),
                "--model", model,
                "--output_dir", str(output_dir),
                "--output_format", "all"  # Generate all formats
            ]

            if language != "auto":
                cmd.extend(["--language", language])

            # Run whisper
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Whisper CLI failed: {result.stderr}"
                }

            # Find generated files
            output_base = audio_path.stem
            output_files = {}

            for fmt in ["txt", "srt", "vtt", "json"]:
                file_path = output_dir / f"{output_base}.{fmt}"
                if file_path.exists():
                    output_files[fmt] = file_path

            # Read text content
            txt_file = output_files.get("txt")
            text = txt_file.read_text() if txt_file else ""

            return {
                "success": True,
                "text": text,
                "output_files": output_files,
                "method": "cli"
            }

        except FileNotFoundError:
            return {
                "success": False,
                "error": "Whisper is not installed. Install with: pip install openai-whisper"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp for SRT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _format_timestamp_vtt(self, seconds: float) -> str:
        """Format timestamp for WebVTT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    def _write_srt(self, file_path: Path, segments: List[Dict[str, Any]]):
        """Write SRT subtitle file"""
        with open(file_path, "w") as f:
            for i, segment in enumerate(segments, 1):
                start = self._format_timestamp(segment["start"])
                end = self._format_timestamp(segment["end"])
                text = segment["text"].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    def _write_vtt(self, file_path: Path, segments: List[Dict[str, Any]]):
        """Write WebVTT subtitle file"""
        with open(file_path, "w") as f:
            f.write("WEBVTT\n\n")
            for segment in segments:
                start = self._format_timestamp_vtt(segment["start"])
                end = self._format_timestamp_vtt(segment["end"])
                text = segment["text"].strip()
                f.write(f"{start} --> {end}\n{text}\n\n")

    def extract_chapters(self, transcript_path: Path, min_duration: int = 30) -> List[Dict[str, Any]]:
        """
        Extract YouTube chapters from transcript

        Args:
            transcript_path: Path to JSON transcript
            min_duration: Minimum chapter duration in seconds

        Returns:
            List of chapter timestamps and titles
        """
        try:
            with open(transcript_path) as f:
                data = json.load(f)

            segments = data.get("segments", [])
            chapters = []
            current_chapter = None

            for segment in segments:
                # Simple chapter detection based on pauses or topic changes
                # This is a basic implementation - can be improved with NLP
                text = segment["text"].strip()

                if not current_chapter:
                    current_chapter = {
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": text[:50]  # First 50 chars as title
                    }
                elif segment["start"] - current_chapter["end"] > 2:  # 2 second pause
                    if current_chapter["end"] - current_chapter["start"] >= min_duration:
                        chapters.append(current_chapter)
                    current_chapter = {
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": text[:50]
                    }
                else:
                    current_chapter["end"] = segment["end"]

            if current_chapter and current_chapter["end"] - current_chapter["start"] >= min_duration:
                chapters.append(current_chapter)

            # Format for YouTube
            formatted_chapters = []
            for chapter in chapters:
                timestamp = self._format_youtube_timestamp(chapter["start"])
                formatted_chapters.append({
                    "timestamp": timestamp,
                    "title": chapter["text"],
                    "start_seconds": chapter["start"]
                })

            return formatted_chapters

        except Exception as e:
            return []

    def _format_youtube_timestamp(self, seconds: float) -> str:
        """Format timestamp for YouTube chapters (MM:SS or HH:MM:SS)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    def _generate_srt_content(self, result: Dict[str, Any]) -> str:
        """Generate SRT content from transcription result"""
        segments = result.get("segments", [])
        if not segments:
            return ""

        srt_lines = []
        for i, segment in enumerate(segments, 1):
            start = self._format_timestamp(segment.get("start", 0))
            end = self._format_timestamp(segment.get("end", 0))
            text = segment.get("text", "").strip()
            srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")

        return "\n".join(srt_lines)