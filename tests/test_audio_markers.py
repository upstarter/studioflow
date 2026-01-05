"""
Unit tests for audio marker detection
"""

import pytest
from pathlib import Path
from typing import Dict, List

from studioflow.core.audio_markers import AudioMarkerDetector, AudioMarker, detect_markers


class TestMarkerDetection:
    """Test marker detection functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AudioMarkerDetector()
    
    def test_detect_single_start_marker(self):
        """Detect single START marker"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "naming", "start": 1.5, "end": 2.0},
                {"word": "setup", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
                {"word": "first", "start": 3.5, "end": 4.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].marker_type == "start"
        assert markers[0].parsed_commands.naming == "setup"
        assert markers[0].timestamp == 1.0
        assert markers[0].done_time == 3.0
    
    def test_detect_single_end_marker(self):
        """Detect single END marker"""
        transcript = {
            "words": [
                {"word": "content", "start": 1.0, "end": 1.5},
                {"word": "slate", "start": 2.0, "end": 2.5},
                {"word": "ending", "start": 2.5, "end": 3.0},
                {"word": "done", "start": 3.0, "end": 3.5},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].marker_type == "end"
        assert markers[0].parsed_commands.ending is True
    
    def test_detect_standalone_marker(self):
        """Detect STANDALONE marker"""
        transcript = {
            "words": [
                {"word": "step", "start": 1.0, "end": 1.5},
                {"word": "one", "start": 1.5, "end": 2.0},
                {"word": "slate", "start": 2.0, "end": 2.5},
                {"word": "mark", "start": 2.5, "end": 3.0},
                {"word": "done", "start": 3.0, "end": 3.5},
                {"word": "step", "start": 4.0, "end": 4.5},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].marker_type == "standalone"
        assert markers[0].parsed_commands.mark is True
    
    def test_detect_multiple_markers(self):
        """Detect multiple markers in sequence"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "naming", "start": 1.5, "end": 2.0},
                {"word": "intro", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
                {"word": "content", "start": 3.5, "end": 4.0},
                {"word": "slate", "start": 5.0, "end": 5.5},
                {"word": "ending", "start": 5.5, "end": 6.0},
                {"word": "done", "start": 6.0, "end": 6.5},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 2
        assert markers[0].marker_type == "start"
        assert markers[1].marker_type == "end"
    
    def test_start_marker_cut_point(self):
        """START marker cuts at start of speech after 'done'"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "done", "start": 2.0, "end": 2.5},
                # Dead space from 2.5 to 4.0
                {"word": "first", "start": 4.0, "end": 4.5},  # Should cut here
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        # Cut point should be BEFORE start of "first" with 0.2s padding for natural jump cuts
        assert abs(markers[0].cut_point - (4.0 - 0.2)) < 0.1  # ~3.8s
    
    def test_end_marker_cut_point(self):
        """END marker cuts at end of content before marker"""
        transcript = {
            "words": [
                {"word": "content", "start": 1.0, "end": 1.5},
                {"word": "ends", "start": 1.5, "end": 2.0},  # Should cut here
                # Dead space from 2.0 to 3.0
                {"word": "slate", "start": 3.0, "end": 3.5},
                {"word": "ending", "start": 3.5, "end": 4.0},
                {"word": "done", "start": 4.0, "end": 4.5},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        # Cut point should be AFTER end of "ends" with 0.3s padding for natural jump cuts
        assert abs(markers[0].cut_point - (2.0 + 0.3)) < 0.1  # ~2.3s
    
    def test_standalone_marker_cut_point(self):
        """STANDALONE marker cuts at start of next speech"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "mark", "start": 1.5, "end": 2.0},
                {"word": "done", "start": 2.0, "end": 2.5},
                # Dead space from 2.5 to 3.5
                {"word": "next", "start": 3.5, "end": 4.0},  # Should cut here
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        # Cut point should be BEFORE start of "next" with 0.2s padding for natural jump cuts
        assert abs(markers[0].cut_point - (3.5 - 0.2)) < 0.1  # ~3.3s
    
    def test_missing_done_10s_window(self):
        """Missing 'done' uses 10-second window"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "naming", "start": 1.5, "end": 2.0},
                {"word": "setup", "start": 2.0, "end": 2.5},
                # No "done" - should use 10s window
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        # done_time should be 10s after slate
        assert markers[0].done_time == 1.0 + 10.0
    
    def test_commands_beyond_10s_window(self):
        """Commands beyond 10s window are ignored"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "naming", "start": 11.5, "end": 12.0},  # Beyond 10s
                {"word": "setup", "start": 12.0, "end": 12.5},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        # Commands beyond 10s window aren't captured, so no marker created
        assert len(markers) == 0
    
    def test_empty_transcript(self):
        """Empty transcript returns no markers"""
        transcript = {"words": []}
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 0
    
    def test_no_slate_keyword(self):
        """No 'slate' keyword returns no markers"""
        transcript = {
            "words": [
                {"word": "hello", "start": 1.0, "end": 1.5},
                {"word": "world", "start": 1.5, "end": 2.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 0
    
    def test_malformed_transcript_missing_timestamps(self):
        """Malformed transcript with missing timestamps handles gracefully"""
        transcript = {
            "words": [
                {"word": "slate"},  # Missing timestamps
            ]
        }
        # Should not crash
        markers = self.detector.detect_markers(transcript)
        # Should either return empty or handle gracefully
        assert isinstance(markers, list)
        # Missing timestamps prevent marker detection
        assert len(markers) == 0
    
    def test_multiple_start_markers(self):
        """Detect multiple START markers"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "naming", "start": 1.5, "end": 2.0},
                {"word": "intro", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
                {"word": "slate", "start": 5.0, "end": 5.5},
                {"word": "naming", "start": 5.5, "end": 6.0},
                {"word": "setup", "start": 6.0, "end": 6.5},
                {"word": "done", "start": 6.5, "end": 7.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 2
        assert all(m.marker_type == "start" for m in markers)
        assert markers[0].parsed_commands.naming == "intro"
        assert markers[1].parsed_commands.naming == "setup"
    
    def test_convenience_function(self):
        """Test convenience detect_markers function"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "naming", "start": 1.5, "end": 2.0},
                {"word": "test", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
            ]
        }
        markers = detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].marker_type == "start"


class TestMarkerTypeClassification:
    """Test marker type classification"""
    
    def setup_method(self):
        self.detector = AudioMarkerDetector()
    
    def test_classify_start_with_naming(self):
        """START marker classified correctly with 'naming' command"""
        from studioflow.core.marker_commands import ParsedCommands
        
        parsed = ParsedCommands(naming="setup")
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "start"
    
    def test_classify_start_with_order(self):
        """START marker classified correctly with 'order' command"""
        from studioflow.core.marker_commands import ParsedCommands
        
        parsed = ParsedCommands(order=1)
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "start"
    
    def test_classify_end(self):
        """END marker classified correctly"""
        from studioflow.core.marker_commands import ParsedCommands
        
        parsed = ParsedCommands(ending=True)
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "end"
    
    def test_classify_standalone(self):
        """STANDALONE marker classified correctly"""
        from studioflow.core.marker_commands import ParsedCommands
        
        parsed = ParsedCommands(mark=True)
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "standalone"


class TestCutPointCalculation:
    """Test cut point calculation"""
    
    def setup_method(self):
        self.detector = AudioMarkerDetector()
    
    def test_cut_point_start_no_speech_after(self):
        """START marker with no speech after 'done' uses done_time"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "done", "start": 2.0, "end": 2.5},
                # No words after done
            ]
        }
        cut_point = self.detector._calculate_cut_point(
            "start", 1.0, 2.5, transcript
        )
        assert cut_point == 2.5  # Falls back to done_time
    
    def test_cut_point_end_no_content_before(self):
        """END marker with no content before uses slate_time"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "ending", "start": 1.5, "end": 2.0},
                {"word": "done", "start": 2.0, "end": 2.5},
            ]
        }
        cut_point = self.detector._calculate_cut_point(
            "end", 1.0, 2.5, transcript
        )
        assert cut_point == 1.0  # Falls back to slate_time
    
    def test_cut_point_standalone_fallback(self):
        """STANDALONE marker with no speech after uses done_time + 0.5"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "mark", "start": 1.5, "end": 2.0},
                {"word": "done", "start": 2.0, "end": 2.5},
                # No words after done
            ]
        }
        cut_point = self.detector._calculate_cut_point(
            "standalone", 1.0, 2.5, transcript
        )
        assert cut_point == 2.5 + 0.5  # Falls back to done_time + 0.5

