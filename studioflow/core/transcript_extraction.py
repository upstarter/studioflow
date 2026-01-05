"""
Extract transcript text for segments from JSON transcripts
"""

from typing import List, Optional, Dict
from pathlib import Path
import json

from .rough_cut import Segment, ClipAnalysis


def extract_segment_text(segment: Segment, clip: ClipAnalysis) -> str:
    """
    Extract transcript text for a segment from JSON transcript
    
    Args:
        segment: Segment with start_time and end_time
        clip: ClipAnalysis with transcript_json_path
    
    Returns:
        Extracted text string, or empty string if not available
    """
    if not clip.transcript_json_path or not clip.transcript_json_path.exists():
        return ""
    
    try:
        with open(clip.transcript_json_path, 'r') as f:
            transcript_data = json.load(f)
        
        words = transcript_data.get("words", [])
        if not words:
            return ""
        
        # Extract words within segment time range
        segment_words = [
            w for w in words
            if (w.get("start", 0) >= segment.start_time and 
                w.get("end", 0) <= segment.end_time)
        ]
        
        if segment_words:
            # Join words with spaces
            text = " ".join(w.get("word", "").strip() for w in segment_words)
            return text
        
        # Fallback: try to extract from segments
        segments = transcript_data.get("segments", [])
        text_parts = []
        for seg in segments:
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)
            # Check if segment overlaps with our time range
            if not (seg_end < segment.start_time or seg_start > segment.end_time):
                text_parts.append(seg.get("text", "").strip())
        
        if text_parts:
            return " ".join(text_parts)
        
        return ""
    
    except Exception:
        # Silently fail - transcript extraction is optional
        return ""


def extract_text_for_segments(segments: List[Segment], clips: List[ClipAnalysis]) -> List[Segment]:
    """
    Extract transcript text for all segments
    
    Args:
        segments: List of Segment objects
        clips: List of ClipAnalysis objects with transcript paths
    
    Returns:
        Updated segments list with text populated
    """
    # Build clip lookup
    clip_map = {clip.file_path: clip for clip in clips}
    
    for segment in segments:
        clip = clip_map.get(segment.source_file)
        if clip and not segment.text:
            segment.text = extract_segment_text(segment, clip)
    
    return segments



