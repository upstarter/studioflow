# My Personal StudioFlow Workflow

**Personal guides and tools for creating YouTube episodes with StudioFlow**

---

## Quick Start

1. **Read:** `EPISODE_WORKFLOW.md` - Complete step-by-step checklist
2. **Read:** `FX30_NAMING_GUIDE.md` - How to name your FX30 clips
3. **Use:** `rename_fx30_clips.py` - Automated renaming helper

---

## Files

### 📋 EPISODE_WORKFLOW.md
**Complete step-by-step checklist for creating episodes**

- Pre-recording setup
- Recording phase
- Post-recording organization
- StudioFlow processing
- Editing phase
- Export & publish
- Post-publish monitoring

**Use this as your main checklist for each episode!**

### 📝 FX30_NAMING_GUIDE.md
**FX30-specific naming conventions and tools**

- Naming patterns for FX30 clips
- Automated renaming script
- Recording template
- Quick reference

**Essential for efficient clip organization!**

### 🔍 DUPLICATE_HANDLING.md
**How StudioFlow handles duplicates vs different takes**

- Numbered takes `(1)`, `(2)` are kept (not duplicates!)
- Normalized files `_normalized` are removed (if original exists)
- Examples and best practices

**Important:** Read this to understand how retakes are handled!

### 🛠️ rename_fx30_clips.py
**Interactive script to rename FX30 clips**

**Usage:**
```bash
cd [PROJECT]/01_footage/A_ROLL/
python3 ~/studioflow/mydocs/rename_fx30_clips.py
```

**What it does:**
- Finds all FX30 clips (C####.MP4)
- Interactive prompts for each clip
- Renames to StudioFlow convention
- Handles hooks, steps, screen recordings, etc.

---

## Typical Workflow

### 1. Before Recording
- [ ] Read `EPISODE_WORKFLOW.md` Step 1-2
- [ ] Plan episode structure
- [ ] Prepare recording setup

### 2. During Recording
- [ ] Record hook options (3-5 takes)
- [ ] Record main content (steps)
- [ ] Record CTA/Outro
- [ ] Use recording log template (from `FX30_NAMING_GUIDE.md`)

### 3. After Recording
- [ ] Import footage: `sf import /path/to/sdcard`
- [ ] Rename clips: Use `rename_fx30_clips.py` OR manual
- [ ] Follow `EPISODE_WORKFLOW.md` Step 6-18

---

## Tips

1. **Always record hooks first** - Get 3-5 different hook options
2. **Use the renaming script** - Saves time and ensures consistency
3. **Mark best takes immediately** - Add `_BEST` suffix
4. **Don't delete mistakes** - Mark as `_MISTAKE` (auto-excluded)
5. **Follow the checklist** - `EPISODE_WORKFLOW.md` has everything

---

## Quick Reference

### Essential Commands

```bash
# Create project
sf new "Episode_Name"

# Import footage
sf import /path/to/sdcard

# Rename clips (if needed)
cd [PROJECT]/01_footage/A_ROLL/
python3 ~/studioflow/mydocs/rename_fx30_clips.py

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

### Filename Patterns

```
Hook:        CAM_HOOK_[FLOW]_Description[_Take#][_BEST].mp4
Step:        CAM_STEP##_Description[ (N)][_BEST].mp4
Screen:      SCREEN_STEP##_Description[_BEST].mov
B-Roll:      BROLL_STEP##_Description[_BEST].mp4
CTA:         CAM_CTA_Description.mp4
Mistake:     CAM_Description_MISTAKE.mp4
```

### Hook Flow Types

- `COH` - Contrarian (1.35x) ⭐ Best
- `CH` - Curiosity (1.3x)
- `AH` - Action (1.25x)
- `PSH` - Problem-Solution (1.2x)
- `TPH` - Time-Promise (1.15x)
- `QH` - Question (1.15x)

---

## See Also

- `../docs/YOUTUBE_EPISODE_GUIDE.md` - Complete YouTube episode guide
- `../docs/FILENAME_CONVENTION.md` - Full naming convention reference
- `../docs/YOUTUBE_HOOK_FLOWS.md` - Hook flow details and examples

---

**Start with `EPISODE_WORKFLOW.md` and follow the checklist!** 🎬

