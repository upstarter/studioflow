# StudioFlow FAQ ❓

## General Questions

### What is StudioFlow?
StudioFlow is a Unix-philosophy video production suite consisting of specialized command-line tools that automate content creation workflows. Each tool does one thing well and can be combined for powerful automation.

### Why command-line instead of GUI?
- **Speed**: Command-line is faster for repetitive tasks
- **Automation**: Easy to script and schedule
- **Composability**: Tools work together via pipes
- **Remote Access**: Works over SSH
- **Version Control**: Text-based configs work with Git

### What platforms does it support?
- **YouTube** (primary focus)
- **Instagram** (Reels, IGTV)
- **TikTok** (short-form)
- Removed: Twitter, Twitch (by design)

### Do I need programming knowledge?
No! Basic command-line familiarity is helpful, but all commands are simple and documented. Start with aliases like `sfnew` and `sfcap`.

---

## Installation Issues

### "Command not found"
```bash
# Reload your shell configuration
source ~/.bashrc

# Or restart your terminal
exit
# Open new terminal
```

### "Permission denied"
```bash
# Make tools executable
cd /mnt/projects/studioflow
chmod +x sf-*

# Fix installation
sudo ./install-full.sh
```

### "Module not found"
```bash
# StudioFlow uses zero dependencies!
# If you see this, you might be in wrong directory
cd /mnt/projects/studioflow
```

### How do I update StudioFlow?
```bash
cd /mnt/projects/studioflow
git pull
./install-full.sh
source ~/.bashrc
```

---

## Project Management

### Where are projects stored?
Projects are stored in `/mnt/studio/Projects/` by default (the "active" storage tier). You can see all projects with:
```bash
sf project list
```

### Can I change the project location?
Yes, edit `~/.config/studioflow/config.yml`:
```yaml
storage:
  active: /my/custom/path
```

### How do I rename a project?
```bash
# Projects include date prefix, so:
mv /mnt/studio/Projects/20250114_Old_Name \
   /mnt/studio/Projects/20250114_New_Name

# Update metadata
sf project refresh "New_Name"
```

### How much space do projects use?
```bash
# Check all projects
sf storage status

# Check specific project
du -sh /mnt/studio/Projects/20250114_My_Project
```

### Can I work with existing projects?
Yes! Just copy your existing project into the StudioFlow structure:
```bash
sf project create "Existing_Video" --template youtube
# Then copy your files into the appropriate folders
```

---

## Recording & Capture

### OBS doesn't record to my project
```bash
# Run setup again
sf obs setup "Project_Name" --auto

# Or manually set in OBS:
# Settings → Output → Recording Path
# Set to: /mnt/studio/Projects/YOUR_PROJECT/01_FOOTAGE/OBS_RECORDINGS
```

### How do I use replay buffer?
```bash
# Enable in OBS
sf obs highlights "Project_Name"

# During recording/streaming:
# Press Alt+H to save last 30 seconds
# Files save to: 01_FOOTAGE/HIGHLIGHTS/
```

### Screenshots have wrong resolution
```bash
# StudioFlow auto-standardizes to:
# - 1920x1080 (landscape)
# - 1080x1920 (portrait)
# - 1080x1080 (square)

# Disable standardization:
sf capture snap --no-standardize
```

### Browser chrome not being cropped
```bash
# Update browser detection
sf capture update-browsers

# Or manually specify crop
sf capture snap --crop-top 100
```

---

## Content Generation

### AI features not working
The `sf-ai` tool requires API keys for AI services:
```bash
# Edit ~/.config/studioflow/ai.yml
api:
  provider: openai  # or anthropic, local
  api_key: YOUR_API_KEY

# For local/free:
# Install Ollama and use provider: local
```

### How accurate is transcription?
Whisper AI accuracy depends on model size:
- `tiny`: Fast, ~85% accurate
- `small`: Balanced, ~90% accurate (recommended)
- `large`: Slow, ~95% accurate

```bash
sf audio transcribe video.mp4 --model small
```

### Can I edit generated scripts?
Yes! Scripts are saved as markdown files:
```bash
sf ai script "Project"
# Edit: Project/07_DOCS/SCRIPT/script.md
```

---

## Platform Optimization

### What's the best upload time?
```bash
sf youtube upload-time

# Generally:
# YouTube: Tue-Thu, 2-4 PM EST
# Instagram: 11 AM, 2 PM, 5 PM
# TikTok: 6 AM, 10 AM, 7 PM
```

### How do I A/B test thumbnails?
```bash
# Create test structure
sf youtube thumbnail-test "Project"

# Creates:
# - variant_A/
# - variant_B/
# - variant_C/

# Upload all three to YouTube Studio
# YouTube will auto-rotate and track CTR
```

### Why focus on "virality"?
StudioFlow optimizes for growth metrics:
- **Virality**: Higher reach and shares
- **Retention**: Longer watch time
- **CTR**: More clicks from impressions
- **Engagement**: More comments/likes

These metrics directly impact channel growth.

---

## Storage Management

### "No space left on device"
```bash
# Check storage usage
sf storage status

# Archive old projects
sf storage archive "Old_Project"

# Clean render cache
rm -rf /mnt/render/cache/*
```

### What are storage tiers?
Storage tiers optimize for speed vs. capacity:
- **Ingest**: Fastest SSD for imports
- **Active**: Fast SSD for current edits
- **Render**: Fast writes for exports
- **Library**: Balanced for assets
- **Archive**: Large, slow for old projects
- **NAS**: Network storage for sharing

### How do I move projects between tiers?
```bash
# Move to archive
sf storage archive "Completed_Project"

# Move to active for editing
sf storage move "Project" active

# Move to render for export
sf storage move "Project" render
```

---

## DaVinci Resolve

### "Python API not available"
The Python API requires DaVinci Resolve **Studio** (paid version). The free version doesn't include scripting support.

Workaround for free version:
```bash
# Manual setup instead of automation
sf resolve setup "Project" --manual
# This creates the structure and instructions
```

### LUTs not showing up
```bash
# Copy LUTs to Resolve directory
sudo cp -r /mnt/nas/Luts/* /opt/resolve/LUT/
sudo chmod -R 755 /opt/resolve/LUT/

# Restart Resolve
```

### Can't import project media
```bash
# Ensure media is in standard folders
sf resolve organize "Project"

# Or manually import from:
# Project/01_FOOTAGE/
# Project/02_AUDIO/
# Project/03_GRAPHICS/
```

---

## Automation

### How do I schedule uploads?
```bash
# Use cron for scheduling
crontab -e

# Add line for daily 2 PM upload:
0 14 * * * sf youtube upload "/path/to/video.mp4"
```

### Can I automate the entire workflow?
Yes! See `EXAMPLES.md` for complete automation scripts. Basic example:
```bash
#!/bin/bash
PROJECT="Daily_Video"
sf project create "$PROJECT"
sf obs setup "$PROJECT"
# ... record ...
sf resolve render "$PROJECT"
sf youtube upload "$PROJECT"
sf storage archive "$PROJECT"
```

### How do I monitor rendering progress?
```bash
# Check Resolve render status
sf resolve status

# Or watch export directory
watch -n 5 ls -la "Project/05_EXPORT/FINAL/"
```

---

## Troubleshooting

### Nothing seems to work
```bash
# Check installation
ls -la /usr/local/bin/sf*

# Verify paths exist
sf storage status

# Check permissions
ls -la /mnt/studio/Projects

# Test basic command
sf project list
```

### Tools can't find each other
```bash
# Ensure sfcore.py is accessible
ls -la /mnt/projects/studioflow/sfcore.py

# Check Python path
python3 -c "import sys; print(sys.path)"
```

### WebSocket connection failed
```bash
# In OBS:
# Tools → WebSocket Server Settings
# ✓ Enable WebSocket Server
# Port: 4455
# Password: (leave blank for local)

# Test connection:
sf obs monitor
```

---

## Best Practices

### Should I use templates or minimal?
- **Templates**: For standard content types (YouTube, tutorials)
- **Minimal**: For quick/simple videos
- **Raw**: When you need custom structure

### How often should I archive?
Archive projects when:
- Video is published
- You won't edit for 30+ days
- Active storage >70% full

### What's the optimal workflow order?
1. Create project (`sf project create`)
2. Generate content (`sf ai script`, `sf youtube titles`)
3. Record (`sf obs setup`)
4. Process (`sf audio transcribe`)
5. Edit (`sf resolve setup`)
6. Optimize (`sf youtube metadata`)
7. Export (`sf resolve render`)
8. Archive (`sf storage archive`)

### How do I back up projects?
```bash
# To NAS
rsync -av "Project/" "/mnt/nas/backup/Project/"

# To cloud
rclone sync "Project/" "gdrive:Projects/Project/"

# Git for scripts/metadata
cd "Project/" && git init && git add -A && git commit
```

---

## Performance

### Commands are slow
StudioFlow is designed to be fast:
- Project creation: <1 second
- Screenshot: <0.5 seconds
- Most commands: <2 seconds

If slow, check:
- Disk I/O (`iotop`)
- Network (for NAS operations)
- CPU usage (`htop`)

### Transcription takes forever
Whisper AI speed depends on:
- Model size (use `small` for balance)
- GPU availability (10x faster with CUDA)
- Audio length

Speed up:
```bash
# Use smaller model
sf audio transcribe video.mp4 --model tiny

# Use GPU if available
sf audio transcribe video.mp4 --device cuda
```

---

## Getting Help

### Where can I report bugs?
- GitHub Issues: [github.com/yourusername/studioflow/issues]
- Include: Command used, error message, `sf --version`

### How can I contribute?
- Submit pull requests for new features
- Improve documentation
- Share your workflow scripts
- Report bugs and suggestions

### Is there a community?
- GitHub Discussions
- YouTube channel comments
- Discord (coming soon)

### Where are the docs?
```bash
# Local documentation
ls /mnt/projects/studioflow/docs/

# Quick help
sf --help
sf project --help
sf youtube --help
```

---

## Future Plans

### What features are coming?
- Direct YouTube upload API
- More AI providers
- Cloud rendering
- Team collaboration
- Mobile companion app

### Can I request features?
Yes! Open a GitHub issue with:
- Use case description
- Expected behavior
- Why it would help your workflow

### Will there be a GUI?
A web UI is planned for:
- Project dashboard
- Analytics visualization
- Render queue management
- Keep CLI for automation

---

## Quick Fixes

### Reset everything
```bash
# backup first!
rm -rf ~/.config/studioflow
rm -rf ~/.cache/studioflow
cd /mnt/projects/studioflow
./install-full.sh
source ~/.bashrc
```

### Update all tools
```bash
cd /mnt/projects/studioflow
git pull
./install-full.sh
```

### Test installation
```bash
sf project create "Test" && \
sf obs setup "Test" && \
sf youtube titles "Test Topic" && \
echo "✅ Everything works!"
```

---

Still have questions? Check the documentation:
- `QUICKSTART.md` - Get started in 5 minutes
- `EXAMPLES.md` - Real-world workflows
- `docs/README.md` - Complete documentation
- `docs/PROJECT_STRUCTURE.md` - Directory organization
- `docs/API_AUTOMATION.md` - Advanced automation