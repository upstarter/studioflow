# YouTube Episode Guide - StudioFlow

**Complete workflow for creating YouTube tutorial episodes with StudioFlow**

This guide walks you through creating a YouTube episode from start to finish, leveraging StudioFlow's AI-powered features for maximum efficiency and quality.

---

## Quick Start (5 Minutes)

### Option 1: Audio Marker Workflow (Recommended) ⭐

**During recording**, use voice commands:
```
SLATE "naming intro mark order one done"
"...welcome to this tutorial..."
SLATE "ending mark cta subscribe done"
```

Then:
```bash
# 1. Create project
sf new "My Tutorial Episode"

# 2. Import footage (auto-detects project)
sf import /path/to/footage

# 3. Generate rough cut with audio markers
sf rough-cut --style tutorial --audio-markers

# 4. Import to Resolve and edit (fully automated!)
sf edit
```

### Option 2: Filename Convention Workflow

```bash
# 1. Create project
sf new "My Tutorial Episode"

# 2. Import footage (auto-detects project)
sf import /path/to/footage

# 3. Generate rough cut (auto-detects footage)
sf rough-cut --style tutorial

# 4. Generate hook tests for A/B testing
sf rough-cut hook-tests

# 5. Import to Resolve and edit
sf edit
```

**See**: [Audio Marker System Guide](AUDIO_MARKER_SYSTEM.md) for complete marker workflow

---

## Complete Workflow

### Phase 1: Preparation & Recording

#### 1.1 Name Your Footage (Critical!)

**Before recording**, plan your filename structure. StudioFlow automatically detects and optimizes based on filenames.

**Essential Naming Patterns:**

```
# Hook Options (record 3-5 different takes)
CAM_HOOK_CH_Secret_Reveal_BEST.mp4          # Curiosity Hook (1.3x boost)
CAM_HOOK_COH_Contrarian_Take.mp4            # Contrarian Hook (1.35x - highest!)
CAM_HOOK_PSH_Common_Mistake.mp4             # Problem-Solution Hook (1.2x)

# Screen Recordings (for tutorials)
SCREEN_STEP01_Installation.mov
SCREEN_STEP02_Configuration.mov
SCREEN_STEP03_Demo_Features.mp4

# Talking Head Explanations
CAM_STEP01_Explanation.mp4
CAM_STEP02_Why_This_Matters.mov

# B-Roll Support
BROLL_STEP01_Product_Shot.mp4
BROLL_STEP02_Environment.mov

# CTA/Outro
CAM_CTA_Subscribe.mp4
CAM_OUTRO_Summary.mov
```

**Key Points:**
- Use `SCREEN_` prefix for screen recordings
- Use `CAM_` prefix for camera/talking head
- Use `STEP##_` for tutorial steps (auto-generates chapters!)
- Use `HOOK_[FLOW]_` for hooks (CH, COH, PSH, etc. - see Hook Flows guide)
- Mark best takes with `BEST_` or `SELECT_`
- Mark mistakes with `MISTAKE_` (auto-excluded)

**See:** Complete filename convention details in [Advanced Features](#complete-filename-convention) section below

---

### Phase 2: Import & Organization

#### 2.1 Create Project

```bash
# Create new episode project
sf new "Python_Tutorial_Episode_01"

# Or use library workflow
sf library create "Python_Tutorial_Episode_01" --type episode
```

**Project Structure Created:**
```
Python_Tutorial_Episode_01/
├── 00_script/
├── 01_footage/
│   ├── A_ROLL/
│   ├── B_ROLL/
│   └── SCREEN_RECORDINGS/
├── 02_graphics/
├── 03_resolve/
│   ├── PROJECT/
│   ├── TIMELINES/
│   └── GRADES/
├── 04_audio/
├── 05_exports/
├── 06_transcripts/
└── 07_documents/
```

#### 2.2 Import Footage

```bash
# Auto-detects project and organizes footage
sf import /path/to/footage

# Or manually specify project
sf import /path/to/footage --project "Python_Tutorial_Episode_01"
```

**What Happens:**
- Files are copied to `01_footage/` with subfolder organization
- Screen recordings → `SCREEN_RECORDINGS/`
- Camera footage → `A_ROLL/`
- B-roll → `B_ROLL/`
- Filenames are parsed for metadata (steps, hooks, quality)

#### 2.3 Verify Organization

```bash
# Check project status
sf status

# Or browse media
sf media-org list --project "Python_Tutorial_Episode_01"
```

---

### Phase 3: Transcription & Analysis

#### 3.1 Auto-Transcription

StudioFlow automatically transcribes footage during rough cut generation, but you can pre-transcribe:

```bash
# Transcribe all footage in project
sf batch transcribe --project "Python_Tutorial_Episode_01"

# Or transcribe specific file
sf transcribe 01_footage/A_ROLL/CAM_HOOK_CH_BEST.mp4
```

**Output:** `.srt` files created alongside video files

#### 3.2 Verify Transcripts

```bash
# Check transcription status
sf status

# View transcript
cat 01_footage/A_ROLL/CAM_HOOK_CH_BEST.srt
```

---

### Phase 4: Rough Cut Generation

#### 4.1 Generate Tutorial Rough Cut

```bash
# Auto-detects footage and generates tutorial-optimized rough cut
sf rough-cut --style tutorial

# Or specify footage directory
sf rough-cut /path/to/footage --style tutorial

# With target duration (optional)
sf rough-cut --style tutorial --duration 10  # 10 minutes
```

**What StudioFlow Does:**
- ✅ Detects screen recordings vs talking head
- ✅ Identifies tutorial steps from filenames (`STEP01_`, `STEP02_`, etc.)
- ✅ Removes mistakes automatically (`MISTAKE_` prefix)
- ✅ Removes retakes (keeps best take)
- ✅ Creates aggressive jump cuts (removes silence, filler words)
- ✅ Matches screen recordings to explanations
- ✅ Generates chapter markers from steps
- ✅ Normalizes audio to -14 LUFS (YouTube standard)
- ✅ Optimizes for retention (first 15 seconds critical)

**Output:**
- `rough_cut_tutorial.edl` - Edit Decision List
- `rough_cut_tutorial.fcpxml` - FCPXML (better for Resolve)

#### 4.2 Preview Rough Cut

The system shows a preview before generating:

```
Rough Cut Preview - TUTORIAL

Total Duration: 8:45
Segments: 23
Steps Detected: 5

Generate EDL/FCPXML? [y/N]: y
```

**Review the preview** - Check segment counts, duration, structure before generating.

---

### Phase 5: Hook Testing (Optional but Recommended)

#### 5.1 Generate Hook Test Timelines

**Before finalizing your hook**, test multiple options to find the best performer:

```bash
# Generate 5 hook test timelines (default)
sf rough-cut hook-tests

# Generate more options
sf rough-cut hook-tests --max 10
```

**What This Does:**
- Analyzes all hook clips (prioritizes named hook flows)
- Generates separate timeline for each hook candidate
- Exports to `04_TIMELINES/02_HOOK_TESTS/`
- Creates metadata files with retention predictions

**Output Structure:**
```
04_TIMELINES/02_HOOK_TESTS/
├── HOOK_TEST_01_COH.fcpxml          # Contrarian Hook (1.35x multiplier)
├── HOOK_TEST_01_COH.edl
├── HOOK_TEST_01_COH_METADATA.txt
├── HOOK_TEST_02_CH.fcpxml           # Curiosity Hook (1.3x multiplier)
├── HOOK_TEST_02_CH.edl
├── HOOK_TEST_02_CH_METADATA.txt
├── HOOK_TEST_03_PSH.fcpxml          # Problem-Solution Hook (1.2x multiplier)
└── HOOK_TESTS_SUMMARY.txt
```

#### 5.2 Test Hooks on YouTube

1. **Import to Resolve:**
   ```bash
   # Open Resolve
   sf edit
   
   # In Resolve: File → Import → Timeline → Import AAF, EDL, XML, FCPXML...
   # Select all .fcpxml files from 04_TIMELINES/02_HOOK_TESTS/
   ```

2. **Render Each Hook Test:**
   - Render each timeline as 1080p, 16-20Mbps
   - Export to `05_exports/HOOK_TESTS/`

3. **Upload as Unlisted:**
   - Upload each hook test as unlisted YouTube video
   - Wait 24-48 hours for analytics

4. **Compare Retention:**
   - Check YouTube Analytics → Audience Retention
   - Compare first 15-second retention rates
   - Select best performing hook

5. **Use Best Hook:**
   - Use winning hook in final video
   - Delete test videos or keep for reference

**Pro Tip:** Name your hook clips with flow types (`HOOK_CH_`, `HOOK_COH_`, etc.) to get automatic prioritization and performance multipliers.

**See:** Complete hook flow details in [Advanced Features](#hook-flow-types-performance-multipliers) section below

---

### Phase 6: Import to DaVinci Resolve

#### 6.1 Open Project in Resolve

```bash
# Auto-opens Resolve with project
sf edit

# Or manually open Resolve and import
```

#### 6.2 Import Rough Cut Timeline

**In DaVinci Resolve:**

1. **File → Import → Timeline → Import AAF, EDL, XML, FCPXML...**
2. **Select:** `rough_cut_tutorial.fcpxml` (or `.edl`)
3. **Check:** "Import clips to Media Pool"
4. **Click:** "OK"

**What Gets Imported:**
- ✅ All clips organized into timeline
- ✅ Rough cut structure (hook, steps, CTA)
- ✅ In/out points set (but fully resizable!)
- ✅ Chapter markers from steps (if generated)

#### 6.3 Review Timeline

**Timeline Structure:**
- **Hook** (first 5-15 seconds)
- **Step 1** segments
- **Step 2** segments
- **Step 3** segments
- ...
- **CTA/Outro** (at end)

**All clips are fully resizable** - You can extend, trim, or adjust any clip. The rough cut is just a starting point!

---

### Phase 7: Refine Edit

#### 7.1 Adjust Rough Cut

- **Extend clips** if needed (handles included)
- **Trim segments** for better pacing
- **Reorder** if structure needs adjustment
- **Add B-roll** from Power Bins or project folders

#### 7.2 Add Graphics & Effects

- **Lower thirds** for step titles
- **Text overlays** for key points
- **Arrows/highlights** for screen recordings
- **Transitions** between steps

#### 7.3 Color Grade

```bash
# Apply color grade preset
sf resolve grade --preset "orange-teal"

# Or grade manually in Resolve
```

#### 7.4 Audio Mix

- **Music bed** (if using)
- **Sound effects** for transitions
- **Audio levels** (already normalized to -14 LUFS)
- **Final mix** check

---

### Phase 8: Export & Publish

#### 8.1 Export Final Video

```bash
# Export with YouTube optimization
sf export youtube --project "Python_Tutorial_Episode_01"

# Or export from Resolve manually
# Settings: 4K, 30-45Mbps, H.264, -14 LUFS audio
```

**Export Settings (Recommended):**
- **Resolution:** 3840x2160 (4K) or 1920x1080 (1080p)
- **Frame Rate:** 30fps or 60fps
- **Codec:** H.264
- **Bitrate:** 30-45Mbps (4K) or 16-20Mbps (1080p)
- **Audio:** -14 LUFS (already normalized)

#### 8.2 Generate YouTube Metadata

```bash
# Generate viral titles
sf youtube titles "Python Tutorial" --style educational

# Generate description with chapters
sf youtube description "Python Tutorial" --chapters
```

**Chapter Markers** (auto-generated from steps):
```
00:00 Introduction
00:15 Step 1: Installation
02:30 Step 2: Configuration
05:45 Step 3: Demo Features
08:20 Summary
09:00 Subscribe
```

#### 8.3 Upload to YouTube

```bash
# Upload with metadata
sf youtube upload final.mp4 \
  --title "Learn Python in 10 Minutes" \
  --description "description.txt" \
  --tags "python,tutorial,coding"
```

**Or upload manually:**
1. Go to YouTube Studio
2. Upload video
3. Paste title, description, chapters
4. Set thumbnail
5. Publish!

---

## Advanced Features

### Complete Filename Convention

StudioFlow automatically detects and optimizes based on filenames. Use these patterns:

#### Footage Type Prefixes

**Screen Recordings**: `SCREEN_` or `SCR_`
```
SCREEN_STEP01_Setup.mp4
SCREEN_Config_Database.mov
SCR_Demo_Feature_Walkthrough.mp4
```

**Camera Footage (Talking Head)**: `CAM_` or `CAMERA_` (or no prefix)
```
CAM_Introduction.mp4
CAMERA_STEP01_Explanation.mov
Intro_Hook_BEST.mp4  # No prefix = camera footage
```

**B-Roll Footage**: `BROLL_` or `B_`
```
BROLL_Product_Shot.mp4
B_Setup_Environment.mov
BROLL_STEP02_Supporting_Visual.mp4
```

**Graphics/Assets**: `GFX_` or `GRAPHICS_`
```
GFX_Logo_Animation.mov
GRAPHICS_Step_Number_01.mp4
GFX_Lower_Third_Template.mov
```

#### Episode Type Prefixes

**Review**: `REVIEW_`
```
REVIEW_Overview.mp4
REVIEW_Features_Display.mp4
REVIEW_Pros_List.mp4
REVIEW_Cons_Issues.mp4
REVIEW_Verdict_Conclusion.mp4
```

**Unboxing**: `UNBOX_`
```
UNBOX_Intro.mp4
UNBOX_Opening_Box.mp4
UNBOX_First_Look_Reaction.mp4
```

**Comparison**: `COMPARE_`
```
COMPARE_Intro.mp4
COMPARE_ProductA_Features.mp4
COMPARE_ProductB_Features.mp4
COMPARE_Winner_Conclusion.mp4
```

**Setup/Installation**: `SETUP_`
```
SETUP_Intro.mp4
SETUP_STEP01_Prerequisites.mp4
SETUP_STEP02_Installation.mp4
SETUP_Verification.mp4
```

**Explainer**: `EXPLAIN_`
```
EXPLAIN_Intro.mp4
EXPLAIN_Concept_Introduction.mp4
EXPLAIN_Explanation_Details.mp4
EXPLAIN_Examples.mp4
EXPLAIN_Summary.mp4
```

#### Hook Flow Types (Performance Multipliers)

**Contrarian Hook (COH)** - 1.35x multiplier ⭐ Highest
```
CAM_HOOK_COH_Contrarian_BEST.mp4
COH_HOOK_What_They_Dont_Tell_You.mov
```
**Example Script**: "Everyone says X, but they're wrong. Here's why..."

**Curiosity Hook (CH)** - 1.3x multiplier
```
CAM_HOOK_CH_Secret_Reveal.mp4
CH_HOOK_What_They_Dont_Tell_You.mov
```
**Example Script**: "One video changed everything for me, but it wasn't the one I expected."

**Action Hook (AH)** - 1.25x multiplier
```
CAM_HOOK_AH_Mid_Action.mp4
AH_HOOK_Real_Time_Demo.mov
```
**Example Script**: "It's 2 a.m. I just lost 43 subscribers in one hour—and I caused it."

**Problem-Solution Hook (PSH)** - 1.2x multiplier
```
CAM_HOOK_PSH_Common_Mistake.mp4
PSH_HOOK_Your_Intros_Killing_Watch_Time.mov
```
**Example Script**: "Your YouTube intros are killing your watch time—and you don't even know it."

**Time-Promise Hook (TPH)** - 1.15x multiplier
```
CAM_HOOK_TPH_60_Seconds.mp4
TPH_HOOK_In_Next_5_Minutes.mov
```
**Example Script**: "In the next 60 seconds, I'll show you exactly how to..."

**Statistic Hook (SH)** - 1.2x multiplier
```
CAM_HOOK_SH_90_Percent.mp4
SH_HOOK_Shocking_Number.mov
```
**Example Script**: "90% of creators make this mistake in their first 10 seconds."

**Question Hook (QH)** - 1.15x multiplier
```
CAM_HOOK_QH_What_If.mp4
QH_HOOK_Do_You_Know.mov
```
**Example Script**: "What if I told you everything you know about editing is wrong?"

#### Quality Markers

- `BEST_` - Best take (highest priority)
- `SELECT_` - Selected/approved
- `HERO_` - Hero shot
- `TEST_` - Test footage (lower priority)
- `MISTAKE_` - Auto-excluded mistake

#### Step Organization

- `STEP01_` - Step 1 (auto-generates chapters!)
- `STEP02_` - Step 2
- `STEP03_` - Step 3

#### Take Numbers

- `(1)`, `(2)`, `(3)` - Numbered takes (kept as distinct takes)
- `_TAKE2`, `_TAKE3` - Alternative take notation

**Note**: Numbered takes like `VID_20251230_081950 (1).mov` are kept as distinct takes. Only `_normalized` duplicates are removed if a non-normalized original exists.

### Removed Footage Review

StudioFlow tracks all removed segments. Review them to ensure nothing good was cut:

```bash
# After rough cut generation, check removed footage
cat rough_cut_REMOVED.edl

# Or generate removed footage transcript
# (available in rough cut output)
```

**Removed Footage Includes:**
- Transcript of removed content
- Reason for removal (low_score, duration_limit, etc.)
- Visual descriptions (if available)
- Source tape EDL for review

### Audio Normalization

All clips are automatically normalized to **-14 LUFS** (YouTube standard) during analysis. No manual audio leveling needed!

**See:** [Audio Normalization Guide](AUDIO_NORMALIZATION.md)

### Screen Recording Intelligence

StudioFlow automatically:
- ✅ Detects screen recordings (`SCREEN_` prefix)
- ✅ Handles differently from talking head (less aggressive cutting)
- ✅ Matches to explanations in transcript
- ✅ Organizes by step number

### Mistake Detection

Automatically removes:
- ✅ Clips marked `MISTAKE_` or `DELETE_`
- ✅ Correction phrases ("wait", "actually", "let me redo")
- ✅ Retakes (keeps best take)
- ✅ Long pauses (>3s)
- ✅ Filler word clusters

---

## Episode Types

StudioFlow supports multiple episode types, each optimized for specific content styles:

### Product Reviews (`--style review`)

**Best for**: In-depth product analysis, feature breakdowns, pros/cons

**Features**:
- Automatic feature mention detection
- Pros/cons statement identification
- Verdict optimization
- B-roll matching to feature descriptions

**Filename Convention**:
```
REVIEW_Overview.mp4
REVIEW_Features_Display.mp4
REVIEW_Pros_List.mp4
REVIEW_Cons_Issues.mp4
REVIEW_Verdict_Conclusion.mp4
```

**Usage**:
```bash
sf rough-cut --style review
```

### Unboxing Videos (`--style unboxing`)

**Best for**: First impressions, product reveals, reaction videos

**Features**:
- Reveal moment detection ("wow", "look at this")
- Reaction prioritization
- Maintains unboxing sequence order
- Fast-paced editing

**Filename Convention**:
```
UNBOX_Intro.mp4
UNBOX_Opening_Box.mp4
UNBOX_First_Look_Reaction.mp4
UNBOX_Initial_Thoughts.mp4
```

**Usage**:
```bash
sf rough-cut --style unboxing
```

### Comparison Videos (`--style comparison`)

**Best for**: Side-by-side product comparisons, "vs" videos

**Features**:
- Comparison statement detection ("vs", "better than")
- Product switching (alternates between Product A and B)
- Specification extraction
- Comprehensive coverage (60% retention)

**Filename Convention**:
```
COMPARE_Intro.mp4
COMPARE_ProductA_Features.mp4
COMPARE_ProductB_Features.mp4
COMPARE_SideBySide_Analysis.mp4
COMPARE_Winner_Conclusion.mp4
```

**Usage**:
```bash
sf rough-cut --style comparison
```

### Setup/Installation Guides (`--style setup`)

**Best for**: Step-by-step setup, configuration, installation tutorials

**Features**:
- Step detection and organization
- Screen recording prioritization
- Command/code snippet extraction
- Methodical pacing

**Filename Convention**:
```
SETUP_Intro.mp4
SETUP_STEP01_Prerequisites.mp4
SETUP_STEP02_Installation.mp4
SETUP_STEP03_Configuration.mp4
SETUP_Verification.mp4
```

**Usage**:
```bash
sf rough-cut --style setup
```

### Explainer Videos (`--style explainer`)

**Best for**: Concept breakdowns, educational content, "how it works" videos

**Features**:
- Concept introduction detection ("let me explain", "here's how")
- Example segment identification
- Visual aid matching
- Slower, educational pacing (70% retention)

**Filename Convention**:
```
EXPLAIN_Intro.mp4
EXPLAIN_Concept_Introduction.mp4
EXPLAIN_Explanation_Details.mp4
EXPLAIN_Examples.mp4
EXPLAIN_Summary.mp4
```

**Usage**:
```bash
sf rough-cut --style explainer
```

### Choosing the Right Style

| Episode Type | Style | Pacing | Retention | Best For |
|-------------|-------|--------|-----------|----------|
| Tutorial | `tutorial` | Very Fast | 30% | Step-by-step tutorials |
| Product Review | `review` | Medium-Fast | 50% | Product analysis |
| Unboxing | `unboxing` | Fast | 40% | First impressions |
| Comparison | `comparison` | Medium | 60% | Side-by-side analysis |
| Setup Guide | `setup` | Medium | 50% | Installation/config |
| Explainer | `explainer` | Slow-Medium | 70% | Concept education |
| Documentary | `doc` | Slow | 80% | Story-driven content |
| Interview | `interview` | Medium | 50% | Q&A format |
| Episode | `episode` | Fast | 40% | General YouTube content |

---

## Workflow Summary

### Complete Command Sequence

```bash
# 1. Create project
sf new "My_Tutorial_Episode"

# 2. Import footage (with proper naming)
sf import /path/to/footage

# 3. Generate rough cut
sf rough-cut --style tutorial --duration 10

# 4. Generate hook tests (optional)
sf rough-cut hook-tests --max 5

# 5. Open in Resolve
sf edit

# 6. (In Resolve) Import rough_cut_tutorial.fcpxml
# 7. (In Resolve) Refine edit, add graphics, grade
# 8. (In Resolve) Export final video

# 9. Generate YouTube metadata
sf youtube titles "My Topic" --style educational

# 10. Upload to YouTube
sf youtube upload final.mp4 --title "My Title"
```

### Time Savings

**Traditional Workflow:** 4-6 hours
- Organizing footage: 30 min
- Rough cut: 2-3 hours
- Hook selection: 30 min
- Refining edit: 1-2 hours

**StudioFlow Workflow:** 1-2 hours
- Organizing footage: 5 min (auto-organized)
- Rough cut: 5 min (automated)
- Hook selection: 10 min (A/B test generation)
- Refining edit: 45-90 min (starting from smart rough cut)

**Time Saved:** 70-80% reduction in editing time!

---

## Best Practices

### 1. Name Files Before Recording

Plan your filename structure before recording:
- Hook options with flow types
- Step numbers for tutorials
- Quality markers for best takes
- Mistake markers for retakes

### 2. Record Multiple Hook Options

Record 3-5 different hook takes with different flow types:
```
CAM_HOOK_COH_Contrarian_BEST.mp4
CAM_HOOK_CH_Curiosity_Take2.mp4
CAM_HOOK_PSH_Problem_Solution_Take3.mp4
```

### 3. Use Step Numbers

Number your steps sequentially:
```
SCREEN_STEP01_Installation.mov
SCREEN_STEP02_Configuration.mov
SCREEN_STEP03_Demo.mov
```

This auto-generates chapter markers!

### 4. Mark Best Takes

Always mark your best takes:
```
CAM_HOOK_COH_BEST_Opening.mp4
SCREEN_STEP02_SELECT_Config.mov
```

### 5. Test Hooks Before Final

Generate hook tests and upload as unlisted to find the best performer.

### 6. Review Removed Footage

Check the removed footage EDL to ensure nothing good was cut.

---

## Troubleshooting

### No Clips Found

**Problem:** `sf rough-cut` says "No video clips found"

**Solutions:**
- Check footage directory path
- Ensure files are video formats (.mp4, .mov, .mxf)
- Check file permissions
- Use `sf import` first to organize footage

### No Transcripts Generated

**Problem:** Rough cut has no segments

**Solutions:**
- Ensure clips have audio
- Run `sf batch transcribe` first
- Check Whisper installation: `sf transcribe --test`

### Hook Tests Not Generated

**Problem:** `sf rough-cut hook-tests` finds no hooks

**Solutions:**
- Name clips with `HOOK_` prefix
- Ensure clips have transcripts
- Check first 60 seconds of footage
- Lower threshold: Use named hook flows (CH, COH, etc.)

### Timeline Import Fails

**Problem:** Resolve can't import FCPXML

**Solutions:**
- Use `.fcpxml` format (better than `.edl`)
- Check file paths are accessible
- Ensure Resolve is up to date
- Try `.edl` format as backup

---

## Next Steps

- **Advanced Features:** [USER_GUIDE.md](USER_GUIDE.md)
- **System Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Audio Marker System:** [AUDIO_MARKER_SYSTEM.md](AUDIO_MARKER_SYSTEM.md)

---

## Quick Reference

### Essential Commands

```bash
sf new "Project"              # Create project
sf import /path               # Import footage
sf rough-cut --style tutorial # Generate rough cut
sf rough-cut hook-tests       # Generate hook tests
sf edit                       # Open in Resolve
sf export youtube             # Export for YouTube
sf youtube upload video.mp4   # Upload to YouTube
```

### Filename Patterns

```
HOOK_[FLOW]_Description       # Hook with flow type (CH, COH, PSH, etc.)
SCREEN_STEP##_Description     # Screen recording with step number
CAM_STEP##_Description        # Talking head with step number
BROLL_STEP##_Description      # B-roll with step number
CAM_CTA_Description           # Call-to-action
MISTAKE_Description           # Auto-excluded mistake
BEST_Description              # Best take (highest priority)
```

### Hook Flow Types

- `COH` - Contrarian (1.35x) ⭐ Highest
- `CH` - Curiosity (1.3x)
- `AH` - Action (1.25x)
- `PSH` - Problem-Solution (1.2x)
- `SH` - Statistic (1.2x)
- `TPH` - Time-Promise (1.15x)
- `QH` - Question (1.15x)

---

**Ready to create your first YouTube episode? Start with `sf new "My Episode"` and follow the workflow above!** 🎬✨
