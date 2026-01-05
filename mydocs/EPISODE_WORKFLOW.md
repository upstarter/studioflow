# My Episode Workflow - Step-by-Step Checklist

**Personal workflow for creating YouTube episodes with StudioFlow**
**Setup: 1x Sony FX30 Camera**

---

## Pre-Recording Setup

### ✅ Step 1: Plan Your Episode Structure

Before recording, plan your episode:

```
[ ] Episode Topic: _________________________
[ ] Target Duration: _____ minutes
[ ] Steps/Topics:
    1. _________________________
    2. _________________________
    3. _________________________
    4. _________________________
    5. _________________________

[ ] Hook Options (record 3-5 takes):
    [ ] Contrarian Hook (COH) - "Stop doing X..."
    [ ] Curiosity Hook (CH) - "The secret to..."
    [ ] Problem-Solution Hook (PSH) - "Most people struggle with..."
    [ ] Time-Promise Hook (TPH) - "In 10 minutes, you'll..."
    [ ] Question Hook (QH) - "Have you ever wondered..."

[ ] CTA/Outro: _________________________
```

### ✅ Step 2: Prepare Recording Setup

```
[ ] FX30 camera ready
[ ] SD card formatted
[ ] Audio levels checked
[ ] Lighting set
[ ] Background/studio ready
[ ] Screen recording software ready (if needed)
```

---

## Recording Phase

### ✅ Step 3: Record Hook Options (First!)

**Record 3-5 different hook takes** - This is critical for A/B testing!

**Naming Convention:**
```
CAM_HOOK_COH_Contrarian_Take1.mp4
CAM_HOOK_CH_Curiosity_Take2.mp4
CAM_HOOK_PSH_Problem_Take3.mp4
CAM_HOOK_TPH_TimePromise_Take4.mp4
```

**After recording, immediately rename files on camera/SD card:**
- Use camera's rename function, OR
- Note the file numbers and rename after import

**See:** `FX30_NAMING_GUIDE.md` for detailed naming patterns

### ✅ Step 4: Record Main Content

**For each step/topic, record:**

1. **Talking Head Explanation:**
   ```
   CAM_STEP01_Introduction.mp4
   CAM_STEP02_Setup.mp4
   CAM_STEP03_Demo.mp4
   ```

2. **Screen Recording (if tutorial):**
   ```
   SCREEN_STEP01_Installation.mov
   SCREEN_STEP02_Configuration.mov
   SCREEN_STEP03_Features.mov
   ```

3. **B-Roll (if needed):**
   ```
   BROLL_STEP01_Product_Shot.mp4
   BROLL_STEP02_Environment.mov
   ```

**Tips:**
- Record multiple takes if needed: `CAM_STEP01_Introduction (1).mp4`, `CAM_STEP01_Introduction (2).mp4`
- **Numbered takes are KEPT** - `(1)`, `(2)`, etc. are treated as different takes, not duplicates
- Mark best take immediately: `CAM_STEP01_Introduction_BEST.mp4`
- Mark mistakes: `CAM_STEP01_Introduction_MISTAKE.mp4`

**Note:** The system only removes `_normalized` duplicates (if original exists). Numbered takes like `(1)`, `(2)` are always kept as distinct files.

### ✅ Step 5: Record CTA/Outro

```
CAM_CTA_Subscribe.mp4
CAM_OUTRO_Summary.mp4
```

---

## Post-Recording: File Organization

### ✅ Step 6: Import from FX30 SD Card

```bash
# Insert SD card
# Auto-import should trigger, OR manually:

sf import /media/[USERNAME]/[SD_CARD_NAME]

# Or specify project:
sf import /media/[USERNAME]/[SD_CARD_NAME] --project "My_Episode_01"
```

**What happens:**
- Files copied to project `01_footage/`
- Auto-organized by type (A_ROLL, B_ROLL, SCREEN_RECORDINGS)
- Filenames parsed for metadata

### ✅ Step 7: Rename Files (If Not Done During Recording)

**If you didn't rename during recording, do it now:**

```bash
# Navigate to footage directory
cd [PROJECT]/01_footage/A_ROLL/

# Use the naming helper script (see FX30_NAMING_GUIDE.md)
# Or manually rename following the convention
```

**Quick Rename Pattern:**
```
Original FX30 filename: C0001.MP4
Rename to: CAM_HOOK_COH_Contrarian_Take1.mp4

Original: C0002.MP4
Rename to: CAM_STEP01_Introduction.mp4
```

**See:** `FX30_NAMING_GUIDE.md` for automated renaming script

---

## StudioFlow Processing

### ✅ Step 8: Generate Rough Cut

```bash
# Navigate to project directory
cd [PROJECT]

# Generate tutorial rough cut
sf rough-cut --style tutorial --duration 10

# Review the preview
# Confirm generation
```

**What to check:**
- [ ] Total duration matches target
- [ ] All steps included
- [ ] Hook selected (best one)
- [ ] No important content missing

### ✅ Step 9: Generate Hook Tests (Optional but Recommended)

```bash
# Generate 5 hook test timelines
sf rough-cut hook-tests --max 5

# Review output in: 04_TIMELINES/02_HOOK_TESTS/
```

**Next Steps:**
- [ ] Import hook tests to Resolve
- [ ] Render each as 1080p
- [ ] Upload as unlisted to YouTube
- [ ] Wait 24-48 hours
- [ ] Check analytics for best performer
- [ ] Use winning hook in final video

### ✅ Step 10: Import to DaVinci Resolve

```bash
# Open Resolve
sf edit

# In Resolve:
# File → Import → Timeline → Import AAF, EDL, XML, FCPXML...
# Select: rough_cut_tutorial.fcpxml
```

**Check:**
- [ ] All clips imported
- [ ] Timeline structure correct
- [ ] Chapter markers present (if generated)

---

## Editing Phase

### ✅ Step 11: Refine Rough Cut

**In Resolve:**

- [ ] Extend/trim clips as needed
- [ ] Add B-roll where appropriate
- [ ] Adjust pacing
- [ ] Add transitions

### ✅ Step 12: Add Graphics & Effects

- [ ] Lower thirds for step titles
- [ ] Text overlays for key points
- [ ] Arrows/highlights (if screen recordings)
- [ ] Transitions between steps

### ✅ Step 13: Color Grade

```bash
# Apply preset
sf resolve grade --preset "orange-teal"

# Or grade manually in Resolve
```

- [ ] Color grade applied
- [ ] Looks consistent across clips
- [ ] Export-ready

### ✅ Step 14: Audio Mix

- [ ] Audio levels consistent (already normalized to -14 LUFS)
- [ ] Music bed added (if using)
- [ ] Sound effects (if using)
- [ ] Final mix check

---

## Export & Publish

### ✅ Step 15: Export Final Video

**In Resolve:**
- [ ] Export settings: 4K, 30-45Mbps, H.264
- [ ] Audio: -14 LUFS (already normalized)
- [ ] Export to: `05_exports/`

**Or use command:**
```bash
sf export youtube --project "[PROJECT_NAME]"
```

### ✅ Step 16: Generate YouTube Metadata

```bash
# Generate titles
sf youtube titles "[Topic]" --style educational

# Generate description with chapters
sf youtube description "[Topic]" --chapters
```

- [ ] Title selected
- [ ] Description written (with chapters)
- [ ] Tags added
- [ ] Thumbnail created

### ✅ Step 17: Upload to YouTube

```bash
# Upload with metadata
sf youtube upload final.mp4 \
  --title "[Title]" \
  --description "description.txt" \
  --tags "[tags]"
```

**Or upload manually:**
- [ ] Upload video
- [ ] Paste title, description, chapters
- [ ] Set thumbnail
- [ ] Publish!

---

## Post-Publish

### ✅ Step 18: Monitor & Learn

- [ ] Check analytics after 24-48 hours
- [ ] Review hook test results
- [ ] Note what worked/didn't work
- [ ] Update workflow for next episode

---

## Quick Reference

### Essential Commands

```bash
# Create project
sf new "Episode_Name"

# Import footage
sf import /path/to/sdcard

# Generate rough cut
sf rough-cut --style tutorial --duration 10

# Generate hook tests
sf rough-cut hook-tests

# Open in Resolve
sf edit

# Export
sf export youtube

# Upload
sf youtube upload video.mp4 --title "Title"
```

### Filename Patterns (Quick)

```
HOOK: CAM_HOOK_[FLOW]_Description.mp4
STEP: CAM_STEP##_Description.mp4
SCREEN: SCREEN_STEP##_Description.mov
BROLL: BROLL_STEP##_Description.mp4
CTA: CAM_CTA_Description.mp4
BEST: CAM_STEP##_Description_BEST.mp4
MISTAKE: CAM_STEP##_Description_MISTAKE.mp4
```

### Hook Flow Types

- `COH` - Contrarian (1.35x) ⭐ Highest
- `CH` - Curiosity (1.3x)
- `AH` - Action (1.25x)
- `PSH` - Problem-Solution (1.2x)
- `TPH` - Time-Promise (1.15x)
- `QH` - Question (1.15x)

---

## Time Estimate

- **Recording:** 30-60 minutes
- **File Organization:** 5-10 minutes
- **Rough Cut Generation:** 5 minutes
- **Hook Testing:** 10 minutes (optional)
- **Resolve Editing:** 45-90 minutes
- **Export & Upload:** 10 minutes

**Total:** ~2-3 hours (vs 4-6 hours traditional)

---

**Next Episode:** Start at Step 1 and repeat! 🎬

