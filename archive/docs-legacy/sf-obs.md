# sf-obs - OBS Studio Automation

## Overview
`sf-obs` provides automated OBS Studio configuration for viral content creation. Features WebSocket control, automatic scene switching, replay buffer management, and optimized streaming settings for YouTube, Instagram, and TikTok.

## Installation
```bash
sf-obs       # Direct command
sf obs       # Via master command
sfobs        # Quick alias

# Required: OBS Studio with WebSocket plugin
# Optional: obs-websocket-py for automation
pip install obs-websocket-py
```

## Commands

### setup
Auto-configure OBS for project recording.

```bash
sf-obs setup "My Project"
sf-obs setup "Tutorial" --auto  # WebSocket auto-config
```

**Creates:**
- Recording directory in project
- Optimized encoding settings
- Hotkey configuration
- WebSocket automation rules

### viral-scenes
Create scene collection optimized for viral content.

```bash
sf-obs viral-scenes
```

**Generates 6 Scenes:**
1. **🔥 Hook Shot** - High energy opening
2. **📱 Screen + Face** - Tutorial layout
3. **🎬 B-Roll Ready** - Quick cuts
4. **💬 Story Time** - Personal segments
5. **📊 Data Display** - Results/proof
6. **🎯 CTA Screen** - Call-to-action

### highlights
Set up automatic highlight detection.

```bash
sf-obs highlights "My Project"
sf-obs highlights "Gaming" --duration 60
```

**Features:**
- Replay buffer (30-60 seconds)
- Audio peak detection
- Scene change markers
- Viral moment checklist

### stream
Configure platform-specific streaming.

```bash
sf-obs stream --platform youtube
sf-obs stream --platform instagram  # Vertical
sf-obs stream --platform tiktok     # Vertical
```

**Optimizes:**
- Bitrate and resolution
- Keyframe intervals
- Audio settings
- Platform requirements

### monitor
Monitor OBS performance in real-time.

```bash
sf-obs monitor
```

**Shows:**
- FPS and CPU usage
- Dropped frames
- Memory usage
- Stream health

## WebSocket Automation

### Enable WebSocket
```bash
# In OBS Studio:
Tools → WebSocket Server Settings
✓ Enable WebSocket Server
Port: 4455
Password: (leave blank for local)
```

### Auto-Configuration
```python
# Automatic via WebSocket:
- Sets recording path
- Configures bitrate
- Updates output format
- Applies optimal settings
```

### Remote Control
```bash
# Control OBS remotely
sf-obs control start-recording
sf-obs control stop-recording
sf-obs control switch-scene "Hook Shot"
sf-obs control save-replay
```

## Viral Scene Templates

### Hook Shot Scene
```yaml
Sources:
  - Webcam: Full frame, tight crop
  - Text: Large hook text (72pt)
  - Border: Red attention grabber
Purpose: First 5 seconds maximum impact
Hotkey: Ctrl+1
```

### Screen + Face Scene
```yaml
Sources:
  - Display: Main content
  - Webcam: PiP bottom-right (20%)
  - Audio: Mic + Desktop (30%)
Purpose: Standard tutorial/reaction
Hotkey: Ctrl+2
```

### B-Roll Ready Scene
```yaml
Sources:
  - Media Slot 1: Quick cuts
  - Media Slot 2: Supporting footage
  - Label: Context text
Purpose: Retention through variety
Hotkey: Ctrl+3
```

## Recording Settings

### High Quality (Local)
```yaml
Encoder: NVENC H.264 (or x264)
Bitrate: 50000 Kbps (50 Mbps)
Keyframe: 2 seconds
Preset: Quality
Profile: High
Format: MKV → MP4 (auto-remux)
```

### Streaming Settings

#### YouTube
```yaml
Server: rtmp://a.rtmp.youtube.com/live2
Bitrate: 6000 Kbps (1080p30)
Audio: 128 Kbps AAC
Keyframe: 2 seconds
```

#### Instagram
```yaml
Server: rtmps://live-upload.instagram.com:443/rtmp
Bitrate: 4000 Kbps
Resolution: 1080x1920 (vertical!)
Requires: Stream key from app
```

#### TikTok
```yaml
Server: rtmp://push.tiktop.com/live
Bitrate: 4000 Kbps
Resolution: 1080x1920 (vertical!)
Requires: 1000+ followers
```

## Automatic Scene Switching

### Scene Automation Rules
```bash
# Install Advanced Scene Switcher plugin
# Then use these rules:

1. Start → Hook Shot (5 seconds)
2. After Hook → Screen + Face
3. On Idle (3s) → Insert B-Roll (2s)
4. Low Audio → Story Time
5. Every 90s → Quick cut (retention)
6. Near End → CTA Screen
```

### Time-Based Switching
```javascript
Rules:
  0:00-0:05 → Hook Shot
  0:05-0:15 → Screen + Face
  Every 1:30 → B-Roll (2 sec)
  Last 0:20 → CTA Screen
```

## Replay Buffer System

### Configuration
```yaml
Replay Buffer:
  Duration: 30 seconds
  Hotkey: Alt+H (save last 30s)
  Path: Project/01_FOOTAGE/HIGHLIGHTS/
  Format: Same as recording
```

### Viral Moment Detection
```python
Auto-Save Triggers:
- Audio peak > -6 dB (reactions)
- Silence > 3 seconds (important points)
- Scene changes (transitions)
- Manual hotkey (Alt+H)
```

### Highlight Checklist
```markdown
□ Big reaction
□ Surprising result
□ Funny moment
□ Key revelation
□ Emotional peak
□ Visual wow factor
```

## Performance Optimization

### GPU Encoding (NVENC)
```bash
# For NVIDIA GPUs
Encoder: NVENC H.264
Preset: Quality
Profile: High
Look-ahead: On
Psycho Visual: On
GPU: 0
Max B-frames: 2
```

### CPU Encoding (x264)
```bash
# For systems without NVENC
Encoder: x264
CPU Usage: Fast
Profile: Main
Tune: Film
```

### Performance Tips
1. **Close unnecessary apps** before recording
2. **Use GPU encoding** when available
3. **Record to SSD** not HDD
4. **Disable preview** when not needed
5. **Lower canvas resolution** if dropping frames

## Growth Optimization

### YouTube Best Practices
```yaml
Schedule:
  Days: Tuesday, Thursday
  Time: 2-4 PM EST
  Consistency: Same time weekly

Stream Setup:
  Starting Soon: 5 minutes
  Engagement: Read chat, acknowledge viewers
  CTAs: Every 10 minutes
  End: Raid similar channel
```

### Instagram Live Tips
```yaml
Preparation:
  Announce: 24h before in stories
  Time: Peak audience hours
  Save: As IGTV after stream
  Collaborate: Use "Live with" feature
```

### TikTok Live Strategy
```yaml
Content:
  Interactive: Games, Q&A
  Trending: Use popular sounds
  Peak Times: 7-9 AM, 7-11 PM
  Gifts: Acknowledge supporters
  Battles: Collaborate with others
```

## Configuration Files

### Project Config
`Project/.sf/obs_config.json`:
```json
{
  "recording": {
    "path": "/path/to/project/01_FOOTAGE/OBS_RECORDINGS",
    "format": "mkv",
    "video_bitrate": 50000,
    "audio_bitrate": 320
  },
  "hotkeys": {
    "start_recording": "Ctrl+R",
    "stop_recording": "Ctrl+Shift+R",
    "save_replay": "Alt+H"
  },
  "automation": {
    "replay_buffer": true,
    "buffer_seconds": 30
  }
}
```

### Global Settings
`~/.config/studioflow/obs.yml`:
```yaml
websocket:
  host: localhost
  port: 4455
  password: ""
  
defaults:
  encoder: nvenc
  quality: 50000
  fps: 30
  
platforms:
  youtube:
    enabled: true
    key: ${YOUTUBE_STREAM_KEY}
  instagram:
    enabled: true
  tiktok:
    enabled: true
```

## Automation Examples

### Complete Recording Setup
```bash
#!/bin/bash
# Full OBS automation

PROJECT="Tutorial_Video"

# Create project
sf-project create "$PROJECT"

# Setup OBS
sf-obs setup "$PROJECT" --auto

# Create viral scenes
sf-obs viral-scenes

# Configure highlights
sf-obs highlights "$PROJECT"

# Start monitoring
sf-obs monitor &

echo "Ready to record! Press Ctrl+R in OBS"
```

### Stream Scheduler
```python
#!/usr/bin/env python3
import schedule
import subprocess

def start_stream():
    subprocess.run(["sf-obs", "control", "start-streaming"])
    
def stop_stream():
    subprocess.run(["sf-obs", "control", "stop-streaming"])

# Schedule streams
schedule.every().tuesday.at("14:00").do(start_stream)
schedule.every().tuesday.at("15:00").do(stop_stream)
```

## Troubleshooting

**"OBS not found":**
```bash
# Install OBS Studio
sudo add-apt-repository ppa:obsproject/obs-studio
sudo apt update
sudo apt install obs-studio
```

**"WebSocket connection failed":**
- Enable WebSocket in OBS settings
- Check port 4455 is not blocked
- Verify password if set

**"Dropping frames":**
- Lower bitrate or resolution
- Switch to GPU encoding
- Close background apps
- Check CPU/GPU usage

**"Stream key error":**
- Get key from platform:
  - YouTube: Studio → Go Live
  - Instagram: Use app
  - TikTok: Need 1000+ followers

## Performance Benchmarks

- **Setup time**: < 30 seconds
- **Scene switching**: < 50ms
- **Replay save**: < 1 second
- **WebSocket latency**: < 10ms
- **CPU overhead**: < 5% for automation

## Related Tools

- `sf-project` - Create recording projects
- `sf-capture` - Alternative capture tool
- `sf-youtube` - Optimize recordings
- `sf-resolve` - Edit captured footage