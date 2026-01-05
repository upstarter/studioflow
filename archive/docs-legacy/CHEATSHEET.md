# StudioFlow Command Cheatsheet 📋

## Quick Reference Card

### 🎬 Project Commands
```bash
sfnew "Name"                    # Create new project
sflist                          # List all projects
sfinfo "Name"                   # Show project details
sfarchive "Name"                # Archive completed project
sf project create "Name" --template youtube/tutorial/comparison/minimal
```

### 📹 Recording & Capture
```bash
sfcap                           # Take screenshot
sfrec                           # Record screen
sforg "Project"                 # Organize captures
sfobs "Project"                 # Setup OBS for project

sf capture snap --window        # Capture specific window
sf capture record --duration 30 # Record for 30 seconds
sf capture grid *.png --labels  # Create comparison grid
sf obs viral-scenes             # Create viral scene collection
sf obs highlights "Project"     # Setup replay buffer
```

### 🎯 Content Generation
```bash
sfscript "Project"              # Generate video script
sfideas "topic"                 # Get video ideas
sfprompt "type"                 # Create AI prompts

sf ai script "Project" --style educational/entertainment/review
sf ai ideas "topic" --trending --count 10
sf ai analyze "script.txt" --metrics all
```

### 📊 YouTube Optimization
```bash
sfseo "title"                   # SEO optimization
sfdesc "Project"                # Generate description
sfthumb "Project"               # Setup thumbnail A/B test

sf youtube titles "Topic" --style viral/tutorial/comparison
sf youtube hooks "Project" --style retention/story/question
sf youtube metadata "Project" --platform youtube/instagram/tiktok
sf youtube upload-time          # Get optimal upload time
sf youtube compete "keywords"   # Analyze competition
```

### 🎵 Audio Processing
```bash
sftrans video.mp4               # Transcribe to subtitles
sfdenoise audio.wav             # Remove background noise
sfmusic "mood"                  # Find background music

sf audio transcribe video.mp4 --format srt/vtt/txt
sf audio denoise recording.wav --profile voice/music/podcast
sf audio normalize *.wav --target -16
sf audio library search "upbeat electronic"
```

### 🎨 Video Editing
```bash
sfresolve "Project"             # Setup DaVinci project
sfcolor "Project"               # Apply color grade
sfrender "Project"              # Export video

sf resolve setup "Project" --framerate 30
sf resolve import "Project" --organize
sf resolve color "Project" --style cinematic/viral/natural
sf resolve render "Project" --preset youtube/instagram/master
```

### 💾 Storage Management
```bash
sfstat                          # Show storage status
sfmove "Project" tier           # Move between tiers
sfarchive "Project"             # Move to archive

sf storage status --json        # Machine-readable output
sf storage optimize             # Get optimization suggestions
sf storage move "Project" active/render/archive
```

---

## Platform-Specific Commands

### YouTube (Long-form)
```bash
sf project create "Video" --template youtube
sf youtube titles "Topic" --style viral
sf resolve render "Video" --preset youtube    # 1080p, H.264, 16Mbps
sf youtube metadata "Video"
```

### Instagram Reel
```bash
sf capture record --duration 30 --vertical
sf resolve render "Video" --preset instagram   # 1080x1920, 60s max
sf youtube metadata "Video" --platform instagram
```

### TikTok
```bash
sf capture record --duration 15 --vertical
sf resolve render "Video" --preset tiktok      # 1080x1920, 15-60s
sf youtube metadata "Video" --platform tiktok
```

---

## Common Workflows

### 🚀 Quick Tutorial
```bash
PROJECT="Tutorial"
sfnew "$PROJECT" && \
sfobs "$PROJECT" && \
sf ai script "$PROJECT" && \
sf youtube titles "Topic"
```

### 📸 Screenshot Comparison
```bash
sf capture snap --window    # Repeat for each tool
sf capture grid *.png --labels --title "Comparison"
```

### 🎙 Process Recording
```bash
sf audio transcribe video.mp4 && \
sf audio denoise video.mp4 && \
sf resolve import "Project"
```

### 📤 Prepare for Upload
```bash
sf resolve render "Project" --preset youtube && \
sf youtube metadata "Project" && \
sf youtube thumbnail-test "Project" && \
sf youtube upload-time
```

---

## Useful Aliases

Add to `~/.bashrc`:
```bash
# Quick workflows
alias sfquick='sf project create "$1" && sf obs setup "$1"'
alias sftutorial='sf project create "$1" --template tutorial && sf ai script "$1"'
alias sfviral='sf youtube titles "$1" --style viral | head -5'

# Batch operations
alias sfarchive-old='sf storage status --json | jq ".projects[] | select(.age_days > 30)" | xargs -I {} sf storage archive "{}"'
alias sftrans-all='for f in *.mp4; do sf audio transcribe "$f"; done'

# Status checks
alias sfcheck='sf storage status && sf project list | head -5'
```

---

## Keyboard Shortcuts (OBS)

Configure in `sf obs setup`:
```
Ctrl+R         Start/Stop Recording
Ctrl+Shift+R   Pause Recording
Alt+H          Save Replay Buffer (last 30s)
Ctrl+1-6       Switch Scenes
Ctrl+M         Mute/Unmute Mic
```

---

## Directory Quick Reference

```bash
01_FOOTAGE/     # Raw video files
  A_ROLL/       # Main camera
  B_ROLL/       # Supporting footage
  SCREENSHOTS/  # sf-capture output

02_AUDIO/       # Audio files
  MUSIC/        # Background tracks
  VO/           # Voice overs
  TRANSCRIPTS/  # sf-audio output

03_GRAPHICS/    # Visual elements
  THUMBNAILS/   # YouTube thumbnails
  OVERLAYS/     # Screen graphics

04_EDIT/        # Project files
  TIMELINE/     # DaVinci projects

05_EXPORT/      # Output files
  FINAL/        # Ready to upload
  SHORTS/       # Platform versions
```

---

## Pipeline Commands

Chain commands with `&&` for automation:
```bash
# Complete production pipeline
sf project create "Video" && \
sf obs setup "Video" && \
sf ai script "Video" && \
echo "Ready to record!"

# Post-production pipeline
sf audio transcribe *.mp4 && \
sf resolve import "Video" && \
sf resolve render "Video" && \
sf youtube metadata "Video"

# Multi-platform export
for p in youtube instagram tiktok; do
  sf resolve render "Video" --preset $p && \
  sf youtube metadata "Video" --platform $p
done
```

---

## JSON Output for Scripting

Many commands support `--json` for automation:
```bash
sf project list --json | jq '.projects[].name'
sf storage status --json | jq '.tiers.active.percent'
sf youtube compete "topic" --json | jq '.competition_score'
```

---

## Environment Variables

```bash
export SF_PROJECTS="/mnt/studio/Projects"
export SF_ARCHIVE="/mnt/archive"
export SF_DEFAULT_TEMPLATE="youtube"
export SF_DEFAULT_PLATFORM="youtube"
```

---

## Quick Troubleshooting

```bash
# Check installation
which sf
ls -la /usr/local/bin/sf*

# Test basic functionality
sf project list
sf storage status

# Reset configuration
rm -rf ~/.config/studioflow
./install-full.sh

# View logs
tail -f ~/.cache/studioflow/sf.log
```

---

## Help Commands

```bash
sf                      # Show all tools
sf project --help       # Tool-specific help
man sf-project          # Full manual (if installed)
ls docs/                # Browse documentation
```

---

**Pro Tip**: Print this cheatsheet and keep it handy! 🎯

```bash
# Generate PDF version
pandoc CHEATSHEET.md -o cheatsheet.pdf
```