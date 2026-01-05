# Test Footage Fixtures

Test clips extracted from recorded footage for comprehensive test suite coverage.

## Format

**Container**: MOV (QuickTime)  
**Video**: H.264 (copied from source, no re-encoding)  
**Audio**: PCM (Linear PCM, lossless, preserved from source)

**Why MOV?**
- ✅ Perfect PCM audio compatibility with mpv and other players
- ✅ Lossless remux (no quality loss, just container change)
- ✅ Standard format for professional video workflows
- ✅ Works with all testing tools (FFmpeg, mpv, DaVinci Resolve)

**Note**: Original MP4 files had PCM audio which doesn't play in mpv. MOV format solves this while preserving lossless audio quality.

## Clips from C0176.MP4 (Comprehensive Marker Test)

1. **C0176-00.00.06.187-00.00.22.528-seg1.mov** (281MB, ~16s)
   - Full introduction segment from first START marker to END marker
   - Tests: START/END pair, full segment extraction

2. **C0176-00.00.20.116-00.00.38.062-seg2.mov** (306MB, ~18s)
   - Topic one segment with order command
   - Tests: START marker with order, segment between markers

3. **C0176-00.00.35.835-00.00.47.681-seg3.mov** (215MB, ~12s)
   - Standalone mark segment
   - Tests: STANDALONE marker extraction

4. **C0176-00.00.46.691-00.01.02.161-seg4.mov** (273MB, ~15s)
   - Topic two segment with order command
   - Tests: START marker with order, sequential markers

5. **C0176-00.01.00.679-00.01.16.341-seg5.mov** (276MB, ~16s)
   - Step one segment
   - Tests: START marker with step command

6. **C0176-00.01.13.588-00.01.28.389-seg6.mov** (260MB, ~15s)
   - Effect zoom segment (standalone)
   - Tests: STANDALONE marker with effect command

7. **C0176-00.01.25.382-00.01.47.107-seg7.mov** (372MB, ~22s)
   - Conclusion segment
   - Tests: END marker, final segment

## Usage in Tests

These clips can be used to test:
- Marker detection accuracy
- Segment extraction precision
- Command parsing
- Rough cut generation
- Timeline creation

## Notes

- All clips manually edited in LosslessCut for precise cuts
- Remuxed to MOV format for mpv compatibility (lossless, no re-encoding)
- PCM audio preserved (lossless, matches original camera recording)
- File sizes are larger due to lossless PCM audio (48kHz, 24-bit, stereo)
- Timestamps in filenames show exact cut points (HH:MM:SS.mmm format)

