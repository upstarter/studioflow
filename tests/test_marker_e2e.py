"""
End-to-end tests for marker system
Tests complete workflows from transcript to export
"""

import pytest
import tempfile
import json
from pathlib import Path

from studioflow.core.rough_cut import RoughCutEngine, ClipAnalysis, CutStyle
from studioflow.core.rough_cut_markers import detect_markers_in_clips, extract_segments_from_markers
from studioflow.core.transcript_extraction import extract_text_for_segments


class TestMarkerE2E:
    """End-to-end tests for marker workflow"""
    
    def test_complete_marker_workflow_e2e(self):
        """Test complete workflow: transcript -> markers -> segments -> export"""
        with tempfile.TemporaryDirectory() as tmp:
            # Create test clip
            clip_path = Path(tmp) / "test_clip.mp4"
            clip_path.touch()
            
            # Create JSON transcript with markers
            transcript_json = Path(tmp) / "test_clip_transcript.json"
            transcript_data = {
                "text": "slate naming intro done this is the intro content slate ending done",
                "language": "en",
                "duration": 15.0,
                "words": [
                    {"word": "slate", "start": 1.0, "end": 1.5},
                    {"word": "naming", "start": 1.5, "end": 2.0},
                    {"word": "intro", "start": 2.0, "end": 2.5},
                    {"word": "done", "start": 2.5, "end": 3.0},
                    {"word": "this", "start": 4.0, "end": 4.5},
                    {"word": "is", "start": 4.5, "end": 5.0},
                    {"word": "the", "start": 5.0, "end": 5.5},
                    {"word": "intro", "start": 5.5, "end": 6.0},
                    {"word": "content", "start": 6.0, "end": 6.5},
                    {"word": "slate", "start": 10.0, "end": 10.5},
                    {"word": "ending", "start": 10.5, "end": 11.0},
                    {"word": "done", "start": 11.0, "end": 11.5},
                ],
                "segments": [
                    {
                        "id": 0,
                        "start": 1.0,
                        "end": 3.0,
                        "text": "slate naming intro done",
                        "words": [
                            {"word": "slate", "start": 1.0, "end": 1.5},
                            {"word": "naming", "start": 1.5, "end": 2.0},
                            {"word": "intro", "start": 2.0, "end": 2.5},
                            {"word": "done", "start": 2.5, "end": 3.0},
                        ]
                    },
                    {
                        "id": 1,
                        "start": 4.0,
                        "end": 6.5,
                        "text": "this is the intro content",
                        "words": [
                            {"word": "this", "start": 4.0, "end": 4.5},
                            {"word": "is", "start": 4.5, "end": 5.0},
                            {"word": "the", "start": 5.0, "end": 5.5},
                            {"word": "intro", "start": 5.5, "end": 6.0},
                            {"word": "content", "start": 6.0, "end": 6.5},
                        ]
                    },
                    {
                        "id": 2,
                        "start": 10.0,
                        "end": 11.5,
                        "text": "slate ending done",
                        "words": [
                            {"word": "slate", "start": 10.0, "end": 10.5},
                            {"word": "ending", "start": 10.5, "end": 11.0},
                            {"word": "done", "start": 11.0, "end": 11.5},
                        ]
                    }
                ]
            }
            
            with open(transcript_json, 'w') as f:
                json.dump(transcript_data, f)
            
            # Create clip analysis
            clip = ClipAnalysis(
                file_path=clip_path,
                duration=15.0,
                transcript_path=None,
                transcript_json_path=transcript_json
            )
            
            # Step 1: Detect markers
            clips = detect_markers_in_clips([clip])
            assert len(clips[0].markers) == 2
            
            # Step 2: Extract segments
            segments = extract_segments_from_markers(clips)
            assert len(segments) == 1
            assert segments[0].topic == "intro"
            
            # Step 3: Extract text (should already be done, but verify)
            segments = extract_text_for_segments(segments, clips)
            assert segments[0].text  # Should have text
            
            # Step 4: Verify segment properties
            segment = segments[0]
            assert segment.source_file == clip_path
            assert segment.topic == "intro"
            assert segment.score == 1.0
            assert segment.start_time >= 0
            assert segment.end_time > segment.start_time
    
    def test_marker_workflow_with_multiple_clips(self):
        """Test marker workflow with multiple clips"""
        with tempfile.TemporaryDirectory() as tmp:
            clips = []
            
            # Create two clips with different markers
            for i, (name, order) in enumerate([("intro", 1), ("outro", 2)]):
                clip_path = Path(tmp) / f"clip_{i}.mp4"
                clip_path.touch()
                
                transcript_json = Path(tmp) / f"clip_{i}_transcript.json"
                transcript_data = {
                    "text": f"slate naming {name} done content",
                    "words": [
                        {"word": "slate", "start": 1.0, "end": 1.5},
                        {"word": "naming", "start": 1.5, "end": 2.0},
                        {"word": name, "start": 2.0, "end": 2.5},
                        {"word": "done", "start": 2.5, "end": 3.0},
                        {"word": "content", "start": 4.0, "end": 4.5},
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
                clips.append(clip)
            
            # Detect markers in all clips
            clips = detect_markers_in_clips(clips)
            
            assert len(clips[0].markers) == 1
            assert clips[0].markers[0].parsed_commands.naming == "intro"
            assert len(clips[1].markers) == 1
            assert clips[1].markers[0].parsed_commands.naming == "outro"
            
            # Extract segments from all clips
            # Note: Without END markers, START markers don't create segments
            # (extract_segments_from_markers only creates segments from START/END pairs)
            segments = extract_segments_from_markers(clips)
            assert len(segments) == 0  # No END markers = no segments
    
    def test_marker_workflow_no_markers(self):
        """Test workflow with clips that have no markers"""
        with tempfile.TemporaryDirectory() as tmp:
            clip_path = Path(tmp) / "test_clip.mp4"
            clip_path.touch()
            
            transcript_json = Path(tmp) / "test_clip_transcript.json"
            transcript_data = {
                "text": "this is regular content without markers",
                "words": [
                    {"word": "this", "start": 1.0, "end": 1.5},
                    {"word": "is", "start": 1.5, "end": 2.0},
                    {"word": "regular", "start": 2.0, "end": 2.5},
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
            
            # Detect markers (should find none)
            clips = detect_markers_in_clips([clip])
            assert len(clips[0].markers) == 0
            
            # Extract segments (should return empty)
            segments = extract_segments_from_markers(clips)
            assert len(segments) == 0
    
    def test_marker_workflow_mixed_clips(self):
        """Test workflow with mix of clips with and without markers"""
        with tempfile.TemporaryDirectory() as tmp:
            clips = []
            
            # Clip with markers
            clip1_path = Path(tmp) / "clip1.mp4"
            clip1_path.touch()
            transcript1_json = Path(tmp) / "clip1_transcript.json"
            with open(transcript1_json, 'w') as f:
                json.dump({
                    "text": "slate naming intro done",
                    "words": [
                        {"word": "slate", "start": 1.0, "end": 1.5},
                        {"word": "naming", "start": 1.5, "end": 2.0},
                        {"word": "intro", "start": 2.0, "end": 2.5},
                        {"word": "done", "start": 2.5, "end": 3.0},
                    ]
                }, f)
            
            clip1 = ClipAnalysis(
                file_path=clip1_path,
                duration=10.0,
                transcript_path=None,
                transcript_json_path=transcript1_json
            )
            clips.append(clip1)
            
            # Clip without markers
            clip2_path = Path(tmp) / "clip2.mp4"
            clip2_path.touch()
            transcript2_json = Path(tmp) / "clip2_transcript.json"
            with open(transcript2_json, 'w') as f:
                json.dump({
                    "text": "regular content",
                    "words": [
                        {"word": "regular", "start": 1.0, "end": 1.5},
                        {"word": "content", "start": 1.5, "end": 2.0},
                    ]
                }, f)
            
            clip2 = ClipAnalysis(
                file_path=clip2_path,
                duration=10.0,
                transcript_path=None,
                transcript_json_path=transcript2_json
            )
            clips.append(clip2)
            
            # Detect markers
            clips = detect_markers_in_clips(clips)
            assert len(clips[0].markers) == 1
            assert len(clips[1].markers) == 0
            
            # Extract segments (should only get segment from clip with markers)
            # Note: Without END markers, START markers don't create segments
            segments = extract_segments_from_markers(clips)
            assert len(segments) == 0  # No END markers = no segments

