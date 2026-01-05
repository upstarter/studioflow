# StudioFlow Commands Reference 📚

Complete reference for all StudioFlow CLI commands.

## Table of Contents

- [Main Commands](#main-commands)
- [Project Commands](#project-commands)
- [Media Commands](#media-commands)
- [YouTube Commands](#youtube-commands)
- [Resolve Commands](#resolve-commands)
- [Publish Commands](#publish-commands)
- [Thumbnail Commands](#thumbnail-commands)
- [AI Commands](#ai-commands)
- [System Commands](#system-commands)

---

## Main Commands

### `sf new`
Create a new video project with complete workflow automation.

```bash
sf new <name> [OPTIONS]

Options:
  -t, --template TEXT     Project template [youtube/vlog/tutorial/shorts/multicam]
  -i, --import PATH       Import media from path after creation
  -p, --platform TEXT     Target platform [youtube/instagram/tiktok]
  -I, --interactive       Interactive mode with prompts

Examples:
  sf new "My Tutorial"
  sf new "Product Review" --template youtube --import /media/sdcard
  sf new "Vlog Episode" -t vlog -p instagram --interactive
```

### `sf import`
Import media from SD card, folder, or device.

```bash
sf import <path> [OPTIONS]

Options:
  -p, --project TEXT      Target project (default: current)
  -o, --organize          Auto-organize by type (default: true)

Examples:
  sf import /media/sdcard
  sf import ~/Downloads/footage --project "My Video"
  sf import /mnt/camera --no-organize
```

### `sf edit`
Open project in DaVinci Resolve.

```bash
sf edit [OPTIONS]

Options:
  -p, --project TEXT      Project to edit (default: current)

Examples:
  sf edit
  sf edit --project "Tutorial"
```

### `sf status`
Show current project status and statistics.

```bash
sf status

Output:
  Project: My Tutorial
  ├── Location: /mnt/studio/Projects/My_Tutorial
  ├── Created: 2024-01-15 14:30
  ├── Media Files: 42
  ├── Total Size: 15.3 GB
  ├── Template: youtube
  └── Platform: youtube
```

---

## Project Commands

### `sf project create`
Create a new project.

```bash
sf project create <name> [OPTIONS]

Options:
  --template TEXT         Project template
  --platform TEXT         Target platform

Examples:
  sf project create "New Video"
  sf project create "Tutorial" --template youtube
```

### `sf project list`
List all projects.

```bash
sf project list [OPTIONS]

Options:
  --archived              Include archived projects
  --sort TEXT            Sort by [name/date/size]

Examples:
  sf project list
  sf project list --archived --sort date
```

### `sf project select`
Select project as current.

```bash
sf project select <name>

Examples:
  sf project select "My Tutorial"
```

### `sf project archive`
Archive a completed project.

```bash
sf project archive <name>

Examples:
  sf project archive "Old Project"
```

---

## Media Commands

### `sf media scan`
Scan path for media files.

```bash
sf media scan <path>

Examples:
  sf media scan /media/sdcard
  sf media scan ~/Downloads
```

### `sf media transcribe` ⭐
Transcribe audio/video using Whisper AI.

```bash
sf media transcribe <file> [OPTIONS]

Options:
  --model TEXT           Whisper model [tiny/base/small/medium/large]
  --language TEXT        Language code or 'auto' for detection
  --formats TEXT         Output formats (comma-separated) [srt,vtt,txt,json]
  --chapters            Extract YouTube chapters from transcript

Examples:
  sf media transcribe video.mp4
  sf media transcribe audio.mp3 --model small
  sf media transcribe video.mp4 --formats srt,vtt,txt,json --chapters
  sf media transcribe interview.mp4 --language en --model medium

Output Files:
  video.srt              # Subtitle file
  video.vtt              # WebVTT subtitles
  video.txt              # Plain text transcript
  video_transcript.json  # Detailed JSON with timestamps
```

---

## YouTube Commands

### `sf youtube titles` ⭐
Generate optimized titles.

```bash
sf youtube titles <topic> [OPTIONS]

Options:
  -v, --viral            Generate viral titles with CTR prediction
  -s, --style TEXT       Content style [educational/entertainment/tutorial/review]

Examples:
  sf youtube titles "Python Tutorial"
  sf youtube titles "Gaming Setup" --viral
  sf youtube titles "Recipe" --style entertainment --viral

Output (viral mode):
  🔥 Viral Titles:
  1. Python Tutorial This Changes Everything (7.5% CTR)
  2. The Revolutionary Python Method (6.9% CTR)
  3. How Python Tutorial Exposed (6.9% CTR)
```

### `sf youtube optimize` ⭐
Generate viral-optimized titles and metadata.

```bash
sf youtube optimize <topic> [OPTIONS]

Options:
  -s, --style TEXT       Style [educational/entertainment/tutorial/review]
  --platform TEXT        Platform [youtube/instagram/tiktok]
  -n, --count INT        Number of titles to generate

Examples:
  sf youtube optimize "Python Tutorial"
  sf youtube optimize "Gaming Setup" --style review --count 20
  sf youtube optimize "Cooking" --platform instagram

Output:
  • Generates viral titles with CTR predictions
  • Creates optimized description with timestamps
  • Provides hook options for intro
  • Platform-specific optimization
```

### `sf youtube upload` ⭐
Upload video to YouTube.

```bash
sf youtube upload <video> [OPTIONS]

Options:
  -t, --title TEXT       Video title
  -d, --description TEXT Video description
  --tags TEXT           Comma-separated tags
  -p, --privacy TEXT     Privacy [private/unlisted/public]
  --thumbnail PATH       Thumbnail image path

Examples:
  sf youtube upload video.mp4 --title "My Video"
  sf youtube upload final.mp4 -t "Tutorial" --tags "python,coding" --privacy unlisted
  sf youtube upload render.mp4 -t "Vlog" --thumbnail thumb.jpg

Note: Requires YouTube API setup (see configuration)
```

### `sf youtube analyze`
Analyze channel performance and competitors.

```bash
sf youtube analyze [OPTIONS]

Options:
  -p, --project TEXT     Project name
  -c, --competitors      Analyze competitors

Examples:
  sf youtube analyze
  sf youtube analyze --competitors
```

---

## Resolve Commands

### `sf resolve sync`
Sync project with DaVinci Resolve.

```bash
sf resolve sync [OPTIONS]

Options:
  --project TEXT         Project name (default: current)

Examples:
  sf resolve sync
  sf resolve sync --project "My Video"
```

### `sf resolve profiles` ⭐
Show DaVinci Resolve optimization profiles.

```bash
sf resolve profiles [TYPE] [OPTIONS]

Arguments:
  TYPE                   Profile type [youtube/fx30/export/all]

Options:
  -d, --details         Show detailed settings

Examples:
  sf resolve profiles
  sf resolve profiles youtube
  sf resolve profiles fx30 --details

Output:
  YouTube Quality Profiles:
  • 4K30 Master: 3840x2160, 45 Mbps (Always VP9/AV1)
  • 1440p30 Fallback: 2560x1440, 24 Mbps
  • 1080p30 Proxy: 1920x1080, 12 Mbps
```

### `sf resolve export` ⭐
Generate optimized export settings.

```bash
sf resolve export <video> [OPTIONS]

Options:
  -p, --preset TEXT      Export preset [youtube_4k/youtube_1080p/instagram_reel/tiktok]
  --platform TEXT        Target platform (overrides preset)
  --show-command        Show FFmpeg command

Examples:
  sf resolve export video.mp4 --preset youtube_4k
  sf resolve export render.mov --platform instagram
  sf resolve export final.mp4 --show-command

Output:
  • Export settings for selected preset
  • Multi-tier export strategy
  • Optional FFmpeg command generation
```

### `sf resolve optimize`
Get optimized settings for your project.

```bash
sf resolve optimize [OPTIONS]

Options:
  -p, --project TEXT     Project name
  -q, --quality TEXT     Quality preset [4k30_master/1440p30_fallback/1080p30_proxy]
  -c, --camera TEXT      Camera type [fx30]

Examples:
  sf resolve optimize
  sf resolve optimize --quality 4k30_master --camera fx30
```

---

## Publish Commands

### `sf publish youtube`
Publish video to YouTube.

```bash
sf publish youtube [OPTIONS]

Options:
  --title TEXT          Video title
  --description TEXT    Video description
  --render             Render before publishing

Examples:
  sf publish youtube --title "My Video"
  sf publish youtube --render
```

### `sf publish instagram`
Publish to Instagram (Reels/IGTV).

```bash
sf publish instagram [OPTIONS]

Options:
  --post-type TEXT      Post type [reels/igtv/post]
  --caption TEXT        Post caption

Examples:
  sf publish instagram --post-type reels
  sf publish instagram --caption "Check out my new video!"
```

### `sf publish all`
Export for all platforms.

```bash
sf publish all

Output:
  • Generates platform-specific exports
  • YouTube 4K, Instagram Reel, TikTok versions
  • Optimized settings for each platform
```

---

## Thumbnail Commands

### `sf thumbnail generate`
Create a single thumbnail.

```bash
sf thumbnail generate [OPTIONS]

Options:
  --text TEXT           Main text for thumbnail
  --template TEXT       Template [viral/modern/tutorial/gaming/minimal]
  --background PATH     Background image

Examples:
  sf thumbnail generate --text "AMAZING RESULTS" --template viral
  sf thumbnail generate --template modern --background image.jpg
```

### `sf thumbnail batch`
Generate multiple templates at once.

```bash
sf thumbnail batch [OPTIONS]

Options:
  --templates TEXT      Comma-separated template names
  --text TEXT          Main text for all thumbnails

Examples:
  sf thumbnail batch --templates "viral,modern,tutorial"
  sf thumbnail batch --text "PYTHON TUTORIAL" --templates "viral,gaming"
```

---

## AI Commands

### `sf ai script`
Generate video script.

```bash
sf ai script <project> [OPTIONS]

Options:
  --style TEXT         Style [educational/entertainment/tutorial/vlog]
  --duration INT       Target duration in minutes

Examples:
  sf ai script "My Tutorial" --style educational
  sf ai script "Product Review" --duration 10
```

### `sf ai ideas`
Generate content ideas.

```bash
sf ai ideas <topic> [OPTIONS]

Options:
  --trending           Focus on trending topics
  --count INT          Number of ideas

Examples:
  sf ai ideas "Python" --trending
  sf ai ideas "Gaming" --count 20
```

---

## System Commands

### `sf config`
Manage StudioFlow configuration.

```bash
sf config [OPTIONS]

Options:
  --set TEXT           Set config value (key=value)
  --get TEXT           Get config value
  --list              List all configuration
  --edit              Edit config file in editor

Examples:
  sf config --list
  sf config --set storage.active=/my/projects
  sf config --get resolve.install_path
  sf config --edit
```

### `sf help`
Show help for commands.

```bash
sf help [COMMAND]

Examples:
  sf help
  sf help new
  sf help youtube
```

### `sf version`
Show version information.

```bash
sf version

Output:
  StudioFlow v1.0.0
```

### `sf completion`
Generate shell completions.

```bash
sf completion [SHELL] [OPTIONS]

Arguments:
  SHELL                Shell type [bash/zsh/fish]

Options:
  --install           Install completions

Examples:
  sf completion bash
  sf completion zsh --install
```

---

## Common Workflows

### Complete YouTube Video
```bash
# 1. Create project
sf new "Python Tutorial" --template youtube

# 2. Import footage
sf import /media/sdcard

# 3. Generate viral content
sf youtube optimize "Python Tutorial" --style educational

# 4. Transcribe for subtitles
sf media transcribe main_video.mp4 --chapters

# 5. Set up Resolve
sf resolve sync

# 6. Check export settings
sf resolve export final.mp4 --platform youtube

# 7. Upload to YouTube
sf youtube upload final.mp4 --title "Learn Python in 10 Minutes"
```

### Multi-Platform Publishing
```bash
# Create and optimize for all platforms
sf new "Product Review" --platform youtube

# Generate platform-specific titles
sf youtube optimize "Product Review" --platform youtube
sf youtube optimize "Product Review" --platform instagram
sf youtube optimize "Product Review" --platform tiktok

# Export for each platform
sf publish all
```

### Podcast/Interview Processing
```bash
# Create podcast project
sf new "Podcast Episode 42" --template podcast

# Import audio
sf import /recordings/episode42.wav

# Transcribe with chapters
sf media transcribe episode42.wav --model medium --chapters

# Generate show notes
sf ai script "Podcast Episode 42" --style podcast

# Export for podcast platforms
sf resolve export episode42.wav --preset podcast
```

---

## Configuration

### YouTube API Setup
```bash
# 1. Get credentials from Google Cloud Console
# 2. Place in ~/.studioflow/youtube/credentials.json
# 3. Run any YouTube command to authenticate
sf youtube analyze
```

### Storage Paths
```yaml
# ~/.studioflow/config.yaml
storage:
  ingest: /mnt/ingest
  active: /mnt/studio/Projects
  archive: /mnt/archive
```

### Resolve Settings
```yaml
resolve:
  install_path: /opt/resolve
  api_path: /opt/resolve/Developer/Scripting
```

---

**Note**: Commands marked with ⭐ are newly ported features with advanced functionality.