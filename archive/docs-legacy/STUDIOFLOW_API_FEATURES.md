# StudioFlow API Features Documentation

## 🎯 Overview

StudioFlow has been enhanced with powerful AI and API integrations that bring professional-grade automation to your video production workflow. These new features include real Whisper AI transcription, YouTube Data API v3 integration for upload and analytics, and more.

## 🎤 Enhanced Audio Processing (sf-audio)

### Whisper AI Integration

The `sf-audio` tool now features complete OpenAI Whisper integration for professional transcription:

#### Features:
- **Multiple Model Sizes**: tiny, base, small, medium, large
- **Multi-Language Support**: Auto-detect or specify language
- **Multiple Output Formats**:
  - SRT (SubRip subtitles)
  - WebVTT (Web Video Text Tracks)
  - Plain text
  - JSON with timestamps and word-level timing
- **Python API Integration**: Direct model control for better accuracy
- **CLI Fallback**: Seamless fallback to Whisper CLI if API unavailable

#### Usage:

```bash
# Basic transcription
sf-audio transcribe video.mp4

# Advanced options
sf-audio transcribe video.mp4 --model large --language en

# Process multiple files
for video in *.mp4; do
    sf-audio transcribe "$video" --model medium
done
```

#### Installation:

```bash
# Install Whisper
pip install openai-whisper

# For GPU acceleration (recommended for large models)
pip install openai-whisper[cuda]
```

#### Output Files:
- `video.txt` - Plain text transcript
- `video.srt` - Subtitles for video editors
- `video.vtt` - Web-ready captions
- `video_transcript.json` - Detailed timing data

### Voice Processing Enhancements

Enhanced voice processing with professional audio filters:
- **EQ Optimization**: Automatic voice clarity enhancement
- **Compression**: Dynamic range control
- **Normalization**: Consistent loudness (-16 LUFS)

```bash
sf-audio voice recording.wav --enhance
```

## 📺 YouTube API Integration (sf-youtube)

### Complete YouTube Data API v3 Support

The `sf-youtube` tool now includes full YouTube automation capabilities:

#### Features:
- **Direct Upload**: Upload videos with full metadata control
- **Analytics Dashboard**: Real-time channel and video statistics
- **Metadata Updates**: Edit titles, descriptions, tags after upload
- **OAuth 2.0 Authentication**: Secure API access
- **Progress Tracking**: Real-time upload progress

#### Setup:

1. **Enable YouTube Data API v3:**
   ```
   1. Go to https://console.cloud.google.com/
   2. Create new project or select existing
   3. Enable "YouTube Data API v3"
   4. Create OAuth 2.0 credentials
   5. Download credentials.json
   6. Place in ~/.studioflow/youtube/credentials.json
   ```

2. **First Authentication:**
   ```bash
   sf-youtube analytics
   # Browser will open for authentication
   # Token saved for future use
   ```

#### Upload Videos:

```bash
# Basic upload (starts as private)
sf-youtube upload render.mp4 "My Amazing Video"

# With full metadata
sf-youtube upload render.mp4 "Tutorial: Python in 2025" \
    --description "Complete Python tutorial..." \
    --tags "python,programming,tutorial,2025"
```

#### Channel Analytics:

```bash
# Get channel statistics
sf-youtube analytics

# Output:
📊 YouTube Analytics
====================================
Channel: Your Channel Name
Subscribers: 10,234
Total Views: 1,234,567
Total Videos: 89

Recent Videos Performance:
  • Latest Video Title
    Views: 12,345 | Likes: 567
```

#### Update Existing Videos:

```bash
# Update video metadata
sf-youtube update VIDEO_ID \
    --title "New Improved Title" \
    --description "Updated description" \
    --tags "new,tags,here"
```

### Viral Optimization Features

Enhanced title generation with CTR predictions:

```bash
# Generate viral titles
sf-youtube titles "Python Tutorial" --style viral

# Output includes:
- 10 title variants
- CTR predictions (8-10%)
- Emotional triggers identified
- Platform-specific versions
```

### Upload Time Optimization

```bash
# Get optimal upload times
sf-youtube upload-time

# Returns best times for:
- YouTube: Tuesday-Thursday, 2PM EST
- Instagram: 11AM, 2PM, 5PM
- TikTok: 6AM, 10AM, 7PM, 9PM
```

## 🚀 Installation Requirements

### Core Dependencies:

```bash
# Audio processing
pip install openai-whisper

# YouTube API
pip install google-auth google-auth-oauthlib google-auth-httplib2
pip install google-api-python-client

# Configuration
pip install PyYAML
```

### Optional GPU Support:

```bash
# For faster Whisper transcription
pip install openai-whisper[cuda]
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 🔧 Configuration

### Audio Settings (config.yaml):

```yaml
audio:
  whisper_model: base  # tiny, base, small, medium, large
  default_language: auto  # or specific like 'en', 'es', 'fr'
  output_formats: [txt, srt, vtt, json]
  voice_enhancement: true
```

### YouTube Settings:

```yaml
youtube:
  default_privacy: private  # private, unlisted, public
  default_category: 22  # People & Blogs
  upload_defaults:
    made_for_kids: false
    embeddable: true
    license: youtube  # or creativeCommon
```

## 📊 Performance Metrics

### Whisper Transcription Speed (on RTX 3080):

| Model | Speed | Accuracy | RAM Usage |
|-------|-------|----------|-----------|
| tiny | 32x realtime | Good | 1 GB |
| base | 16x realtime | Better | 1 GB |
| small | 8x realtime | Great | 2 GB |
| medium | 4x realtime | Excellent | 5 GB |
| large | 2x realtime | Best | 10 GB |

### YouTube Upload Speeds:

- **Resumable uploads**: Automatic retry on failure
- **Chunk size**: Optimized for large files
- **Progress tracking**: Real-time percentage updates

## 🎯 Workflow Examples

### Complete YouTube Production Pipeline:

```bash
# 1. Create project
sf new "Python Tutorial 2025"

# 2. Import footage
# [SD card auto-imports]

# 3. Generate Resolve project
sf resolve

# 4. [Edit in DaVinci Resolve]

# 5. Extract and transcribe audio
sf-audio extract final_render.mp4
sf-audio transcribe final_render_audio.wav --model medium

# 6. Generate viral titles
sf-youtube titles "Python Tutorial" --style tutorial

# 7. Create metadata
sf-youtube metadata "Python Tutorial 2025" --platform youtube

# 8. Upload to YouTube
sf-youtube upload final_render.mp4 "Python Tutorial 2025 - Complete Guide" \
    --description "$(cat metadata/youtube_description.txt)" \
    --tags "python,tutorial,programming,2025"

# 9. Check analytics
sf-youtube analytics
```

### Batch Transcription Pipeline:

```bash
# Transcribe all videos in project
for video in 01_MEDIA/*.mp4; do
    echo "Processing: $video"
    sf-audio transcribe "$video" --model small --language en
done

# Combine all transcripts
cat 01_MEDIA/*.txt > full_transcript.txt
```

## 🔒 Security Notes

### API Credentials:
- **Never commit** credentials.json to version control
- OAuth tokens stored securely in ~/.studioflow/youtube/
- Tokens auto-refresh when expired
- Revoke access anytime at: https://myaccount.google.com/permissions

### Privacy Settings:
- Videos upload as **private** by default
- Change privacy in YouTube Studio after review
- No automatic public publishing for safety

## 🐛 Troubleshooting

### Whisper Issues:

```bash
# If Whisper fails to load model:
export TORCH_HOME=/path/to/cache

# If out of memory:
sf-audio transcribe video.mp4 --model tiny  # Use smaller model

# If no GPU detected:
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### YouTube API Issues:

```bash
# Reset authentication:
rm ~/.studioflow/youtube/token.json
sf-youtube analytics  # Re-authenticate

# API quota exceeded:
# Wait 24 hours or create new project in Google Console

# Upload fails:
# Check file size (<128GB)
# Verify format (MP4, MOV, AVI supported)
```

## 📈 Future Enhancements

### Coming Soon:
- **Automatic captioning**: Burn subtitles into video
- **Translation**: Multi-language subtitle generation
- **Thumbnail upload**: Direct thumbnail API support
- **Playlist management**: Organize videos into playlists
- **Comment moderation**: AI-powered comment filtering
- **Live streaming**: Schedule and manage live streams
- **Analytics export**: CSV/JSON export for analysis

## 📚 Additional Resources

- [Whisper Documentation](https://github.com/openai/whisper)
- [YouTube Data API Reference](https://developers.google.com/youtube/v3)
- [Google Cloud Console](https://console.cloud.google.com/)
- [StudioFlow GitHub](https://github.com/yourusername/studioflow)

---

**StudioFlow** - Professional video production automation, now with AI and API superpowers! 🚀