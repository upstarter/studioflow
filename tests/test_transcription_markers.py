"""
Integration tests for transcription and marker detection
Tests that transcription output works with marker detection
"""

import pytest
import tempfile
import json
from pathlib import Path

from studioflow.core.transcription import TranscriptionService
from studioflow.core.audio_markers import detect_markers
from studioflow.core.rough_cut_markers import detect_markers_in_clips
from studioflow.core.rough_cut import ClipAnalysis


class TestTranscriptionMarkerIntegration:
    """Test transcription output compatibility with marker detection"""
    
    def test_json_transcript_format_for_markers(self):
        """Test that JSON transcript format is compatible with marker detection"""
        # Create mock transcript in the format Whisper produces
        transcript_data = {
            "text": "slate naming setup done content here",
            "language": "en",
            "duration": 10.0,
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "naming", "start": 1.5, "end": 2.0},
                {"word": "setup", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
                {"word": "content", "start": 4.0, "end": 4.5},
                {"word": "here", "start": 4.5, "end": 5.0},
            ],
            "segments": [
                {
                    "id": 0,
                    "start": 1.0,
                    "end": 3.0,
                    "text": "slate naming setup done",
                    "words": [
                        {"word": "slate", "start": 1.0, "end": 1.5},
                        {"word": "naming", "start": 1.5, "end": 2.0},
                        {"word": "setup", "start": 2.0, "end": 2.5},
                        {"word": "done", "start": 2.5, "end": 3.0},
                    ]
                },
                {
                    "id": 1,
                    "start": 4.0,
                    "end": 5.0,
                    "text": "content here",
                    "words": [
                        {"word": "content", "start": 4.0, "end": 4.5},
                        {"word": "here", "start": 4.5, "end": 5.0},
                    ]
                }
            ]
        }
        
        # Test marker detection with this format
        markers = detect_markers(transcript_data)
        
        assert len(markers) == 1
        assert markers[0].marker_type == "start"
        assert markers[0].parsed_commands.naming == "setup"
    
    def test_transcript_word_timestamps_required(self):
        """Test that word-level timestamps are required for markers"""
        # Transcript without word timestamps
        transcript_no_words = {
            "text": "slate naming setup done",
            "language": "en",
            "duration": 5.0,
            "segments": [
                {
                    "id": 0,
                    "start": 1.0,
                    "end": 3.0,
                    "text": "slate naming setup done"
                }
            ]
        }
        
        # Should handle gracefully (no words = no markers)
        markers = detect_markers(transcript_no_words)
        assert len(markers) == 0
    
    def test_flattened_words_array(self):
        """Test that flattened words array works for marker detection"""
        transcript_data = {
            "text": "slate mark done",
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "mark", "start": 1.5, "end": 2.0},
                {"word": "done", "start": 2.0, "end": 2.5},
            ]
        }
        
        markers = detect_markers(transcript_data)
        assert len(markers) == 1
        assert markers[0].marker_type == "standalone"
        assert markers[0].parsed_commands.mark is True
    
    def test_marker_detection_with_missing_fields(self):
        """Test marker detection handles missing fields gracefully"""
        # Transcript with some words missing timestamps
        transcript_partial = {
            "text": "slate naming setup done",
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "naming"},  # Missing timestamps
                {"word": "setup", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
            ]
        }
        
        # Should not crash, but may not detect marker correctly
        markers = detect_markers(transcript_partial)
        # Behavior depends on implementation - just verify it doesn't crash
        assert isinstance(markers, list)
    
    def test_multiple_markers_in_transcript(self):
        """Test detecting multiple markers in single transcript"""
        transcript_data = {
            "text": "slate naming intro done content slate naming outro done more content slate ending done",
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "naming", "start": 1.5, "end": 2.0},
                {"word": "intro", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
                {"word": "content", "start": 4.0, "end": 4.5},
                {"word": "slate", "start": 10.0, "end": 10.5},
                {"word": "naming", "start": 10.5, "end": 11.0},
                {"word": "outro", "start": 11.0, "end": 11.5},
                {"word": "done", "start": 11.5, "end": 12.0},
                {"word": "more", "start": 13.0, "end": 13.5},
                {"word": "content", "start": 13.5, "end": 14.0},
                {"word": "slate", "start": 20.0, "end": 20.5},
                {"word": "ending", "start": 20.5, "end": 21.0},
                {"word": "done", "start": 21.0, "end": 21.5},
            ]
        }
        
        markers = detect_markers(transcript_data)
        
        assert len(markers) == 3
        assert markers[0].marker_type == "start"
        assert markers[0].parsed_commands.naming == "intro"
        assert markers[1].marker_type == "start"
        assert markers[1].parsed_commands.naming == "outro"
        assert markers[2].marker_type == "end"
        assert markers[2].parsed_commands.ending is True


class TestClipAnalysisMarkerIntegration:
    """Test ClipAnalysis integration with marker detection"""
    
    def test_clip_with_json_transcript_path(self):
        """Test ClipAnalysis with transcript_json_path"""
        with tempfile.TemporaryDirectory() as tmp:
            clip_path = Path(tmp) / "test.mp4"
            clip_path.touch()
            
            transcript_json = Path(tmp) / "test_transcript.json"
            transcript_data = {
                "text": "slate naming test done",
                "words": [
                    {"word": "slate", "start": 1.0, "end": 1.5},
                    {"word": "naming", "start": 1.5, "end": 2.0},
                    {"word": "test", "start": 2.0, "end": 2.5},
                    {"word": "done", "start": 2.5, "end": 3.0},
                ]
            }
            
            with open(transcript_json, 'w') as f:
                json.dump(transcript_data, f)
            
            clip = ClipAnalysis(
                file_path=clip_path,
                duration=10.0,
                transcript_path=None,
                transcript_json_path=transcript_json
            )
            
            # Detect markers
            clips = detect_markers_in_clips([clip])
            
            assert len(clips[0].markers) == 1
            assert clips[0].markers[0].parsed_commands.naming == "test"
    
    def test_clip_without_transcript(self):
        """Test ClipAnalysis without transcript (should handle gracefully)"""
        with tempfile.TemporaryDirectory() as tmp:
            clip_path = Path(tmp) / "test.mp4"
            clip_path.touch()
            
            clip = ClipAnalysis(
                file_path=clip_path,
                duration=10.0,
                transcript_path=None,
                transcript_json_path=None
            )
            
            # Should not crash
            clips = detect_markers_in_clips([clip])
            assert len(clips[0].markers) == 0
    
    def test_clip_with_invalid_json_path(self):
        """Test ClipAnalysis with invalid JSON path (should handle gracefully)"""
        with tempfile.TemporaryDirectory() as tmp:
            clip_path = Path(tmp) / "test.mp4"
            clip_path.touch()
            
            invalid_path = Path(tmp) / "nonexistent.json"
            
            clip = ClipAnalysis(
                file_path=clip_path,
                duration=10.0,
                transcript_path=None,
                transcript_json_path=invalid_path
            )
            
            # Should not crash
            clips = detect_markers_in_clips([clip])
            assert len(clips[0].markers) == 0


