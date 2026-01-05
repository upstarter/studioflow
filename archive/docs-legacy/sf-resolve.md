# sf-resolve - DaVinci Resolve Automation

## Overview
`sf-resolve` automates DaVinci Resolve project setup, color grading, rendering, and workflow optimization. Integrates with Resolve's Python API for advanced automation and uses PowerGrades for consistent color workflows.

## Installation
```bash
sf-resolve   # Direct command
sf resolve   # Via master command
sfresolve    # Quick alias

# Required: DaVinci Resolve Studio (for Python API)
# Note: Python API requires Studio version
```

## Commands

### setup
Create and configure Resolve project.

```bash
sf-resolve setup "My Project"
sf-resolve setup "Tutorial" --template youtube
sf-resolve setup "Commercial" --framerate 24
```

**Options:**
- `-t, --template` - Project template
- `-f, --framerate` - FPS (24/25/30/60)
- `-r, --resolution` - 1080p/4K/8K
- `--color-space` - Rec709/Rec2020/ACES

### import
Auto-import footage from project directories.

```bash
sf-resolve import "My Project"
sf-resolve import "Tutorial" --organize
```

**Features:**
- Scans project folders
- Creates bins by type
- Detects framerate
- Organizes by date

### color
Apply color grading presets.

```bash
sf-resolve color "My Project" --style cinematic
sf-resolve color "Tutorial" --lut osiris
sf-resolve color "Review" --powergrade viral
```

**Styles:**
- `cinematic` - Film look
- `viral` - High contrast YouTube
- `natural` - Minimal grading
- `vintage` - Retro aesthetic
- `osiris` - VisionColor LUTs

### render
Export with optimized settings.

```bash
sf-resolve render "My Project"
sf-resolve render "Tutorial" --preset youtube
sf-resolve render "Short" --preset instagram
```

**Presets:**
- `youtube` - H.264, 1080p, high quality
- `instagram` - Square/vertical, optimized
- `tiktok` - Vertical, mobile-optimized
- `master` - ProRes/DNxHR archival

### powergrade
Manage PowerGrade templates.

```bash
sf-resolve powergrade create "My Look"
sf-resolve powergrade apply "Cinematic" "My Project"
sf-resolve powergrade list
```

## Python API Automation

### Project Setup
```python
# Automated via Python API:
import DaVinciResolveScript as dvr

resolve = dvr.scriptapp("Resolve")
project_manager = resolve.GetProjectManager()

# Create project
project = project_manager.CreateProject("My_Project")
project.SetSetting("timelineFrameRate", "30")
project.SetSetting("timelineResolutionWidth", "1920")
project.SetSetting("timelineResolutionHeight", "1080")
```

### Auto-Import
```python
# Import footage automatically
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()

# Create organized bins
footage_bin = media_pool.AddSubFolder(root_folder, "01_FOOTAGE")
audio_bin = media_pool.AddSubFolder(root_folder, "02_AUDIO")
graphics_bin = media_pool.AddSubFolder(root_folder, "03_GRAPHICS")

# Import files
media_pool.ImportMedia(["/path/to/footage/*.mp4"], footage_bin)
```

### Timeline Creation
```python
# Create timeline with settings
timeline = media_pool.CreateEmptyTimeline("Main Edit")
timeline.SetSetting("useCustomSettings", True)
timeline.SetSetting("timelineFrameRate", "30")
timeline.SetSetting("timelineResolutionWidth", "1920")
timeline.SetSetting("timelineResolutionHeight", "1080")
```

## Color Grading

### PowerGrade System
```
PowerGrades Location:
~/.local/share/DaVinciResolve/PowerGrades/

Categories:
├── YouTube/
│   ├── HighContrast.dpx
│   ├── Vibrant.dpx
│   └── Cinematic.dpx
├── Instagram/
│   ├── Warm.dpx
│   └── Film.dpx
└── Master/
    └── Neutral.dpx
```

### Osiris VisionColor LUTs
```yaml
Installed LUTs:
  Vision6: Film emulation
  Vision8: Modern cinema
  VisionT: Vintage film
  KDX: Kodak emulation
  FPE: Fuji emulation
  
Locations:
  - /opt/resolve/LUT/
  - ~/.local/share/DaVinciResolve/LUT/
  - /mnt/nas/Luts/Osiris/
```

### Node Templates
```python
Basic Color Correction:
  1. Primary Correction (Lift/Gamma/Gain)
  2. Curves (S-curve for contrast)
  3. Color Warper (Skin tone)
  4. Vignette (Subtle darkening)
  5. Film Grain (Texture)

YouTube Optimization:
  1. Contrast boost (+15%)
  2. Saturation boost (+10%)
  3. Sharpening (minimal)
  4. Skin tone protection
  5. Highlight roll-off
```

## Rendering Presets

### YouTube (H.264)
```yaml
Format: QuickTime
Codec: H.264
Resolution: 1920x1080
Framerate: Match timeline
Bitrate: 16-20 Mbps
Audio: AAC 320kbps
Color: Rec.709
```

### Instagram (Square/Vertical)
```yaml
Format: MP4
Codec: H.264
Resolution: 1080x1080 or 1080x1920
Framerate: 30fps
Bitrate: 10-15 Mbps
Audio: AAC 128kbps
Duration: Max 60 seconds (feed)
```

### TikTok (Vertical)
```yaml
Format: MP4
Codec: H.264
Resolution: 1080x1920
Framerate: 30fps
Bitrate: 10-12 Mbps
Audio: AAC 128kbps
Duration: 15-60 seconds
```

### Master Archive (ProRes)
```yaml
Format: QuickTime
Codec: ProRes 422 HQ
Resolution: Original
Framerate: Original
Bitrate: ~220 Mbps (1080p)
Audio: PCM 48kHz 24-bit
Color: Original space
```

## Workflow Optimization

### Proxy Workflow
```bash
# Generate proxies for smooth editing
sf-resolve proxy "My Project" --resolution quarter

# Settings:
Format: ProRes Proxy
Resolution: 1/4 original
Location: Project/Proxies/
Auto-link: Yes
```

### Cache Management
```bash
# Optimize cache settings
sf-resolve cache --clean
sf-resolve cache --size 100GB
sf-resolve cache --location /fast-ssd/
```

### Collaborative Features
```bash
# Set up project for collaboration
sf-resolve collaborate "My Project" --database postgresql
sf-resolve collaborate --share "Editor Name"
```

## Project Templates

### YouTube Template
```python
Settings:
  - Timeline: 1920x1080 @ 30fps
  - Color: Rec.709 Gamma 2.4
  - Audio: 48kHz 24-bit
  - Render: H.264 16 Mbps
  
Bin Structure:
  - 01_FOOTAGE/A_ROLL
  - 01_FOOTAGE/B_ROLL
  - 02_AUDIO/MUSIC
  - 02_AUDIO/SFX
  - 03_GRAPHICS/TITLES
  - 03_GRAPHICS/OVERLAYS
  - 04_EXPORTS/DRAFTS
  - 04_EXPORTS/FINAL
```

### Commercial Template
```python
Settings:
  - Timeline: 3840x2160 @ 24fps
  - Color: Rec.2020 or ACES
  - Audio: 48kHz 24-bit
  - Render: ProRes 422 HQ
  
Bin Structure:
  - RAW_FOOTAGE/
  - SELECTS/
  - COLOR_CORRECTED/
  - VFX_SHOTS/
  - AUDIO_MIX/
  - DELIVERABLES/
```

## Advanced Features

### AI Scene Detection
```bash
# Auto-detect and mark scenes
sf-resolve detect-scenes "My Project"
# Creates markers at:
# - Scene changes
# - Face appearances
# - Action sequences
```

### Auto-Edit
```bash
# Basic auto-edit from markers
sf-resolve auto-edit "My Project" --style rhythmic
# Cuts to beat
# Removes dead space
# Applies transitions
```

### Batch Processing
```bash
# Process multiple projects
for project in Project1 Project2 Project3; do
  sf-resolve setup "$project"
  sf-resolve import "$project"
  sf-resolve color "$project" --style viral
  sf-resolve render "$project" --preset youtube
done
```

## Integration Examples

### With sf-project
```bash
# Complete project setup
sf-project create "Tutorial"
sf-resolve setup "Tutorial"
sf-resolve import "Tutorial"
```

### With sf-obs
```bash
# Import OBS recordings
sf-obs setup "Tutorial"
# Record in OBS...
sf-resolve import "Tutorial" --from-obs
```

### With sf-youtube
```bash
# Optimize for YouTube
sf-youtube metadata "Tutorial"
sf-resolve render "Tutorial" --preset youtube
sf-youtube thumbnail-test "Tutorial"
```

## Configuration

`~/.config/studioflow/resolve.yml`:
```yaml
paths:
  projects: /mnt/studio/Projects
  cache: /mnt/fast-ssd/resolve-cache
  renders: /mnt/render
  
defaults:
  framerate: 30
  resolution: 1080p
  colorspace: Rec709
  
render_presets:
  youtube:
    codec: h264
    bitrate: 16000
  instagram:
    codec: h264
    bitrate: 10000
    resolution: 1080x1080
  master:
    codec: prores422hq
    
powergrade_paths:
  - ~/.local/share/DaVinciResolve/PowerGrades
  - /mnt/nas/PowerGrades
  
lut_paths:
  - /opt/resolve/LUT
  - ~/.local/share/DaVinciResolve/LUT
  - /mnt/nas/Luts
```

## Performance Tips

### System Optimization
1. **Use dedicated GPU** for processing
2. **Fast SSD for cache** (NVMe preferred)
3. **Separate drives** for media and cache
4. **32GB+ RAM** for 4K editing
5. **Disable unused video tracks**

### Workflow Tips
1. **Use proxies** for complex timelines
2. **Render cache** for effects-heavy sections
3. **Optimize media** before importing
4. **Use adjustment clips** for global changes
5. **Export with smart render** when possible

## Troubleshooting

**"Resolve not found":**
- Check installation path
- Verify `/opt/resolve/bin/resolve`
- Add to PATH if needed

**"Python API not available":**
- Requires DaVinci Resolve Studio
- Check Python path in Resolve
- Install script module

**"LUTs not showing":**
- Copy to `/opt/resolve/LUT/`
- Set permissions: `chmod 755`
- Refresh LUT list in Resolve

**"Slow playback":**
- Generate optimized media
- Use proxy mode
- Lower timeline resolution
- Clear render cache

**"Export failed":**
- Check disk space
- Verify codec support
- Try different format
- Check render settings

## Performance Benchmarks

- **Project creation**: < 5 seconds
- **Import 100 clips**: < 30 seconds
- **Apply PowerGrade**: < 1 second
- **Proxy generation**: ~5x realtime
- **H.264 render**: ~2x realtime (GPU)

## Related Tools

- `sf-project` - Create project structure
- `sf-storage` - Manage media storage
- `sf-obs` - Import OBS recordings
- `sf-youtube` - Optimize for platforms