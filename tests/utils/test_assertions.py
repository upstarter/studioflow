"""
Test assertion helpers for common quality checks
Reusable assertions for rough cut quality, segment validation, etc.
"""

from pathlib import Path
from typing import List, Set, Tuple

# Import types (will be available when modules are imported)
try:
    from studioflow.core.rough_cut import Segment, RoughCutPlan
except ImportError:
    Segment = None
    RoughCutPlan = None


def assert_no_duplicate_segments(segments: List[Segment], overlap_threshold: float = 0.3):
    """
    Assert no duplicate segments (overlapping segments)
    
    Args:
        segments: List of Segment objects
        overlap_threshold: Overlap percentage threshold (0.3 = 30%)
    
    Raises:
        AssertionError: If duplicate segments found
    """
    if not segments:
        return
    
    for i, seg1 in enumerate(segments):
        for seg2 in segments[i + 1:]:
            # Check if segments are from same file
            if seg1.source_file != seg2.source_file:
                continue
            
            # Check for overlap
            overlap = _calculate_overlap(seg1, seg2)
            if overlap > overlap_threshold:
                raise AssertionError(
                    f"Duplicate segments found: {seg1} and {seg2} "
                    f"(overlap: {overlap:.1%})"
                )


def assert_no_overlapping_segments(segments: List[Segment], allow_touching: bool = True):
    """
    Assert no overlapping segments (segments should not overlap in time)
    
    Args:
        segments: List of Segment objects
        allow_touching: If True, segments can touch (end == start)
    
    Raises:
        AssertionError: If overlapping segments found
    """
    if not segments:
        return
    
    # Group by source file
    by_file: dict = {}
    for seg in segments:
        file_key = str(seg.source_file)
        if file_key not in by_file:
            by_file[file_key] = []
        by_file[file_key].append(seg)
    
    # Check each file's segments
    for file_key, file_segments in by_file.items():
        if len(file_segments) < 2:
            continue
        
        # Sort by start time
        sorted_segments = sorted(file_segments, key=lambda s: s.start_time)
        
        for i in range(len(sorted_segments) - 1):
            seg1 = sorted_segments[i]
            seg2 = sorted_segments[i + 1]
            
            # Check for overlap
            if seg1.end_time > seg2.start_time:
                if not allow_touching or seg1.end_time != seg2.start_time:
                    raise AssertionError(
                        f"Overlapping segments in {file_key}: "
                        f"{seg1.start_time:.2f}-{seg1.end_time:.2f} and "
                        f"{seg2.start_time:.2f}-{seg2.end_time:.2f}"
                    )


def assert_segments_in_order(segments: List[Segment]):
    """
    Assert segments are in chronological order
    
    Args:
        segments: List of Segment objects
    
    Raises:
        AssertionError: If segments are not in order
    """
    if len(segments) < 2:
        return
    
    for i in range(len(segments) - 1):
        seg1 = segments[i]
        seg2 = segments[i + 1]
        
        # Segments should be ordered by start time
        if seg1.start_time > seg2.start_time:
            raise AssertionError(
                f"Segments not in order: {seg1.start_time:.2f} > {seg2.start_time:.2f}"
            )


def assert_valid_timestamps(segments: List[Segment]):
    """
    Assert all segments have valid timestamps
    
    Args:
        segments: List of Segment objects
    
    Raises:
        AssertionError: If invalid timestamps found
    """
    for seg in segments:
        # Start time should be >= 0
        assert seg.start_time >= 0, f"Segment has negative start time: {seg.start_time}"
        
        # End time should be > start time
        assert seg.end_time > seg.start_time, (
            f"Segment end time ({seg.end_time}) not greater than start time ({seg.start_time})"
        )
        
        # Times should be reasonable (not too large)
        assert seg.start_time < 86400, f"Segment start time too large: {seg.start_time}"  # 24 hours
        assert seg.end_time < 86400, f"Segment end time too large: {seg.end_time}"


def assert_segment_times_within_clip(segments: List[Segment], clip_duration: float):
    """
    Assert segment times are within clip duration
    
    Args:
        segments: List of Segment objects
        clip_duration: Clip duration in seconds
    
    Raises:
        AssertionError: If segments exceed clip duration
    """
    for seg in segments:
        assert seg.start_time <= clip_duration, (
            f"Segment start time ({seg.start_time}) exceeds clip duration ({clip_duration})"
        )
        assert seg.end_time <= clip_duration, (
            f"Segment end time ({seg.end_time}) exceeds clip duration ({clip_duration})"
        )


def assert_no_empty_segments(segments: List[Segment]):
    """
    Assert no empty segments (zero duration)
    
    Args:
        segments: List of Segment objects
    
    Raises:
        AssertionError: If empty segments found
    """
    for seg in segments:
        duration = seg.end_time - seg.start_time
        assert duration > 0, f"Empty segment found: {seg.start_time} to {seg.end_time}"


def assert_segment_text_not_empty(segments: List[Segment], allow_empty: bool = False):
    """
    Assert segment text is not empty (unless allowed)
    
    Args:
        segments: List of Segment objects
        allow_empty: If True, empty text is allowed
    
    Raises:
        AssertionError: If empty text found (and not allowed)
    """
    if allow_empty:
        return
    
    for seg in segments:
        assert seg.text and seg.text.strip(), f"Segment has empty text: {seg}"


def assert_segment_scores_meaningful(segments: List[Segment], min_score: float = 0.0, max_score: float = 1.0):
    """
    Assert segment scores are in valid range
    
    Args:
        segments: List of Segment objects
        min_score: Minimum valid score
        max_score: Maximum valid score
    
    Raises:
        AssertionError: If scores out of range
    """
    for seg in segments:
        assert min_score <= seg.score <= max_score, (
            f"Segment score ({seg.score}) out of range [{min_score}, {max_score}]"
        )


def assert_rough_cut_quality(plan: RoughCutPlan):
    """
    Assert rough cut plan meets quality standards
    
    Args:
        plan: RoughCutPlan object
    
    Raises:
        AssertionError: If quality checks fail
    """
    if not plan:
        raise AssertionError("Rough cut plan is None")
    
    # Check segments
    if plan.segments:
        assert_no_duplicate_segments(plan.segments)
        assert_no_overlapping_segments(plan.segments)
        assert_segments_in_order(plan.segments)
        assert_valid_timestamps(plan.segments)
        assert_no_empty_segments(plan.segments)
        assert_segment_scores_meaningful(plan.segments)
    
    # Check clips
    if plan.clips:
        for clip in plan.clips:
            # Check segments reference valid clips
            clip_segments = [s for s in plan.segments if s.source_file == clip.file_path]
            if clip_segments:
                assert_segment_times_within_clip(clip_segments, clip.duration)
    
    # Check duration
    if plan.total_duration:
        assert plan.total_duration > 0, f"Total duration should be positive: {plan.total_duration}"
    
    # Check structure
    assert isinstance(plan.structure, dict), "Plan structure should be a dict"
    
    # Check style
    assert plan.style is not None, "Plan style should be set"


def assert_valid_edl(edl_path: Path):
    """
    Assert EDL file is valid
    
    Args:
        edl_path: Path to EDL file
    
    Raises:
        AssertionError: If EDL is invalid
    """
    assert edl_path.exists(), f"EDL file does not exist: {edl_path}"
    
    content = edl_path.read_text()
    
    # Basic EDL structure checks
    assert "TITLE:" in content or "TITLE " in content, "EDL missing TITLE"
    assert "FCM:" in content or "FCM " in content, "EDL missing FCM (frame count mode)"
    
    # Should have at least one event
    assert "001" in content or "1 " in content, "EDL missing events"


def assert_valid_fcpxml(fcpxml_path: Path):
    """
    Assert FCPXML file is valid
    
    Args:
        fcpxml_path: Path to FCPXML file
    
    Raises:
        AssertionError: If FCPXML is invalid
    """
    assert fcpxml_path.exists(), f"FCPXML file does not exist: {fcpxml_path}"
    
    content = fcpxml_path.read_text()
    
    # Basic XML structure checks
    assert '<?xml' in content, "FCPXML missing XML declaration"
    assert '<fcpxml' in content or '<fcpxml>' in content, "FCPXML missing root element"
    
    # Should be well-formed XML (basic check)
    assert content.count('<') > 0, "FCPXML has no XML tags"
    assert content.count('>') > 0, "FCPXML has no XML tags"


def assert_narrative_arc_completeness(plan: RoughCutPlan):
    """
    Assert narrative arc has required sections
    
    Args:
        plan: RoughCutPlan object
    
    Raises:
        AssertionError: If narrative arc incomplete
    """
    if not plan.narrative_arc:
        # Narrative arc is optional, so this is not an error
        return
    
    required_sections = ['hook', 'setup', 'act_1', 'act_2', 'act_3', 'conclusion']
    
    for section in required_sections:
        # Section should exist (even if empty)
        assert section in plan.narrative_arc, f"Narrative arc missing section: {section}"


def assert_theme_organization_validity(plan: RoughCutPlan):
    """
    Assert theme organization is valid
    
    Args:
        plan: RoughCutPlan object
    
    Raises:
        AssertionError: If themes invalid
    """
    if not plan.themes:
        # Themes are optional
        return
    
    for theme in plan.themes:
        assert theme.name, f"Theme missing name: {theme}"
        assert theme.duration_target >= 0, f"Theme duration target invalid: {theme.duration_target}"
        
        if theme.key_quotes:
            assert len(theme.key_quotes) > 0, f"Theme {theme.name} has empty quotes list"


def _calculate_overlap(seg1: Segment, seg2: Segment) -> float:
    """Calculate overlap percentage between two segments"""
    if seg1.source_file != seg2.source_file:
        return 0.0
    
    # Calculate overlap
    overlap_start = max(seg1.start_time, seg2.start_time)
    overlap_end = min(seg1.end_time, seg2.end_time)
    
    if overlap_end <= overlap_start:
        return 0.0
    
    overlap_duration = overlap_end - overlap_start
    seg1_duration = seg1.end_time - seg1.start_time
    seg2_duration = seg2.end_time - seg2.start_time
    
    # Return overlap as percentage of smaller segment
    min_duration = min(seg1_duration, seg2_duration)
    if min_duration == 0:
        return 0.0
    
    return overlap_duration / min_duration

