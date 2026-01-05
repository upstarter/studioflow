"""
Mock utilities for testing external dependencies
"""

from unittest.mock import Mock, MagicMock
from pathlib import Path
from typing import Optional, Dict, Any


def create_mock_ffmpeg_processor(
    available: bool = True,
    processing_success: bool = True,
    media_info: Optional[Dict[str, Any]] = None
) -> Mock:
    """Create a mock FFmpegProcessor for testing"""
    from studioflow.core.ffmpeg import ProcessResult
    
    mock = Mock()
    mock.check_ffmpeg.return_value = available
    
    if media_info is None:
        media_info = {
            "duration_seconds": 10.0,
            "resolution": "1920x1080",
            "fps": 30.0,
            "video_codec": "h264",
            "audio_codec": "aac",
            "bitrate_kbps": 5000
        }
    
    mock.get_media_info.return_value = media_info
    
    if processing_success:
        result = ProcessResult(
            success=True,
            output_path=Path("/tmp/test_output.mp4"),
            duration=10.0
        )
        mock.process_video.return_value = result
        mock.normalize_audio.return_value = result
        mock.cut_video.return_value = result
    else:
        result = ProcessResult(
            success=False,
            error_message="Mocked error"
        )
        mock.process_video.return_value = result
        mock.normalize_audio.return_value = result
        mock.cut_video.return_value = result
    
    return mock


def create_mock_resolve_api(connected: bool = True) -> Mock:
    """Create a mock Resolve API for testing"""
    mock_resolve = Mock()
    
    if connected:
        mock_pm = Mock()
        mock_project = Mock()
        mock_media_pool = Mock()
        
        mock_project.GetMediaPool.return_value = mock_media_pool
        mock_project.GetTimelineCount.return_value = 0
        mock_project.SetSetting.return_value = True
        
        mock_pm.CreateProject.return_value = mock_project
        mock_resolve.GetProjectManager.return_value = mock_pm
    else:
        mock_resolve.GetProjectManager.return_value = None
    
    return mock_resolve


def create_mock_config_manager(
    base_path: Optional[Path] = None,
    custom_values: Optional[Dict[str, Any]] = None
) -> Mock:
    """Create a mock ConfigManager for testing"""
    from studioflow.core.config import ConfigManager
    
    mock_manager = Mock(spec=ConfigManager)
    
    if base_path is None:
        import tempfile
        base_path = Path(tempfile.mkdtemp())
    
    # Set default config values
    default_config = {
        "storage": {
            "active": str(base_path / "Projects"),
            "ingest": str(base_path / "Ingest"),
            "archive": str(base_path / "Archive"),
            "library": str(base_path / "Library"),
            "render": str(base_path / "Render")
        },
        "resolve": {
            "install_path": Path("/opt/resolve"),
            "api_path": Path("/opt/resolve/Developer/Scripting"),
            "enabled": True
        },
        "project": {
            "resolution": "3840x2160",
            "framerate": 29.97,
            "audio_target_lufs": -14.0
        }
    }
    
    if custom_values:
        # Merge custom values
        for key, value in custom_values.items():
            keys = key.split('.')
            d = default_config
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = value
    
    mock_config = Mock()
    mock_config.dict.return_value = default_config
    mock_manager.config = mock_config
    mock_manager.get.return_value = None  # Override per test if needed
    mock_manager.set.return_value = None
    
    return mock_manager



