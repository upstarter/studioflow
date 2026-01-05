# Sample Documentary Test Dataset

This directory contains sample test data for rough cut integration tests.

## Structure

- `interview1.mp4` / `interview1.srt` - Sample interview clip with transcript
- `interview2.mp4` / `interview2.srt` - Another interview clip
- `broll1.mp4`, `broll2.mp4`, etc. - B-roll footage clips
- `ground_truth.edl` - Manual rough cut for comparison
- `manual_edit_notes.md` - Notes about manual edit decisions

## Usage

These fixtures are used by integration tests to validate:
- Full pipeline workflow
- Narrative arc structure
- Thematic grouping
- B-roll matching
- Duplicate detection
- Continuous clip preservation

## Generating Test Data

For real testing, replace placeholder files with actual video clips and transcripts.
The test framework will create temporary files if these don't exist.

