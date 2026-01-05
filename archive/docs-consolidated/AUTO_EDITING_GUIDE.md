# Auto-Editing System for YouTube Episodes

## Overview

StudioFlow's auto-editing system intelligently automates the entire YouTube episode editing workflow - from raw footage to a fully structured Resolve project ready for final editing.

## 🎯 Core Philosophy

**Automate the boring, repetitive tasks so you can focus on creative editing.**

The system:
- Analyzes your footage intelligently
- Creates organized bin structures automatically
- Generates initial timeline assemblies
- Adds chapter markers from transcripts
- Prepares everything for final creative editing

---

## 🚀 Quick Start

```bash
# One command to set up entire episode
sf auto-edit episode EP001 --footage /path/to/footage --transcript transcript.srt

# Or let it auto-detect everything
sf auto-edit episode EP001 --smart
```

**What it does:**
1. ✅ Analyzes all footage (camera type, duration, content type)
2. ✅ Creates smart bins (A-roll, B-roll, talking head, screen recordings)
3. ✅ Generates Power Bins (reusable across projects)
4. ✅ Creates initial timeline assembly
5. ✅ Adds chapter markers from transcript
6. ✅ Sets up color grading presets
7. ✅ Ready for final editing

---

## 📁 Smart Bin System

### Automatic Bin Creation

Smart bins are automatically created based on content analysis:

```
PROJECT/
├── 01_SMART_BINS/
│   ├── A_ROLL_TALKING_HEAD/      # Person speaking to camera
│   ├── A_ROLL_DIALOGUE/          # Conversations/interviews
│   ├── B_ROLL_PRODUCT/           # Product shots
│   ├── B_ROLL_DEMONSTRATION/     # Screen recordings/demos
│   ├── B_ROLL_B_ROLL/            # Generic B-roll
│   ├── AUDIO_ONLY/               # Good audio, visual not important
│   ├── MUSIC/                    # Background music
│   ├── SFX/                      # Sound effects
│   └── REJECTS/                  # Test clips, corrupted files
```

### Bin Organization Rules

**A-Roll Detection:**
- Face detection in frame
- Audio presence with speech
- Duration > 30 seconds typically
- Camera type (FX30 main camera)

**B-Roll Detection:**
- No faces detected
- Short duration (10-60 seconds)
- Different camera angle
- Screen recording patterns

**Categorization by Content:**
```python
# Automatic categorization rules
if has_face and has_speech and duration > 30:
    bin = "A_ROLL_TALKING_HEAD"
elif has_face and has_speech:
    bin = "A_ROLL_DIALOGUE"
elif is_screen_recording:
    bin = "B_ROLL_DEMONSTRATION"
elif has_product_in_frame:
    bin = "B_ROLL_PRODUCT"
elif no_audio or audio_quality < threshold:
    bin = "REJECTS"
```

---

## ⚡ Power Bins (Reusable Assets)

Power Bins are persistent bins that appear in ALL projects. They contain:
- Stock music
- Sound effects
- Lower thirds templates
- Graphics/overlays
- Transition presets
- Color grading LUTs

### Auto-Creation of Power Bins

```bash
sf auto-edit power-bins create  # First time setup
sf auto-edit power-bins sync     # Sync library assets to Power Bins
```

**Default Power Bin Structure:**
```
_POWER_BINS/
├── MUSIC/
│   ├── INTRO/          # Intro music
│   ├── BACKGROUND/     # Background music
│   ├── OUTRO/          # Outro music
│   └── TRANSITION/     # Transition music
├── SFX/
│   ├── SWISHES/        # Whoosh sounds
│   ├── CLICKS/         # UI sounds
│   ├── IMPACTS/        # Impact sounds
│   └── AMBIENT/        # Ambient sounds
├── GRAPHICS/
│   ├── LOWER_THIRDS/   # Name titles
│   ├── INTROS/         # Intro animations
│   ├── OUTROS/         # Outro animations
│   └── OVERLAYS/       # Screen overlays
├── LUTS/
│   ├── CINEMATIC/      # Cinematic looks
│   ├── YOUTUBE/        # YouTube optimized
│   └── BRANDS/         # Brand-specific
└── TRANSITIONS/
    ├── SMOOTH/         # Smooth transitions
    ├── DYNAMIC/        # Dynamic transitions
    └── STYLIZED/       # Stylized transitions
```

**Source Locations:**
- Music: `/mnt/library/ASSETS/MUSIC/`
- SFX: `/mnt/library/ASSETS/SFX/`
- Graphics: `/mnt/library/ASSETS/GRAPHICS/`
- LUTs: `/mnt/library/ASSETS/LUTS/`

---

## 📖 Chapter Marker System

### Automatic Chapter Creation

Chapters are automatically created from transcripts, markers, or manual input.

#### Method 1: From Transcript (Auto-Detection)

```bash
sf auto-edit chapters --from-transcript transcript.srt
```

**Smart Chapter Detection:**
- Detects topic changes (NLP analysis)
- Detects pauses/long silences
- Detects tone changes (question → answer)
- Uses keywords (intro, outro, conclusion)
- Minimum chapter length: 60 seconds

**Chapter Format:**
```
00:00 - Introduction
02:34 - Main Topic Overview
05:12 - Deep Dive: Feature 1
12:45 - Deep Dive: Feature 2
18:30 - Conclusion & CTA
```

#### Method 2: From Markers

```bash
sf auto-edit chapters --from-markers  # Import Resolve markers
```

#### Method 3: Manual Entry

```bash
sf auto-edit chapters add "Introduction" --timestamp 0:00
sf auto-edit chapters add "Feature Demo" --timestamp 5:30
sf auto-edit chapters list
sf auto-edit chapters export  # Export as YouTube description format
```

### Chapter Optimization for YouTube

**Auto-Generated YouTube Description:**
```
00:00 Introduction
02:34 What is StudioFlow?
05:12 Key Features
12:45 Deep Dive
18:30 Conclusion
22:15 Subscribe!
```

**Features:**
- Auto-formats for YouTube (timestamps)
- SEO-optimized chapter names
- Adds to video description automatically
- Creates chapter markers in Resolve

---

## 🎬 Timeline Automation

### Initial Timeline Assembly

```bash
sf auto-edit timeline create --smart
```

**Smart Assembly Rules:**
1. **Hook Creation** (First 5-15 seconds)
   - Selects most engaging clip
   - Prefers talking head with high energy
   - Adds dramatic music/stinger

2. **A-Roll Foundation**
   - Places main talking head clips
   - Removes long pauses/silence
   - Smooth transitions between clips

3. **B-Roll Insertion**
   - Automatically inserts B-roll over A-roll
   - Matches B-roll to A-roll topic (if possible)
   - Maintains visual interest

4. **Music Bed**
   - Adds background music
   - Automatically ducks when speech detected
   - Smooth intro/outro music

5. **Chapter Markers**
   - Places markers at chapter points
   - Color-coded markers
   - Named for easy reference

### Timeline Structure

```
Timeline: 01_AUTO_ASSEMBLY
├── Video Track 1: A-Roll (Primary)
├── Video Track 2: B-Roll (Overlay)
├── Video Track 3: Graphics/Overlays
├── Audio Track 1: A-Roll Audio
├── Audio Track 2: Music
├── Audio Track 3: SFX
└── Markers: Chapters
```

---

## 🤖 Intelligent Editing Features

### 1. Silence Removal

```bash
sf auto-edit remove-silence --threshold -40dB --min-duration 0.5s
```

**Smart Silence Detection:**
- Detects pauses in speech
- Removes filler words ("um", "uh", "like")
- Preserves natural pacing
- Maintains audio sync

### 2. Filler Word Removal

```bash
sf auto-edit remove-fillers --aggressive
```

**Detected Fillers:**
- "um", "uh", "er", "ah"
- "like", "you know", "so"
- Long pauses between words

### 3. Auto-Pacing

```bash
sf auto-edit pace --target-duration 15:00
```

**Pacing Features:**
- Speeds up slow sections
- Removes redundant content
- Maintains story flow
- Preserves important information

### 4. Auto-Transitions

```bash
sf auto-edit transitions --style smooth
```

**Transition Styles:**
- **Smooth**: Cross-dissolve, fade
- **Dynamic**: Whip, zoom, slide
- **Stylized**: Glitch, morph, custom

**Placement Rules:**
- Scene changes
- Topic transitions
- Camera angle changes

### 5. B-Roll Matching

```bash
sf auto-edit match-broll --smart
```

**Matching Logic:**
- Analyzes A-roll audio content
- Matches B-roll by topic/keywords
- Syncs duration to A-roll gaps
- Maintains visual coherence

---

## 🎨 Color Grading Automation

### Auto-Apply LUTs

```bash
sf auto-edit grade --lut youtube_optimized --auto-match
```

**LUT Selection:**
- Matches footage to appropriate LUT
- FX30 S-Log3 → Rec.709 conversion
- YouTube-optimized looks
- Consistent across clips

### Smart Color Matching

```bash
sf auto-edit grade match --reference-clip clip01.mp4
```

**Features:**
- Matches color across all clips
- Balances exposure
- Corrects white balance
- Maintains skin tones

---

## 📊 Quality Checks

### Pre-Export Validation

```bash
sf auto-edit validate
```

**Checks:**
- ✅ Audio levels (-14 LUFS)
- ✅ Video resolution (4K/1080p)
- ✅ Frame rate consistency
- ✅ Color space (Rec.709)
- ✅ Chapter markers present
- ✅ No gaps in timeline
- ✅ No audio sync issues
- ✅ Duration appropriate

---

## 🔄 Complete Workflow

### Full Episode Automation

```bash
# Step 1: Import and organize
sf import /media/sdcard --organize

# Step 2: Auto-edit setup
sf auto-edit episode EP001 \
  --footage /mnt/library/PROJECTS/EPISODES/EP001/01_footage \
  --transcript /mnt/library/PROJECTS/EPISODES/EP001/02_transcripts/main.srt \
  --template youtube_tutorial

# Step 3: Review and refine (manual creative work)

# Step 4: Finalize
sf auto-edit finalize --export --validate
```

### Workflow Stages

1. **Import** → Raw footage imported, verified
2. **Analyze** → Content analyzed, categorized
3. **Organize** → Smart bins created, clips organized
4. **Assemble** → Initial timeline created
5. **Enhance** → Music, transitions, B-roll added
6. **Refine** → Manual creative editing
7. **Finalize** → Validation, export, upload

---

## 🎛️ Configuration

### Auto-Edit Settings

```yaml
# ~/.studioflow/config.yaml
auto_edit:
  # Smart bin settings
  smart_bins:
    a_roll_min_duration: 30  # seconds
    b_roll_max_duration: 60
    face_detection: true
    speech_detection: true
    
  # Timeline settings
  timeline:
    hook_duration: 10  # seconds
    min_chapter_length: 60
    auto_transitions: true
    transition_style: smooth
    
  # Music settings
  music:
    auto_add: true
    duck_threshold: -12  # dB
    intro_duration: 5
    outro_duration: 10
    
  # Quality settings
  quality:
    min_audio_level: -14  # LUFS
    max_audio_level: -12
    min_resolution: 1080
    target_frame_rate: 30
```

---

## 🚀 Advanced Features

### 1. AI-Powered Clip Selection

```bash
sf auto-edit select-best --criteria "high_energy,good_audio,clear_visual"
```

**Selection Criteria:**
- Energy level (audio analysis)
- Visual quality (focus, exposure)
- Audio quality (clarity, noise)
- Engagement (if analytics available)

### 2. Multi-Camera Sync

```bash
sf auto-edit sync-cameras --cameras fx30,zve10 --method audio
```

**Sync Methods:**
- Audio waveform matching
- Timecode sync
- Visual marker detection
- Manual offset

### 3. Scene Detection

```bash
sf auto-edit detect-scenes --sensitivity medium
```

**Features:**
- Automatic scene breaks
- Creates bins per scene
- Generates scene markers
- Organizes by scene content

### 4. Auto-Thumbnail Generation

```bash
sf auto-edit thumbnails --extract-best-frames --count 10
```

**Selection:**
- High-energy moments
- Clear facial expressions
- Good composition
- Visual interest

---

## 📈 Optimization Tips

### For Efficiency

1. **Use Templates** - Save workflow as template
2. **Batch Process** - Process multiple episodes
3. **Smart Bins First** - Organization before editing
4. **Chapter Early** - Add chapters during rough cut
5. **Validate Often** - Check quality throughout

### For Quality

1. **Review Auto-Assembly** - Always review before finalizing
2. **Manual B-Roll Selection** - AI helps, but you choose final B-roll
3. **Refine Transitions** - Adjust auto-transitions as needed
4. **Custom Music** - Auto-adds, but customize for brand
5. **Chapter Optimization** - Edit auto-chapters for SEO

---

## 🎯 Use Cases

### Tutorial Videos
- Auto-detect demonstration segments
- Match screen recordings to explanations
- Create clear chapter structure
- Add callout graphics

### Talking Head Videos
- Remove silence and fillers
- Add B-roll for visual interest
- Create engaging hook
- Optimize pacing

### Product Reviews
- Organize by product features
- Match product shots to commentary
- Create comparison sections
- Add affiliate callouts

---

## 🔧 Troubleshooting

### Common Issues

**Issue:** Smart bins not created
- **Solution:** Ensure footage is analyzed first with `sf auto-edit analyze`

**Issue:** Chapters not detected
- **Solution:** Check transcript format, use `--force-detection`

**Issue:** B-roll not matching
- **Solution:** Improve A-roll transcript quality or manually tag clips

**Issue:** Timeline too long/short
- **Solution:** Adjust pacing settings or use `--target-duration`

---

## 📚 Next Steps

1. **Start Simple** - Use auto-assembly for rough cut
2. **Iterate** - Refine based on results
3. **Customize** - Adjust settings to your style
4. **Templates** - Save successful workflows
5. **Share** - Export templates for team use

---

## 🎬 Example: Complete Episode in 5 Minutes

```bash
# 1. Import (2 min)
sf import /media/fx30_card --organize

# 2. Auto-edit setup (2 min)
sf auto-edit episode EP001 --smart

# 3. Review auto-assembly (1 min)
# Open Resolve, review timeline

# 4. Manual refinements (creative work)
# Adjust timing, add custom B-roll, refine color

# 5. Finalize (auto)
sf auto-edit finalize --export --validate --upload
```

**Result:** Professional YouTube episode ready for upload in minimal time, with maximum creative control where it matters.

