"""
Comprehensive unit tests for audio marker detection and parsing
Covers all edge cases and tricky scenarios
"""

import pytest
from typing import Dict, List

from studioflow.core.audio_markers import AudioMarkerDetector, extract_segments_from_markers
from studioflow.core.marker_commands import MarkerCommandParser


class TestMarkerDetectionBasics:
    """Test basic marker detection functionality"""
    
    def setup_method(self):
        self.detector = AudioMarkerDetector()
    
    def test_detect_slate_with_done(self):
        """Basic: slate ... done"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "order", "start": 1.5, "end": 2.0},
                {"word": "one", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].timestamp == 1.0
        assert markers[0].done_time == 3.0
        assert markers[0].commands == ["order", "one"]
    
    def test_detect_done_with_punctuation(self):
        """Edge case: 'done.' with period"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "mark", "start": 1.5, "end": 2.0},
                {"word": "done.", "start": 2.5, "end": 3.0},  # With period
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].done_time == 3.0
        assert "done" not in markers[0].commands  # Should not include "done" in commands
    
    def test_detect_done_with_comma(self):
        """Edge case: 'done,' with comma"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "mark", "start": 1.5, "end": 2.0},
                {"word": "done,", "start": 2.5, "end": 3.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].done_time == 3.0
    
    def test_detect_done_with_exclamation(self):
        """Edge case: 'done!' with exclamation"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "mark", "start": 1.5, "end": 2.0},
                {"word": "done!", "start": 2.5, "end": 3.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].done_time == 3.0
    
    def test_whisper_slate_variants(self):
        """Edge case: Whisper mis-transcriptions of 'slate'"""
        variants = ["state", "slait", "slayt", "sleight"]
        for variant in variants:
            transcript = {
                "words": [
                    {"word": variant, "start": 1.0, "end": 1.5},
                    {"word": "mark", "start": 1.5, "end": 2.0},
                    {"word": "done", "start": 2.5, "end": 3.0},
                ]
            }
            markers = self.detector.detect_markers(transcript)
            assert len(markers) == 1, f"Failed for variant: {variant}"
    
    def test_whisper_done_variants(self):
        """Edge case: Whisper mis-transcriptions of 'done'"""
        variants = ["don", "dun", "dunn", "doan", "doone"]
        for variant in variants:
            transcript = {
                "words": [
                    {"word": "slate", "start": 1.0, "end": 1.5},
                    {"word": "mark", "start": 1.5, "end": 2.0},
                    {"word": variant, "start": 2.5, "end": 3.0},
                ]
            }
            markers = self.detector.detect_markers(transcript)
            assert len(markers) == 1, f"Failed for variant: {variant}"
            assert markers[0].done_time == 3.0
    
    def test_missing_done_uses_10s_window(self):
        """Edge case: No 'done' found, uses 10-second window"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "order", "start": 1.5, "end": 2.0},
                {"word": "one", "start": 2.0, "end": 2.5},
                # No "done" - should use 10s window
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].done_time == 1.0 + 10.0  # 10s after slate
    
    def test_commands_beyond_10s_ignored(self):
        """Edge case: Commands beyond 10s window are ignored"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "order", "start": 12.0, "end": 12.5},  # Beyond 10s
                {"word": "one", "start": 12.5, "end": 13.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        # Should not create marker because commands are beyond 10s window
        assert len(markers) == 0
    
    def test_empty_commands_list(self):
        """Edge case: Slate with no commands before done"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "done", "start": 2.0, "end": 2.5},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].commands == []  # Empty commands list


class TestCommandParsing:
    """Test command parsing with all keywords"""
    
    def setup_method(self):
        self.parser = MarkerCommandParser()
    
    def test_naming_disabled(self):
        """Verify 'naming' keyword is disabled (skipped)"""
        commands = ["naming", "introduction", "order", "one"]
        parsed = self.parser.parse(commands)
        assert parsed.naming is None  # Should be None (disabled)
        assert parsed.order == 1  # Should still parse other commands
    
    def test_naming_skips_to_next_keyword(self):
        """Verify 'naming' is skipped and parsing continues"""
        commands = ["naming", "topic", "one", "order", "one"]
        parsed = self.parser.parse(commands)
        assert parsed.naming is None
        assert parsed.order == 1  # Should parse "order one" after skipping "naming"
    
    def test_order_command(self):
        """Test 'order <number>' command"""
        test_cases = [
            (["order", "one"], 1),
            (["order", "five"], 5),
            (["order", "ten"], 10),
            (["order", "1"], 1),
            (["order", "20"], 20),
        ]
        for commands, expected in test_cases:
            parsed = self.parser.parse(commands)
            assert parsed.order == expected, f"Failed for {commands}"
    
    def test_step_command(self):
        """Test 'step <number>' command"""
        test_cases = [
            (["step", "one"], 1),
            (["step", "five"], 5),
            (["step", "ten"], 10),
            (["step", "1"], 1),
        ]
        for commands, expected in test_cases:
            parsed = self.parser.parse(commands)
            assert parsed.step == expected, f"Failed for {commands}"
    
    def test_mark_flag(self):
        """Test 'mark' flag command"""
        commands = ["mark"]
        parsed = self.parser.parse(commands)
        assert parsed.mark is True
    
    def test_ending_flag(self):
        """Test 'ending' flag command"""
        commands = ["ending"]
        parsed = self.parser.parse(commands)
        assert parsed.ending is True
    
    def test_effect_command(self):
        """Test 'effect <product> <name>' command"""
        commands = ["effect", "mtuber", "intro"]
        parsed = self.parser.parse(commands)
        assert parsed.effect == "mtuber:intro"
        assert parsed.effect_product == "mtuber"
        assert parsed.effect_name == "intro"
    
    def test_transition_product(self):
        """Test 'transition <product> <name>' command"""
        commands = ["transition", "mtuber", "fade"]
        parsed = self.parser.parse(commands)
        assert parsed.transition == "mtuber:fade"
        assert parsed.transition_product == "mtuber"
        assert parsed.transition_name == "fade"
    
    def test_transition_generic(self):
        """Test 'transition <generic>' command"""
        commands = ["transition", "warp"]
        parsed = self.parser.parse(commands)
        assert parsed.transition == "warp"
        assert parsed.transition_generic == "warp"
    
    def test_type_command(self):
        """Test 'type <word>' command"""
        commands = ["type", "camera"]
        parsed = self.parser.parse(commands)
        assert parsed.segment_type == "camera"
    
    def test_hook_command(self):
        """Test 'hook <type>' command"""
        commands = ["hook", "coh"]
        parsed = self.parser.parse(commands)
        assert parsed.hook == "coh"
    
    def test_screen_command(self):
        """Test 'screen <type>' command"""
        commands = ["screen", "hud"]
        parsed = self.parser.parse(commands)
        assert parsed.screen == "hud"
    
    def test_cta_command(self):
        """Test 'cta <action>' command"""
        commands = ["cta", "subscribe"]
        parsed = self.parser.parse(commands)
        assert parsed.cta == "subscribe"
    
    def test_broll_command(self):
        """Test 'broll <type>' command"""
        commands = ["broll", "screen"]
        parsed = self.parser.parse(commands)
        assert parsed.broll == "screen"
    
    def test_quality_markers(self):
        """Test quality markers: best, select, backup"""
        for quality in ["best", "select", "backup"]:
            parsed = self.parser.parse([quality])
            assert parsed.quality == quality
    
    def test_multiple_commands(self):
        """Test multiple commands in one marker"""
        commands = ["order", "one", "step", "five", "mark", "type", "camera"]
        parsed = self.parser.parse(commands)
        assert parsed.order == 1
        assert parsed.step == 5
        assert parsed.mark is True
        assert parsed.segment_type == "camera"
    
    def test_unknown_commands_ignored(self):
        """Test that unknown words are ignored"""
        commands = ["unknown", "word", "order", "one", "random", "text"]
        parsed = self.parser.parse(commands)
        assert parsed.order == 1
        # Unknown words should be ignored


class TestMarkerTypeClassification:
    """Test marker type classification logic"""
    
    def setup_method(self):
        self.detector = AudioMarkerDetector()
    
    def test_start_with_order(self):
        """START marker: has 'order' command"""
        from studioflow.core.marker_commands import ParsedCommands
        parsed = ParsedCommands(order=1)
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "start"
    
    def test_start_with_step(self):
        """START marker: has 'step' command"""
        from studioflow.core.marker_commands import ParsedCommands
        parsed = ParsedCommands(step=1)
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "start"
    
    def test_start_with_order_and_step(self):
        """START marker: has both 'order' and 'step'"""
        from studioflow.core.marker_commands import ParsedCommands
        parsed = ParsedCommands(order=1, step=1)
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "start"
    
    def test_end_marker(self):
        """END marker: has 'ending' command"""
        from studioflow.core.marker_commands import ParsedCommands
        parsed = ParsedCommands(ending=True)
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "end"
    
    def test_standalone_with_mark(self):
        """STANDALONE marker: has 'mark' command"""
        from studioflow.core.marker_commands import ParsedCommands
        parsed = ParsedCommands(mark=True)
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "standalone"
    
    def test_standalone_with_effect(self):
        """STANDALONE marker: has 'effect' command"""
        from studioflow.core.marker_commands import ParsedCommands
        parsed = ParsedCommands(effect="mtuber:intro")
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "standalone"
    
    def test_standalone_with_transition(self):
        """STANDALONE marker: has 'transition' command"""
        from studioflow.core.marker_commands import ParsedCommands
        parsed = ParsedCommands(transition="warp")
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "standalone"
    
    def test_standalone_no_commands(self):
        """STANDALONE marker: no recognized commands"""
        from studioflow.core.marker_commands import ParsedCommands
        parsed = ParsedCommands()  # Empty
        marker_type = self.detector._classify_marker_type(parsed)
        assert marker_type == "standalone"  # Default to standalone


class TestCutPointCalculation:
    """Test cut point calculation with padding"""
    
    def setup_method(self):
        self.detector = AudioMarkerDetector()
    
    def test_start_cut_point_with_padding(self):
        """START marker: cut point is before first word with 0.2s padding"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "done", "start": 2.0, "end": 2.5},
                {"word": "first", "start": 3.0, "end": 3.5},  # First content word
            ]
        }
        cut_point = self.detector._calculate_cut_point("start", 1.0, 2.5, transcript)
        # Should be 3.0 - 0.2 = 2.8s (but not before done_time 2.5)
        assert cut_point == max(2.5, 3.0 - 0.2)  # 2.8s
    
    def test_start_cut_point_no_speech_after(self):
        """START marker: no speech after 'done', uses done_time"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "done", "start": 2.0, "end": 2.5},
                # No words after done
            ]
        }
        cut_point = self.detector._calculate_cut_point("start", 1.0, 2.5, transcript)
        assert cut_point == 2.5  # Falls back to done_time
    
    def test_end_cut_point_with_padding(self):
        """END marker: cut point is after last word with 0.3s padding"""
        transcript = {
            "words": [
                {"word": "last", "start": 1.0, "end": 1.5},  # Last content word
                {"word": "word", "start": 1.5, "end": 2.0},
                {"word": "slate", "start": 3.0, "end": 3.5},
                {"word": "ending", "start": 3.5, "end": 4.0},
                {"word": "done", "start": 4.0, "end": 4.5},
            ]
        }
        cut_point = self.detector._calculate_cut_point("end", 3.0, 4.5, transcript)
        # Should be 2.0 + 0.3 = 2.3s (but not after slate_time 3.0)
        assert cut_point == min(3.0, 2.0 + 0.3)  # 2.3s
    
    def test_end_cut_point_no_content_before(self):
        """END marker: no content before 'slate', uses slate_time"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "ending", "start": 1.5, "end": 2.0},
                {"word": "done", "start": 2.0, "end": 2.5},
            ]
        }
        cut_point = self.detector._calculate_cut_point("end", 1.0, 2.5, transcript)
        assert cut_point == 1.0  # Falls back to slate_time
    
    def test_standalone_cut_point_with_padding(self):
        """STANDALONE marker: cut point is before first word with 0.2s padding"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "mark", "start": 1.5, "end": 2.0},
                {"word": "done", "start": 2.0, "end": 2.5},
                {"word": "next", "start": 3.0, "end": 3.5},  # First content word
            ]
        }
        cut_point = self.detector._calculate_cut_point("standalone", 1.0, 2.5, transcript)
        # Should be 3.0 - 0.2 = 2.8s (but not before done_time 2.5)
        assert cut_point == max(2.5, 3.0 - 0.2)  # 2.8s
    
    def test_standalone_cut_point_no_speech_after(self):
        """STANDALONE marker: no speech after 'done', uses done_time + 0.5"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "mark", "start": 1.5, "end": 2.0},
                {"word": "done", "start": 2.0, "end": 2.5},
                # No words after done
            ]
        }
        cut_point = self.detector._calculate_cut_point("standalone", 1.0, 2.5, transcript)
        assert cut_point == 2.5 + 0.5  # Falls back to done_time + 0.5


class TestSegmentExtraction:
    """Test segment extraction from markers"""
    
    def setup_method(self):
        self.detector = AudioMarkerDetector()
    
    def test_extract_segment_from_start_marker(self):
        """Extract segment from START marker to next START marker"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "order", "start": 1.5, "end": 2.0},
                {"word": "one", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
                {"word": "content", "start": 3.5, "end": 4.0},
                {"word": "slate", "start": 10.0, "end": 10.5},
                {"word": "order", "start": 10.5, "end": 11.0},
                {"word": "two", "start": 11.0, "end": 11.5},
                {"word": "done", "start": 11.5, "end": 12.0},
            ],
            "duration": 20.0
        }
        markers = self.detector.detect_markers(transcript)
        segments = extract_segments_from_markers(markers, transcript, clip_duration=20.0)
        
        assert len(segments) == 2
        # First segment: from first START to second START
        assert segments[0]["start"] == markers[0].cut_point
        assert segments[0]["end"] == markers[1].cut_point
        # Second segment: from second START to end (no more START markers)
        assert segments[1]["start"] == markers[1].cut_point
        assert segments[1]["end"] == 20.0  # Clip duration
    
    def test_extract_segment_with_end_marker(self):
        """Extract segment ending at END marker"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "order", "start": 1.5, "end": 2.0},
                {"word": "one", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
                {"word": "content", "start": 3.5, "end": 4.0},
                {"word": "slate", "start": 10.0, "end": 10.5},
                {"word": "ending", "start": 10.5, "end": 11.0},
                {"word": "done", "start": 11.0, "end": 11.5},
            ],
            "duration": 20.0
        }
        markers = self.detector.detect_markers(transcript)
        segments = extract_segments_from_markers(markers, transcript, clip_duration=20.0)
        
        assert len(segments) == 1
        # Segment should end at END marker's cut_point
        assert segments[0]["end"] == markers[1].cut_point
    
    def test_extract_segment_no_overlap(self):
        """Verify segments don't overlap"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "order", "start": 1.5, "end": 2.0},
                {"word": "one", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
                {"word": "slate", "start": 10.0, "end": 10.5},
                {"word": "order", "start": 10.5, "end": 11.0},
                {"word": "two", "start": 11.0, "end": 11.5},
                {"word": "done", "start": 11.5, "end": 12.0},
                {"word": "slate", "start": 20.0, "end": 20.5},
                {"word": "order", "start": 20.5, "end": 21.0},
                {"word": "three", "start": 21.0, "end": 21.5},
                {"word": "done", "start": 21.5, "end": 22.0},
            ],
            "duration": 30.0
        }
        markers = self.detector.detect_markers(transcript)
        segments = extract_segments_from_markers(markers, transcript, clip_duration=30.0)
        
        assert len(segments) == 3
        # Verify no overlap
        for i in range(len(segments) - 1):
            assert segments[i]["end"] <= segments[i + 1]["start"], \
                f"Segment {i} overlaps with segment {i+1}"
    
    def test_extract_segment_standalone_does_not_create_segment(self):
        """STANDALONE markers without order/step don't create segments"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "order", "start": 1.5, "end": 2.0},
                {"word": "one", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
                {"word": "slate", "start": 10.0, "end": 10.5},
                {"word": "mark", "start": 10.5, "end": 11.0},
                {"word": "done", "start": 11.0, "end": 11.5},
                {"word": "slate", "start": 20.0, "end": 20.5},
                {"word": "order", "start": 20.5, "end": 21.0},
                {"word": "two", "start": 21.0, "end": 21.5},
                {"word": "done", "start": 21.5, "end": 22.0},
            ],
            "duration": 30.0
        }
        markers = self.detector.detect_markers(transcript)
        segments = extract_segments_from_markers(markers, transcript, clip_duration=30.0)
        
        # Should only have 2 segments (from the 2 START markers)
        # The STANDALONE marker should not create a segment
        assert len(segments) == 2


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        self.detector = AudioMarkerDetector()
        self.parser = MarkerCommandParser()
    
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
    
    def test_missing_timestamps(self):
        """Missing timestamps handled gracefully"""
        transcript = {
            "words": [
                {"word": "slate"},  # Missing timestamps
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert isinstance(markers, list)
        assert len(markers) == 0  # Should not crash
    
    def test_consecutive_slates(self):
        """Consecutive slates without done"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "slate", "start": 2.0, "end": 2.5},  # Another slate before done
                {"word": "order", "start": 2.5, "end": 3.0},
                {"word": "one", "start": 3.0, "end": 3.5},
                {"word": "done", "start": 3.5, "end": 4.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        # Should detect 2 markers (first one has no done, second one does)
        assert len(markers) >= 1
        # First marker should use 10s window
        assert markers[0].done_time == 1.0 + 10.0
    
    def test_very_long_commands(self):
        """Very long command list"""
        commands = ["order", "one"] + ["word"] * 100
        parsed = self.parser.parse(commands)
        assert parsed.order == 1
        # Should handle gracefully
    
    def test_special_characters_in_commands(self):
        """Commands with special characters"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "type", "start": 1.5, "end": 2.0},
                {"word": "test-video_01", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert "test-video_01" in markers[0].commands
    
    def test_unicode_characters(self):
        """Commands with unicode characters"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "type", "start": 1.5, "end": 2.0},
                {"word": "testé", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert "testé" in markers[0].commands
    
    def test_case_insensitive_commands(self):
        """Commands are case insensitive"""
        transcript = {
            "words": [
                {"word": "SLATE", "start": 1.0, "end": 1.5},
                {"word": "ORDER", "start": 1.5, "end": 2.0},
                {"word": "ONE", "start": 2.0, "end": 2.5},
                {"word": "DONE", "start": 2.5, "end": 3.0},
            ]
        }
        markers = self.detector.detect_markers(transcript)
        assert len(markers) == 1
        assert markers[0].commands == ["ORDER", "ONE"]
    
    def test_multiple_order_commands_takes_last(self):
        """Multiple 'order' commands - takes last"""
        commands = ["order", "one", "order", "two", "order", "three"]
        parsed = self.parser.parse(commands)
        assert parsed.order == 3  # Should take last
    
    def test_multiple_step_commands_takes_last(self):
        """Multiple 'step' commands - takes last"""
        commands = ["step", "one", "step", "two"]
        parsed = self.parser.parse(commands)
        assert parsed.step == 2  # Should take last
    
    def test_invalid_number_words(self):
        """Invalid number words return None"""
        commands = ["order", "invalid"]
        parsed = self.parser.parse(commands)
        assert parsed.order is None  # Should not parse invalid number
    
    def test_content_extraction_includes_all_words(self):
        """Content extraction includes all words between done and next slate"""
        transcript = {
            "words": [
                {"word": "slate", "start": 1.0, "end": 1.5},
                {"word": "order", "start": 1.5, "end": 2.0},
                {"word": "one", "start": 2.0, "end": 2.5},
                {"word": "done", "start": 2.5, "end": 3.0},
                {"word": "This", "start": 3.5, "end": 4.0},
                {"word": "is", "start": 4.0, "end": 4.5},
                {"word": "content", "start": 4.5, "end": 5.0},
                {"word": "slate", "start": 10.0, "end": 10.5},
            ],
            "duration": 15.0
        }
        markers = self.detector.detect_markers(transcript)
        segments = extract_segments_from_markers(markers, transcript, clip_duration=15.0)
        
        assert len(segments) == 1
        segment_words = segments[0]["words"]
        # Should include all words after done
        word_texts = [w["word"] for w in segment_words]
        assert "This" in word_texts
        assert "is" in word_texts
        assert "content" in word_texts


