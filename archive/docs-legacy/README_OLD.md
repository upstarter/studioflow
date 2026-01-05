# StudioFlow Suite Documentation

## Overview
StudioFlow is a Unix-philosophy based video production suite consisting of specialized tools that work together to create a professional content creation workflow. Each tool does one thing well and can be combined for powerful automation.

## Philosophy
- **Unix Principles**: Small, focused tools that excel at specific tasks
- **Zero Dependencies**: Pure Python stdlib for maximum reliability
- **JSON Streaming**: Tools communicate via structured JSON events
- **Viral Optimization**: Every feature designed for growth metrics
- **Platform Focus**: YouTube, Instagram, and TikTok only

## Quick Start

### Installation
```bash
# Full installation
cd /mnt/projects/studioflow
./install-full.sh

# Activate aliases
source ~/.bashrc

# Create your first project
sf project create "My First Video"

# Or use the alias
sfnew "My First Video"
```

## Tool Suite

### Core Tools
| Tool | Purpose | Key Commands |
|------|---------|-------------|
| **sf-project** | Project creation & management | `create`, `list`, `info` |
| **sf-storage** | Storage tier optimization | `status`, `move`, `archive` |
| **sf-capture** | Screenshot & recording | `snap`, `record`, `grid` |

### YouTube Tools
| Tool | Purpose | Key Commands |
|------|---------|-------------|
| **sf-youtube** | Viral optimization | `titles`, `hooks`, `metadata` |
| **sf-audio** | Audio & transcription | `transcribe`, `denoise`, `normalize` |
| **sf-ai** | Content generation | `script`, `ideas`, `analyze` |

### Integration Tools
| Tool | Purpose | Key Commands |
|------|---------|-------------|
| **sf-obs** | OBS automation | `setup`, `viral-scenes`, `highlights` |
| **sf-resolve** | DaVinci Resolve | `setup`, `color`, `render` |

## Common Workflows

### YouTube Tutorial
```bash
# 1. Create project
sf project create "Python Tutorial" --template tutorial

# 2. Generate viral content
sf ai script "Python Tutorial" --style educational
sf youtube titles "Python Programming" --style tutorial

# 3. Set up recording
sf obs setup "Python Tutorial" --auto
sf obs viral-scenes

# 4. Post-production
sf audio transcribe recording.mp4
sf resolve setup "Python Tutorial"
sf resolve render "Python Tutorial" --preset youtube

# 5. Optimize for upload
sf youtube metadata "Python Tutorial"
sf youtube upload-time
```

### AI Tool Comparison
```bash
# 1. Create comparison project
sf project create "AI Tools 2025" --template comparison

# 2. Capture screenshots
for tool in chatgpt claude gemini; do
  sf capture snap --window
  sleep 2
done

# 3. Create comparison grid
sf capture grid *.png --labels --title "AI Comparison"

# 4. Generate script
sf ai script "AI Tools 2025" --style comparison

# 5. Process and render
sf resolve setup "AI Tools 2025"
sf resolve render "AI Tools 2025" --preset youtube
```

### Quick Social Media
```bash
# Instagram Reel
sf project create "Quick Tip" --template minimal
sf obs record --duration 30
sf resolve render "Quick Tip" --preset instagram
sf youtube metadata "Quick Tip" --platform instagram

# TikTok Video
sf capture record --duration 15 --vertical
sf audio normalize recording.mp4 --standard tiktok
sf youtube metadata "Quick Tip" --platform tiktok
```

## Storage Tiers

| Tier | Path | Purpose | Speed |
|------|------|---------|-------|
| **Ingest** | `/mnt/ingest` | Initial import | Fastest SSD |
| **Active** | `/mnt/studio/Projects` | Current edits | Fast SSD |
| **Render** | `/mnt/render` | Exports | Fast write |
| **Library** | `/mnt/library` | Reusable assets | Balanced |
| **Archive** | `/mnt/archive` | Long-term | Large HDD |
| **NAS** | `/mnt/nas` | Shared/backup | Network |

## Viral Optimization Features

### Title Psychology
- Curiosity gaps: "Nobody talks about..."
- Social proof: "Everyone's using..."
- Urgency: "2025 update"
- Emotion: "Mind-blowing results"

### Retention Strategies
- Hook in first 3 seconds
- Pattern interrupt every 30 seconds
- Multiple CTAs throughout
- End screen optimization

### Platform-Specific
- **YouTube**: 8-12 minutes, high CTR thumbnails
- **Instagram**: 30-60 seconds, vertical format
- **TikTok**: 15-30 seconds, trending audio

## Automation Examples

### Complete Production Pipeline
```bash
#!/bin/bash
# Full automated workflow

PROJECT="Tutorial_$(date +%Y%m%d)"
TOPIC="Python Web Scraping"

# Setup
sf project create "$PROJECT" --template tutorial
sf ai script "$PROJECT" --style educational
sf youtube titles "$TOPIC" --style viral

# Recording
sf obs setup "$PROJECT" --auto
sf obs viral-scenes
echo "Record your video now..."
read -p "Press Enter when done recording"

# Post-production
sf audio transcribe "$PROJECT"/01_FOOTAGE/*.mp4
sf resolve setup "$PROJECT"
sf resolve color "$PROJECT" --style viral
sf resolve render "$PROJECT" --preset youtube

# Upload optimization
sf youtube metadata "$PROJECT"
sf youtube thumbnail-test "$PROJECT"
sf youtube upload-time

# Archive when done
sf storage archive "$PROJECT"
```

## Configuration

Global settings: `~/.config/studioflow/config.yml`

Tool-specific:
- `~/.config/studioflow/youtube.yml`
- `~/.config/studioflow/obs.yml`
- `~/.config/studioflow/resolve.yml`
- `~/.config/studioflow/audio.yml`
- `~/.config/studioflow/ai.yml`

## Best Practices

1. **Project Organization**
   - One project per video
   - Use descriptive names
   - Archive completed projects

2. **Recording**
   - Set up OBS scenes before recording
   - Use replay buffer for highlights
   - Monitor performance during streams

3. **Editing**
   - Use proxies for 4K content
   - Apply PowerGrades consistently
   - Render to platform specifications

4. **Optimization**
   - Test 3+ title variants
   - A/B test thumbnails
   - Upload at optimal times
   - Track metrics and iterate

## Troubleshooting

See individual tool documentation:
- [sf-project](sf-project.md#troubleshooting)
- [sf-storage](sf-storage.md#troubleshooting)
- [sf-capture](sf-capture.md#troubleshooting)
- [sf-youtube](sf-youtube.md#troubleshooting)
- [sf-audio](sf-audio.md#troubleshooting)
- [sf-ai](sf-ai.md#troubleshooting)
- [sf-obs](sf-obs.md#troubleshooting)
- [sf-resolve](sf-resolve.md#troubleshooting)

## Performance

- Project creation: < 1 second
- Screenshot capture: < 0.5 seconds
- Title generation: < 2 seconds
- Script generation: < 5 seconds
- OBS setup: < 30 seconds
- Resolve project: < 5 seconds

## Support

- GitHub Issues: Report bugs and request features
- Documentation: This directory
- CLAUDE.md: AI assistant context