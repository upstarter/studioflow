"""
Pytest configuration and shared fixtures for StudioFlow tests
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Generator

from studioflow.core.config import Config, ConfigManager, StorageConfig


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory with structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir(parents=True)
        
        # Create standard project structure
        (project_path / "01_MEDIA").mkdir()
        (project_path / "02_AUDIO").mkdir()
        (project_path / "03_RENDERS").mkdir()
        (project_path / "04_ASSETS").mkdir()
        (project_path / ".studioflow").mkdir()
        
        yield project_path


@pytest.fixture
def mock_config() -> Generator[Config, None, None]:
    """Mock config manager with test-friendly defaults"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".studioflow"
        config_dir.mkdir(parents=True)
        
        manager = ConfigManager(config_dir)
        
        # Override paths to use temp directory
        test_base = Path(tmpdir)
        manager.set("storage.active", str(test_base / "Projects"))
        manager.set("storage.ingest", str(test_base / "Ingest"))
        manager.set("storage.archive", str(test_base / "Archive"))
        manager.set("storage.studio", str(test_base / "Studio"))
        manager.set("storage.render", str(test_base / "Render"))
        
        yield manager.config


@pytest.fixture
def mock_ffmpeg() -> Generator[Mock, None, None]:
    """Mock FFmpeg processor"""
    from studioflow.core.ffmpeg import FFmpegProcessor
    
    mock = Mock(spec=FFmpegProcessor)
    mock.check_ffmpeg.return_value = True
    
    # Mock successful processing
    from studioflow.core.ffmpeg import ProcessResult
    mock.process_video.return_value = ProcessResult(
        success=True,
        output_path=Path("/tmp/test_output.mp4"),
        duration=10.0
    )
    mock.normalize_audio.return_value = ProcessResult(
        success=True,
        output_path=Path("/tmp/test_normalized.mp4"),
        duration=10.0
    )
    
    # Mock media info
    mock.get_media_info.return_value = {
        "duration_seconds": 10.0,
        "resolution": "1920x1080",
        "fps": 30.0,
        "video_codec": "h264",
        "audio_codec": "aac",
        "bitrate_kbps": 5000
    }
    
    yield mock


@pytest.fixture
def mock_resolve() -> Generator[Mock, None, None]:
    """Mock DaVinci Resolve API"""
    mock_resolve = Mock()
    mock_resolve.GetProjectManager.return_value = Mock()
    
    mock_project = Mock()
    mock_project.GetMediaPool.return_value = Mock()
    mock_project.GetTimelineCount.return_value = 0
    
    mock_pm = Mock()
    mock_pm.CreateProject.return_value = mock_project
    mock_resolve.GetProjectManager.return_value = mock_pm
    
    yield mock_resolve


@pytest.fixture
def sample_video_file(temp_project_dir: Path) -> Path:
    """Create a minimal test video file (empty file that can be used as placeholder)"""
    video_file = temp_project_dir / "01_MEDIA" / "test_video.mp4"
    video_file.parent.mkdir(parents=True, exist_ok=True)
    video_file.write_bytes(b"fake video data")
    return video_file


@pytest.fixture
def sample_audio_file(temp_project_dir: Path) -> Path:
    """Create a minimal test audio file (empty file that can be used as placeholder)"""
    audio_file = temp_project_dir / "02_AUDIO" / "test_audio.wav"
    audio_file.parent.mkdir(parents=True, exist_ok=True)
    audio_file.write_bytes(b"fake audio data")
    return audio_file


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for testing"""
    with patch('subprocess.run') as mock_run:
        # Default successful response
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_result.stderr = b""
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create temporary config directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".studioflow"
        config_dir.mkdir(parents=True)
        yield config_dir


@pytest.fixture
def sample_whisper_transcript_json() -> dict:
    """Sample Whisper JSON transcript with markers"""
    return {
        "text": "slate naming introduction done This is an introduction to our test footage.",
        "language": "en",
        "words": [
            {"word": "slate", "start": 0.0, "end": 0.5},
            {"word": "naming", "start": 0.6, "end": 1.0},
            {"word": "introduction", "start": 1.1, "end": 1.8},
            {"word": "done", "start": 1.9, "end": 2.2},
            {"word": "This", "start": 2.5, "end": 2.7},
            {"word": "is", "start": 2.8, "end": 2.9},
            {"word": "an", "start": 3.0, "end": 3.1},
            {"word": "introduction", "start": 3.2, "end": 3.8},
            {"word": "to", "start": 3.9, "end": 4.0},
            {"word": "our", "start": 4.1, "end": 4.3},
            {"word": "test", "start": 4.4, "end": 4.7},
            {"word": "footage", "start": 4.8, "end": 5.2},
        ]
    }


@pytest.fixture
def sample_srt_transcript() -> str:
    """Sample SRT transcript"""
    return """1
00:00:00,000 --> 00:00:05,000
This is the first subtitle.

2
00:00:05,000 --> 00:00:10,000
This is the second subtitle.

3
00:00:10,000 --> 00:00:15,000
This is the third subtitle.
"""


@pytest.fixture
def sample_clip_analysis(temp_project_dir: Path):
    """Sample ClipAnalysis object"""
    from studioflow.core.rough_cut import ClipAnalysis, SRTEntry
    from tests.utils.test_data_generators import generate_clip_analysis
    
    clip_file = temp_project_dir / "01_MEDIA" / "test_clip.mp4"
    clip_file.parent.mkdir(parents=True, exist_ok=True)
    clip_file.touch()
    
    return generate_clip_analysis(
        file_path=clip_file,
        duration=60.0,
        has_transcript=True,
        has_markers=False
    )


@pytest.fixture
def sample_rough_cut_plan(sample_clip_analysis):
    """Sample RoughCutPlan for testing"""
    from studioflow.core.rough_cut import RoughCutPlan, CutStyle, Segment
    from tests.utils.test_data_generators import generate_segment
    
    segments = [
        generate_segment(
            source_file=sample_clip_analysis.file_path,
            start_time=0.0,
            end_time=10.0,
            text="First segment",
            score=0.8
        ),
        generate_segment(
            source_file=sample_clip_analysis.file_path,
            start_time=10.0,
            end_time=20.0,
            text="Second segment",
            score=0.7
        ),
    ]
    
    return RoughCutPlan(
        style=CutStyle.DOC,
        clips=[sample_clip_analysis],
        segments=segments,
        total_duration=20.0,
        structure={}
    )


@pytest.fixture
def test_output_dir() -> Generator[Path, None, None]:
    """
    Create persistent test output directory for inspection
    
    Output is saved to tests/output/ so you can verify split clips are correct.
    Directory structure:
    tests/output/
      test_ingest_to_split_workflow/
        original_clip.mov
        segments/
          segment_001_introduction.mov
          segment_002_topic_one.mov
          ...
        transcripts/
          original_clip_transcript.json
        markers.json
    """
    output_base = Path(__file__).parent / "output" / "e2e_test_runs"
    output_base.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectory for this test run
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_output = output_base / f"test_run_{timestamp}"
    test_output.mkdir(parents=True, exist_ok=True)
    
    # Create standard subdirectories
    (test_output / "segments").mkdir()
    (test_output / "transcripts").mkdir()
    (test_output / "normalized").mkdir()
    (test_output / "project_structure").mkdir()
    
    yield test_output
    
    # Note: We don't clean up - output persists for inspection
    # User can manually clean up when done verifying

