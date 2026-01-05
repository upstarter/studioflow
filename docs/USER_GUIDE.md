# StudioFlow User Guide

Complete reference guide for all StudioFlow commands and features.

> **🎯 New to StudioFlow?** Start with the [YouTube Episode Guide](YOUTUBE_EPISODE_GUIDE.md) for a complete walkthrough of creating a YouTube episode.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Core Commands](#core-commands)
4. [Rough Cut System](#rough-cut-system) ⭐ **NEW**
5. [Hook Testing](#hook-testing) ⭐ **NEW**
6. [Filename Convention](#filename-convention) ⭐ **NEW**
7. [Workflows](#workflows)
8. [Auto-Editing System](#auto-editing-system)
9. [Library Workflow](#library-workflow)
10. [Auto-Import](#auto-import)
11. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Your First Video Project (5 minutes)

```bash
# 1. Create a project
sf new "My First Video"

# 2. Import your footage
sf media import /media/sdcard

# 3. Transcribe for subtitles
sf media transcribe video.mp4

# 4. Generate viral titles
sf youtube optimize "My Topic" --style educational

# 5. Upload to YouTube
sf youtube upload final.mp4 --title "My Video"
```

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/studioflow.git
cd studioflow

# Install dependencies
pip install -r requirements.txt

# Make the CLI available globally
pip install -e .

# Run first-time setup
sf setup
```

---

## Core Commands

### Project Management

```bash
# Create new project
sf new "Project Name" [OPTIONS]
  -t, --template TEXT     Project template [youtube/vlog/tutorial/shorts]
  -i, --import PATH       Import media from path after creation
  -p, --platform TEXT     Target platform [youtube/instagram/tiktok]
  -I, --interactive       Interactive mode with prompts

# List all projects
sf project list [OPTIONS]
  --archived              Include archived projects
  --sort TEXT            Sort by [name/date/size]

# Select project as current
sf project select "Name"

# Show current project status
sf status

# Archive completed project
sf project archive "Name"
```

### Media Operations

```bash
# Import media from SD card or folder
sf import <path> [OPTIONS]
  -p, --project TEXT      Target project (default: current)
  -o, --organize          Auto-organize by type (default: true)

# Scan path for media files
sf media scan <path>

# Transcribe audio/video using Whisper AI
sf media transcribe <file> [OPTIONS]
  --model TEXT           Whisper model [tiny/base/small/medium/large]
  --language TEXT        Language code or 'auto' for detection
  --formats TEXT         Output formats (comma-separated) [srt,vtt,txt,json]
  --chapters            Extract YouTube chapters from transcript
```

### YouTube Tools

```bash
# Generate optimized titles
sf youtube titles <topic> [OPTIONS]
  -v, --viral            Generate viral titles with CTR prediction
  -s, --style TEXT       Content style [educational/entertainment/tutorial/review]

# Generate viral-optimized titles and metadata
sf youtube optimize <topic> [OPTIONS]
  -s, --style TEXT       Style [educational/entertainment/tutorial/review]
  --platform TEXT        Platform [youtube/instagram/tiktok]
  -n, --count INT        Number of titles to generate

# Upload video to YouTube
sf youtube upload <video> [OPTIONS]
  -t, --title TEXT       Video title
  -d, --description TEXT Video description
  --tags TEXT           Comma-separated tags
  -p, --privacy TEXT     Privacy [private/unlisted/public]
  --thumbnail PATH       Thumbnail image path

# Analyze channel performance
sf youtube analyze [OPTIONS]
  -p, --project TEXT     Project name
  -c, --competitors      Analyze competitors
```

### DaVinci Resolve

```bash
# Sync project with DaVinci Resolve
sf resolve sync [OPTIONS]
  --project TEXT         Project name (default: current)

# Show DaVinci Resolve optimization profiles
sf resolve profiles [TYPE] [OPTIONS]
  TYPE                   Profile type [youtube/fx30/export/all]
  -d, --details         Show detailed settings

# Generate optimized export settings
sf resolve export <video> [OPTIONS]
  -p, --preset TEXT      Export preset [youtube_4k/youtube_1080p/instagram_reel/tiktok]
  --platform TEXT        Target platform (overrides preset)
  --show-command        Show FFmpeg command

# Open project in Resolve
sf edit [OPTIONS]
  -p, --project TEXT      Project to edit (default: current)
```

### Publishing

```bash
# Publish to YouTube
sf publish youtube [OPTIONS]
  --title TEXT          Video title
  --description TEXT    Video description
  --render             Render before publishing

# Publish to Instagram
sf publish instagram [OPTIONS]
  --post-type TEXT      Post type [reels/igtv/post]
  --caption TEXT        Post caption

# Export for all platforms
sf publish all
```

### Thumbnails

```bash
# Generate thumbnail
sf thumbnail generate [OPTIONS]
  --text TEXT           Main text for thumbnail
  --template TEXT       Template [viral/modern/tutorial/gaming/minimal]
  --background PATH     Background image

# Generate multiple templates
sf thumbnail batch [OPTIONS]
  --templates TEXT      Comma-separated template names
  --text TEXT          Main text for all thumbnails
```

### Configuration

```bash
# Manage configuration
sf config [OPTIONS]
  --set TEXT           Set config value (key=value)
  --get TEXT           Get config value
  --list              List all configuration
  --edit              Edit config file in editor
```

---

## Workflows

### Complete YouTube Video Workflow

```bash
# 1. Create project
sf new "Python Tutorial" --template youtube

# 2. Import footage
sf import /media/sdcard

# 3. Generate viral content
sf youtube optimize "Python Tutorial" --style educational

# 4. Transcribe for subtitles
sf media transcribe main_video.mp4 --chapters

# 5. Set up Resolve
sf resolve sync

# 6. Check export settings
sf resolve export final.mp4 --platform youtube

# 7. Upload to YouTube
sf youtube upload final.mp4 --title "Learn Python in 10 Minutes"
```

### Podcast Episode Workflow

```bash
# 1. Create podcast project
sf new "Podcast Ep 50" --template podcast

# 2. Import audio files
sf media import recordings/host.wav recordings/guest.wav

# 3. Process audio
sf effects apply podcast_mastering host.wav host_final.wav

# 4. Generate transcript
sf media transcribe host_final.wav --format srt

# 5. Create video version
sf resolve create "Podcast Video" --audio host_final.wav

# 6. Upload
sf publish multi-platform final.mp4
```

### Screen Recording Tutorial

```bash
# 1. Record screen
sf capture screen --audio --resolution 1080p

# 2. Create project
sf new "Python Tutorial" --template tutorial

# 3. Import recording
sf media import screen_recording.mp4

# 4. Remove silence
sf ai edit screen_recording.mp4 --remove-silence

# 5. Add annotations
sf effects compose "Tutorial" --template lower_third

# 6. Export and upload
sf youtube upload tutorial_final.mp4
```

### Multi-Platform Publishing

```bash
# Create and optimize for all platforms
sf new "Product Review" --platform youtube

# Generate platform-specific titles
sf youtube optimize "Product Review" --platform youtube
sf youtube optimize "Product Review" --platform instagram
sf youtube optimize "Product Review" --platform tiktok

# Export for each platform
sf publish all
```

---

## Auto-Editing System

The auto-editing system intelligently automates the entire YouTube episode editing workflow - from raw footage to a fully structured Resolve project ready for final editing.

### Quick Start

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

### Smart Bin System

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

### Power Bins (Reusable Assets)

Power Bins are persistent bins that appear in ALL projects:

```bash
# First time setup
sf auto-edit power-bins create

# Sync library assets to Power Bins
sf auto-edit power-bins sync
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

### Chapter Marker System

Chapters are automatically created from transcripts:

```bash
# From transcript (auto-detection)
sf auto-edit chapters --from-transcript transcript.srt

# From markers
sf auto-edit chapters --from-markers  # Import Resolve markers

# Manual entry
sf auto-edit chapters add "Introduction" --timestamp 0:00
sf auto-edit chapters add "Feature Demo" --timestamp 5:30
sf auto-edit chapters list
sf auto-edit chapters export  # Export as YouTube description format
```

**Smart Chapter Detection:**
- Detects topic changes (NLP analysis)
- Detects pauses/long silences
- Detects tone changes (question → answer)
- Uses keywords (intro, outro, conclusion)
- Minimum chapter length: 60 seconds

### Timeline Automation

```bash
# Create initial timeline assembly
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

### Intelligent Editing Features

```bash
# Silence removal
sf auto-edit remove-silence --threshold -40dB --min-duration 0.5s

# Filler word removal
sf auto-edit remove-fillers --aggressive

# Auto-pacing
sf auto-edit pace --target-duration 15:00

# Auto-transitions
sf auto-edit transitions --style smooth

# B-roll matching
sf auto-edit match-broll --smart
```

### Complete Episode Automation

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

---

## Library Workflow

> **📖 See [STORAGE_PATHS.md](STORAGE_PATHS.md) for complete storage paths reference.**

StudioFlow is optimized for working with the library directory structure (default: `/mnt/library`) where Resolve projects are managed.

### Initialize Library Workspace

```bash
# Initialize library with standard structure (defaults to /mnt/library)
sf library init

# Or specify a custom path
sf library init --path /path/to/library

# This creates:
# {library_path}/
#   ├── PROJECTS/
#   │   ├── DOCS/
#   │   ├── EPISODES/
#   │   └── FILMS/
#   ├── CACHE/
#   ├── PROXIES/
#   ├── EXPORTS/
#   │   ├── YOUTUBE/
#   │   ├── INSTAGRAM/
#   │   └── TIKTOK/
#   └── ASSETS/
#       ├── MUSIC/
#       ├── SFX/
#       ├── GRAPHICS/
#       └── LUTS/
```

### Check Library Status

```bash
# View library structure and disk usage
sf library status
```

### Create Resolve Project

```bash
# Create episode project
sf library create "EP001_My_Episode" --type episode

# Create documentary project
sf library create "DOC001_Dad_Project" --type doc --media /path/to/footage

# Create film project
sf library create "FILM001_Short" --type film
```

This automatically:
- Creates project in appropriate library subdirectory
- Configures Resolve with library paths (cache, proxies)
- Sets up bin structure
- Creates timeline stack
- Imports media if provided

### Complete Episode Workflow

```bash
# 1. Initialize library (one-time)
sf library init

# 2. Import Sony camera footage (library path defaults to /mnt/library)
sf import-sony --output /mnt/library/PROJECTS/EPISODES/EP001_Raw/01_footage

# 3. Create Resolve project
sf library create "EP001_My_Episode" --type episode \
  --media /mnt/library/PROJECTS/EPISODES/EP001_Raw/01_footage

# 4. Work in Resolve (project is now open)

# 5. Export when ready
sf export-youtube /mnt/library/EXPORTS/YOUTUBE/final.mp4
```

**Note**: Paths shown use `/mnt/library` (the default). If you've configured a different library path, use that instead. See [STORAGE_PATHS.md](STORAGE_PATHS.md) for configuration details.

# 6. Check all projects
sf library projects
```

---

## Auto-Import

Automatic SD card import with intelligent detection and organization.

### Installation

```bash
# Install the auto-import system
sudo /mnt/projects/studioflow/scripts/install-auto-import.sh
```

This will:
- Install udev rules for automatic SD card detection
- Set up logging
- Configure the import pipeline

### Usage

**Automatic (Recommended):**
Just insert your camera's SD card! StudioFlow will:
1. Detect it automatically
2. Show desktop notification
3. Import all media
4. Generate proxies
5. Organize everything

**Manual:**
```bash
# Import from specific mount point
sf media auto-import /media/eric/SONY_SD

# Watch for changes
sf media auto-import /media/eric/SONY_SD --watch
```

### File Organization

```
/mnt/ingest/Camera/Pool/
├── 2024-09/
│   ├── 20240923_Shoot/
│   │   ├── FX30_20240923_143022_C0001.MP4
│   │   ├── FX30_20240923_143522_C0002.MP4
│   │   └── ...

/mnt/studio/Projects/20240923_Shoot/
├── 01_Media/
│   ├── Original/
│   │   └── FX30/
│   │       ├── FX30_20240923_143022_C0001.MP4
│   │       └── ...
│   └── Proxy/
│       ├── FX30_20240923_143022_C0001_proxy.mov
│       └── ...
├── 02_Project/
│   └── create_timeline.py  # Run in Resolve console
└── import_20240923_143022.json  # Import manifest
```

### Supported Cameras

**Sony:**
- **FX30/FX3** - 4K XAVC-S, S-Cinetone
- **ZV-E10** - 1080p/4K, S-Cinetone
- **A7 IV** - 4K, S-Log3

### Monitoring

```bash
# Watch import progress
tail -f /var/log/studioflow-import.log

# Check if service is working
journalctl -f | grep studioflow

# Test udev rule
udevadm test /dev/sdb1
```

---

## Configuration

### YouTube API Setup

```bash
# 1. Get credentials from Google Cloud Console
# 2. Place in ~/.studioflow/youtube/credentials.json
# 3. Run any YouTube command to authenticate
sf youtube analyze
```

### Storage Paths

> **📖 See [STORAGE_PATHS.md](STORAGE_PATHS.md) for complete storage paths reference and configuration details.**

```yaml
# ~/.studioflow/config.yaml
storage:
  # Override defaults for your system
  ingest: /mnt/ingest              # SD card dumps
  active: /mnt/studio/Projects     # Current working projects
  archive: /mnt/archive           # Completed projects
  library: /mnt/library            # Resolve projects (default in CLI)
  
  # Optional: Separate cache/proxy for better performance
  cache: /mnt/cache               # Fast disk for cache
  proxy: /mnt/cache/Proxies        # Proxy files on cache disk
```

### Resolve Settings

```yaml
resolve:
  install_path: /opt/resolve
  api_path: /opt/resolve/Developer/Scripting
```

### Auto-Edit Settings

```yaml
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
```

---

## Troubleshooting

### Common Issues

**SD card not detected:**
1. Check if mounted: `lsblk`
2. Check udev: `udevadm monitor` (then insert card)
3. Check logs: `tail /var/log/studioflow-import.log`

**Import fails:**
1. Check permissions: `ls -la /mnt/ingest/Camera/Pool`
2. Check space: `df -h /mnt/ingest`
3. Run manually: `sf media auto-import /media/eric/CARD_NAME`

**Resolve can't find projects:**
1. Check Resolve connection: `sf resolve status`
2. List projects: `sf library projects`
3. Sync specific project: `sf resolve sync --project "PROJECT_NAME"`

**Chapters not detected:**
1. Check transcript format (SRT/JSON)
2. Verify timestamps are present
3. Try adjusting `min_duration` in config

**Smart bins not created:**
1. Ensure Resolve is running
2. Check footage path is accessible
3. Verify project can be created

### Getting Help

```bash
sf --help                    # General help
sf [command] --help          # Command help
sf quickstart                # Interactive guide
sf docs                      # Open documentation
```

### Debug Mode

```bash
# Enable debug logging
export SF_DEBUG=1
sf new "Test"

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

Debug output locations:
- `~/.studioflow/logs/` - Application logs
- `~/.studioflow/debug/` - Debug dumps
- Console with `SF_DEBUG=1`

---

**Last Updated**: 2025-01-22  
**Status**: Active Development


