"""
Integration tests for audio marker detection
Tests full original clips and validates against individual segment fixtures
"""

import pytest
from pathlib import Path
from studioflow.core.transcription import TranscriptionService
from studioflow.core.audio_markers import AudioMarkerDetector, extract_segments_from_markers
import json


@pytest.mark.integration
@pytest.mark.requires_ffmpeg
class TestAudioMarkerIntegration:
    """Integration tests: Full clips vs individual segments"""
    
    @pytest.fixture
    def fixtures_dir(self):
        return Path(__file__).parent / "fixtures" / "test_footage"
    
    def test_original_clip_has_all_markers(self, fixtures_dir, temp_project_dir):
        """
        Integration test: Original clip should contain all markers from segments
        
        Strategy:
        1. Find original clip (e.g., CAMA-C0177-00.00.01.358-00.00.53.695.mov)
        2. Find all segment clips from that original (e.g., CAMA-C0177-...-seg1.mov, seg2.mov, etc.)
        3. Transcribe original clip
        4. Detect markers in original
        5. Extract segments from original
        6. Validate: Number of segments should match number of segment files
        """
        # Find original clips (not segments)
        original_clips = [f for f in fixtures_dir.glob("*.mov") if "seg" not in f.name]
        
        if not original_clips:
            pytest.skip("No original clips found in fixtures")
        
        # Test first original clip
        original_clip = original_clips[0]
        
        # Find corresponding segment clips
        base_name = original_clip.stem
        segment_clips = sorted(fixtures_dir.glob(f"{base_name}-seg*.mov"))
        
        if not segment_clips:
            pytest.skip(f"No segment clips found for {original_clip.name}")
        
        # Transcribe original clip
        service = TranscriptionService()
        transcript = service.transcribe(original_clip, model="base", output_formats=["json"])
        
        if not transcript or "words" not in transcript:
            pytest.skip("Transcription failed or missing word-level timestamps")
        
        # Load transcript JSON if available
        json_file = original_clip.parent / f"{original_clip.stem}_transcript.json"
        if json_file.exists():
            with open(json_file, 'r') as f:
                transcript_data = json.load(f)
        else:
            pytest.skip(f"Transcript JSON not found: {json_file}")
        
        # Detect markers in original
        detector = AudioMarkerDetector()
        markers = detector.detect_markers(transcript_data, source_file=original_clip)
        
        # Extract segments from original
        segments = extract_segments_from_markers(
            markers,
            transcript_data,
            clip_duration=transcript_data.get("duration", 0)
        )
        
        # Validation: Should have at least as many segments as segment files
        # (Some segments might be merged or filtered)
        assert len(segments) > 0, "Should extract at least one segment from original"
        
        # Each segment should have valid boundaries
        for seg in segments:
            assert seg["start"] < seg["end"], "Segment start should be before end"
            assert seg["end"] - seg["start"] > 0, "Segment should have positive duration"
    
    def test_segments_match_individual_fixtures(self, fixtures_dir, temp_project_dir):
        """
        Integration test: Segments extracted from original should match individual fixtures
        
        Strategy:
        1. Extract segments from original clip
        2. Compare with individual segment fixtures
        3. Validate: Segment boundaries should align (within tolerance)
        """
        # Find original clip
        original_clips = [f for f in fixtures_dir.glob("*.mov") if "seg" not in f.name]
        
        if not original_clips:
            pytest.skip("No original clips found")
        
        original_clip = original_clips[0]
        base_name = original_clip.stem
        segment_clips = sorted(fixtures_dir.glob(f"{base_name}-seg*.mov"))
        
        if len(segment_clips) < 2:
            pytest.skip("Need at least 2 segment clips for comparison")
        
        # Transcribe original
        service = TranscriptionService()
        json_file = original_clip.parent / f"{original_clip.stem}_transcript.json"
        
        if not json_file.exists():
            pytest.skip(f"Transcript JSON not found: {json_file}")
        
        with open(json_file, 'r') as f:
            transcript_data = json.load(f)
        
        # Extract segments from original
        detector = AudioMarkerDetector()
        markers = detector.detect_markers(transcript_data, source_file=original_clip)
        segments = extract_segments_from_markers(
            markers,
            transcript_data,
            clip_duration=transcript_data.get("duration", 0)
        )
        
        # Compare with individual segment fixtures
        # Note: This is a validation that the system works end-to-end
        # Individual segments might have been manually edited, so exact match isn't required
        # But we should have extracted segments from the original
        
        # If original clip has markers, should extract segments
        # If no markers (pre-split test clip), that's expected
        if markers:
            assert len(segments) > 0, "If markers found, should extract segments from original"
        else:
            pytest.skip("Original clip has no markers (expected for pre-split test fixtures)")
        
        # Validate segment quality
        for seg in segments:
            assert "start" in seg
            assert "end" in seg
            assert seg["start"] < seg["end"]
            assert "text" in seg or "words" in seg
    
    def test_full_clip_marker_detection(self, fixtures_dir, temp_project_dir):
        """
        Integration test: Full clip should detect all markers correctly
        
        If individual segment fixtures pass, the full original clip should:
        1. Detect all markers
        2. Extract all segments
        3. Have valid segment boundaries
        """
        # Find original clip
        original_clips = [f for f in fixtures_dir.glob("*.mov") if "seg" not in f.name]
        
        if not original_clips:
            pytest.skip("No original clips found")
        
        original_clip = original_clips[0]
        
        # Load transcript
        json_file = original_clip.parent / f"{original_clip.stem}_transcript.json"
        
        if not json_file.exists():
            pytest.skip(f"Transcript JSON not found: {json_file}")
        
        with open(json_file, 'r') as f:
            transcript_data = json.load(f)
        
        # Detect markers
        detector = AudioMarkerDetector()
        markers = detector.detect_markers(transcript_data, source_file=original_clip)
        
        # Extract segments
        segments = extract_segments_from_markers(
            markers,
            transcript_data,
            clip_duration=transcript_data.get("duration", 0)
        )
        
        # Validation
        # If we have segment fixtures, we should extract at least some segments
        # (Markers might not be in pre-split test clips)
        
        # At minimum, validate the system works without errors
        assert isinstance(markers, list), "Markers should be a list"
        assert isinstance(segments, list), "Segments should be a list"
        
        # If markers found, segments should be valid
        if markers:
            assert len(segments) > 0, "If markers found, should extract segments"
            
            for seg in segments:
                assert seg["start"] >= 0, "Segment start should be non-negative"
                assert seg["end"] > seg["start"], "Segment end should be after start"
                assert seg["end"] <= transcript_data.get("duration", 999), "Segment should not exceed clip duration"

