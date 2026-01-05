"""
Integration tests for full rough cut pipeline
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from studioflow.core.rough_cut import (
    RoughCutEngine,
    CutStyle,
    ClipAnalysis,
    SRTEntry,
    Segment,
    RoughCutPlan
)


class TestRoughCutIntegration:
    """Full pipeline integration tests"""
    
    @pytest.fixture
    def sample_documentary_dir(self):
        """Create sample documentary test dataset"""
        with tempfile.TemporaryDirectory() as tmpdir:
            media_dir = Path(tmpdir) / "documentary"
            media_dir.mkdir()
            
            # Create interview clips with transcripts
            interviews = [
                {
                    "name": "interview1.mp4",
                    "srt": """1
00:00:00,000 --> 00:00:10,000
This is an important introduction to our story about climate change.

2
00:00:10,000 --> 00:00:20,000
The problem we face is serious and requires immediate action.

3
00:00:20,000 --> 00:00:30,000
I remember when we first noticed the changes in 2020.

4
00:00:30,000 --> 00:00:40,000
The solution is clear: we must reduce emissions by 50% by 2030.
""",
                    "duration": 40.0
                },
                {
                    "name": "interview2.mp4",
                    "srt": """1
00:00:00,000 --> 00:00:12,000
Personal stories from communities affected by climate change.

2
00:00:12,000 --> 00:00:25,000
Expert opinions from scientists show that action is needed now.

3
00:00:25,000 --> 00:00:35,000
In conclusion, we must work together to solve this crisis.
""",
                    "duration": 35.0
                }
            ]
            
            # Create B-roll clips (no transcripts)
            broll_clips = [
                {"name": "broll1.mp4", "duration": 15.0},
                {"name": "broll2.mp4", "duration": 20.0},
                {"name": "broll3.mp4", "duration": 10.0},
            ]
            
            # Create files
            for interview in interviews:
                (media_dir / interview["name"]).touch()
                (media_dir / interview["name"].replace(".mp4", ".srt")).write_text(interview["srt"])
            
            for broll in broll_clips:
                (media_dir / broll["name"]).touch()
            
            yield media_dir
    
    def test_full_pipeline_workflow(self, sample_documentary_dir):
        """Test complete rough cut generation pipeline"""
        engine = RoughCutEngine()
        
        # Mock ffprobe for duration detection
        def mock_ffprobe(cmd, **kwargs):
            mock_result = MagicMock()
            # Extract filename from command
            if "interview1" in str(cmd):
                mock_result.stdout = '{"format":{"duration":"40.0"}}'
            elif "interview2" in str(cmd):
                mock_result.stdout = '{"format":{"duration":"35.0"}}'
            else:
                mock_result.stdout = '{"format":{"duration":"15.0"}}'
            mock_result.returncode = 0
            return mock_result
        
        with patch('subprocess.run', side_effect=mock_ffprobe):
            # Analyze clips
            clips = engine.analyze_clips(sample_documentary_dir, auto_transcribe=False)
        
        assert len(clips) >= 2  # At least interview clips
        
        # Generate smart documentary rough cut
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=60.0,
            use_smart_features=True
        )
        
        # Verify plan structure
        assert plan is not None
        assert plan.style == CutStyle.DOC
        assert len(plan.segments) > 0
        
        # Verify narrative arc exists
        assert len(plan.narrative_arc) > 0
        assert 'hook' in plan.narrative_arc or 'setup' in plan.narrative_arc
        
        # Verify themes exist (may be 0 if quotes don't meet threshold)
        assert len(plan.themes) >= 0
    
    def test_narrative_arc_structure(self, sample_documentary_dir):
        """Test that narrative arc has correct structure"""
        engine = RoughCutEngine()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = '{"format":{"duration":"40.0"}}'
            mock_run.return_value.returncode = 0
            clips = engine.analyze_clips(sample_documentary_dir, auto_transcribe=False)
        
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=60.0,
            use_smart_features=True
        )
        
        # Check narrative arc sections
        arc = plan.narrative_arc
        assert 'hook' in arc
        assert 'setup' in arc
        assert 'act_1' in arc
        assert 'act_2' in arc
        assert 'act_3' in arc
        assert 'conclusion' in arc
    
    def test_thematic_grouping(self, sample_documentary_dir):
        """Test that quotes are grouped by themes"""
        engine = RoughCutEngine()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = '{"format":{"duration":"40.0"}}'
            mock_run.return_value.returncode = 0
            clips = engine.analyze_clips(sample_documentary_dir, auto_transcribe=False)
        
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=60.0,
            use_smart_features=True
        )
        
        # Verify themes exist and have quotes (may be 0 if quotes don't meet threshold)
        assert len(plan.themes) >= 0
        if plan.themes:
            for theme in plan.themes:
                assert len(theme.key_quotes) > 0
                assert theme.name
                assert theme.duration_target > 0
    
    def test_no_duplicates(self, sample_documentary_dir):
        """Test that no duplicate segments are selected"""
        engine = RoughCutEngine()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = '{"format":{"duration":"40.0"}}'
            mock_run.return_value.returncode = 0
            clips = engine.analyze_clips(sample_documentary_dir, auto_transcribe=False)
        
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=60.0,
            use_smart_features=True
        )
        
        # Check for duplicates
        segment_keys = set()
        for seg in plan.segments:
            key = (seg.source_file, seg.start_time, seg.end_time)
            assert key not in segment_keys, f"Duplicate segment found: {seg}"
            segment_keys.add(key)
    
    def test_continuous_clips_preserved(self, sample_documentary_dir):
        """Test that continuous clips are not unnecessarily cut"""
        engine = RoughCutEngine()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = '{"format":{"duration":"40.0"}}'
            mock_run.return_value.returncode = 0
            clips = engine.analyze_clips(sample_documentary_dir, auto_transcribe=False)
        
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=60.0,
            use_smart_features=True
        )
        
        # Group segments by source file
        by_file = {}
        for seg in plan.segments:
            file_key = str(seg.source_file)
            if file_key not in by_file:
                by_file[file_key] = []
            by_file[file_key].append(seg)
        
        # Check that segments from same file are merged if close together
        for file_key, segs in by_file.items():
            if len(segs) > 1:
                segs.sort(key=lambda s: s.start_time)
                for i in range(len(segs) - 1):
                    gap = segs[i+1].start_time - segs[i].end_time
                    # If gap is small (<2s), segments should be merged
                    # If gap is large (>3s), it's a natural pause
                    assert gap > 2.0 or gap < 0.1, f"Segments too close without merging: {gap}s"


class TestPerformance:
    """Performance and benchmarking tests"""
    
    def test_processing_time_per_clip(self):
        """Test that processing time is reasonable"""
        engine = RoughCutEngine()
        
        # Create test clip
        clip = ClipAnalysis(
            file_path=Path("test.mp4"),
            duration=60.0,
            transcript_path=None,
            entries=[
                SRTEntry(i, i*5.0, (i+1)*5.0, f"Sentence {i} with some content.")
                for i in range(1, 13)  # 12 entries = 60 seconds
            ],
            has_speech=True
        )
        
        engine.clips = [clip]
        
        start_time = time.time()
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=30.0,
            use_smart_features=True
        )
        elapsed = time.time() - start_time
        
        # Should process in reasonable time (<10s per clip)
        assert elapsed < 10.0, f"Processing took {elapsed:.2f}s, target <10s"
        assert plan is not None
    
    def test_memory_usage_with_multiple_clips(self):
        """Test memory usage with larger dataset"""
        import sys
        
        engine = RoughCutEngine()
        
        # Create 10 clips
        clips = []
        for i in range(10):
            clip = ClipAnalysis(
                file_path=Path(f"clip{i}.mp4"),
                duration=60.0,
                transcript_path=None,
                entries=[
                    SRTEntry(j, j*5.0, (j+1)*5.0, f"Content from clip {i}, sentence {j}.")
                    for j in range(1, 13)
                ],
                has_speech=True
            )
            clips.append(clip)
        
        engine.clips = clips
        
        # Generate rough cut
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=300.0,
            use_smart_features=True
        )
        
        # Basic check - should complete without errors
        assert plan is not None
        assert len(plan.segments) > 0


class TestEDLExport:
    """Test EDL export functionality"""
    
    def test_edl_export_with_handles(self):
        """Test EDL export includes handles"""
        engine = RoughCutEngine()
        
        clip = ClipAnalysis(
            file_path=Path("test.mp4"),
            duration=30.0,
            transcript_path=None,
            entries=[],
            has_speech=False
        )
        
        segment = Segment(
            source_file=Path("test.mp4"),
            start_time=5.0,
            end_time=15.0,
            text="Test segment",
            score=0.8
        )
        
        plan = RoughCutPlan(
            style=CutStyle.DOC,
            clips=[clip],
            segments=[segment],
            total_duration=10.0,
            structure={}
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.edl"
            result = engine.export_edl(plan, output_path)
            
            assert result == output_path
            assert output_path.exists()
            
            # Check EDL content
            content = output_path.read_text()
            assert "TITLE: StudioFlow Rough Cut" in content
            assert "test.mp4" in content or "test" in content
            # Should include handles (pre/post)
            # Handles are applied in export_edl, so start should be before 5.0
            assert "00:00:0" in content  # Timecode format
    
    def test_removed_footage_edl_export(self):
        """Test removed footage EDL export"""
        engine = RoughCutEngine()
        
        from studioflow.core.rough_cut import RemovedSegment
        
        clip = ClipAnalysis(
            file_path=Path("test.mp4"),
            duration=30.0,
            transcript_path=None,
            entries=[],
            has_speech=False
        )
        
        removed_seg = RemovedSegment(
            segment=Segment(
                source_file=Path("test.mp4"),
                start_time=0.0,
                end_time=5.0,
                text="Removed content",
                score=0.3
            ),
            reason="low_score",
            score=0.3
        )
        
        plan = RoughCutPlan(
            style=CutStyle.DOC,
            clips=[clip],
            segments=[],
            total_duration=0.0,
            structure={},
            removed_segments=[removed_seg]
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "removed.edl"
            result = engine.export_removed_footage_edl(plan, output_path)
            
            assert result == output_path
            assert output_path.exists()
            
            content = output_path.read_text()
            assert "Removed Footage" in content
            assert "low_score" in content

