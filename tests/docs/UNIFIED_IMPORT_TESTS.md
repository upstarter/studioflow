# Unified Import Pipeline Tests

## Overview

Comprehensive test suite for the unified import pipeline, covering:
- **E2E Tests**: Full pipeline from ingest to ready-to-edit project
- **Unit Tests**: Individual components and methods

## Test Files

### `test_unified_import_e2e.py`
End-to-end tests for the complete pipeline workflow.

**Test Classes:**
- `TestUnifiedImportPipeline`: Full E2E tests

**Key Tests:**
- `test_phase1_immediate_processing`: Tests Phase 1 (Import, Normalize, Proxies)
- `test_phase2_background_processing`: Tests Phase 2 (Transcription, Markers)
- `test_full_pipeline_e2e`: Tests complete pipeline (all phases)
- `test_project_selection_priority`: Tests project selection logic
- `test_library_path_handling`: Tests library path configuration
- `test_error_handling_non_critical`: Tests error recovery
- `test_phased_processing_flags`: Tests phased processing flags

**Markers:**
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.requires_ffmpeg`: Requires FFmpeg
- `@pytest.mark.slow`: Slow tests

### `test_unified_import_unit.py`
Unit tests for individual components.

**Test Classes:**
- `TestProjectSelection`: Project selection logic
- `TestLibraryPathHandling`: Library path configuration
- `TestPhasedProcessing`: Phased processing methods
- `TestErrorHandling`: Error handling and recovery
- `TestResolveSetup`: Resolve project setup

**Markers:**
- `@pytest.mark.unit`: Unit tests (fast, no external dependencies)

## Running Tests

### Run All Tests
```bash
# All unified import tests
pytest tests/test_unified_import_*.py -v

# E2E tests only
pytest tests/test_unified_import_e2e.py -v -m e2e

# Unit tests only
pytest tests/test_unified_import_unit.py -v -m unit
```

### Run Specific Test
```bash
# Specific test class
pytest tests/test_unified_import_e2e.py::TestUnifiedImportPipeline -v

# Specific test method
pytest tests/test_unified_import_e2e.py::TestUnifiedImportPipeline::test_phase1_immediate_processing -v
```

### Run with Coverage
```bash
pytest tests/test_unified_import_*.py --cov=studioflow.core.unified_import --cov-report=html
```

## Test Fixtures

Tests use the following fixtures (from `conftest.py`):
- `temp_project_dir`: Temporary project directory
- `test_output_dir`: Persistent output directory for inspection
- `mock_config`: Mock configuration
- `mock_ffmpeg`: Mock FFmpeg processor
- `mock_resolve`: Mock DaVinci Resolve API

## Test Data

Tests use original clips with markers from:
- `tests/fixtures/test_footage/*original-markers.*`
  - `CAMA-C0176-original-markers.MP4` (FX30)
  - `CAMB-C0030-original-markers.MP4` (ZV-E10)

These clips contain audio markers for testing segment extraction.

## Expected Behavior

### Phase 1 (Immediate)
- ✅ Files imported to project
- ✅ Audio normalized to -14 LUFS
- ✅ Proxies generated
- ✅ Project structure created

### Phase 2 (Background)
- ✅ Transcripts generated (JSON + SRT)
- ✅ Audio markers detected
- ✅ Segments extracted
- ✅ Segment info saved

### Phase 3 (On-Demand)
- ✅ Rough cut generated (EDL)
- ✅ Resolve project created (if Resolve running)
- ✅ Bins created
- ✅ Media imported to Resolve

## Test Output

E2E tests save output to:
- `tests/output/test_run_*/`: Test run output
  - `e2e_summary.json`: Test summary
  - Project structure: Full project directory

## Troubleshooting

### Tests Fail with "No original clips found"
- Ensure test fixtures exist in `tests/fixtures/test_footage/`
- Check for `*original-markers.*` files

### Tests Fail with FFmpeg Errors
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check `@pytest.mark.requires_ffmpeg` marker

### Tests Fail with Resolve Errors
- Resolve tests are optional (skip if Resolve not running)
- Use `--no-resolve` flag or skip Resolve tests

### Tests Timeout
- E2E tests are slow (transcription, marker detection)
- Use `-m "not slow"` to skip slow tests
- Run unit tests separately: `pytest -m unit`

## Continuous Integration

Tests are designed to run in CI/CD:
- Unit tests: Fast, no external dependencies
- E2E tests: May require FFmpeg, can skip Resolve
- Markers allow selective test execution

## Next Steps

1. **Add More Test Cases:**
   - Multicam workflow
   - Error recovery scenarios
   - Edge cases (empty clips, invalid markers)

2. **Performance Tests:**
   - Large file handling
   - Concurrent processing
   - Memory usage

3. **Integration Tests:**
   - Full SD card workflow
   - Network storage
   - Resolve API integration


