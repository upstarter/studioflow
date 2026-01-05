# Production Test Output Verification

## Test Run Location

**Project:** `production_verification-20260104_Import`  
**Path:** `/mnt/dev/studioflow/tests/output/unified_pipeline/projects/20260104_production_verification-20260104_Import`

## What Was Created

### 1. Original Media
**Location:** `01_Media/Original/FX30/`
- Original video files copied from ingest pool
- Preserves original quality and metadata

### 2. Normalized Media  
**Location:** `01_Media/Normalized/`
- Audio normalized to -14 LUFS (YouTube standard)
- Files named: `{original_name}_normalized.MP4`
- **Verify:** Play normalized files and check audio levels are consistent

### 3. Transcripts
**Location:** `02_Transcription/`
- **JSON files:** `{clip_name}_transcript.json`
  - Contains word-level timestamps (needed for marker detection)
  - Full text transcription
- **SRT files:** `{clip_name}.srt`
  - Subtitle format for video players
- **Verify:** 
  - Open JSON files and check `words` array has timestamps
  - Check that "slate" markers are present in text
  - Verify SRT files are readable in video players

### 4. Segments
**Location:** `03_Segments/`
- **JSON files:** `{clip_name}_segments.json`
  - Contains segment boundaries based on audio markers
  - Each segment has `start`, `end`, and `marker_info`
- **Verify:**
  - Check segments start/end times are correct
  - Verify segments don't overlap
  - Check that segments align with "slate" markers in transcript

### 5. Rough Cut
**Location:** `04_Timelines/`
- **EDL file:** `rough_cut.edl`
  - Edit Decision List format
  - Can be imported into DaVinci Resolve or other NLEs
- **Verify:**
  - EDL file exists and is readable
  - Contains references to normalized media files

## Verification Steps

### Step 1: Check Audio Normalization
```bash
# Play normalized files and verify audio levels
mpv /mnt/studio/PROJECTS/20260104_production_verification-20260104_Import/01_Media/Normalized/*.MP4
```
**Expected:** Audio should be at consistent level (-14 LUFS), no clipping

### Step 2: Verify Transcripts
```bash
# Check transcript JSON structure
cat /mnt/studio/PROJECTS/20260104_production_verification-20260104_Import/02_Transcription/*_transcript.json | jq '.words[0:5]'
```
**Expected:** Should show word objects with `word`, `start`, `end` fields

### Step 3: Verify Marker Detection
```bash
# Check segments file
cat /mnt/studio/PROJECTS/20260104_production_verification-20260104_Import/03_Segments/*_segments.json | jq '.markers, .segments | length'
```
**Expected:** Should show markers detected and segments extracted

### Step 4: Verify Segment Cut Points
```bash
# Check segment boundaries
cat /mnt/studio/PROJECTS/20260104_production_verification-20260104_Import/03_Segments/*_segments.json | jq '.segments[] | {start, end, duration: (.end - .start)}'
```
**Expected:** 
- Segments should start after "done" (with padding)
- Segments should end before next "slate" (with padding)
- No overlapping segments

### Step 5: Verify Rough Cut
```bash
# Check EDL file
head -20 /mnt/studio/PROJECTS/20260104_production_verification-20260104_Import/04_Timelines/rough_cut.edl
```
**Expected:** EDL should contain timeline entries with file paths and timecodes

## Manual Verification

### Watch Normalized Clips
1. Open normalized files in video player
2. Verify audio is normalized (consistent levels)
3. Check that video quality is preserved

### Check Transcript Accuracy
1. Play video with SRT subtitles
2. Verify transcription matches spoken words
3. Check that "slate" markers are transcribed correctly

### Verify Segment Cut Points
1. Open original video
2. Check transcript JSON for "slate" marker timestamps
3. Compare with segment start/end times in segments.json
4. Verify segments start after "done" and end before next "slate"

### Test Rough Cut in Resolve
1. Import EDL into DaVinci Resolve
2. Verify timeline is created correctly
3. Check that clips reference normalized media
4. Play timeline and verify cuts are at correct points

## Expected Results

For `CAMB-C0030-original-markers.MP4`:
- **Markers detected:** 7
- **Segments extracted:** 7
- **Rough cut:** Created with 7 segments

## Troubleshooting

### No Markers Detected
- Check transcript JSON contains "slate" in text
- Verify word timestamps are present
- Check marker detection logs

### Segments Not Extracted
- Verify markers were detected first
- Check segments.json file exists
- Verify segment boundaries are valid

### Rough Cut Not Created
- Check segments were extracted
- Verify EDL file was generated
- Check rough cut engine logs


