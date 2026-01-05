# Test Suite Development Guide

Complete guide for developing and maintaining the StudioFlow test suite.

## Overview

This guide covers test infrastructure, development patterns, implementation strategy, and best practices. The goal is **ultra-high quality rough cuts** with 95%+ coverage on the rough cut system and 85%+ overall coverage.

## Table of Contents

1. [Current State](#current-state)
2. [Test Infrastructure](#test-infrastructure)
3. [Implementation Strategy](#implementation-strategy)
4. [Development Guidelines](#development-guidelines)
5. [Testing Patterns](#testing-patterns)
6. [Running Tests](#running-tests)

---

## Current State

### Test Coverage Status

- **Existing Tests**: 138+ test cases across multiple test files
- **Test Framework**: pytest (7.4.0+)
- **Test Infrastructure**: Complete (conftest.py, fixtures, utilities)
- **Test Collection**: All tests collectable (no import errors)
- **Test Execution**: Tests run successfully

### Codebase Statistics

- **CLI Command Modules**: 26 files in `studioflow/cli/commands/`
- **Core Modules**: 50 files in `studioflow/core/`
- **Test Files**: Multiple files in `tests/`
- **Hardcoded Paths**: Fixed (all use config system)
- **Legacy Code**: Cleaned (eric.py archived, broken tests removed)

### Key Infrastructure Files

- **`tests/conftest.py`**: Shared pytest fixtures
- **`tests/utils/test_data_generators.py`**: Synthetic data generators
- **`tests/utils/test_assertions.py`**: Quality assertion helpers
- **`pytest.ini`**: Pytest configuration with markers

---

## Test Infrastructure

### Available Fixtures

#### Core Fixtures (`tests/conftest.py`)

- **`temp_project_dir`**: Temporary project with standard structure
- **`mock_config`**: Mock config manager with test-friendly defaults
- **`mock_ffmpeg`**: Mock FFmpeg processor
- **`mock_resolve`**: Mock DaVinci Resolve API
- **`sample_video_file`**: Placeholder video file
- **`sample_audio_file`**: Placeholder audio file
- **`temp_config_dir`**: Temporary config directory

#### Data Generators (`tests/utils/test_data_generators.py`)

- **`generate_whisper_transcript_json()`**: Synthetic Whisper transcripts
- **`generate_srt_transcript()`**: SRT format transcripts
- **`generate_clip_analysis()`**: ClipAnalysis objects
- **`generate_audio_marker()`**: AudioMarker objects
- **`generate_segment()`**: Segment objects

#### Assertion Helpers (`tests/utils/test_assertions.py`)

- **`assert_rough_cut_quality()`**: Complete quality check
- **`assert_no_duplicate_segments()`**: No duplicates
- **`assert_no_overlapping_segments()`**: No overlaps
- **`assert_segments_in_order()`**: Chronological ordering
- **`assert_valid_edl()`**: EDL format validation
- **`assert_valid_fcpxml()`**: FCPXML format validation

### Test Markers

Use pytest markers to categorize tests:

- **`@pytest.mark.unit`**: Fast unit tests (<100ms)
- **`@pytest.mark.integration`**: Integration tests (<5s)
- **`@pytest.mark.slow`**: Slow tests (>5s)
- **`@pytest.mark.requires_resolve`**: Needs DaVinci Resolve
- **`@pytest.mark.requires_ffmpeg`**: Needs FFmpeg
- **`@pytest.mark.requires_network`**: Needs network

---

## Implementation Strategy

### Priority Order (Bottom-Up Testing)

**Strategy**: Test foundation components first, then build up to the critical rough cut system.

#### Phase 1: Foundation Layer (Week 1) - CRITICAL

**Why First**: Rough cut depends on these. If broken, rough cut can't work.

1. **Configuration System** (`test_config.py`)
   - Config loading/saving/migration
   - Path resolution
   - Nested value access
   - **Target**: 90%+ coverage

2. **FFmpeg Integration** (`test_ffmpeg.py`)
   - Media info extraction
   - Video/audio operations
   - Error handling
   - **Target**: 80%+ coverage (with mocks)

3. **Media Analysis** (`test_media.py`)
   - File scanning
   - Media type detection
   - Metadata extraction
   - **Target**: 85%+ coverage

#### Phase 2: Core Feature Layer (Week 2) - HIGH

**Why Second**: Direct dependencies of rough cut engine.

1. **Transcription Service** (`test_transcription.py`)
   - Video/audio transcription
   - Export formats (SRT, VTT, JSON, TXT)
   - Whisper fallback
   - **Target**: 80%+ coverage

2. **Marker Commands** (`test_marker_commands.py`)
   - All command types (naming, order, step, ending, effect, transition, mark)
   - Fuzzy matching, case insensitive, typo handling
   - **Target**: 95%+ coverage

3. **Audio Marker Detection** (`test_audio_markers.py`)
   - START/END pairs, standalone markers
   - 10s window handling
   - Cut point calculation
   - **Target**: 90%+ coverage

4. **Transcript Extraction** (`test_transcript_extraction.py`)
   - Extract from SRT/JSON
   - Missing transcript handling
   - **Target**: 85%+ coverage

#### Phase 3: Integration Layer (Week 3) - CRITICAL

**Why Third**: Integrates dependencies before testing rough cut.

1. **Rough Cut Markers Integration** (`test_rough_cut_markers.py`)
   - Extract segments from markers
   - Marker metadata application
   - Marker ordering preservation
   - **Target**: 95%+ coverage

2. **Transcript Analyzer** (`test_transcript_analyzer.py`)
   - Quote extraction, importance scoring
   - Sentiment analysis, emotion detection
   - Natural edit points
   - **Target**: 90%+ coverage

#### Phase 4: Rough Cut Engine (Weeks 4-5) - CRITICAL

**Why Fourth**: All dependencies are now tested and solid.

1. **Core Engine** (`test_rough_cut_engine_unit.py`)
   - Engine initialization
   - Clip analysis
   - Transcript loading
   - **Target**: 95%+ coverage

2. **Integration Tests** (`test_rough_cut_engine_integration.py`)
   - Full pipeline for all cut styles
   - Marker-based and transcript-based rough cuts
   - EDL/FCPXML export
   - **Target**: 95%+ coverage

3. **Quality Assurance** (`test_rough_cut_quality.py`)
   - No duplicates/overlaps
   - Chronological ordering
   - Valid timestamps
   - **Target**: 95%+ coverage

4. **Property-Based Tests** (`test_rough_cut_properties.py`)
   - Duration never exceeds target
   - All segments reference valid clips
   - Segment times within clip duration
   - **Target**: 95%+ coverage

#### Phase 5: CLI & E2E (Weeks 6-7) - MEDIUM

1. **CLI Commands** (`test_*_commands.py`)
   - All command modules
   - Error handling
   - **Target**: 85%+ coverage

2. **End-to-End Workflows** (`test_*_workflow_e2e.py`)
   - Episode workflow
   - Documentary workflow
   - **Target**: 85%+ coverage

### Coverage Targets

| Component | Target | Priority |
|-----------|--------|----------|
| `rough_cut.py` | 95%+ | CRITICAL |
| `rough_cut_markers.py` | 95%+ | CRITICAL |
| `audio_markers.py` | 90%+ | HIGH |
| `marker_commands.py` | 95%+ | HIGH |
| `transcript_analyzer.py` | 90%+ | HIGH |
| Supporting features | 80-90% | MEDIUM |
| CLI commands | 85%+ | MEDIUM |
| **Overall** | **85%+** | - |

---

## Development Guidelines

### Test Organization

- **File naming**: `test_<module_name>.py`
- **Class naming**: `Test<ClassName>`
- **Function naming**: `test_<description>`

### Test Structure

#### Unit Tests

```python
@pytest.mark.unit
def test_config_loading(temp_config_dir):
    """Test config loads correctly"""
    from studioflow.core.config import ConfigManager
    
    manager = ConfigManager(temp_config_dir)
    assert manager.config is not None
```

#### Integration Tests

```python
@pytest.mark.integration
def test_project_creation_workflow(temp_project_dir):
    """Test complete project creation workflow"""
    project = Project("Test", temp_project_dir)
    result = project.create(template="youtube")
    assert result.success
```

#### Mocking External Dependencies

```python
@patch('studioflow.core.ffmpeg.subprocess.run')
def test_normalize_audio(mock_subprocess, sample_video_file):
    """Test normalization with mocked subprocess"""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_subprocess.return_value = mock_result
    
    normalizer = MediaNormalizer()
    result = normalizer.normalize_video(sample_video_file)
    assert mock_subprocess.called
```

### Important Notes

#### Path Handling

Config system returns `Path` objects, not strings:

```python
# Correct
assert manager.get("storage.active") == Path("/test/path")

# Or convert to string
assert str(manager.get("storage.active")) == "/test/path"
```

#### Test Isolation

- Use fixtures for setup/teardown
- Don't rely on test execution order
- Use temporary directories (never hardcoded paths)
- Clean up after tests (fixtures handle this automatically)

---

## Testing Patterns

### Pattern 1: Config System

```python
def test_config_system(temp_config_dir):
    manager = ConfigManager(temp_config_dir)
    manager.set("log_level", "DEBUG")
    assert manager.get("log_level") == "DEBUG"
```

### Pattern 2: Media Processing

```python
def test_media_normalization(mock_ffmpeg, sample_video_file):
    normalizer = MediaNormalizer()
    result = normalizer.normalize_video(sample_video_file)
    assert result.success
```

### Pattern 3: CLI Commands

```python
from typer.testing import CliRunner

def test_normalize_command():
    runner = CliRunner()
    result = runner.invoke(app, ["normalize", "file", str(test_file)])
    assert result.exit_code == 0
```

### Pattern 4: Quality Assertions

```python
def test_rough_cut_quality(rough_cut_plan):
    from tests.utils.test_assertions import assert_rough_cut_quality
    assert_rough_cut_quality(rough_cut_plan)
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=studioflow --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::test_config_loading

# Run with markers
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run with verbose output
pytest -v

# Run with output capture disabled
pytest -s
```

### Coverage Commands

```bash
# Check coverage for specific module
pytest --cov=studioflow.core.rough_cut --cov-report=html

# Check overall coverage
pytest --cov=studioflow --cov-report=term-missing --cov-fail-under=85
```

---

## Quick Reference

### File Locations

- **Test files**: `tests/test_*.py`
- **Fixtures**: `tests/conftest.py`
- **Utilities**: `tests/utils/`
- **Config**: `pytest.ini`

### Key Modules to Test

- **Config**: `studioflow/core/config.py`
- **Project**: `studioflow/core/project.py`
- **Media**: `studioflow/core/media.py`
- **FFmpeg**: `studioflow/core/ffmpeg.py`
- **Audio Markers**: `studioflow/core/audio_markers.py`
- **Rough Cut**: `studioflow/core/rough_cut.py`

### Common Issues

**Q: Test fails with "Module not found"**  
A: Check imports. All test files should import from `studioflow.core` or `studioflow.cli`.

**Q: Test fails with path errors**  
A: Use `tmp_path` or `temp_project_dir` fixtures. Never use hardcoded paths.

**Q: Test fails because Resolve/FFmpeg not available**  
A: Mock external dependencies. Use `mock_resolve` or `mock_ffmpeg` fixtures.

---

## Summary

**Key Achievements**:
- ✅ Test infrastructure complete
- ✅ Hardcoded paths fixed
- ✅ Broken tests removed
- ✅ User-specific code archived
- ✅ All tests collectable
- ✅ Fixtures and utilities available

**Next Steps**:
1. Start with Phase 1: Foundation Layer (config, FFmpeg, media)
2. Follow the phase-by-phase plan
3. Use the fixtures and patterns provided
4. Aim for 95%+ coverage on rough cut system, 85%+ overall

