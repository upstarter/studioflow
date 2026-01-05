# Ultimate Fixture Footage Creation Guide

This guide will help you create the comprehensive test fixture footage for StudioFlow.

## Quick Start

1. **Read the specification**: `tests/docs/ULTIMATE_FIXTURE_FOOTAGE.md`
2. **Get the recording script**: 
   ```bash
   python3 scripts/create_ultimate_fixture.py script > recording_script.txt
   ```
3. **Record the footage** following the script
4. **Validate** using the checklist:
   ```bash
   python3 scripts/create_ultimate_fixture.py checklist
   ```
5. **Test the fixture**:
   ```bash
   python3 test_unified_pipeline_fixtures.py
   ```

## Recording Tips

### Equipment
- Use FX30 or ZV-E10 camera (or any camera with good audio)
- Record in a quiet environment
- Use external microphone if available for best transcription quality

### Speaking
- **Speak clearly** - enunciate each word
- **Pause briefly** after saying "slate" and "done"
- **Provide content** - at least 5 seconds of speaking between markers
- **Use exact commands** - follow the script exactly

### Marker Format
Every marker follows this pattern:
```
[Slate] <command> [Done]
```

Examples:
- `slate scene one intro done`
- `slate mark done`
- `slate apply best done`
- `slate apply conclusion done`

## Expected Results

After processing, you should see:

### Segments Created (6 total)
1. **Segment 001**: scene 1, intro (starts at first scene marker)
2. **Segment 002**: mark (starts at mark marker), **scored "best"** (retroactive)
3. **Segment 003**: scene 2, main (starts at second scene marker)
4. **Segment 004**: step 1, setup (starts at step one marker)
5. **Segment 005**: step 2, execute (starts at step two marker)
6. **Segment 006**: effect zoom (starts at effect marker), **marked "conclusion"** (retroactive)

### Important Notes
- **No segment 007** - The "ending" marker does NOT create a segment
- **Retroactive markers** apply to the previous segment, not create new ones
- **Last segment** extends to the natural end of the video (not cut off)

## File Naming

Save your fixture as:
```
TEST-FIXTURE-comprehensive-markers.MP4
```

Place it in:
```
tests/fixtures/test_footage/
```

## Validation Checklist

After recording, verify:

- [ ] File is 30-90 seconds long
- [ ] All marker commands are clearly audible
- [ ] "slate" and "done" words are detected
- [ ] At least 5 seconds of content between markers
- [ ] All retroactive actions use "apply" (not deprecated "ending")
- [ ] File plays correctly in a video player

## Testing

Run the test suite:
```bash
python3 test_unified_pipeline_fixtures.py
```

Expected test results:
- [ ] 6 segments created (not 7)
- [ ] Segment 002 is scored "best"
- [ ] Segment 006 is marked "conclusion"
- [ ] No segment created after "ending" marker
- [ ] All markers detected correctly
- [ ] Transcription is accurate

## Troubleshooting

### Transcription Issues
- **Problem**: Markers not detected
- **Solution**: Speak more clearly, ensure quiet environment, check audio levels

### Segment Count Wrong
- **Problem**: Wrong number of segments
- **Solution**: Verify marker commands are exact, check transcription output

### Black Video
- **Problem**: Segments are black
- **Solution**: Ensure source video has content, check FFmpeg processing logs

## Next Steps

Once your fixture is validated:
1. Replace old fixtures (keep as backup)
2. Update test expectations if needed
3. Run full test suite to ensure everything works
4. Document any issues or improvements

## Reference

- **Full Specification**: `tests/docs/ULTIMATE_FIXTURE_FOOTAGE.md`
- **Helper Script**: `scripts/create_ultimate_fixture.py`
- **Test Runner**: `test_unified_pipeline_fixtures.py`

