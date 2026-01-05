# StudioFlow QuickStart Guide 🚀

## 5-Minute Setup

### 1. Install Everything
```bash
cd /mnt/projects/studioflow
./install-full.sh
source ~/.bashrc
```

### 2. Run Setup Wizard (Recommended)
```bash
# Interactive setup for first-time users
sf-wizard setup

# This will:
# - Configure your creator profile
# - Set up storage directories
# - Install optional packages
# - Create command aliases
```

### 3. Create Your First Project
```bash
# Use the interactive wizard (recommended)
sf-wizard project

# Or quick create
sfnew "My First Video"

# Or use the full command
sf project create "Tutorial" --template youtube
```

### 4. Start Recording
```bash
# Set up OBS with one command
sf obs setup "My First Video" --auto

# Create viral scenes
sf obs viral-scenes

# Start recording in OBS (Ctrl+R)
```

### 5. Generate Content
```bash
# Get viral title ideas
sf youtube titles "Python Tutorial" --style viral

# Generate a script
sf ai script "My First Video" --style educational

# Create opening hooks
sf youtube hooks "My First Video"
```

---

## Common Workflows

### 📹 Quick Tutorial Video
```bash
# Complete setup in 30 seconds
PROJECT="Python_Tutorial"
sfnew "$PROJECT"
sf obs setup "$PROJECT"
sf ai script "$PROJECT"
sf youtube titles "Python" --style tutorial
# Now record!
```

### 📸 AI Tool Comparison
```bash
# Capture and compare tools
PROJECT="AI_Tools_2025"
sfnew "$PROJECT" --template comparison

# Take screenshots (open each tool first)
sf capture snap --window  # ChatGPT
sf capture snap --window  # Claude
sf capture snap --window  # Gemini

# Create comparison grid
sf capture grid *.png --labels
```

### 🎬 Process Recorded Video
```bash
# After recording
sf audio transcribe video.mp4           # Generate subtitles
sf audio denoise video.mp4              # Clean audio
sf resolve setup "My First Video"       # Setup DaVinci project
sf resolve render "My First Video"      # Export for YouTube
```

### 📊 Optimize for Upload
```bash
# Prepare for YouTube
sf youtube metadata "My First Video"    # Generate description
sf youtube thumbnail-test "My First Video"  # A/B test setup
sf youtube upload-time                  # Best time to post
```

---

## Essential Commands Cheatsheet

### Project Management
```bash
sfnew "Video Name"         # Create project
sflist                     # List all projects
sfinfo "Video Name"        # Project details
sfarchive "Video Name"     # Archive completed
```

### Recording & Capture
```bash
sfobs "Project"           # Setup OBS
sfcap                     # Take screenshot
sfrec                     # Record screen
sforg "Project"           # Organize captures
```

### Content Generation
```bash
sfscript "Project"        # Generate script
sfideas "topic"           # Get video ideas
sfseo "title"            # Optimize for SEO
sfhooks "Project"        # Create opening hooks
```

### Audio Processing
```bash
sftrans video.mp4        # Transcribe to subtitles
sfdenoise audio.wav      # Remove background noise
sfmusic "upbeat"         # Find background music
```

### Video Editing
```bash
sfresolve "Project"      # Setup DaVinci project
sfcolor "Project"        # Apply color grade
sfrender "Project"       # Export final video
```

---

## Platform-Specific Quick Commands

### YouTube (Long-form)
```bash
sf youtube titles "Topic" --style viral
sf youtube metadata "Project"
sf resolve render "Project" --preset youtube
```

### Instagram Reel
```bash
sf capture record --duration 30 --vertical
sf resolve render "Project" --preset instagram
sf youtube metadata "Project" --platform instagram
```

### TikTok
```bash
sf capture record --duration 15 --vertical
sf audio normalize video.mp4 --standard tiktok
sf youtube metadata "Project" --platform tiktok
```

---

## Troubleshooting

### "Command not found"
```bash
source ~/.bashrc  # Reload aliases
```

### "Project not found"
```bash
sf project list  # See all projects
```

### "OBS not recording to project"
```bash
sf obs setup "Project Name" --auto
```

### "Storage full"
```bash
sf storage status          # Check usage
sf storage archive "Old"   # Archive old projects
```

---

## Next Steps

1. **Read the full docs**: `docs/README.md`
2. **Learn the structure**: `docs/PROJECT_STRUCTURE.md`
3. **Explore automation**: `docs/API_AUTOMATION.md`
4. **Join the community**: GitHub Issues

---

## Get Help

```bash
# See all tools
sf

# Get tool help
sf project --help
sf youtube --help
sf obs --help

# Check documentation
ls docs/
```

Happy Creating! 🎬