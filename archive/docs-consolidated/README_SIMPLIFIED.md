# StudioFlow (Simplified) 🎬

**Automated video production pipeline - now 70% simpler!**

## What It Does

StudioFlow helps you:
1. **Import** media with verification
2. **Edit** videos using FFmpeg
3. **Export** optimized for platforms
4. **Upload** to YouTube

That's it. No complex abstractions. Just what works.

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Create a project
sf new "My Video" --template youtube

# Import media (with verification)
sf import /media/sdcard

# Cut a clip
sf cut video.mp4 10 30 --output clip.mp4

# Concatenate clips
sf concat clip1.mp4 clip2.mp4 clip3.mp4

# Apply simple effect
sf effect video.mp4 fade_in --duration 2

# Normalize audio
sf audio video.mp4 --action normalize --lufs -16

# Export for platform
sf export video.mp4 --platform youtube

# Generate thumbnail
sf thumbnail video.mp4 --time 5.0

# Upload to YouTube
sf upload final.mp4 --title "My Awesome Video"
```

## Core Commands

### Project Management
```bash
sf new "Project Name" --template youtube
```
Templates: `youtube`, `podcast`, `short`, `basic`

### Media Import
```bash
sf import /path/to/media --verify
```
Imports with hash verification to prevent corruption.

### Video Editing
```bash
# Cut video
sf cut input.mp4 10 30 --output clip.mp4

# Concatenate videos
sf concat video1.mp4 video2.mp4 --output combined.mp4
```

### Effects (Simple)
```bash
sf effect video.mp4 fade_in --duration 2
sf effect video.mp4 brightness --value 0.2
sf effect video.mp4 blur --amount 5
```

Available effects: `fade_in`, `fade_out`, `blur`, `sharpen`, `brightness`, `contrast`, `saturation`, `crop`, `scale`, `speed`

### Audio
```bash
# Normalize to -16 LUFS (YouTube standard)
sf audio video.mp4 --action normalize --lufs -16

# Extract audio
sf audio video.mp4 --action extract
```

### Export
```bash
# Platform-optimized export
sf export video.mp4 --platform youtube
sf export video.mp4 --platform instagram
sf export video.mp4 --platform tiktok
```

### Upload
```bash
sf upload video.mp4 --title "Title" --description "Description"
```

### Utilities
```bash
# Get media info
sf info video.mp4

# Generate thumbnail
sf thumbnail video.mp4 --time 10.5

# Transcribe audio
sf transcribe audio.wav --model base
```

## What We Removed

We removed 70% of the codebase:
- ❌ Complex node graph system
- ❌ Abstract template polymorphism
- ❌ Particle animations
- ❌ 12 interpolation types
- ❌ Custom shaders
- ❌ Blockchain verification
- ❌ Complex composition layers
- ❌ AI everything
- ❌ Multi-format timeline exports
- ❌ Complex state management

## What We Kept

The essentials that actually matter:
- ✅ Media import with verification
- ✅ FFmpeg-based processing
- ✅ Platform-optimized export
- ✅ YouTube upload
- ✅ Audio normalization
- ✅ Whisper transcription
- ✅ Simple effects
- ✅ Thumbnail generation

## Architecture

```
studioflow/
├── core/
│   ├── ffmpeg.py          # All video operations
│   ├── simple_effects.py  # Basic effects
│   ├── simple_templates.py # Project templates
│   ├── verify.py          # File verification
│   ├── youtube_api.py     # YouTube upload
│   └── transcription.py   # Whisper transcription
└── cli/
    ├── main.py            # Entry point
    └── commands/
        └── simple.py      # All commands
```

Total: ~1,500 lines (was 5,000+)

## Dependencies

```
ffmpeg          # Video processing
typer           # CLI framework
rich            # Beautiful output
pyyaml          # Config files
google-api      # YouTube upload
openai-whisper  # Transcription (optional)
```

## Platform Presets

### YouTube
- Resolution: 1920x1080 or 3840x2160
- Codec: H.264 (libx264)
- Audio: AAC 320kbps
- Target: -14 LUFS

### Instagram
- Resolution: 1080x1080 or 1080x1920
- Max size: 100MB
- Duration: 60s (feed) / 90s (reels)

### TikTok
- Resolution: 1080x1920
- Codec: H.264
- Duration: Up to 3 minutes

## Error Handling

Every command:
- Verifies inputs exist
- Checks dependencies
- Reports clear errors
- Never corrupts data

## Examples

### Complete YouTube Workflow
```bash
# 1. Create project
sf new "Tutorial Video" --template youtube

# 2. Import footage
sf import /media/camera --verify

# 3. Edit clips
sf cut raw.mp4 10 120 --output main.mp4
sf cut raw.mp4 150 30 --output outro.mp4

# 4. Combine
sf concat intro.mp4 main.mp4 outro.mp4 --output combined.mp4

# 5. Add effects
sf effect combined.mp4 fade_in --output final.mp4

# 6. Normalize audio
sf audio final.mp4 --action normalize

# 7. Export
sf export final_normalized.mp4 --platform youtube

# 8. Generate thumbnail
sf thumbnail final_youtube.mp4 --time 30

# 9. Upload
sf upload final_youtube.mp4 --title "Amazing Tutorial"
```

### Podcast Workflow
```bash
# 1. Create project
sf new "Podcast Ep 1" --template podcast

# 2. Import audio
sf import recordings/

# 3. Normalize audio
sf audio episode.wav --action normalize --lufs -16

# 4. Transcribe
sf transcribe episode_normalized.wav

# 5. Create video with waveform
sf export episode_normalized.wav --platform youtube
```

## Why It's Better Now

1. **Simpler**: 70% less code
2. **Faster**: No complex abstractions
3. **Reliable**: Fewer things to break
4. **Clear**: Obvious what each command does
5. **Maintainable**: Anyone can contribute

## Support

- GitHub Issues: Report bugs
- Documentation: This README
- Dependencies: Just install FFmpeg

---

**StudioFlow: Do less, but do it well.**