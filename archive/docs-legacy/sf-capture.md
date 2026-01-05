# sf-capture - Screenshot & Recording Tools

## Overview
`sf-capture` provides intelligent screenshot and screen recording tools optimized for tutorial creation, software documentation, and comparison videos. It automatically crops browser chrome, standardizes resolutions, and organizes captures.

## Installation
```bash
sf-capture  # Direct command
sf capture  # Via master command
sfcap       # Alias for snap (after sourcing .bashrc)
sfrec       # Alias for record
```

## Commands

### snap
Take an intelligent screenshot with automatic processing.

```bash
sf-capture snap
sf-capture snap --window  # Select specific window
sf-capture snap --area    # Select screen area
sf-capture snap --delay 5  # 5-second delay
```

**Features:**
- Auto-detects browser windows
- Crops browser chrome (tabs, URL bar)
- Standardizes to 1920x1080 or 1080x1920
- Names with timestamp
- Saves to project or ~/Captures

### record
Record screen with optimized settings.

```bash
sf-capture record
sf-capture record --duration 60  # 60-second recording
sf-capture record --audio        # Include audio
sf-capture record --webcam       # Picture-in-picture
```

**Options:**
- `-d, --duration` - Recording length (seconds)
- `-a, --audio` - Include system/mic audio
- `-w, --webcam` - Add webcam overlay
- `-f, --fps` - Frame rate (default: 30)

### organize
Organize captures into project structure.

```bash
sf-capture organize "My Project"
sf-capture organize ~/Captures --auto
```

**Actions:**
- Moves captures to project folders
- Renames by content type
- Groups by date/session
- Removes duplicates

### grid
Create comparison grids for AI tool videos.

```bash
sf-capture grid tool1.png tool2.png tool3.png
sf-capture grid *.png --columns 2 --labels
```

**Options:**
- `-c, --columns` - Grid columns (default: auto)
- `-l, --labels` - Add tool names
- `-t, --title` - Grid title
- `-b, --border` - Border width

## Intelligent Features

### Browser Chrome Detection
```python
# Automatically detects and crops:
- Chrome/Firefox/Safari chrome
- Tab bars
- URL bars
- Bookmarks
- Extensions
```

### Resolution Standardization
- **Landscape**: 1920x1080 (16:9)
- **Portrait**: 1080x1920 (9:16)
- **Square**: 1080x1080 (1:1)
- **Auto-padding**: Maintains aspect ratio

### AI Tool Comparison
Optimized for comparing AI tools:
```bash
# Capture multiple tools
for tool in chatgpt claude gemini; do
  sf-capture snap --window "$tool"
  sleep 2
done

# Create comparison grid
sf-capture grid *.png --labels --title "AI Comparison"
```

## Project Integration

### Auto-Organization
Captures automatically organize into projects:
```
Project/
├── 01_FOOTAGE/
│   ├── SCREENSHOTS/
│   │   ├── 20250114_143022_chrome.png
│   │   └── 20250114_143045_vscode.png
│   └── RECORDINGS/
│       └── 20250114_143100_tutorial.mp4
```

### Naming Convention
```
YYYYMMDD_HHMMSS_[source]_[type].[ext]

Examples:
20250114_143022_chrome_snap.png
20250114_143100_obs_record.mp4
20250114_143200_grid_comparison.png
```

## Advanced Features

### Batch Processing
```bash
# Process all screenshots in directory
sf-capture process ~/Downloads/*.png

# Standardize resolution
sf-capture standardize *.png --resolution 1920x1080

# Create thumbnails
sf-capture thumbnail *.png --size 320x180
```

### OCR Text Extraction
```bash
sf-capture ocr screenshot.png
sf-capture ocr *.png --output text.md
```

### Annotation
```bash
sf-capture annotate screenshot.png
# Opens simple annotation tool:
# - Arrows
# - Rectangles
# - Text
# - Blur sensitive info
```

## Platform-Specific Formats

### YouTube (Landscape)
```bash
sf-capture snap --youtube  # 1920x1080, 16:9
```

### Instagram (Square/Portrait)
```bash
sf-capture snap --instagram  # 1080x1080 or 1080x1920
```

### TikTok (Portrait)
```bash
sf-capture snap --tiktok  # 1080x1920, 9:16
```

## Recording Presets

### Tutorial Recording
```bash
sf-capture record --preset tutorial
# Settings:
# - 1920x1080 @ 30fps
# - System audio + mic
# - Mouse highlighting
# - Keystroke display
```

### Quick Demo
```bash
sf-capture record --preset demo
# Settings:
# - 1280x720 @ 60fps
# - Webcam overlay
# - 60-second limit
```

### Software Review
```bash
sf-capture record --preset review
# Settings:
# - 1920x1080 @ 24fps
# - High quality
# - No time limit
```

## Automation Scripts

### Auto-Capture Workflow
```bash
#!/bin/bash
# Capture AI tool comparison

tools=("ChatGPT" "Claude" "Gemini")
project="AI_Comparison_$(date +%Y%m%d)"

sf-project create "$project"

for tool in "${tools[@]}"; do
  echo "Open $tool and press Enter"
  read
  sf-capture snap --window
  sleep 1
done

sf-capture grid *.png --labels --title "AI Tools Comparison"
sf-capture organize "$project"
```

## Configuration

`~/.config/studioflow/capture.yml`:
```yaml
defaults:
  screenshot:
    format: png
    quality: 95
    crop_browser: true
    standardize: true
  
  recording:
    fps: 30
    codec: h264
    audio: true
    webcam: false
  
  storage:
    screenshots: ~/Captures/Screenshots
    recordings: ~/Captures/Recordings
    auto_organize: true

hotkeys:
  snap: "Ctrl+Shift+S"
  record: "Ctrl+Shift+R"
  stop: "Ctrl+Shift+X"
```

## Tips & Tricks

### High-Quality Captures
1. **Clean desktop** before recording
2. **Hide personal info** in browser
3. **Use consistent window sizes**
4. **Disable notifications**
5. **Check audio levels** before recording

### For Tutorials
1. **Plan captures** in advance
2. **Use consistent theme** across apps
3. **Capture at highest resolution**
4. **Keep file names descriptive**
5. **Organize immediately** after session

### For Comparisons
1. **Same viewport size** for all tools
2. **Similar content** in each capture
3. **Consistent positioning**
4. **Clear labels** in grids
5. **Export at target resolution**

## Troubleshooting

**"No window detected":**
- Click on window to focus
- Use `--area` for manual selection
- Check window manager compatibility

**"Browser chrome not cropped":**
- Update browser detection rules
- Use `--no-crop` to disable
- Manually specify crop region

**"Recording has no audio":**
- Check PulseAudio/PipeWire settings
- Test with `--audio-test`
- Verify microphone permissions

## Performance

- **Screenshot**: < 0.5 seconds
- **Chrome crop**: < 0.2 seconds
- **Standardization**: < 0.3 seconds
- **Grid creation**: < 1 second for 9 images
- **Recording**: Negligible overhead

## Related Tools

- `sf-project` - Organize captures into projects
- `sf-obs` - Advanced recording with OBS
- `sf-youtube` - Optimize captures for YouTube
- `sf-storage` - Manage capture storage