# sf-youtube - YouTube Viral Optimization

## Overview
`sf-youtube` provides tools for maximizing YouTube video performance through viral title generation, retention optimization, metadata creation, and competitive analysis. Focused on growth metrics: virality, subscribership, viewtime, and upload frequency.

## Installation
```bash
sf-youtube  # Direct command
sf youtube  # Via master command
sf yt       # Short alias
```

## Commands

### titles
Generate viral-optimized title variants with psychological triggers.

```bash
sf-youtube titles "Python Tutorial" --style viral
sf-youtube titles "Camera Review" --style comparison
sf-youtube titles "How to Edit" --style tutorial
```

**Styles:**
- `viral` - Maximum CTR with curiosity gaps
- `tutorial` - Educational, SEO-optimized
- `comparison` - "X vs Y" format

**Output includes:**
- 10 title variants
- CTR predictions (8-10%)
- Emotional triggers identified
- Platform-specific versions

### hooks
Generate opening hooks for maximum retention.

```bash
sf-youtube hooks "My Project" --style retention
sf-youtube hooks "Tutorial" --style story
sf-youtube hooks "Review" --style question
```

**Hook Types:**
- `retention` - "Watch entire video" psychology
- `story` - Personal narrative opening
- `question` - Engaging curiosity

### metadata
Generate platform-optimized descriptions and tags.

```bash
sf-youtube metadata "My Project" --platform youtube
sf-youtube metadata "Reel Project" --platform instagram
sf-youtube metadata "Short" --platform tiktok
```

**Generates:**
- SEO-optimized descriptions
- Timestamp templates
- Hashtag strategies
- Platform-specific formatting

### upload-time
Calculate optimal upload times for maximum reach.

```bash
sf-youtube upload-time
sf-youtube upload-time --timezone EST
sf-youtube upload-time --audience US
```

**Shows:**
- Best days (Tue-Thu for YouTube)
- Peak hours by platform
- Regional optimization
- Avoid times

### compete
Analyze competition and find content gaps.

```bash
sf-youtube compete "python tutorial"
sf-youtube compete "camera review" --count 10
```

**Analysis:**
- Market saturation score
- Content gap opportunities
- Recommended angles
- Thumbnail styles
- Optimal video length

### thumbnail-test
Set up A/B testing for thumbnails.

```bash
sf-youtube thumbnail-test "My Project"
```

**Creates:**
- 3 variant directories
- Testing checklist
- Rotation schedule
- Performance tracking

## Viral Optimization Features

### Title Psychology
```python
Psychological Triggers:
- Curiosity: "Nobody Talks About"
- Urgency: "2025", "Breaking"
- Social Proof: "Everyone's Wrong"
- Emotion: "Mind-Blowing", "Insane"
- Value: "Ultimate", "Complete"
```

### Retention Strategies
```
First 3 Seconds:
- Hook with pattern interrupt
- Promise clear value
- Create open loop
- Match thumbnail expectation
```

### CTR Optimization
```
Title Best Practices:
- 50-60 characters optimal
- Numbers increase CTR 36%
- Questions increase CTR 23%
- "How to" remains evergreen
- Brackets [EASY] add context
```

## Platform-Specific Optimization

### YouTube
```yaml
Optimal Settings:
  video_length: 8-12 minutes
  upload_time: "2-4 PM EST Tue-Thu"
  thumbnail: "High contrast, face + text"
  description: "600+ words, timestamps, links"
  tags: "10-15 targeted keywords"
  retention_goal: ">50% average view duration"
```

### Instagram Reels
```yaml
Optimal Settings:
  video_length: 30-60 seconds
  upload_time: "11 AM, 2 PM, 5 PM"
  format: "9:16 vertical"
  caption: "125 chars hook + hashtags"
  hashtags: "10 high, 10 medium, 10 niche"
  engagement: "Reply to comments in first hour"
```

### TikTok
```yaml
Optimal Settings:
  video_length: 15-30 seconds
  upload_time: "6 AM, 10 AM, 7 PM"
  format: "9:16 vertical"
  trends: "Jump within 24-48 hours"
  sounds: "Use trending audio"
  frequency: "3-5 posts daily"
```

## Growth Formulas

### Viral Title Templates
```bash
# Curiosity Gap
"The {topic} Nobody Talks About"
"Why Everyone's Wrong About {topic}"

# Social Proof
"{topic} Is Breaking The Internet"
"Why {topic} Is Going Viral"

# Value Promise
"Master {topic} in 10 Minutes"
"The Only {topic} Guide You'll Need"

# Emotional Hook
"This {topic} Trick Blew My Mind"
"I Can't Believe {topic} Works"
```

### Description Framework
```markdown
📺 WHAT'S IN THIS VIDEO:
[Compelling 2-line summary]

⏱️ TIMESTAMPS:
00:00 Hook
00:30 Main Point 1
...

🔗 RESOURCES:
[Links mentioned]

📱 CONNECT:
[Social media]

#hashtag1 #hashtag2 #hashtag3

👍 LIKE & SUBSCRIBE for more!
```

## Automation Examples

### Complete Upload Workflow
```bash
#!/bin/bash
# Full YouTube optimization

PROJECT="Tutorial_Video"
TOPIC="Python Programming"

# Generate viral titles
sf-youtube titles "$TOPIC" --style tutorial > titles.txt

# Create hooks
sf-youtube hooks "$PROJECT" --style retention

# Generate metadata
sf-youtube metadata "$PROJECT" --platform youtube

# Set up thumbnail testing
sf-youtube thumbnail-test "$PROJECT"

# Check optimal upload time
sf-youtube upload-time

# Analyze competition
sf-youtube compete "$TOPIC"
```

### Multi-Platform Export
```bash
# Generate platform-specific versions
for platform in youtube instagram tiktok; do
  sf-youtube metadata "$PROJECT" --platform $platform
done
```

## Analytics Integration

### Tracking Metrics
```json
{
  "video": "Tutorial_Video",
  "metrics": {
    "ctr": 8.5,
    "retention": 52,
    "like_ratio": 0.95,
    "comment_rate": 0.03,
    "share_rate": 0.01
  },
  "growth": {
    "subscribers_gained": 250,
    "watch_hours": 450
  }
}
```

### A/B Test Results
```json
{
  "thumbnail_test": {
    "variant_a": {"ctr": 7.2, "winner": false},
    "variant_b": {"ctr": 9.1, "winner": true},
    "variant_c": {"ctr": 8.3, "winner": false}
  }
}
```

## Best Practices

### For Virality
1. **Test 3+ title variants** using YouTube's test feature
2. **Hook in first 3 seconds** or lose 30% of viewers
3. **Pattern interrupt** every 30 seconds
4. **End screen CTR** should be >20%
5. **Reply to early comments** for algorithm boost

### For Growth
1. **Consistent upload schedule** (algorithm favors consistency)
2. **Series/playlists** increase session duration
3. **Community posts** between uploads
4. **Premiere features** for event feel
5. **Shorts** as discovery funnel

### For Retention
1. **Chapter markers** improve accessibility
2. **Visual changes** every 3-5 seconds
3. **Multiple hooks** throughout video
4. **Clear value delivery** matching title promise
5. **Strong CTA** without being pushy

## Configuration

`~/.config/studioflow/youtube.yml`:
```yaml
defaults:
  channel_name: "Your Channel"
  upload_time: "14:00 EST"
  tags_strategy: "broad_to_specific"
  
optimization:
  title_length: 60
  description_length: 600
  tags_count: 15
  
platforms:
  youtube:
    enabled: true
    api_key: "your_api_key"
  instagram:
    enabled: true
    username: "@handle"
  tiktok:
    enabled: true
    username: "@handle"
```

## Advanced Features

### SEO Research
```bash
sf-youtube seo "topic" --depth full
# Returns:
# - Search volume
# - Competition score
# - Related keywords
# - Trending topics
```

### Script Optimization
```bash
sf-youtube script "project" --optimize retention
# Analyzes script for:
# - Hook strength
# - Pacing issues
# - CTA placement
# - Value delivery
```

### Competitor Tracking
```bash
sf-youtube track "competitor_channel"
# Monitors:
# - Upload frequency
# - Title patterns
# - Thumbnail styles
# - Performance metrics
```

## Troubleshooting

**Low CTR (<5%):**
- Test more title variants
- Improve thumbnail contrast
- Check title-thumbnail alignment
- Analyze competitor success

**Poor Retention (<40%):**
- Strengthen opening hook
- Add pattern interrupts
- Improve pacing
- Deliver value faster

**Slow Growth:**
- Increase upload consistency
- Improve SEO optimization
- Engage with community
- Create series/playlists

## Related Tools

- `sf-project` - Organize video projects
- `sf-obs` - Create viral scenes
- `sf-ai` - Generate optimized scripts
- `sf-resolve` - Edit with retention in mind