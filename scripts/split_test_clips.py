#!/usr/bin/env python3
"""
Split test footage into individual clips based on markers
Processes files according to TEST_FIXTURES_PRIORITY_CLIPS.md specifications
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Add studioflow to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from studioflow.core.ffmpeg import FFmpegProcessor
from studioflow.core.transcription import TranscriptionService
from studioflow.core.audio_markers import AudioMarkerDetector
from studioflow.core.rough_cut_markers import detect_markers_in_clips
from studioflow.core.marker_commands import MarkerCommandParser
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


@dataclass
class ClipSegment:
    """Segment to extract from clip"""
    start_time: float
    end_time: float
    name: str
    marker_type: str
    commands: Dict


class TestClipSplitter:
    """Split test footage into individual clips based on markers"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.transcription_service = TranscriptionService()
        self.marker_detector = AudioMarkerDetector()
        self.command_parser = MarkerCommandParser()
    
    def process_file(self, video_file: Path) -> List[Path]:
        """
        Process a video file and split into clips based on markers
        
        Returns:
            List of output clip paths
        """
        console.print(f"\n[cyan]Processing: {video_file.name}[/cyan]")
        
        # Step 1: Transcribe
        console.print("[yellow]Step 1: Transcribing...[/yellow]")
        transcript_path = self._transcribe(video_file)
        if not transcript_path:
            console.print("[red]Failed to transcribe[/red]")
            return []
        
        # Step 2: Detect markers
        console.print("[yellow]Step 2: Detecting markers...[/yellow]")
        segments = self._detect_markers(video_file, transcript_path)
        if not segments:
            console.print("[yellow]No markers found - extracting as single full clip[/yellow]")
            # Extract entire clip
            info = FFmpegProcessor.get_media_info(video_file)
            duration = info.get("duration_seconds", 0)
            # Use MOV for better PCM audio compatibility
            output_file = self.output_dir / f"{video_file.stem}_full.mov"
            result = FFmpegProcessor.cut_video(
                video_file,
                output_file,
                start_time=0.0,
                duration=duration,
                reencode=True  # Re-encode for consistency
            )
            if result and result.success:
                return [output_file]
            return []
        
        # Step 3: Extract segments
        console.print(f"[yellow]Step 3: Extracting {len(segments)} segments...[/yellow]")
        output_files = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Extracting segments...", total=len(segments))
            
            for i, segment in enumerate(segments, 1):
                output_file = self._extract_segment(video_file, segment, i)
                if output_file:
                    output_files.append(output_file)
                progress.update(task, advance=1)
        
        return output_files
    
    def _transcribe(self, video_file: Path) -> Optional[Path]:
        """Transcribe video file"""
        try:
            # Transcribe with word timestamps enabled
            # The transcription service needs word_timestamps=True for marker detection
            result = self.transcription_service.transcribe(
                video_file,
                model="base",  # Fast model for test clips
                language="en"
            )
            
            # Find JSON transcript file (transcribe creates multiple formats)
            json_path = video_file.parent / f"{video_file.stem}_transcript.json"
            if not json_path.exists():
                # Try alternative location
                json_path = self.output_dir / f"{video_file.stem}_transcript.json"
            
            if json_path.exists():
                # Check if words are present, if not extract from segments
                with open(json_path) as f:
                    data = json.load(f)
                
                if not data.get("words") and data.get("segments"):
                    # Extract words from segments
                    all_words = []
                    for seg in data.get("segments", []):
                        seg_words = seg.get("words", [])
                        if seg_words:
                            all_words.extend(seg_words)
                        else:
                            # Fallback: split segment text into words with approximate timestamps
                            text = seg.get("text", "")
                            start = seg.get("start", 0)
                            end = seg.get("end", 0)
                            duration = end - start
                            words_text = text.split()
                            if words_text:
                                word_duration = duration / len(words_text)
                                for i, word in enumerate(words_text):
                                    all_words.append({
                                        "word": word.strip(".,!?"),
                                        "start": start + (i * word_duration),
                                        "end": start + ((i + 1) * word_duration)
                                    })
                    
                    data["words"] = all_words
                    with open(json_path, "w") as f:
                        json.dump(data, f, indent=2)
                
                return json_path
            
            return None
        except Exception as e:
            console.print(f"[red]Transcription error: {e}[/red]")
            return None
    
    def _detect_markers(self, video_file: Path, transcript_path: Path) -> List[ClipSegment]:
        """Detect markers and extract segments"""
        try:
            # Load transcript
            with open(transcript_path) as f:
                transcript_data = json.load(f)
            
            # Detect markers
            markers = self.marker_detector.detect_markers(transcript_data, source_file=video_file)
            
            if not markers:
                return []
            
            # Get video duration
            info = FFmpegProcessor.get_media_info(video_file)
            duration = info.get("duration_seconds", 0)
            
            # Extract segments based on markers
            segments = []
            
            # Group markers by type (note: types are lowercase)
            start_markers = [m for m in markers if m.marker_type == "start"]
            end_markers = [m for m in markers if m.marker_type == "end"]
            standalone_markers = [m for m in markers if m.marker_type == "standalone"]
            
            # Process all markers in order to create segments
            # Sort all markers by cut_point (when content actually starts/ends)
            all_markers_sorted = sorted(markers, key=lambda x: x.cut_point)
            
            # Process START/END pairs first
            start_markers_sorted = sorted(start_markers, key=lambda x: x.timestamp)
            end_markers_sorted = sorted(end_markers, key=lambda x: x.timestamp)
            
            # Match START with next END marker
            start_idx = 0
            for end_marker in end_markers_sorted:
                # Find the START marker that comes before this END marker
                matching_start = None
                for i in range(start_idx, len(start_markers_sorted)):
                    if start_markers_sorted[i].timestamp < end_marker.timestamp:
                        matching_start = start_markers_sorted[i]
                        start_idx = i + 1
                        break
                
                if matching_start:
                    # Use cut_point (calculated edit point) not timestamp
                    segment_start = matching_start.cut_point  # Start of content after "done"
                    segment_end = end_marker.cut_point  # End of content before "slate"
                    
                    if segment_end > segment_start:
                        # Use parsed commands from marker
                        parsed = matching_start.parsed_commands
                        commands = {
                            "naming": parsed.naming,
                            "order": parsed.order,
                            "step": parsed.step,
                            "effect": parsed.effect,
                            "transition": parsed.transition
                        }
                        
                        # Generate name
                        name = parsed.naming or "segment"
                        if parsed.order is not None:
                            name = f"{name}_order_{parsed.order}"
                        elif parsed.step is not None:
                            name = f"{name}_step_{parsed.step}"
                        if parsed.effect:
                            name = f"{name}_{parsed.effect}"
                        
                        segments.append(ClipSegment(
                            start_time=segment_start,
                            end_time=segment_end,
                            name=name,
                            marker_type="start_end",
                            commands=commands
                        ))
            
            # Process START markers without matching END (extract to next marker)
            for start in start_markers_sorted:
                # Check if this START was already used in a START/END pair
                already_used = any(
                    seg.start_time == start.cut_point and seg.marker_type == "start_end"
                    for seg in segments
                )
                
                if not already_used:
                    # Find next marker (any type) after this START
                    next_marker = None
                    for m in all_markers_sorted:
                        if m.cut_point > start.cut_point:
                            next_marker = m
                            break
                    
                    segment_start = start.cut_point
                    segment_end = next_marker.cut_point if next_marker else duration
                    
                    if segment_end > segment_start:
                        parsed = start.parsed_commands
                        name = parsed.naming or "segment"
                        if parsed.order is not None:
                            name = f"{name}_order_{parsed.order}"
                        elif parsed.step is not None:
                            name = f"{name}_step_{parsed.step}"
                        
                        segments.append(ClipSegment(
                            start_time=segment_start,
                            end_time=segment_end,
                            name=name,
                            marker_type="start",
                            commands={
                                "naming": parsed.naming,
                                "order": parsed.order,
                                "step": parsed.step
                            }
                        ))
            
            # Process standalone markers
            # Sort standalone markers by cut_point
            standalone_sorted = sorted(standalone_markers, key=lambda x: x.cut_point)
            
            # Create segments between standalone markers (or from marker to next content)
            for i, marker in enumerate(standalone_sorted):
                # Start at cut_point (after "done")
                segment_start = marker.cut_point
                
                # Find next marker of ANY type by cut_point (not timestamp)
                next_marker = None
                for m in all_markers_sorted:
                    if m.cut_point > marker.cut_point:
                        next_marker = m
                        break
                
                if next_marker:
                    segment_end = next_marker.cut_point
                else:
                    # Use clip duration
                    segment_end = duration
                
                parsed = marker.parsed_commands
                commands = {
                    "naming": parsed.naming,
                    "order": parsed.order,
                    "step": parsed.step,
                    "effect": parsed.effect,
                    "transition": parsed.transition,
                    "mark": parsed.mark
                }
                # Generate name - check if it's a boolean True vs string
                if parsed.effect:
                    name = parsed.effect.replace(":", "_")  # Handle effect names like "mtuber:intro"
                elif parsed.mark is True:
                    name = "mark"
                elif parsed.mark:
                    name = str(parsed.mark)
                else:
                    name = "mark"
                
                segments.append(ClipSegment(
                    start_time=segment_start,
                    end_time=segment_end,
                    name=name,
                    marker_type="standalone",
                    commands=commands
                ))
            
            # Sort by start time
            segments.sort(key=lambda s: s.start_time)
            
            return segments
            
        except Exception as e:
            console.print(f"[red]Marker detection error: {e}[/red]")
            import traceback
            traceback.print_exc()
            return []
    
    def _cut_with_pcm_audio(self, video_file: Path, output_file: Path, 
                            start_time: float, duration: float) -> Optional[object]:
        """Cut video with PCM audio preservation"""
        from studioflow.core.ffmpeg import FFmpegProcessor
        import subprocess
        
        # Use MOV container (better PCM support) or keep MP4 with PCM
        if output_file.suffix == ".mp4":
            # Change to MOV for better PCM compatibility
            output_file = output_file.with_suffix(".mov")
        
        cmd = [
            "ffmpeg",
            "-ss", str(start_time),
            "-i", str(video_file),
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "pcm_s16le",  # Preserve PCM audio (little-endian for compatibility)
            "-y", str(output_file)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            from studioflow.core.ffmpeg import ProcessResult
            size_mb = output_file.stat().st_size / (1024 * 1024) if output_file.exists() else 0
            return ProcessResult(success=True, output_path=output_file, file_size_mb=size_mb)
        except subprocess.CalledProcessError as e:
            from studioflow.core.ffmpeg import ProcessResult
            return ProcessResult(
                success=False,
                error_message=e.stderr[:200] if e.stderr else str(e)
            )
    
    def _extract_segment(self, video_file: Path, segment: ClipSegment, index: int) -> Optional[Path]:
        """Extract a segment from video"""
        try:
            duration = segment.end_time - segment.start_time
            
            # Generate output filename - ensure name is a string
            name_str = str(segment.name) if segment.name else f"seg{index}"
            safe_name = "".join(c for c in name_str if c.isalnum() or c in ('_', '-'))
            if not safe_name:
                safe_name = f"seg{index}"
            
            output_file = self.output_dir / f"{video_file.stem}_seg{index:02d}_{safe_name}.mp4"
            
            # Check original audio codec
            info = FFmpegProcessor.get_media_info(video_file)
            audio_codec = None
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "audio":
                    audio_codec = stream.get("codec_name")
                    break
            
            # Use copy mode for audio if PCM (lossless), otherwise re-encode
            # For test fixtures, we want to preserve original audio quality
            if audio_codec and "pcm" in audio_codec.lower():
                # Try copy mode first (faster, preserves PCM)
                result = FFmpegProcessor.cut_video(
                    video_file,
                    output_file,
                    start_time=segment.start_time,
                    duration=duration,
                    reencode=False  # Copy mode preserves PCM audio
                )
                # If copy fails (keyframe issues), fall back to re-encode
                if not (result and result.success):
                    # Re-encode but keep PCM audio
                    result = self._cut_with_pcm_audio(
                        video_file, output_file, segment.start_time, duration
                    )
            else:
                # Re-encode for precise cuts
                result = FFmpegProcessor.cut_video(
                    video_file,
                    output_file,
                    start_time=segment.start_time,
                    duration=duration,
                    reencode=True
                )
            
            if result and hasattr(result, 'success') and result.success:
                console.print(f"  [green]✓[/green] {output_file.name} ({duration:.1f}s)")
                return output_file
            else:
                error_msg = getattr(result, 'error_message', 'Unknown error') if result else 'No result'
                console.print(f"  [red]✗[/red] Failed: {segment.name} - {error_msg}")
                return None
                
        except Exception as e:
            import traceback
            console.print(f"[red]Extraction error: {e}[/red]")
            traceback.print_exc()
            return None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Split test footage into clips based on markers")
    parser.add_argument("input", type=Path, help="Input video file or directory")
    parser.add_argument("-o", "--output", type=Path, default=Path("test_clips"), help="Output directory")
    parser.add_argument("--pattern", default="*.MP4", help="File pattern (if input is directory)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_path.exists():
        console.print(f"[red]Input not found: {input_path}[/red]")
        return 1
    
    splitter = TestClipSplitter(output_dir)
    
    # Find video files
    if input_path.is_file():
        video_files = [input_path]
    else:
        video_files = list(input_path.rglob(args.pattern))
    
    if not video_files:
        console.print(f"[yellow]No video files found[/yellow]")
        return 1
    
    console.print(f"[cyan]Found {len(video_files)} video file(s)[/cyan]")
    
    # Process each file
    all_outputs = []
    for video_file in video_files:
        outputs = splitter.process_file(video_file)
        all_outputs.extend(outputs)
    
    # Summary
    console.print(f"\n[green]✓[/green] Extracted {len(all_outputs)} clips to: {output_dir}")
    
    # List outputs
    if all_outputs:
        console.print("\n[cyan]Output clips:[/cyan]")
        for output in sorted(all_outputs):
            size_mb = output.stat().st_size / (1024 * 1024)
            console.print(f"  {output.name} ({size_mb:.1f}MB)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

