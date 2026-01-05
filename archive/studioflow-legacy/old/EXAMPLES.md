# StudioFlow Real-World Examples 🎬

## Complete Production Workflows

### 1. Educational Tutorial (Start to Finish)

```bash
#!/bin/bash
# Complete Python tutorial production

# Setup
PROJECT="Python_Web_Scraping_Tutorial"
TOPIC="Web Scraping with Python"

echo "📁 Creating project..."
sf project create "$PROJECT" --template tutorial

echo "🤖 Generating content..."
sf ai script "$PROJECT" --style educational --length 10
sf youtube titles "$TOPIC" --style tutorial
sf youtube hooks "$PROJECT" --style retention

echo "🎥 Setting up recording..."
sf obs setup "$PROJECT" --auto
sf obs viral-scenes

echo "Ready to record! Press Enter when done..."
read

echo "🎵 Processing audio..."
RECORDING=$(ls "$PROJECT/01_FOOTAGE/OBS_RECORDINGS"/*.mkv | head -1)
sf audio transcribe "$RECORDING" --format srt
sf audio denoise "$RECORDING"

echo "✂️ Setting up edit..."
sf resolve setup "$PROJECT"
sf resolve import "$PROJECT"
sf resolve color "$PROJECT" --style viral

echo "📤 Rendering..."
sf resolve render "$PROJECT" --preset youtube

echo "📊 Optimizing for upload..."
sf youtube metadata "$PROJECT" --platform youtube
sf youtube thumbnail-test "$PROJECT"
sf youtube upload-time

echo "✅ Production complete!"
```

### 2. Multi-Platform Content (One Video, Three Platforms)

```bash
#!/bin/bash
# Create once, publish everywhere

PROJECT="AI_News_$(date +%Y%m%d)"
sf project create "$PROJECT"

# Record main content
sf obs setup "$PROJECT"
echo "Record your content now (5-10 minutes)..."
read -p "Press Enter when done"

# Process for each platform
for platform in youtube instagram tiktok; do
    echo "Processing for $platform..."

    # Platform-specific render
    sf resolve render "$PROJECT" --preset $platform

    # Platform-specific metadata
    sf youtube metadata "$PROJECT" --platform $platform

    # Platform-specific optimization
    case $platform in
        youtube)
            sf youtube thumbnail-test "$PROJECT"
            ;;
        instagram)
            # Add Instagram-specific text overlays
            sf ai prompt "instagram text overlay" > "$PROJECT/07_DOCS/instagram_text.txt"
            ;;
        tiktok)
            # Find trending audio
            sf audio library search --trending --platform tiktok
            ;;
    esac
done
```

### 3. AI Tool Comparison Video

```bash
#!/bin/bash
# Comprehensive tool comparison

PROJECT="ChatGPT_vs_Claude_vs_Gemini"
sf project create "$PROJECT" --template comparison

# Test prompt for all tools
TEST_PROMPT="Write a Python function to scrape a website"

echo "Testing each tool with: $TEST_PROMPT"
echo "Open each tool and run the test, then press Enter"

# Capture each tool
for tool in ChatGPT Claude Gemini; do
    echo "Open $tool and press Enter..."
    read
    sf capture snap --window
    mv ~/Captures/Screenshots/latest.png "$PROJECT/01_CAPTURES/TOOL_${tool}/interface.png"
done

# Create comparison grid
sf capture grid "$PROJECT/01_CAPTURES/"*/*.png \
    --labels "ChatGPT,Claude,Gemini" \
    --title "AI Comparison 2025"

# Generate analysis script
sf ai script "$PROJECT" --style comparison

# Create data visualization
cat > "$PROJECT/03_ANALYSIS/comparison.json" << EOF
{
    "ChatGPT": {"speed": 8, "accuracy": 9, "features": 8},
    "Claude": {"speed": 9, "accuracy": 9, "features": 9},
    "Gemini": {"speed": 7, "accuracy": 8, "features": 7}
}
EOF

# Generate viral title
sf youtube titles "AI Tool Comparison" --style comparison
```

### 4. Daily Vlog Workflow

```bash
#!/bin/bash
# Streamlined daily vlog production

DATE=$(date +%Y%m%d)
PROJECT="Vlog_${DATE}"

# Morning setup
sf project create "$PROJECT" --template minimal
sf obs setup "$PROJECT"

# Throughout the day
alias vlog-clip='sf obs control save-replay'  # Save last 30 seconds

# Evening edit
sf resolve import "$PROJECT"
sf audio normalize "$PROJECT/FOOTAGE"/*.mp4
sf resolve auto-edit "$PROJECT" --style rhythmic

# Quick export
sf resolve render "$PROJECT" --preset youtube --quality fast

# Upload
sf youtube metadata "$PROJECT" --template vlog
echo "Vlog ready for upload!"
```

### 5. Podcast to Video Conversion

```bash
#!/bin/bash
# Convert podcast to video with visuals

PODCAST="podcast_episode_42.mp3"
PROJECT="Podcast_Ep42_Video"

sf project create "$PROJECT"

# Transcribe for captions
sf audio transcribe "$PODCAST" --format srt --style podcast

# Generate video script from audio
sf ai analyze "$PODCAST" --suggest "video scenes"

# Create visual elements
sf ai prompt "podcast cover art" > "$PROJECT/03_GRAPHICS/cover.txt"
sf capture create-waveform "$PODCAST" "$PROJECT/03_GRAPHICS/waveform.mp4"

# Setup Resolve project
sf resolve setup "$PROJECT"
sf resolve import-audio "$PODCAST"
sf resolve add-captions "$PROJECT/*.srt"

# Render video version
sf resolve render "$PROJECT" --preset youtube
```

### 6. Product Review Video

```bash
#!/bin/bash
# Professional product review

PRODUCT="iPhone 15 Pro"
PROJECT="${PRODUCT// /_}_Review"

sf project create "$PROJECT"

# Generate review structure
sf ai script "$PROJECT" --style review --product "$PRODUCT"

# Capture product shots
echo "Set up product for photography..."
read -p "Press Enter to start capture sequence"

# Multiple angles
for angle in front back side top detail; do
    echo "Position: $angle shot"
    read -p "Press Enter to capture"
    sf capture snap
    mv ~/Captures/Screenshots/latest.png \
        "$PROJECT/01_FOOTAGE/SCREENSHOTS/${angle}.png"
done

# B-roll recording
sf obs setup "$PROJECT"
sf obs scenes add "Unboxing" "Hands-on" "Testing" "Comparison"

# Generate comparison data
sf youtube compete "$PRODUCT"

# SEO optimization
sf youtube titles "$PRODUCT Review" --style review
sf youtube metadata "$PROJECT" --keywords "tech,review,$PRODUCT"
```

### 7. Live Stream Setup

```bash
#!/bin/bash
# Professional live stream configuration

PROJECT="Live_Tutorial_$(date +%Y%m%d)"
PLATFORM="youtube"  # or instagram, tiktok

sf project create "$PROJECT"

# Configure streaming
sf obs stream --platform $PLATFORM

# Set up scenes for live
sf obs viral-scenes
sf obs scenes add "Starting Soon" "Main Content" "Q&A" "Ending"

# Prepare content
sf ai script "$PROJECT" --style live --duration 60

# Schedule stream
sf youtube schedule "Python Live Coding" \
    --date "$(date -d 'next Tuesday 2pm' --iso-8601)"

# Start streaming
echo "Starting stream in 5 minutes..."
sleep 300
sf obs control start-streaming

# During stream
# sf obs control switch-scene "Main Content"
# sf obs control save-replay  # Save highlights
```

### 8. Batch Processing Multiple Videos

```bash
#!/bin/bash
# Process multiple videos efficiently

VIDEOS_DIR="/media/sdcard/videos"
TEMPLATE="tutorial"

# Import and process all videos
for video in "$VIDEOS_DIR"/*.mp4; do
    basename=$(basename "$video" .mp4)
    PROJECT="Import_${basename}"

    echo "Processing: $basename"

    # Create project
    sf project create "$PROJECT" --template $TEMPLATE

    # Copy video
    cp "$video" "$PROJECT/01_FOOTAGE/A_ROLL/"

    # Process audio
    sf audio transcribe "$video"
    sf audio denoise "$video"

    # Quick edit
    sf resolve setup "$PROJECT"
    sf resolve import "$PROJECT"
    sf resolve auto-edit "$PROJECT"

    # Render
    sf resolve render "$PROJECT" --preset youtube

    # Archive
    sf storage archive "$PROJECT"
done
```

### 9. Viral Shorts Creation

```bash
#!/bin/bash
# Create viral short-form content

TOPIC="Life Hack"
PROJECT="Viral_Short_$(date +%Y%m%d)"

sf project create "$PROJECT" --template minimal

# Generate viral hook
sf ai ideas "$TOPIC" --trending --platform tiktok
sf youtube titles "$TOPIC" --style viral | head -1 > title.txt

# Quick record
sf capture record --duration 15 --vertical

# Add text overlays
sf ai prompt "viral text overlay" --style "gen-z"

# Process for multiple platforms
for platform in youtube instagram tiktok; do
    sf resolve render "$PROJECT" --preset ${platform}_short
    sf youtube metadata "$PROJECT" --platform $platform
done

# A/B test different hooks
sf youtube hooks "$PROJECT" --count 5
```

### 10. Documentary Style Production

```bash
#!/bin/bash
# Long-form documentary workflow

PROJECT="Documentary_Climate_Change"
sf project create "$PROJECT" --template youtube

# Research phase
sf ai research "climate change" --depth comprehensive
sf ai script "$PROJECT" --style documentary --length 30

# Organize footage
FOOTAGE_SOURCES=(
    "/mnt/archive/stock_footage"
    "/mnt/nas/interviews"
    "/mnt/ingest/b_roll"
)

for source in "${FOOTAGE_SOURCES[@]}"; do
    sf storage import "$source" "$PROJECT/01_FOOTAGE"
done

# Create interview segments
for interview in "$PROJECT/01_FOOTAGE/interviews"/*.mp4; do
    sf audio transcribe "$interview"
    sf ai summarize "$interview" >> "$PROJECT/07_DOCS/interview_notes.md"
done

# Color grade for cinematic look
sf resolve setup "$PROJECT"
sf resolve color "$PROJECT" --style cinematic --lut "osiris/Vision6"

# Multi-part rendering
for part in 1 2 3; do
    sf resolve render "$PROJECT" --segment $part --preset youtube
done
```

## Quick Automation Scripts

### Auto-Upload When Render Completes
```bash
#!/bin/bash
# Watch for completed renders and upload

inotifywait -m "$PROJECT/05_EXPORT/FINAL" -e create |
while read path action file; do
    if [[ "$file" =~ .*\.mp4$ ]]; then
        echo "New render detected: $file"
        sf youtube upload "$file" --private
        sf youtube thumbnail-test "${file%.mp4}"
    fi
done
```

### Daily Content Calendar
```bash
#!/bin/bash
# Generate week of content ideas

WEEK_NUM=$(date +%V)
YEAR=$(date +%Y)

sf ai calendar \
    --week $WEEK_NUM \
    --year $YEAR \
    --videos-per-week 5 \
    --style mixed > "content_week_${WEEK_NUM}.json"

# Create projects for each video
jq -r '.videos[].title' "content_week_${WEEK_NUM}.json" | while read title; do
    sf project create "$title"
    sf ai script "$title"
done
```

### Performance Analytics Dashboard
```bash
#!/bin/bash
# Track video performance

sf youtube analytics --last 10 > stats.json

# Generate report
echo "## Performance Report $(date +%F)"
echo
echo "### Top Performers"
jq -r '.videos | sort_by(.views) | reverse | .[0:3] |
    .[] | "- \(.title): \(.views) views, \(.retention)% retention"' stats.json

echo
echo "### Optimization Suggestions"
sf ai analyze stats.json --suggest improvements
```

## Advanced Techniques

### Dynamic Thumbnail Generation
```bash
# Create thumbnails with real-time data
TEXT="$(sf youtube trending | head -1)"
sf capture create-thumbnail \
    --background "$PROJECT/03_GRAPHICS/background.png" \
    --text "$TEXT" \
    --style "high-contrast"
```

### AI Voice-Over Generation
```bash
# Generate voice-over from script
sf ai script "$PROJECT" > script.txt
sf audio generate-voice script.txt \
    --voice "professional" \
    --speed 1.1 \
    --output "$PROJECT/02_AUDIO/VO/ai_narration.mp3"
```

### Smart B-Roll Selection
```bash
# Find relevant b-roll based on script
sf ai analyze "$PROJECT/07_DOCS/SCRIPT/script.md" \
    --extract "visual scenes"

sf storage search --tags "nature,timelapse" \
    --copy-to "$PROJECT/01_FOOTAGE/B_ROLL"
```

## Tips for Maximum Efficiency

1. **Use Aliases**: `sfnew`, `sfcap`, `sftrans` are faster than full commands
2. **Chain Commands**: Use `&&` to run multiple commands sequentially
3. **Create Templates**: Save your workflows as bash scripts
4. **Batch Process**: Process multiple files with loops
5. **Schedule Tasks**: Use cron for regular exports/uploads
6. **Monitor Performance**: Track what works with analytics
7. **Iterate Quickly**: Test thumbnails/titles before committing
8. **Archive Regularly**: Keep active storage fast
9. **Version Control**: Git commit important project states
10. **Document Workflows**: Save successful patterns

---

## Your Turn!

Copy any of these examples and modify them for your specific needs. The StudioFlow suite is designed to be flexible and composable - mix and match tools to create your perfect workflow.