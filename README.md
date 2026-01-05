# StudioFlow 🎬

**AI-powered video production pipeline for content creators**

StudioFlow is a unified command-line tool that automates your entire video production workflow - from importing footage to publishing on YouTube with viral-optimized titles.

## ✨ Key Features

- **🎙️ Whisper Transcription** - Generate subtitles, chapters, and transcripts
- **📈 Viral Optimization** - AI-powered titles with CTR prediction
- **📤 YouTube Integration** - Direct upload with metadata optimization
- **🎨 DaVinci Resolve** - Automated project setup and export profiles
- **💾 Smart Storage** - 6-tier system from ingest to archive
- **🎯 Platform-Specific** - Optimized for YouTube, Instagram, TikTok

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/studioflow.git
cd studioflow

# Install dependencies
pip install -r requirements.txt

# Make the CLI available globally
pip install -e .

# Run setup wizard (first time only)
sf setup
```

### Your First Commands

```bash
# See essential commands (simplified view)
sf

# Create a new project
sf new "My Tutorial"

# Import media from SD card
sf import /media/sdcard

# Open in DaVinci Resolve
sf edit

# Transcribe a video
sf transcribe video.mp4

# Publish to YouTube
sf publish youtube

# See all commands (advanced)
sf --all
```

## 📚 Core Commands

StudioFlow shows essential commands by default. Use `sf --all` to see all commands.

### Essential Commands
```bash
sf new "Project Name"           # Create new project
sf import <path>                # Import media from SD card or folder
sf edit                         # Open project in DaVinci Resolve
sf status                       # Show current project status
sf transcribe <file>            # Transcribe video/audio
sf publish <platform>           # Publish video to platform
```

### Common Subcommands
```bash
sf project list                 # List all projects
sf project select "Name"        # Switch active project
sf media scan /path/to/files   # Scan for media
sf resolve sync                 # Sync with Resolve
sf youtube titles "Topic"       # Generate viral titles
sf auto-edit                    # Auto-editing with smart bins
```

### Getting Help
```bash
sf                              # Show essential commands (default)
sf --all                        # Show all commands
sf commands                     # Browse commands by category
sf commands --interactive       # Interactive command browser
sf help <command>               # Get help for a specific command
```

## 🎯 Example Workflow

```bash
# 1. Create project
sf new "Python Tutorial"

# 2. Import and organize media
sf import /media/sdcard

# 3. Generate optimized content
sf youtube optimize "Python Tutorial" --style educational

# 4. Transcribe for subtitles
sf media transcribe recording.mp4

# 5. Set up Resolve project
sf resolve sync

# 6. Export with optimized settings
sf resolve export final.mp4 --platform youtube

# 7. Upload to YouTube
sf youtube upload final.mp4 --title "Learn Python in 10 Minutes"
```

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:

### Getting Started
- [**YouTube Episode Guide**](docs/YOUTUBE_EPISODE_GUIDE.md) ⭐ **START HERE** - Complete workflow for creating YouTube tutorial episodes
- [**Filename Convention**](docs/FILENAME_CONVENTION.md) - How to name files for automatic optimization
- [**Hook Flows Guide**](docs/YOUTUBE_HOOK_FLOWS.md) - YouTube hook patterns for maximum retention

### Reference
- [**User Guide**](docs/USER_GUIDE.md) - Complete user documentation with all commands
- [**Storage Paths**](docs/STORAGE_PATHS.md) - Complete storage paths reference and configuration
- [**Architecture**](docs/ARCHITECTURE.md) - System design and technical details
- [**Development Guide**](docs/DEVELOPMENT.md) - How to extend and contribute
- [**AI Features**](docs/AI_FEATURES.md) - AI-powered features and capabilities
- [**Roadmap**](docs/ROADMAP.md) - Future plans and development roadmap

## 🛠️ Configuration

> **📖 See [docs/STORAGE_PATHS.md](docs/STORAGE_PATHS.md) for complete storage paths reference.**

StudioFlow uses a simple YAML configuration file at `~/.studioflow/config.yaml`:

```yaml
storage:
  # Library defaults to /mnt/library in CLI commands
  # Other paths default to ~/Videos/StudioFlow/* for portability
  library: /mnt/library            # Recommended: dedicated drive for Resolve projects
  active: /mnt/studio/Projects     # Current working projects
  ingest: /mnt/ingest              # SD card dumps
  archive: /mnt/archive            # Completed projects
  
  # Optional: Separate cache/proxy for better performance
  cache: /mnt/cache                # Fast disk for cache
  proxy: /mnt/cache/Proxies         # Proxy files on cache disk

youtube:
  api_key: your-api-key
  channel_id: your-channel-id

resolve:
  install_path: /opt/resolve
  api_path: /opt/resolve/Developer/Scripting
```

**Note:** 
- Library path defaults to `/mnt/library` in CLI commands (can be overridden in config)
- Other paths default to `${HOME}/Videos/StudioFlow/*` for portability
- Override in your config file for custom locations

### Optional Features

- **Power Bins**: Configure `storage.nas` or `storage.library` to enable Power Bins for stock footage organization
- **Advanced Commands**: Use `sf --all` to see all available commands

## 🤝 Contributing

We welcome contributions! See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for guidelines.

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- OpenAI Whisper for transcription
- Google YouTube Data API
- Blackmagic DaVinci Resolve
- The amazing open source community

---

**Built for creators, by creators** 🎥✨