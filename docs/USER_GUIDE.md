# StudioFlow User Guide

Complete guide to using StudioFlow for video production automation.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Basic Workflows](#basic-workflows)
5. [Project Workflow](#project-workflow)
6. [Auto-Import](#auto-import)
7. [Transcription](#transcription)
8. [Audio Markers](#audio-markers)
9. [Rough Cut Generation](#rough-cut-generation)
10. [Export & Publishing](#export--publishing)
11. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/studioflow.git
cd studioflow

# Install
./install.sh

# Verify installation
sf --version
```

### Basic Usage

```bash
# Import footage from SD card
sf import /media/sdcard --codeword MyProject

# This automatically:
# - Detects camera type
# - Creates project in /mnt/studio/PROJECTS/
# - Imports and organizes media
# - Normalizes audio
# - Transcribes footage
# - Detects audio markers
# - Extracts segments
# - Generates rough cut
```

---

## Installation

### System Requirements

- Linux (Ubuntu 20.04+ recommended)
- Python 3.10+
- FFmpeg
- DaVinci Resolve (optional, for Resolve integration)

### Install Dependencies

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y ffmpeg python3-pip

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-ai.txt  # For AI features
```

### Install StudioFlow

```bash
# Run install script
./install.sh

# Or install manually
pip install -e .
```

---

## Configuration

### Initial Setup

On first run, StudioFlow creates a config file at `~/.studioflow/config.yaml`.

### Storage Paths

Configure storage locations in `~/.studioflow/config.yaml`:

```yaml
storage:
  active: /mnt/studio/PROJECTS    # Current working projects
  ingest: /mnt/ingest             # SD card dumps
  archive: /mnt/archive           # Completed projects
  
  # Optional: Separate cache/proxy for better performance
  cache: /mnt/cache               # Fast disk for cache
  proxy: /mnt/cache/Proxies       # Proxy files on cache disk
```

**Note**: Projects are stored in `/mnt/studio/PROJECTS/` by default. Test outputs go to `/mnt/dev/studioflow/tests/output/`. See [ARCHITECTURE.md](ARCHITECTURE.md) for configuration details.

---

## Basic Workflows

### Import Footage

```bash
# Import from SD card
sf import /media/sdcard --codeword MyProject

# Import from directory
sf import /path/to/footage --codeword MyProject

# Import with custom settings
sf import /media/sdcard \
  --codeword MyProject \
  --normalize \
  --transcribe \
  --detect-markers
```

### Create Project

```bash
# Create new project
sf project create "MyProject" --template youtube

# List projects
sf project list

# Select active project
sf project select "MyProject"
```

---

## Project Workflow

> **📖 See [ARCHITECTURE.md](ARCHITECTURE.md) for complete storage paths reference.**

StudioFlow stores projects in `/mnt/studio/PROJECTS/` by default. Projects are organized by name with standard directory structures.

### Project Organization

Projects are stored in `/mnt/studio/PROJECTS/` with the following structure:

```
/mnt/studio/PROJECTS/
└── {project_name}/
    ├── 01_Media/           # Original and normalized media
    ├── 02_Transcription/   # Transcripts (JSON and SRT)
    ├── 03_Segments/        # Extracted video segments
    └── 04_Timelines/       # Rough cut EDL files
```

### Create Project

Projects are created automatically by the unified import pipeline, or manually:

```bash
# Create project via unified import (recommended)
sf import --source /mnt/ingest/Camera --codeword EP001_My_Episode

# Or create project manually
sf project create "EP001_My_Episode" --template youtube
```

This automatically:
- Creates project in `/mnt/studio/PROJECTS/`
- Sets up directory structure
- Configures project metadata
- Ready for media import

### Complete Episode Workflow

```bash
# 1. Import Sony camera footage (uses unified import pipeline)
sf import --source /mnt/ingest/Camera --codeword EP001_My_Episode

# 2. Project is automatically created in /mnt/studio/PROJECTS/
#    - Media imported and organized
#    - Audio normalized
#    - Transcripts generated
#    - Segments extracted

# 3. Work in Resolve (project is ready for editing)

# 4. Export when ready
sf export-youtube /mnt/render/EP001_final.mp4

# 5. Check all projects
sf project list
```

---

## Auto-Import

Automatic SD card import with intelligent detection and organization.

### Installation

```bash
# Install the auto-import system
sudo /mnt/projects/studioflow/scripts/install-auto-import.sh
```

### Usage

Once installed, simply insert an SD card. The system will:
1. Detect the card
2. Copy to ingest pool
3. Run unified import pipeline
4. Create project in `/mnt/studio/PROJECTS/`
5. Send desktop notification

---

## Transcription

Automatic transcription using Whisper AI.

### Basic Usage

```bash
# Transcribe video file
sf transcribe /path/to/video.mp4

# Transcribe with specific model
sf transcribe /path/to/video.mp4 --model large

# Transcribe and save to project
sf transcribe /path/to/video.mp4 --project MyProject
```

### Output Formats

Transcripts are saved in multiple formats:
- **JSON**: Word-level timestamps (for marker detection)
- **SRT**: Subtitle format (for video players)
- **TXT**: Plain text

---

## Audio Markers

Detect and extract audio markers (slate commands) from transcribed footage.

### Marker Types

- **START**: Beginning of a segment
- **END**: End of a segment
- **STANDALONE**: Single-point marker

### Commands

Markers can include commands:
- **order**: Segment ordering (e.g., "order 1", "order 2")
- **step**: Step numbering (e.g., "step 1", "step 2")
- **naming**: Naming convention
- **take**: Take number

### Usage

```bash
# Detect markers in project
sf markers detect --project MyProject

# List detected markers
sf markers list --project MyProject

# Extract segments based on markers
sf markers extract --project MyProject
```

---

## Rough Cut Generation

Automatically generate rough cuts from transcribed footage with markers.

### Basic Usage

```bash
# Generate rough cut
sf rough-cut generate --project MyProject

# Generate with custom style
sf rough-cut generate --project MyProject --style doc

# Export rough cut EDL
sf rough-cut export --project MyProject --output rough_cut.edl
```

### Cut Styles

- **doc**: Documentary style (preserves natural flow)
- **tutorial**: Tutorial style (tighter pacing)
- **vlog**: Vlog style (fast-paced)

---

## Export & Publishing

### Export to YouTube

```bash
# Export project
sf export-youtube --project MyProject

# Export with custom settings
sf export-youtube \
  --project MyProject \
  --quality 4K \
  --fps 60
```

### Multi-Platform Export

```bash
# Export to all platforms
sf export-all --project MyProject

# This exports:
# - YouTube (4K, optimized)
# - Instagram (1080p, square)
# - TikTok (1080p, vertical)
```

---

## Troubleshooting

### Common Issues

**Import fails:**
1. Check SD card is mounted: `ls /media/`
2. Verify permissions: `ls -la /mnt/ingest/`
3. Check camera detection: `sf import --dry-run /media/sdcard`

**Transcription fails:**
1. Check audio track exists: `ffprobe video.mp4`
2. Verify Whisper model is installed
3. Check disk space for temporary files

**Markers not detected:**
1. Verify transcription completed successfully
2. Check transcript contains "slate" keywords
3. Review marker detection logs

**Segments not extracted:**
1. Verify markers were detected
2. Check segment boundaries are valid
3. Review segment extraction logs

**Resolve can't find projects:**
1. Check Resolve connection: `sf resolve status`
2. List projects: `sf project list`
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
# View help for any command
sf --help
sf import --help
sf transcribe --help

# Check system status
sf status

# View logs
tail -f ~/.studioflow/studioflow.log
```

---

## Advanced Topics

### Custom Templates

Create custom project templates:

```bash
# Copy default template
cp ~/.studioflow/templates/youtube.yaml ~/.studioflow/templates/my_template.yaml

# Edit template
nano ~/.studioflow/templates/my_template.yaml

# Use custom template
sf project create "MyProject" --template my_template
```

### Batch Processing

```bash
# Process multiple files
for file in /path/to/videos/*.mp4; do
  sf transcribe "$file"
done

# Process with parallel execution
find /path/to/videos -name "*.mp4" -exec sf transcribe {} \;
```

### Integration with DaVinci Resolve

```bash
# Create Resolve project
sf resolve create-project "MyProject"

# Import media to Resolve
sf resolve import-media --project MyProject --path /mnt/studio/PROJECTS/MyProject/01_Media

# Export timeline
sf resolve export-timeline --project MyProject --output timeline.fcpxml
```

---

## Best Practices

1. **Organize by Project**: Use codewords to group related footage
2. **Regular Backups**: Archive completed projects to `/mnt/archive`
3. **Monitor Disk Space**: Check storage usage regularly
4. **Use Proxies**: Generate proxies for faster editing
5. **Normalize Audio**: Always normalize audio for consistent levels
6. **Test First**: Test workflows with small clips before processing large projects

---

## Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [Development Guide](DEVELOPMENT.md)
- [API Reference](API_REFERENCE.md)
- [FAQ](FAQ.md)

---

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/your-org/studioflow/issues
- Documentation: See `docs/` directory
- Logs: `~/.studioflow/studioflow.log`
