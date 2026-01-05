# Test Fixtures

## Overview

This directory contains test fixtures for the StudioFlow test suite. **Large video files are NOT tracked in git** to keep the repository size manageable.

## File Organization

### Video Files (Not in Git)

Large video files (`.MP4`, `.mov`, `.mkv`, etc.) are excluded from git via `.gitignore`. These files should be stored locally for testing but not committed to the repository.

**Location:** Files remain in `tests/fixtures/test_footage/` but are not tracked by git.

### Metadata Files (Tracked in Git)

The following files ARE tracked in git:
- `*.json` - Transcripts and metadata
- `*.srt`, `*.vtt`, `*.txt` - Subtitle files
- `*.md` - Documentation
- `README.md` - This file

## Getting Test Fixtures

### Option 1: Use Existing Files (Recommended)

If you have access to the original test footage:
1. Place video files in `tests/fixtures/test_footage/`
2. Files will be automatically ignored by git
3. Tests will use them when present

### Option 2: Download from NAS

Original test footage is stored on NAS:
```bash
# Copy from NAS to fixtures
cp /mnt/nas/Scratch/Ingest/2026-01-04/fixtures/*.MP4 tests/fixtures/test_footage/
```

### Option 3: Record New Test Footage

If you need to create new test fixtures:
1. Record footage with audio markers (see `AUDIO_MARKERS_BEST_PRACTICES.md`)
2. Place in `tests/fixtures/test_footage/`
3. Files will be automatically ignored by git

## Test Output

Test output is stored in `/mnt/dev/studioflow/tests/output/` and is also excluded from git. The structure is organized as follows:

```
tests/output/
  unified_pipeline/          # Unified import pipeline test outputs
    projects/               # Full test project structures
    summaries/              # Test summary JSON files
  e2e_test_runs/            # End-to-end test run outputs (timestamped)
    test_run_YYYYMMDD_HHMMSS/
      segments/
      transcripts/
      normalized/
      project_output/
  legacy/                   # Old test projects (for reference)
```

## Running Tests Without Fixtures

If test fixtures are not available, tests will:
- Skip with a clear message
- Still run unit tests (which don't require fixtures)
- Allow you to verify logic without large files

## Fixture Requirements

### For E2E Tests

E2E tests require original clips with audio markers:
- `*original-markers.MP4` - Clips with audio markers
- `*original-no-markers.MP4` - Clips without markers (optional)

### For Unit Tests

Unit tests use mocks and don't require actual video files.

## File Naming Convention

- `CAMA-*` - FX30 camera footage
- `CAMB-*` - ZV-E10 camera footage
- `*original-markers.*` - Original clips with audio markers
- `*original-no-markers.*` - Original clips without markers
- `*seg*.mov` - Pre-split segments (for reference)

## Storage Recommendations

For production use:
- Store test fixtures on NAS: `/mnt/nas/Scratch/Ingest/YYYY-MM-DD/fixtures/`
- Keep local copies in `tests/fixtures/test_footage/` for development
- Don't commit large files to git (already configured in `.gitignore`)


