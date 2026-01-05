# Test Fixtures Guide

Complete guide for creating and using test video clips for StudioFlow testing.

## Overview

This guide covers camera settings, recording procedures, required clips, and best practices for creating test fixtures with FX30 and ZVE10 cameras.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Camera Settings](#camera-settings)
3. [Priority Clips](#priority-clips)
4. [Recording Procedure](#recording-procedure)
5. [Filenaming Conventions](#filenaming-conventions)
6. [Post-Processing](#post-processing)

---

## Quick Start

### Minimum Required Clips (Start Here)

If you can only create 1-2 clips, these provide maximum test coverage:

1. **Comprehensive Marker Test** (FX30, ~90s)
   - Tests all marker types in one clip
   - Filename: `TEST_MARKER_comprehensive_FX30.mp4`
   - See [Priority Clips](#priority-clips) for script

2. **Talking Head Baseline** (FX30, ~60s)
   - Tests transcript analysis without markers
   - Filename: `TEST_CAMERA_talking_head_baseline_FX30.mp4`
   - Natural speech, no markers

### Recording Checklist

**Before Recording**:
- [ ] Camera settings configured (see [Camera Settings](#camera-settings))
- [ ] Audio levels checked (-12dB to -6dB)
- [ ] Good lighting
- [ ] Quiet environment
- [ ] Script ready

**During Recording**:
- [ ] Say "slate" clearly
- [ ] Pause 0.5-1s after "slate"
- [ ] Say commands clearly
- [ ] Say "done" clearly
- [ ] Wait 1-2s after "done" before content

**After Recording**:
- [ ] Verify file saved
- [ ] Check audio in playback
- [ ] Rename to standard convention
- [ ] Organize in `tests/fixtures/test_footage/`

---

## Camera Settings

### FX30 Settings (Recommended)

#### Video Settings
- **Format**: XAVC S 4K ✅ (RECOMMENDED)
  - OR XAVC S-I HD (alternative: 10-bit 4:2:2)
- **Resolution**: 4K UHD (3840x2160)
- **Frame Rate**: 30p
- **Bitrate**: 100Mbps

#### Picture Profile (CRITICAL)
- **Profile**: PP10 (S-Cinetone) ✅ (RECOMMENDED)
  - Ready to view, no LUT needed
- **Log Shooting**: **OFF** ✅ (CRITICAL!)
  - Menu → Image Quality/Rec → Log Shooting Setting → Log Shooting: OFF
  - If ON, it uses S-Log3 even with PP10

#### Audio Settings
- **Audio Recording**: ON
- **Audio Format**: Linear PCM (48kHz, 24-bit) ✅ (BEST for marker detection)
- **Audio Level**: -12dB to -6dB (manual)
- **Wind Noise Reduction**: OFF

#### Focus & Exposure
- **Focus Mode**: Manual Focus (MF) ✅
- **ISO**: 100-400 (for S-Cinetone)
- **Shutter**: 1/60s (for 30fps)
- **White Balance**: AWB (Auto)

#### Menu Navigation (Do in Order)
1. Menu → Shooting → ISO → ISO Mode → **Flexible ISO** ✅
2. Menu → Image Quality/Rec → **Log Shooting Setting** → **Log Shooting: OFF** ✅
3. Menu → Shooting → Picture Profile → **PP10 (S-Cinetone)** ✅
4. Menu → Shooting → File Format → **XAVC S 4K** ✅
5. Menu → Shooting → Record Setting → **30p 100M** ✅
6. Menu → Audio → Audio Recording → **ON** ✅
7. Menu → Audio → Audio Format → **Linear PCM** ✅
8. Menu → Focus → Focus Mode → **Manual Focus** ✅

### ZVE10 Settings

#### Video Settings
- **Format**: XAVC S 4K (or HD)
- **Resolution**: 4K UHD (3840x2160) or 1080p
- **Frame Rate**: 30p
- **Bitrate**: 100Mbps (4K) or 50Mbps (1080p)

#### Picture Profile
- **Profile**: PP10 (S-Cinetone) ✅

#### Audio Settings
- **Audio Recording**: ON
- **Audio Format**: Linear PCM (48kHz, 24-bit) ✅
- **Audio Level**: -12dB to -6dB
- **Mic Direction**: Front

#### Focus & Exposure
- **Focus Mode**: Continuous AF (Product Showcase) ✅
- **ISO**: Auto (or 100-400)
- **Shutter**: 1/60s (for 30fps)
- **White Balance**: AWB (Auto)

---

## Priority Clips

### Clip 1: Comprehensive Marker Test (HIGHEST VALUE)

**Camera**: FX30  
**Duration**: ~90 seconds  
**Filename**: `TEST_MARKER_comprehensive_FX30.mp4`

**Script**:
```
[0:00] Say: "slate naming introduction done"
[Pause 2s]
[0:02-0:12] Speak: "This is an introduction to our comprehensive test. We're testing multiple marker types and scenarios in a single clip."

[0:12] Say: "slate naming topic one order 1 done"
[Pause 2s]
[0:14-0:24] Speak: "This is topic one. It's the first subject we're discussing. This content is important for testing."

[0:24] Say: "slate mark done"
[Pause 1s]
[0:25-0:30] Speak: "This is a standalone marker test. It creates a jump cut point."

[0:30] Say: "slate naming topic two order 2 done"
[Pause 2s]
[0:32-0:42] Speak: "This is topic two. It's the second subject. We're testing sequential markers here."

[0:42] Say: "slate naming step one step 1 done"
[Pause 2s]
[0:44-0:54] Speak: "This is step one of our tutorial. First, we need to understand the basics."

[0:54] Say: "slate effect zoom done"
[Pause 1s]
[0:55-1:00] Speak: "This marker has an effect command. It should be detected and applied."

[1:00] Say: "slate ending conclusion done"
[Pause 2s]
[1:02-1:12] Speak: "This is our conclusion. We've tested multiple marker types including START, END, and standalone markers."
```

**What This Tests**:
- ✅ Marker detection (START, END, standalone)
- ✅ Command parsing (naming, order, step, effect, ending)
- ✅ Segment extraction
- ✅ Marker ordering
- ✅ Full marker-to-segment pipeline

### Clip 2: Talking Head Baseline

**Camera**: FX30  
**Duration**: ~60 seconds  
**Filename**: `TEST_CAMERA_talking_head_baseline_FX30.mp4`

**Script** (NO MARKERS - just natural speech):
```
[0:00-0:10] "In 2024, we saw a significant increase in climate change awareness. The data shows a 50% increase in public concern."

[0:10-0:20] "The problem we face is serious. We need immediate action to address this crisis. Scientists agree that time is running out."

[0:20-0:30] "The solution is clear. We must reduce emissions by 50% by 2030. This requires cooperation from governments, businesses, and individuals."

[0:30-0:40] "I remember when we first noticed the changes. It was in 2020 when the wildfires became more frequent and intense."

[0:40-0:50] "What can we do? We can start by making small changes in our daily lives. Every action counts."

[0:50-1:00] "In conclusion, we must work together to solve this challenge. The future depends on our actions today."
```

**What This Tests**:
- ✅ Transcript analysis
- ✅ Quote extraction
- ✅ Importance scoring
- ✅ Sentiment analysis
- ✅ Non-marker workflow

### Additional Priority Clips

#### Clip 3: Basic START/END Pair
- **Say**: `"slate naming introduction done"`
- **Speak 10s**
- **Say**: `"slate ending conclusion done"`
- **File**: `TEST_MARKER_basic_start_end_FX30.mp4`

#### Clip 4: Multiple START/END Pairs
- **Say**: `"slate naming topic one done"`
- **Speak 15s**
- **Say**: `"slate naming topic two done"`
- **Speak 15s**
- **Say**: `"slate ending final thoughts done"`
- **File**: `TEST_MARKER_multiple_pairs_FX30.mp4`

#### Clip 5: ZVE10 B-Roll
- **No speech**, visual content only
- **30-60 seconds**
- **File**: `TEST_CAMERA_broll_ZVE10.mp4`

---

## Recording Procedure

### Step 1: Setup

1. **Configure Camera** (see [Camera Settings](#camera-settings))
2. **Check Audio Levels**: -12dB to -6dB
3. **Set Focus**: Manual for FX30, Continuous AF for ZVE10
4. **Verify Settings**: PP10, Linear PCM, correct format

### Step 2: Record Priority Clips

Follow the scripts in [Priority Clips](#priority-clips) section.

### Step 3: Marker Pronunciation Tips

- **"slate"**: Say clearly, pause 0.5-1s after
- **Commands**: Say at normal pace, clearly
- **"done"**: Say clearly, wait 1-2s before content
- **Content**: Speak naturally after "done"

### Step 4: Quality Checks

After each clip:
- [ ] Verify file saved (check camera display)
- [ ] Note original filename (C####.MP4 or DSC#####.MP4)
- [ ] Check audio in playback
- [ ] Verify markers are audible

### Step 5: File Management

1. **Rename files** to standard convention (see [Filenaming Conventions](#filenaming-conventions))
2. **Organize** in `tests/fixtures/test_footage/`
3. **Create manifest** file listing all clips

---

## Filenaming Conventions

### Standard Format

```
TEST_[CATEGORY]_[DESCRIPTION]_[CAMERA].mp4
```

### Categories

- **`MARKER`** - Audio marker tests
- **`CAMERA`** - Camera detection/content classification
- **`EDGE`** - Edge cases
- **`DOC`** - Documentary/interview
- **`BROLL`** - B-roll footage
- **`MULTICAM`** - Multi-camera
- **`TUTORIAL`** - Tutorial/educational

### Examples

```
TEST_MARKER_basic_start_end_FX30.mp4
TEST_MARKER_comprehensive_FX30.mp4
TEST_CAMERA_talking_head_baseline_FX30.mp4
TEST_CAMERA_broll_ZVE10.mp4
TEST_EDGE_no_markers_FX30.mp4
TEST_DOC_interview_opening_FX30.mp4
```

### Keywords for Optimal Detection

#### Content Type
- `TALKING_HEAD`, `BROLL`, `INTERVIEW`, `TUTORIAL`, `SCREEN`

#### Topics
- `CLIMATE`, `TECH`, `PRODUCT`, `NATURE`, `INDOOR`

#### Steps/Order
- `STEP01`, `STEP02`, `PART1`, `PART2`, `SCENE01`

#### Quality
- `BEST`, `SELECT`, `HOOK`, `CTA`, `MISTAKE`, `DELETE`

---

## Post-Processing

### Format Recommendations

**Best Approach**: Use original camera files directly.

**If Conversion Needed**:
- **Container**: MOV or MKV (not MP4 with PCM audio)
- **Video**: Copy (no re-encoding)
- **Audio**: AAC 320kbps (not PCM - PCM causes compatibility issues)

### File Organization

```
tests/fixtures/test_footage/
├── TEST_MARKER_basic_start_end_FX30.mp4
├── TEST_MARKER_comprehensive_FX30.mp4
├── TEST_CAMERA_talking_head_baseline_FX30.mp4
├── TEST_CAMERA_broll_ZVE10.mp4
└── README.md (manifest)
```

### Manifest File

Create `tests/fixtures/test_footage/README.md`:

```markdown
# Test Footage Manifest

## Priority Clips

1. `TEST_MARKER_comprehensive_FX30.mp4` - Comprehensive marker test
2. `TEST_CAMERA_talking_head_baseline_FX30.mp4` - Talking head baseline

## Additional Clips

3. `TEST_MARKER_basic_start_end_FX30.mp4` - Basic START/END pair
...
```

---

## Quick Reference

### FX30 Quick Settings
```
Format: XAVC S 4K
Picture Profile: PP10 (S-Cinetone) ✅
Log Shooting: OFF ✅ (CRITICAL!)
Audio: Linear PCM, 48kHz, 24-bit
Audio Level: -12dB to -6dB
Focus: Manual Focus
ISO: 100-400
Shutter: 1/60s
```

### Marker Template
```
[Say] "slate"
[Pause 0.5-1s]
[Say commands] "naming introduction"
[Say] "done"
[Pause 1-2s]
[Start content - speak naturally]
```

### Recording Checklist
- [ ] Camera settings correct
- [ ] Audio levels checked
- [ ] Good lighting
- [ ] Quiet environment
- [ ] Script ready
- [ ] Say "slate" clearly
- [ ] Pause after "slate"
- [ ] Say "done" clearly
- [ ] Wait after "done" before content

---

## Summary

**Minimum Required**:
1. Comprehensive Marker Test (FX30, ~90s)
2. Talking Head Baseline (FX30, ~60s)

**Key Settings**:
- FX30: PP10 (S-Cinetone), Log Shooting OFF, Linear PCM
- ZVE10: PP10 (S-Cinetone), Linear PCM

**Best Practices**:
- Use original camera files
- Clear marker pronunciation
- Standard filenaming convention
- Organize in `tests/fixtures/test_footage/`

