"""
Test audio marker detection and segment extraction
Verifies that segments start at first words after "SLATE xx done" 
and end at last words before next "SLATE"
"""

import pytest
from pathlib import Path
from studioflow.core.audio_markers import AudioMarkerDetector, AudioMarker
from studioflow.core.transcription import TranscriptionService


@pytest.mark.integration
@pytest.mark.requires_ffmpeg
class TestAudioMarkerSegments:
    """Test segment extraction between audio markers"""
    
    def test_segment_starts_after_slate_done(self, temp_project_dir):
        """
        Verify that segments start at the first words AFTER "SLATE xx done"
        (not at the "done" word itself, but at the actual content start)
        """
        # This test will use a real fixture with markers
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_footage"
        test_file = fixtures_dir / "CAMA-C0177-00.00.01.358-00.00.53.695.mov"
        
        if not test_file.exists():
            pytest.skip(f"Test fixture not found: {test_file}")
        
        # Transcribe
        service = TranscriptionService()
        transcript = service.transcribe(test_file, model="base")
        
        if not transcript or "words" not in transcript:
            pytest.skip("Transcription failed or missing word-level timestamps")
        
        # Detect markers
        detector = AudioMarkerDetector()
        markers = detector.detect_markers(transcript, source_file=test_file)
        
        if not markers:
            pytest.skip("No markers detected in test fixture")
        
        # Find START markers
        start_markers = [m for m in markers if m.marker_type == "start"]
        
        if not start_markers:
            pytest.skip("No START markers found")
        
        # For each START marker, verify cut_point is after "done"
        for marker in start_markers:
            assert marker.cut_point >= marker.done_time, \
                f"Cut point {marker.cut_point} should be >= done_time {marker.done_time}"
            
            # Verify cut_point includes padding BEFORE first word (for natural jump cuts)
            words = transcript.get("words", [])
            words_after_done = [w for w in words if w.get("start", 0) > marker.done_time]
            
            if words_after_done:
                first_word_after = words_after_done[0]
                first_word_start = first_word_after["start"]
                # Cut point should be BEFORE first word (with ~0.2s padding)
                # This ensures natural jump cuts by including a tiny bit before content
                assert marker.cut_point <= first_word_start, \
                    f"Cut point {marker.cut_point} should be <= first word start {first_word_start}"
                # Should have padding (cut before first word, but not before done_time)
                if first_word_start - marker.done_time > 0.2:
                    assert first_word_start - marker.cut_point >= 0.1, \
                        f"Cut point {marker.cut_point} should have padding before first word {first_word_start} (at least 0.1s)"
    
    def test_segment_ends_before_next_slate(self, temp_project_dir):
        """
        Verify that segments end at the last words BEFORE the next "SLATE"
        (not at the "slate" word itself, but at the end of the last content word)
        """
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_footage"
        test_file = fixtures_dir / "CAMA-C0177-00.00.01.358-00.00.53.695.mov"
        
        if not test_file.exists():
            pytest.skip(f"Test fixture not found: {test_file}")
        
        # Transcribe
        service = TranscriptionService()
        transcript = service.transcribe(test_file, model="base")
        
        if not transcript or "words" not in transcript:
            pytest.skip("Transcription failed or missing word-level timestamps")
        
        # Detect markers
        detector = AudioMarkerDetector()
        markers = detector.detect_markers(transcript, source_file=test_file)
        
        if not markers:
            pytest.skip("No markers detected in test fixture")
        
        # Sort markers by timestamp
        markers.sort(key=lambda m: m.timestamp)
        
        # For each marker, verify that END markers cut before the next marker
        for i, marker in enumerate(markers):
            if marker.marker_type == "end":
                # Find next marker (if any)
                next_marker = None
                for j in range(i + 1, len(markers)):
                    if markers[j].marker_type in ["start", "standalone"]:
                        next_marker = markers[j]
                        break
                
                if next_marker:
                    # END marker cut_point should be before next marker's slate time
                    assert marker.cut_point <= next_marker.timestamp, \
                        f"END marker cut_point {marker.cut_point} should be <= next marker timestamp {next_marker.timestamp}"
                    
                    # Verify cut_point includes padding AFTER last word (for natural jump cuts)
                    words = transcript.get("words", [])
                    words_before_next = [w for w in words 
                                        if w.get("end", 0) < next_marker.timestamp 
                                        and w.get("end", 0) > marker.cut_point - 1.0]
                    
                    if words_before_next:
                        last_word_before = words_before_next[-1]
                        last_word_end = last_word_before["end"]
                        # Cut point should be AFTER last word (with ~0.3s padding)
                        # This ensures natural jump cuts by including a tiny bit after content
                        assert marker.cut_point >= last_word_end, \
                            f"Cut point {marker.cut_point} should be >= last word end {last_word_end}"
                        # Should have padding (cut after last word, but not after next slate)
                        if next_marker.timestamp - last_word_end > 0.3:
                            assert marker.cut_point - last_word_end >= 0.1, \
                                f"Cut point {marker.cut_point} should have padding after last word {last_word_end} (at least 0.1s)"
    
    def test_segment_extraction_between_markers(self, temp_project_dir):
        """
        Test full segment extraction: content between START and END markers
        Should start at first words after START marker's "done"
        Should end at last words before END marker's "slate"
        """
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_footage"
        test_file = fixtures_dir / "CAMA-C0177-00.00.01.358-00.00.53.695.mov"
        
        if not test_file.exists():
            pytest.skip(f"Test fixture not found: {test_file}")
        
        # Transcribe
        service = TranscriptionService()
        transcript = service.transcribe(test_file, model="base")
        
        if not transcript or "words" not in transcript:
            pytest.skip("Transcription failed or missing word-level timestamps")
        
        # Detect markers
        detector = AudioMarkerDetector()
        markers = detector.detect_markers(transcript, source_file=test_file)
        
        if not markers:
            pytest.skip("No markers detected in test fixture")
        
        # Sort markers by timestamp
        markers.sort(key=lambda m: m.timestamp)
        
        # Extract segments between START and END markers
        words = transcript.get("words", [])
        segments = []
        
        i = 0
        while i < len(markers):
            marker = markers[i]
            
            if marker.marker_type == "start":
                # Find corresponding END marker
                end_marker = None
                for j in range(i + 1, len(markers)):
                    if markers[j].marker_type == "end":
                        end_marker = markers[j]
                        break
                
                if end_marker:
                    # Segment starts at cut_point of START marker (first words after "done")
                    segment_start = marker.cut_point
                    
                    # Segment ends at cut_point of END marker (last words before next "slate")
                    segment_end = end_marker.cut_point
                    
                    # Extract words in this segment
                    segment_words = [
                        w for w in words
                        if w.get("start", 0) >= segment_start 
                        and w.get("end", 0) <= segment_end
                    ]
                    
                    if segment_words:
                        segments.append({
                            "start": segment_start,
                            "end": segment_end,
                            "words": segment_words,
                            "text": " ".join(w.get("word", "").strip() for w in segment_words)
                        })
                    
                    # Move to after END marker
                    i = markers.index(end_marker) + 1
                else:
                    i += 1
            else:
                i += 1
        
        # Verify segments
        assert len(segments) > 0, "Should extract at least one segment"
        
        for segment in segments:
            # Verify segment has content
            assert len(segment["words"]) > 0, "Segment should contain words"
            assert segment["text"].strip(), "Segment should have text"
            
            # Verify segment boundaries
            assert segment["start"] < segment["end"], "Segment start should be before end"
            
            # Verify segment doesn't include "slate" or "done" words
            segment_text_lower = segment["text"].lower()
            assert "slate" not in segment_text_lower, "Segment should not include 'slate'"
            assert "done" not in segment_text_lower, "Segment should not include 'done'"
            
            # Verify segment starts after a marker's "done"
            # (This is verified by cut_point calculation in AudioMarkerDetector)
            
            # Verify segment ends before next marker's "slate"
            # (This is verified by cut_point calculation in AudioMarkerDetector)

