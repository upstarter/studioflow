# sf-audio - Audio Processing & Transcription

## Overview
`sf-audio` provides professional audio tools for video production including AI transcription, noise reduction, music library management, and audio optimization. Integrates with Whisper AI for accurate subtitles and captions.

## Installation
```bash
sf-audio      # Direct command
sf audio      # Via master command
sftrans       # Alias for transcribe
sfdenoise     # Alias for denoise
```

## Commands

### transcribe
Generate accurate transcriptions using Whisper AI.

```bash
sf-audio transcribe video.mp4
sf-audio transcribe podcast.wav --model large
sf-audio transcribe "My Project" --format srt
```

**Options:**
- `-m, --model` - Whisper model (tiny/base/small/medium/large)
- `-f, --format` - Output format (srt/vtt/txt/json)
- `-l, --language` - Force language (auto-detect default)
- `--timestamps` - Include word-level timestamps

**Output Formats:**
- **SRT** - YouTube/video platforms
- **VTT** - Web video players
- **TXT** - Clean transcript
- **JSON** - Programmatic use

### denoise
Remove background noise and enhance audio.

```bash
sf-audio denoise recording.wav
sf-audio denoise "My Project" --aggressive
sf-audio denoise video.mp4 --profile voice
```

**Profiles:**
- `voice` - Optimize for speech
- `music` - Preserve music quality
- `podcast` - Balanced for talk shows
- `aggressive` - Maximum noise removal

### normalize
Standardize audio levels for consistency.

```bash
sf-audio normalize *.wav --target -16
sf-audio normalize "My Project" --standard youtube
```

**Standards:**
- `youtube` - -13 to -15 LUFS
- `podcast` - -16 to -18 LUFS
- `broadcast` - -23 LUFS
- `streaming` - -14 LUFS

### compress
Apply dynamic range compression.

```bash
sf-audio compress voice.wav --ratio 3:1
sf-audio compress podcast.mp3 --preset vocal
```

**Presets:**
- `vocal` - Speech optimization
- `music` - Musical dynamics
- `broadcast` - TV/radio standard
- `youtube` - Online video

### library
Manage royalty-free music library.

```bash
sf-audio library search "upbeat electronic"
sf-audio library add /path/to/music --category "background"
sf-audio library list --mood energetic
```

**Categories:**
- Background music
- Intro/outro stings
- Sound effects
- Ambient tracks
- Transitions

## Transcription Features

### Whisper AI Integration
```python
Models Available:
- tiny: 39M params, ~1GB, fastest
- base: 74M params, ~1.5GB
- small: 244M params, ~2GB
- medium: 769M params, ~5GB
- large: 1550M params, ~10GB, most accurate
```

### Multi-Language Support
```bash
# Auto-detect language
sf-audio transcribe video.mp4

# Force specific language
sf-audio transcribe video.mp4 --language spanish
sf-audio transcribe video.mp4 --language japanese
```

### Caption Generation
```bash
# YouTube captions
sf-audio transcribe video.mp4 --format srt --style youtube

# Instagram captions (centered)
sf-audio transcribe reel.mp4 --format srt --style instagram

# TikTok captions (animated)
sf-audio transcribe short.mp4 --format srt --style tiktok
```

## Audio Enhancement

### Podcast Processing Chain
```bash
#!/bin/bash
# Complete podcast audio pipeline

INPUT="podcast_raw.wav"
OUTPUT="podcast_final.mp3"

# 1. Remove noise
sf-audio denoise "$INPUT" --profile podcast

# 2. Normalize levels
sf-audio normalize "${INPUT%.wav}_denoised.wav" --target -16

# 3. Apply compression
sf-audio compress "${INPUT%.wav}_normalized.wav" --preset podcast

# 4. Generate transcript
sf-audio transcribe "${INPUT%.wav}_compressed.wav" --format txt

# 5. Export final
ffmpeg -i "${INPUT%.wav}_compressed.wav" -b:a 128k "$OUTPUT"
```

### Voice Over Optimization
```bash
# Clean up voice recording
sf-audio denoise voiceover.wav --profile voice
sf-audio normalize voiceover_denoised.wav --standard youtube
sf-audio compress voiceover_normalized.wav --gentle
```

## Music Library Management

### Organization Structure
```
~/.config/studioflow/music/
├── background/
│   ├── calm/
│   ├── energetic/
│   └── dramatic/
├── intros/
├── outros/
├── transitions/
└── sfx/
    ├── whoosh/
    ├── impacts/
    └── ambient/
```

### Smart Search
```bash
# Search by mood
sf-audio library search --mood "uplifting"

# Search by tempo
sf-audio library search --bpm 120-140

# Search by duration
sf-audio library search --duration 30-60

# Combined search
sf-audio library search "electronic" --mood "energetic" --bpm 128
```

### Metadata Management
```json
{
  "file": "track_001.mp3",
  "title": "Upbeat Electronic",
  "mood": ["energetic", "positive"],
  "bpm": 128,
  "duration": 180,
  "tags": ["background", "tech", "modern"],
  "license": "CC0",
  "usage_count": 5
}
```

## Platform-Specific Processing

### YouTube
```bash
# Optimal YouTube audio
sf-audio process "project" --platform youtube
# Sets: -13 LUFS, light compression, clear speech
```

### Instagram
```bash
# Instagram-ready audio
sf-audio process "project" --platform instagram
# Sets: -14 LUFS, mobile-optimized EQ
```

### TikTok
```bash
# TikTok audio optimization
sf-audio process "project" --platform tiktok
# Sets: -14 LUFS, enhanced bass for phone speakers
```

## Batch Processing

### Project-Wide Processing
```bash
# Process all audio in project
sf-audio process-project "My Video"
# Automatically:
# - Denoises all audio
# - Normalizes levels
# - Generates transcripts
# - Creates subtitles
```

### Bulk Transcription
```bash
# Transcribe multiple files
for file in *.mp4; do
  sf-audio transcribe "$file" --model small
done

# Or use batch mode
sf-audio transcribe-batch *.mp4 --parallel 4
```

## Advanced Features

### Audio Ducking
```bash
# Duck music under voice
sf-audio duck music.mp3 --sidechain voice.wav --ratio 0.3
```

### EQ Presets
```bash
# Apply EQ curves
sf-audio eq voice.wav --preset "podcast"
sf-audio eq music.mp3 --preset "youtube"
sf-audio eq voice.wav --custom "100:+3,1000:-2,10000:+1"
```

### Crossfade Generation
```bash
# Create smooth transitions
sf-audio crossfade track1.mp3 track2.mp3 --duration 2
```

## Quality Settings

### Export Formats
```yaml
YouTube:
  format: AAC
  bitrate: 256kbps
  sample_rate: 48kHz
  
Podcast:
  format: MP3
  bitrate: 128kbps
  sample_rate: 44.1kHz
  
Professional:
  format: WAV
  bit_depth: 24bit
  sample_rate: 48kHz
```

## Configuration

`~/.config/studioflow/audio.yml`:
```yaml
whisper:
  model: small
  language: auto
  device: cuda  # or cpu
  
processing:
  denoise_level: medium
  normalize_target: -16
  compression_ratio: 3:1
  
library:
  path: ~/.config/studioflow/music
  auto_tag: true
  scan_on_add: true
  
defaults:
  output_format: wav
  sample_rate: 48000
  bit_depth: 24
```

## Performance Tips

### Whisper Optimization
1. **Use GPU** if available (10x faster)
2. **Choose right model** - small is usually sufficient
3. **Batch process** overnight for large projects
4. **Pre-process** audio (denoise first)
5. **Cache results** for repeated use

### Processing Speed
- **Denoise**: ~10x realtime on CPU
- **Normalize**: ~100x realtime
- **Compress**: ~50x realtime
- **Transcribe**: ~1-5x realtime (model dependent)

## Troubleshooting

**"Whisper model not found":**
```bash
# Install Whisper
pip install openai-whisper

# Download model
whisper --model small --download-only
```

**"CUDA out of memory":**
- Use smaller Whisper model
- Process in chunks
- Switch to CPU mode

**"Audio sync issues":**
- Check frame rates match
- Verify sample rates
- Use constant bitrate encoding

**"Poor transcription accuracy":**
- Use larger model
- Pre-process audio (denoise)
- Specify language explicitly
- Check audio quality

## Integration Examples

### With sf-youtube
```bash
# Generate optimized captions
sf-audio transcribe video.mp4 --format srt
sf-youtube metadata "project" --captions video.srt
```

### With sf-resolve
```bash
# Prepare audio for editing
sf-audio process-project "My Video"
sf-resolve import-audio "My Video"
```

### Automation Script
```bash
#!/bin/bash
# Auto-process new recordings

inotifywait -m ~/Recordings -e create |
while read path action file; do
  if [[ "$file" =~ .*\.wav$ ]]; then
    sf-audio denoise "$path/$file"
    sf-audio transcribe "$path/$file"
  fi
done
```

## Related Tools

- `sf-project` - Organize audio in projects
- `sf-youtube` - Optimize for platforms
- `sf-ai` - Generate voice-over scripts
- `sf-resolve` - Import processed audio