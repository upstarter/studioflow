"""
Audio Marker System
Detects and parses audio markers ("slate" ... "done") from Whisper transcripts
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from .marker_commands import MarkerCommandParser, ParsedCommands


@dataclass
class AudioMarker:
    """An audio marker detected in transcript"""
    timestamp: float  # Time of "slate" word
    marker_type: str  # "start", "end", "standalone"
    commands: List[str]  # Raw command words (between "slate" and "done")
    parsed_commands: ParsedCommands  # Parsed command structure
    done_time: float  # Time of "done" word (or end of 10s window)
    cut_point: float  # Calculated cut point (removes dead space)
    
    # Metadata
    source_file: Optional[Path] = None


class AudioMarkerDetector:
    """Detect audio markers from Whisper transcripts"""
    
    # Common mis-transcriptions of "slate" and "done" by Whisper
    SLATE_VARIANTS = ["slate", "state", "slait", "slait", "slayt", "sleight"]
    DONE_VARIANTS = ["done", "don", "dun", "dunn", "doan", "doone"]
    
    def __init__(self):
        self.parser = MarkerCommandParser()
    
    def _is_slate_word(self, word: str) -> bool:
        """Check if word is a variant of 'slate' (handles Whisper mis-transcriptions and punctuation)"""
        # Remove punctuation (periods, commas, etc.) before checking
        word_lower = word.lower().strip().rstrip('.,!?;:')
        return word_lower in self.SLATE_VARIANTS
    
    def _is_done_word(self, word: str) -> bool:
        """Check if word is a variant of 'done' (handles Whisper mis-transcriptions and punctuation)"""
        # Remove punctuation (periods, commas, etc.) before checking
        word_lower = word.lower().strip().rstrip('.,!?;:')
        return word_lower in self.DONE_VARIANTS
    
    def detect_markers(self, transcript: Dict, source_file: Optional[Path] = None) -> List[AudioMarker]:
        """
        Detect all markers in transcript
        
        Args:
            transcript: Whisper transcript dict with "words" key
                       Each word should have: {"word": str, "start": float, "end": float}
            source_file: Optional source file path for metadata
        
        Returns:
            List of AudioMarker objects
        """
        markers = []
        words = transcript.get("words", [])
        
        if not words:
            return markers
        
        i = 0
        while i < len(words):
            word_text = words[i].get("word", "").strip()
            
            # Look for "slate" (with fuzzy matching for Whisper mis-transcriptions)
            if self._is_slate_word(word_text):
                # Check for required timestamps
                if "start" not in words[i]:
                    i += 1
                    continue
                
                slate_time = words[i]["start"]
                commands = []
                done_found = False
                done_time = slate_time + 10.0  # Default fallback
                
                # Collect words until "done" (or 10-second window)
                j = i + 1
                cutoff_time = slate_time + 10.0
                
                while j < len(words) and "start" in words[j] and words[j]["start"] <= cutoff_time:
                    word = words[j].get("word", "").strip()
                    
                    # Check for "done" (with fuzzy matching for Whisper mis-transcriptions)
                    if self._is_done_word(word):
                        done_found = True
                        done_time = words[j]["end"]
                        break
                    
                    commands.append(word)
                    j += 1
                
                # Process marker if we found commands
                if commands or done_found:
                    # Parse commands
                    parsed = self.parser.parse(commands)
                    
                    # Classify marker type
                    marker_type = self._classify_marker_type(parsed)
                    
                    # Calculate cut point
                    cut_point = self._calculate_cut_point(
                        marker_type, slate_time, done_time, transcript
                    )
                    
                    marker = AudioMarker(
                        timestamp=slate_time,
                        marker_type=marker_type,
                        commands=commands,
                        parsed_commands=parsed,
                        done_time=done_time,
                        cut_point=cut_point,
                        source_file=source_file
                    )
                    markers.append(marker)
                    
                    # Move past "done" if found
                    if done_found:
                        i = j + 1
                    else:
                        i = j
                else:
                    # No commands found, skip this "slate"
                    i += 1
            else:
                i += 1
        
        return markers
    
    def _classify_marker_type(self, parsed: ParsedCommands) -> str:
        """
        Classify marker type: START, RETROACTIVE, or STANDALONE
        
        Rules:
        - RETROACTIVE: Has "apply" (or deprecated "ending" with commands) - retroactive actions
        - START: Has "order", "step", "scene_number", or "take" (organization commands)
        - STANDALONE: Just "mark" or effects/transitions (no organization commands)
        
        Note: 
        - "ending" is deprecated - use "apply" for all retroactive actions
        - "ending" alone no longer creates sequence end (segments end naturally)
        - "naming" is temporarily disabled to avoid ambiguity
        """
        # RETROACTIVE: Has "apply" (or deprecated "ending" with commands)
        if parsed.retroactive_actions:
            return "retroactive"
        
        # DEPRECATED: "ending" alone no longer creates sequence end
        # Segments naturally end at next marker or end of video
        # This check is kept for backwards compatibility but should not be used
        if parsed.ending:
            import warnings
            warnings.warn(
                "The 'ending' marker alone is deprecated and no longer creates a sequence end. "
                "Segments end naturally at the next marker or end of video.",
                DeprecationWarning,
                stacklevel=2
            )
            # Treat as retroactive (does nothing, but doesn't create segment)
            return "retroactive"
        
        # START markers have "take", "order", "scene_number", or "step" (organization commands)
        # "naming" is temporarily disabled
        if parsed.take is not None or parsed.order is not None or parsed.scene_number is not None or parsed.step is not None:
            return "start"
        
        # STANDALONE markers are just "mark" or effects/transitions
        if parsed.mark or parsed.effect or parsed.transition:
            return "standalone"
        
        # Default to standalone if just effects/transitions
        return "standalone"
    
    def _calculate_cut_point(self, marker_type: str, slate_time: float, 
                            done_time: float, transcript: Dict) -> float:
        """
        Calculate cut point to remove dead space, with padding for natural jump cuts
        
        Args:
            marker_type: "start", "end", or "standalone"
            slate_time: Time of "slate" word
            done_time: Time of "done" word (or end of window)
            transcript: Full transcript dict with "words"
        
        Returns:
            Cut point timestamp in seconds (with padding for natural cuts)
        """
        words = transcript.get("words", [])
        
        # Padding for natural jump cuts (tiny amount before/after content)
        # This ensures cuts feel natural, not jarring
        PADDING_BEFORE = 0.2  # 200ms before first content word (for START)
        PADDING_AFTER = 0.3   # 300ms after last content word (for END)
        
        if marker_type == "start":
            # START marker: Cut BEFORE first content word (with padding)
            # This removes dead space but includes a tiny bit before first word
            # for natural jump cuts (ensures we capture the start of the word)
            words_after_done = [w for w in words if w.get("start", 0) > done_time]
            if words_after_done:
                first_word_start = words_after_done[0]["start"]
                # Add small padding BEFORE first word (go back a bit)
                # This gives a tiny bit of audio/video before the word starts
                # But don't go back before "done" time
                cut_point = max(done_time, first_word_start - PADDING_BEFORE)
                return cut_point
            return done_time
        
        # Note: "end" marker type is deprecated - segments end naturally
        # This code path should not be reached in normal operation
        # but kept for backwards compatibility
        else:  # standalone or deprecated "end"
            # STANDALONE marker: Cut at start of next speech after "done"
            # This removes dead space between "done" and next content
            words_after_done = [w for w in words if w.get("start", 0) > done_time]
            if words_after_done:
                first_word_start = words_after_done[0]["start"]
                # Add small padding before for natural cuts
                return max(done_time, first_word_start - PADDING_BEFORE)
            # Fallback: small buffer after "done"
            return done_time + 0.5


def detect_markers(transcript: Dict, source_file: Optional[Path] = None) -> List[AudioMarker]:
    """
    Convenience function to detect markers in transcript
    
    Args:
        transcript: Whisper transcript dict with "words" key
        source_file: Optional source file path
    
    Returns:
        List of AudioMarker objects
    """
    detector = AudioMarkerDetector()
    return detector.detect_markers(transcript, source_file)


def extract_segments_from_markers(
    markers: List[AudioMarker], 
    transcript: Dict,
    clip_duration: Optional[float] = None
) -> List[Dict]:
    """
    Extract segments from markers
    
    Each START marker creates its own segment/clip:
    - Segment starts at cut_point of START marker (after "done")
    - Segment ends at cut_point of next marker (END or next START) or clip end
    
    Args:
        markers: List of AudioMarker objects (should be sorted by timestamp)
        transcript: Transcript dict with "words" key
        clip_duration: Optional clip duration (for last segment)
    
    Returns:
        List of segment dicts with: start, end, words, text, marker_info
    """
    if not markers:
        return []
    
    # Sort markers by timestamp
    sorted_markers = sorted(markers, key=lambda m: m.timestamp)
    words = transcript.get("words", [])
    segments = []
    
    i = 0
    while i < len(sorted_markers):
        marker = sorted_markers[i]
        
        # ALL markers with content after "done" create segments
        # This includes:
        # - START markers (with order/step)
        # - STANDALONE markers (mark, effect, transition, etc.) - they all create segments
        # - END markers don't create segments (they end previous segments)
        # - RETROACTIVE markers don't create segments (they apply actions to previous segments)
        if marker.marker_type != "end" and marker.marker_type != "retroactive":
            # Segment starts at cut_point of START marker (first words after "done")
            segment_start = marker.cut_point
            
            # Find where segment ends:
            # 1. Look for next START marker (implicit END) - PRIORITY
            # 2. Or look for standalone marker with naming/order/step
            # 3. Or use explicit END marker (only if no next START)
            # 4. Or use clip end
            segment_end = None
            
            # FIRST: Look for next marker of ANY type (implicit END)
            # Segment should end AFTER last words before next marker's "slate" timestamp
            # (not at the next marker's cut_point, which is after "done")
            for j in range(i + 1, len(sorted_markers)):
                next_marker = sorted_markers[j]
                # Use the next marker's timestamp (when "slate" is said) as the boundary
                next_slate_time = next_marker.timestamp
                
                # Find last words before the next slate
                words_before_slate = [w for w in words if w.get("end", 0) < next_slate_time]
                if words_before_slate:
                    last_word_end = words_before_slate[-1].get("end", 0)
                    # End after last word with padding, but not after slate timestamp
                    segment_end = min(next_slate_time, last_word_end + 0.3)  # 0.3s padding after last word
                else:
                    # No words before next slate, end at slate time
                    segment_end = next_slate_time
                break
            
            # SECOND: If no next START marker, look for explicit END marker
            # (Only the last segment should end at END marker)
            if segment_end is None:
                for j in range(i + 1, len(sorted_markers)):
                    if sorted_markers[j].marker_type == "end":
                        segment_end = sorted_markers[j].cut_point
                        break
            
            # If still no end, use clip duration or last word
            if segment_end is None:
                if clip_duration:
                    segment_end = clip_duration
                elif words:
                    segment_end = words[-1].get("end", marker.cut_point + 10.0)
                else:
                    segment_end = marker.cut_point + 10.0  # Fallback
            
            # Extract words in this segment
            segment_words = [
                w for w in words
                if w.get("start", 0) >= segment_start 
                and w.get("end", 0) <= segment_end
            ]
            
            if segment_words or segment_end > segment_start:
                # Build segment with marker info
                segment = {
                    "start": segment_start,
                    "end": segment_end,
                    "words": segment_words,
                    "text": " ".join(w.get("word", "").strip() for w in segment_words),
                    "marker_info": {
                        "type": marker.marker_type,
                        "commands": marker.commands,
                        "naming": None,  # Temporarily disabled
                        "take": marker.parsed_commands.take,
                        "order": marker.parsed_commands.order,  # Deprecated, use scene_number
                        "scene_number": marker.parsed_commands.scene_number,
                        "scene_name": marker.parsed_commands.scene_name,
                        "step": marker.parsed_commands.step,
                        "emotion": marker.parsed_commands.emotion,
                        "energy": marker.parsed_commands.energy,
                        "hook": marker.parsed_commands.hook,
                        "quote": "quote" in marker.parsed_commands.retroactive_actions,
                    }
                }
                segments.append(segment)
            
            i += 1
        elif marker.marker_type == "end":
            # END markers don't create segments, they end previous segments
            # (handled above when looking for END markers)
            i += 1
        elif marker.marker_type == "retroactive":
            # RETROACTIVE markers apply actions to previous segment
            # Find the previous segment and apply retroactive actions
            if segments:
                previous_segment = segments[-1]
                
                # Apply score if present
                if marker.parsed_commands.score:
                    previous_segment["score"] = marker.parsed_commands.score
                    previous_segment["score_level"] = marker.parsed_commands.score_level
                    
                    # If "best", demote previous "best" to "good"
                    if marker.parsed_commands.score == "best":
                        for seg in segments[:-1]:  # All segments except the one we just updated
                            if seg.get("score") == "best":
                                seg["score"] = "good"
                                seg["score_level"] = 2  # SCORE_SCALE["good"]
                                break
                
                # Apply other retroactive actions
                for action in marker.parsed_commands.retroactive_actions:
                    if action == "remove" or action == "skip":
                        previous_segment["remove"] = True
                    elif action == "hook":
                        previous_segment["marker_info"]["hook"] = True
                    elif action == "quote":
                        previous_segment["marker_info"]["quote"] = True
                
                # Update marker_info with retroactive actions
                previous_segment["marker_info"]["retroactive_actions"] = marker.parsed_commands.retroactive_actions
            
            i += 1
        else:  # standalone
            # STANDALONE markers don't create segments
            i += 1
    
    # Sort segments for rough cut assembly
    # Priority: scene_number > take > chronological (timestamp)
    segments = _sort_segments_for_rough_cut(segments)
    
    return segments


def _sort_segments_for_rough_cut(segments: List[Dict]) -> List[Dict]:
    """
    Sort segments for rough cut assembly.
    
    Priority:
    1. scene_number (ascending) - explicit sequence order
    2. take (ascending, if same scene_number) - multiple attempts
    3. start timestamp (chronological, if no scene_number or same scene/take)
    
    This allows:
    - Shooting scenes out of order
    - Inserting scenes between existing ones (using decimals)
    - Multiple takes of same scene
    - Backwards compatibility (chronological if no scene number)
    
    Args:
        segments: List of segment dicts
        
    Returns:
        Sorted list of segments
    """
    def sort_key(seg):
        marker_info = seg.get("marker_info", {})
        scene_num = marker_info.get("scene_number")
        take = marker_info.get("take")
        start = seg.get("start", 0)
        
        # If scene_number exists, use it; otherwise use large number to push to end
        # This ensures numbered scenes come before unnumbered ones
        scene_sort = scene_num if scene_num is not None else float('inf')
        
        # Take number (0 if not present)
        take_sort = take if take is not None else 0
        
        return (scene_sort, take_sort, start)
    
    return sorted(segments, key=sort_key)

