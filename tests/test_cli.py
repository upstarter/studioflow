#!/usr/bin/env python3
"""
Test Suite for StudioFlow CLI
Tests core functionality without external dependencies
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from studioflow.core.config import Config, ConfigManager, StorageConfig
from studioflow.core.project import Project, ProjectManager, ProjectMetadata
from studioflow.core.media import MediaScanner, MediaFile, MediaType, ClipCategory
from studioflow.core.state import StateManager


def test_config_system():
    """Test configuration management"""
    print("Testing configuration system...")

    # Test default config creation
    with tempfile.TemporaryDirectory() as tmp:
        config_dir = Path(tmp) / ".studioflow"
        manager = ConfigManager(config_dir)

        assert manager.config is not None
        assert manager.config.user_name
        assert isinstance(manager.config.storage, StorageConfig)

        # Test setting values
        manager.set("log_level", "DEBUG")
        assert manager.get("log_level") == "DEBUG"

        # Test nested values
        manager.set("storage.active", "/test/path")
        assert manager.get("storage.active") == "/test/path"

    print("  ✓ Configuration system works")
    return True


def test_project_creation():
    """Test project creation and management"""
    print("Testing project creation...")

    with tempfile.TemporaryDirectory() as tmp:
        # Create project
        project = Project("Test_Project", Path(tmp) / "Test_Project")
        result = project.create(template="youtube", platform="youtube")

        assert result.success
        assert result.project_path.exists()

        # Check folder structure
        expected_folders = ["01_MEDIA", "02_AUDIO", ".studioflow"]
        for folder in expected_folders:
            assert (result.project_path / folder).exists()

        # Check metadata
        assert project.metadata.name == "Test_Project"
        assert project.metadata.template == "youtube"

        # Test project manager
        manager = ProjectManager()
        manager.projects_dir = Path(tmp)

        projects = manager.list_projects()
        assert len(projects) >= 1

    print("  ✓ Project creation works")
    return True


def test_media_scanner():
    """Test media file scanning and categorization"""
    print("Testing media scanner...")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Create test files
        (tmp_path / "video1.mp4").touch()
        (tmp_path / "video2.mov").touch()
        (tmp_path / "image.jpg").touch()
        (tmp_path / "audio.mp3").touch()
        (tmp_path / "document.pdf").touch()  # Should be ignored

        scanner = MediaScanner()
        files = scanner.scan(tmp_path)

        # Check correct files found
        assert len(files) == 4  # 2 videos, 1 image, 1 audio

        # Check media types
        types = {f.type for f in files}
        assert MediaType.VIDEO in types
        assert MediaType.IMAGE in types
        assert MediaType.AUDIO in types

    print("  ✓ Media scanner works")
    return True


def test_state_management():
    """Test session state management"""
    print("Testing state management...")

    with tempfile.TemporaryDirectory() as tmp:
        state_file = Path(tmp) / ".state"
        state = StateManager()
        state.state_file = state_file

        # Test setting current project
        state.current_project = "Test_Project"
        assert state.current_project == "Test_Project"

        # Test recent projects
        state.add_recent_project("Project1")
        state.add_recent_project("Project2")
        state.add_recent_project("Project1")  # Should move to top

        recent = state.get_recent_projects()
        assert recent[0] == "Project1"
        assert len(recent) == 2  # No duplicates

    print("  ✓ State management works")
    return True


def test_media_categorization():
    """Test clip categorization logic"""
    print("Testing media categorization...")

    # Test duration-based categorization
    scanner = MediaScanner()

    # Create mock media files with durations
    test_clip = MediaFile(
        path=Path("test.mp4"),
        size=1000,
        type=MediaType.VIDEO,
        duration=2.0  # 2 seconds
    )
    test_clip.category = scanner._categorize_clip(test_clip)
    assert test_clip.category == ClipCategory.TEST_CLIP

    b_roll = MediaFile(
        path=Path("broll.mp4"),
        size=1000,
        type=MediaType.VIDEO,
        duration=15.0  # 15 seconds
    )
    b_roll.category = scanner._categorize_clip(b_roll)
    assert b_roll.category == ClipCategory.B_ROLL

    a_roll = MediaFile(
        path=Path("interview.mp4"),
        size=1000,
        type=MediaType.VIDEO,
        duration=120.0  # 2 minutes
    )
    a_roll.category = scanner._categorize_clip(a_roll)
    assert a_roll.category == ClipCategory.A_ROLL

    print("  ✓ Media categorization works")
    return True


def test_project_templates():
    """Test different project templates"""
    print("Testing project templates...")

    templates = ["youtube", "vlog", "tutorial", "shorts", "multicam"]

    with tempfile.TemporaryDirectory() as tmp:
        for template in templates:
            project = Project(f"Test_{template}", Path(tmp) / f"Test_{template}")
            result = project.create(template=template)

            assert result.success, f"Failed to create {template} template"

            # Check template-specific folders
            if template == "tutorial":
                assert (result.project_path / "SCREEN_RECORDINGS").exists()
            elif template == "vlog":
                assert (result.project_path / "B_ROLL").exists()
            elif template == "shorts":
                assert (result.project_path / "VERTICAL_MEDIA").exists()

    print("  ✓ All project templates work")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*50)
    print("StudioFlow Test Suite")
    print("="*50 + "\n")

    tests = [
        test_config_system,
        test_project_creation,
        test_media_scanner,
        test_state_management,
        test_media_categorization,
        test_project_templates
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            results.append((test.__name__, False))

    print("\n" + "="*50)
    print("Test Results")
    print("="*50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())