"""
Test data generators for creating synthetic test data
Useful for testing without real footage
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Import types (will be available when modules are imported)
try:
    from studioflow.core.rough_cut import ClipAnalysis, SRTEntry, Segment
    from studioflow.core.audio_markers import AudioMarker
    from studioflow.core.marker_commands import ParsedCommands
except ImportError:
    # Types not available yet, will be set later
    ClipAnalysis = None
    SRTEntry = None
    Segment = None
    AudioMarker = None
    ParsedCommands = None


def generate_whisper_transcript_json(
    words: Optional[List[Dict]] = None,
    text: Optional[str] = None,
    language: str = "en",
    include_markers: bool = False
) -> Dict:
    """
    Generate synthetic Whisper JSON transcript
    
    Args:
        words: List of word dicts with "word", "start", "end" keys
        text: Full transcript text (auto-generated if not provided)
        language: Language code
        include_markers: Whether to include "slate" and "done" markers
    
    Returns:
        Dict in Whisper JSON format
    """
    if words is None:
        if include_markers:
            # Generate transcript with markers
            words = [
                {"word": "slate", "start": 0.0, "end": 0.5},
                {"word": "naming", "start": 0.6, "end": 1.0},
                {"word": "introduction", "start": 1.1, "end": 1.8},
                {"word": "done", "start": 1.9, "end": 2.2},
                {"word": "This", "start": 2.5, "end": 2.7},
                {"word": "is", "start": 2.8, "end": 2.9},
                {"word": "an", "start": 3.0, "end": 3.1},
                {"word": "introduction", "start": 3.2, "end": 3.8},
                {"word": "to", "start": 3.9, "end": 4.0},
                {"word": "our", "start": 4.1, "end": 4.3},
                {"word": "test", "start": 4.4, "end": 4.7},
                {"word": "footage", "start": 4.8, "end": 5.2},
            ]
        else:
            # Generate simple transcript
            words = [
                {"word": "This", "start": 0.0, "end": 0.3},
                {"word": "is", "start": 0.4, "end": 0.5},
                {"word": "a", "start": 0.6, "end": 0.7},
                {"word": "test", "start": 0.8, "end": 1.1},
                {"word": "transcript", "start": 1.2, "end": 1.8},
            ]
    
    if text is None:
        text = " ".join(w.get("word", "") for w in words)
    
    return {
        "text": text,
        "words": words,
        "language": language
    }


def generate_srt_transcript(
    entries: Optional[List[Tuple[float, float, str]]] = None
) -> str:
    """
    Generate SRT format transcript
    
    Args:
        entries: List of (start_time, end_time, text) tuples
    
    Returns:
        SRT format string
    """
    if entries is None:
        entries = [
            (0.0, 5.0, "This is the first subtitle."),
            (5.0, 10.0, "This is the second subtitle."),
            (10.0, 15.0, "This is the third subtitle."),
        ]
    
    srt_lines = []
    for i, (start, end, text) in enumerate(entries, 1):
        # Convert seconds to SRT timecode
        start_tc = _seconds_to_srt_timecode(start)
        end_tc = _seconds_to_srt_timecode(end)
        
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start_tc} --> {end_tc}")
        srt_lines.append(text)
        srt_lines.append("")
    
    return "\n".join(srt_lines)


def _seconds_to_srt_timecode(seconds: float) -> str:
    """Convert seconds to SRT timecode format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_clip_analysis(
    file_path: Path,
    duration: float = 60.0,
    has_transcript: bool = True,
    has_markers: bool = False,
    transcript_format: str = "json"  # "json" or "srt"
) -> 'ClipAnalysis':
    """
    Generate ClipAnalysis object for testing
    
    Args:
        file_path: Path to clip file
        duration: Clip duration in seconds
        has_transcript: Whether clip has transcript
        has_markers: Whether transcript has markers
        transcript_format: "json" or "srt"
    
    Returns:
        ClipAnalysis object
    """
    if ClipAnalysis is None:
        from studioflow.core.rough_cut import ClipAnalysis, SRTEntry
    
    # Generate transcript entries
    entries = []
    if has_transcript:
        # Create SRT entries
        num_entries = int(duration / 5)  # One entry per 5 seconds
        for i in range(num_entries):
            start = i * 5.0
            end = min((i + 1) * 5.0, duration)
            text = f"This is subtitle entry {i + 1}."
            entries.append(SRTEntry(
                index=i + 1,
                start_time=start,
                end_time=end,
                text=text
            ))
    
    # Create transcript path if needed
    transcript_path = None
    transcript_json_path = None
    if has_transcript:
        if transcript_format == "srt":
            transcript_path = file_path.with_suffix(".srt")
        elif transcript_format == "json":
            transcript_json_path = file_path.with_suffix(".json")
    
    clip = ClipAnalysis(
        file_path=file_path,
        duration=duration,
        transcript_path=transcript_path,
        transcript_json_path=transcript_json_path,
        entries=entries,
        has_speech=has_transcript,
        speakers=[],
        topics=[],
        best_moments=[],
        silence_regions=[],
        filler_regions=[]
    )
    
    # Add markers if requested
    if has_markers and transcript_json_path:
        # This would be added by marker detection, but we can simulate
        pass
    
    return clip


def generate_audio_marker(
    timestamp: float,
    marker_type: str,  # "start", "end", "standalone"
    commands: List[str],
    done_time: Optional[float] = None,
    source_file: Optional[Path] = None
) -> 'AudioMarker':
    """
    Generate AudioMarker for testing
    
    Args:
        timestamp: Time of "slate" word
        marker_type: "start", "end", or "standalone"
        commands: List of command words
        done_time: Time of "done" word (auto-calculated if None)
        source_file: Source file path
    
    Returns:
        AudioMarker object
    """
    if AudioMarker is None:
        from studioflow.core.audio_markers import AudioMarker
        from studioflow.core.marker_commands import MarkerCommandParser
    
    if done_time is None:
        # Default: 2 seconds after timestamp
        done_time = timestamp + 2.0
    
    # Parse commands
    parser = MarkerCommandParser()
    parsed_commands = parser.parse(commands)
    
    # Calculate cut point (simplified)
    cut_point = done_time + 0.5  # Default cut point
    
    return AudioMarker(
        timestamp=timestamp,
        marker_type=marker_type,
        commands=commands,
        parsed_commands=parsed_commands,
        done_time=done_time,
        cut_point=cut_point,
        source_file=source_file
    )


def generate_segment(
    source_file: Path,
    start_time: float,
    end_time: float,
    text: str = "",
    score: float = 0.8,
    topic: Optional[str] = None,
    segment_type: str = "content"
) -> 'Segment':
    """
    Generate Segment for testing
    
    Args:
        source_file: Source file path
        start_time: Start time in seconds
        end_time: End time in seconds
        text: Segment text
        score: Quality score (0-1)
        topic: Topic name
        segment_type: Segment type
    
    Returns:
        Segment object
    """
    if Segment is None:
        from studioflow.core.rough_cut import Segment
    
    return Segment(
        source_file=source_file,
        start_time=start_time,
        end_time=end_time,
        text=text or f"Segment from {start_time:.1f}s to {end_time:.1f}s",
        speaker=None,
        topic=topic,
        score=score,
        segment_type=segment_type
    )


def generate_marker_transcript_json(
    marker_phrases: List[Tuple[float, str, str, float]]
) -> Dict:
    """
    Generate Whisper JSON transcript with multiple markers
    
    Args:
        marker_phrases: List of (timestamp, "slate", commands, "done" time) tuples
                       Example: [(0.0, "slate", "naming introduction", 2.0), ...]
    
    Returns:
        Whisper JSON format dict
    """
    words = []
    current_time = 0.0
    
    for slate_time, slate_word, commands_str, done_time in marker_phrases:
        # Add content before marker (if any)
        if slate_time > current_time:
            gap_words = _generate_filler_words(current_time, slate_time - 0.5)
            words.extend(gap_words)
            current_time = slate_time - 0.5
        
        # Add "slate"
        words.append({
            "word": slate_word,
            "start": slate_time,
            "end": slate_time + 0.5
        })
        current_time = slate_time + 0.5
        
        # Add commands
        command_words = commands_str.split()
        for cmd_word in command_words:
            words.append({
                "word": cmd_word,
                "start": current_time,
                "end": current_time + 0.4
            })
            current_time += 0.4
        
        # Add "done"
        words.append({
            "word": "done",
            "start": done_time,
            "end": done_time + 0.3
        })
        current_time = done_time + 0.3
        
        # Add content after "done"
        content_start = done_time + 0.5
        content_words = _generate_filler_words(content_start, content_start + 5.0)
        words.extend(content_words)
        current_time = content_start + 5.0
    
    return generate_whisper_transcript_json(words=words)


def _generate_filler_words(start_time: float, end_time: float) -> List[Dict]:
    """Generate filler words for a time range"""
    duration = end_time - start_time
    num_words = int(duration / 0.3)  # ~3 words per second
    
    filler_texts = [
        "This", "is", "a", "test", "transcript", "with", "some", "content",
        "that", "can", "be", "used", "for", "testing", "purposes"
    ]
    
    words = []
    current = start_time
    for i in range(num_words):
        word_text = filler_texts[i % len(filler_texts)]
        word_duration = 0.3
        words.append({
            "word": word_text,
            "start": current,
            "end": current + word_duration
        })
        current += word_duration
    
    return words

