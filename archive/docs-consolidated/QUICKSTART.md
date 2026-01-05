# StudioFlow Quick Start Guide 🚀

Welcome to StudioFlow! This guide will get you creating videos in minutes.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/studioflow.git
cd studioflow

# Install StudioFlow
pip install -e .

# Run first-time setup
sf setup
```

## Your First Video Project (5 minutes)

### 1. Create a Project
```bash
sf new "My First Video"
```

### 2. Import Your Footage
```bash
# From SD card
sf media import /media/sdcard

# From folder
sf media import ~/Downloads/footage
```

### 3. Edit in DaVinci Resolve
```bash
# Create timeline and sync with Resolve
sf resolve create "Main Edit"

# Or open existing project
sf edit
```

### 4. Apply Effects (Optional)
```bash
# Add glow effect
sf effects apply glow video.mp4 output.mp4

# Master audio
sf effects apply podcast_mastering audio.wav final.wav
```

### 5. Generate Thumbnail
```bash
sf thumbnail generate --text "AMAZING VIDEO" --style viral
```

### 6. Publish
```bash
# To YouTube
sf youtube upload final.mp4 --title "My Video"

# To multiple platforms
sf publish all
```

## Interactive Workflows

StudioFlow includes step-by-step guides for common workflows:

### YouTube Video
```bash
sf quickstart --workflow youtube
```
Complete YouTube production from recording to upload.

### Podcast Episode
```bash
sf quickstart --workflow podcast
```
Audio recording, mastering, and multi-platform distribution.

### Tutorial/Course
```bash
sf quickstart --workflow tutorial
```
Screen recording with annotations and chapters.

### Short-Form Content
```bash
sf quickstart --workflow short_form
```
Create TikToks, Reels, and YouTube Shorts.

### Multi-Camera
```bash
sf quickstart --workflow multicam
```
Sync and edit multiple camera angles.

## Essential Commands

### Project Management
```bash
sf new "Project Name"        # Create new project
sf project list              # List all projects
sf project select "Name"     # Switch projects
sf status                    # Show current project
```

### Media Operations
```bash
sf media import /path        # Import footage
sf media scan                # Find all media
sf media organize            # Auto-organize files
```

### Editing
```bash
sf resolve create "Timeline" # Create timeline
sf resolve sync              # Sync with Resolve
sf edit                      # Open in Resolve
```

### Effects
```bash
sf effects list              # Show available effects
sf effects apply [effect]    # Apply effect
sf effects preview [effect]  # Preview effect
```

### Publishing
```bash
sf youtube upload video.mp4  # Upload to YouTube
sf publish instagram         # Optimize for Instagram
sf thumbnail generate        # Create thumbnail
```

## Common Workflows

### YouTube Creator Workflow
1. Record your video
2. `sf new "Episode Title" --template youtube`
3. `sf media import /path/to/footage`
4. `sf resolve create "Main Edit"`
5. Edit in DaVinci Resolve
6. `sf effects apply podcast_mastering audio.wav`
7. `sf thumbnail generate --style youtube`
8. `sf youtube upload final.mp4`

### Podcast Production
1. Record audio
2. `sf new "Episode 1" --template podcast`
3. `sf media import recordings/`
4. `sf effects apply podcast_mastering raw.wav --preset spotify`
5. `sf ai transcribe final.wav`
6. `sf publish multi-platform`

### Quick Tutorial
1. `sf capture screen --audio`
2. `sf ai edit recording.mp4 --remove-silence`
3. `sf effects compose "Tutorial" --template lower_third`
4. `sf resolve export mp4 --preset tutorial`

## Pro Tips

### Batch Processing
```bash
# Process multiple files
for file in *.mp4; do
    sf effects apply glow "$file" "processed_$file"
done
```

### Templates
```bash
# List all templates
sf template list

# Apply template
sf template apply video_effect glow --output my_effect.setting
```

### Automation
```bash
# Full automated workflow
sf new "Daily Vlog" && \
sf media import /media/sd && \
sf resolve create "Edit" --effects && \
sf thumbnail generate --auto && \
sf youtube upload final.mp4 --schedule tomorrow
```

## Keyboard Shortcuts

When using interactive commands:
- `Enter` - Confirm/Continue
- `Ctrl+C` - Cancel
- `Tab` - Auto-complete
- `↑/↓` - Navigate options

## Getting Help

```bash
sf --help                    # General help
sf [command] --help          # Command help
sf quickstart                # Interactive guide
sf docs                      # Open documentation
```

## Troubleshooting

### First-Time Setup Issues
```bash
# Re-run setup
sf setup

# Check configuration
sf config --list
```

### Missing Dependencies
```bash
# Install FFmpeg (macOS)
brew install ffmpeg

# Install FFmpeg (Ubuntu)
sudo apt install ffmpeg

# Install Python packages
pip install -r requirements.txt
```

### DaVinci Resolve Connection
```bash
# Check Resolve status
sf resolve status

# Start Resolve
sf resolve start
```

## Join the Community

- GitHub Issues: Report bugs and request features
- Discord: Join our creator community
- YouTube: Watch tutorials and demos

---

**Ready to create?** Run `sf quickstart` to begin! 🎬