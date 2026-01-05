"""
Audio Marker Integration for Rough Cut Engine
Extracts segments from audio markers and applies marker metadata
"""

from typing import List, Dict, Optional
from pathlib import Path
import json

from .audio_markers import AudioMarkerDetector, AudioMarker
from .rough_cut import Segment, ClipAnalysis
from .transcript_extraction import extract_segment_text


def extract_segments_from_markers(clips: List[ClipAnalysis]) -> List[Segment]:
    """
    Extract segments from START/END marker pairs and STANDALONE markers
    
    Args:
        clips: List of ClipAnalysis objects with markers detected
    
    Returns:
        List of Segment objects with marker metadata applied
    """
    segments = []
    detector = AudioMarkerDetector()
    
    for clip in clips:
        if not clip.markers:
            continue
        
        # Group markers by type
        start_markers = [m for m in clip.markers if m.marker_type == "start"]
        end_markers = [m for m in clip.markers if m.marker_type == "end"]
        standalone_markers = [m for m in clip.markers if m.marker_type == "standalone"]
        
        # Process START/END pairs
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
                # Create segment from START to END
                segment = Segment(
                    source_file=clip.file_path,
                    start_time=matching_start.cut_point,
                    end_time=end_marker.cut_point,
                    text="",  # Will be filled from transcript below
                    segment_type="content",
                    score=1.0  # Marker-based segments are high priority
                )
                
                # Apply marker metadata
                parsed = matching_start.parsed_commands
                if parsed.naming:
                    segment.topic = parsed.naming
                if parsed.step is not None:
                    segment.segment_type = f"step_{parsed.step}"
                if parsed.order is not None:
                    # Store order in metadata (could be used for sorting)
                    pass  # Order handled separately
                
                # Extract transcript text
                segment.text = extract_segment_text(segment, clip)
                
                segments.append(segment)
        
        # Process standalone markers as jump cut points
        # These create segments between standalone markers
        if standalone_markers:
            standalone_sorted = sorted(standalone_markers, key=lambda x: x.timestamp)
            # Create segments between standalone markers
            for i in range(len(standalone_sorted)):
                start_time = standalone_sorted[i].cut_point
                end_time = (standalone_sorted[i + 1].cut_point 
                          if i + 1 < len(standalone_sorted) 
                          else clip.duration)
                
                segment = Segment(
                    source_file=clip.file_path,
                    start_time=start_time,
                    end_time=end_time,
                    text="",  # Will be filled from transcript below
                    segment_type="jump_cut",
                    score=1.0
                )
                
                # Extract transcript text
                segment.text = extract_segment_text(segment, clip)
                
                segments.append(segment)
    
    return segments


def detect_markers_in_clips(clips: List[ClipAnalysis]) -> List[ClipAnalysis]:
    """
    Detect audio markers in clips that have JSON transcripts
    
    Args:
        clips: List of ClipAnalysis objects
    
    Returns:
        Updated clips list with markers detected
    """
    detector = AudioMarkerDetector()
    
    for clip in clips:
        if not clip.transcript_json_path or not clip.transcript_json_path.exists():
            continue
        
        try:
            # Load JSON transcript
            with open(clip.transcript_json_path, 'r') as f:
                transcript_data = json.load(f)
            
            # Detect markers
            markers = detector.detect_markers(transcript_data, source_file=clip.file_path)
            clip.markers = markers
            
        except Exception as e:
            # Silently fail - markers are optional
            pass
    
    return clips

