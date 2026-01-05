# sf-ai - AI Content Generation

## Overview
`sf-ai` leverages AI to generate video scripts, content ideas, titles, and creative prompts. Optimized for viral content creation with psychological triggers and retention strategies.

## Installation
```bash
sf-ai        # Direct command
sf ai        # Via master command
sfscript     # Alias for script generation
sfideas      # Alias for idea generation
```

## Commands

### script
Generate complete video scripts with hooks and CTAs.

```bash
sf-ai script "My Project" --style educational
sf-ai script "Review Video" --style review --length 10
sf-ai script "Tutorial" --style tutorial --tone casual
```

**Styles:**
- `educational` - Teaching format with clear steps
- `entertainment` - Story-driven, high energy
- `review` - Product/service analysis
- `tutorial` - Step-by-step guide
- `documentary` - Narrative storytelling

**Options:**
- `-l, --length` - Target video length (minutes)
- `-t, --tone` - casual/professional/humorous
- `-a, --audience` - Target demographic

### ideas
Generate viral video ideas based on trends.

```bash
sf-ai ideas "python programming" --count 10
sf-ai ideas --trending --platform youtube
sf-ai ideas --niche "tech reviews"
```

**Output:**
- Video title
- Hook concept
- Unique angle
- Estimated views potential
- Competition level

### prompt
Create AI image generation prompts.

```bash
sf-ai prompt "thumbnail" --style "high contrast"
sf-ai prompt "b-roll" --mood "cinematic"
sf-ai prompt "transition" --effect "glitch"
```

**Types:**
- `thumbnail` - YouTube thumbnail prompts
- `b-roll` - Supporting footage ideas
- `overlay` - Graphic overlay concepts
- `transition` - Scene transition effects

### analyze
Analyze content for viral potential.

```bash
sf-ai analyze "script.txt" --metrics all
sf-ai analyze "My Project" --suggest improvements
```

**Metrics:**
- Hook strength (0-10)
- Retention prediction
- Emotional triggers
- CTA effectiveness
- SEO score

### optimize
Optimize existing content for virality.

```bash
sf-ai optimize "script.txt" --goal retention
sf-ai optimize "title.txt" --goal ctr
sf-ai optimize "description.txt" --goal seo
```

## Script Generation

### Script Structure
```markdown
# VIDEO SCRIPT: [Title]

## HOOK (0:00-0:05)
[Attention-grabbing opening]

## INTRO (0:05-0:15)
[Set expectations, preview value]

## MAIN CONTENT
### Section 1 (0:15-2:00)
[Core content with retention hooks]

### Section 2 (2:00-4:00)
[Detailed explanation/demonstration]

### Section 3 (4:00-6:00)
[Examples and applications]

## CONCLUSION (6:00-6:30)
[Recap and CTA]

## END SCREEN (6:30-7:00)
[Subscribe prompt, next video teaser]
```

### Psychological Triggers
```python
Triggers Used:
- Curiosity Gap: "You won't believe..."
- Social Proof: "Everyone is talking about..."
- FOMO: "Before it's too late..."
- Authority: "Experts agree..."
- Scarcity: "Limited time..."
- Reciprocity: "Free value..."
```

### Platform Optimization

#### YouTube Scripts
```bash
sf-ai script "Tutorial" --platform youtube
# Generates:
# - 8-12 minute optimal length
# - Multiple retention hooks
# - Clear chapter structure
# - End screen setup
```

#### Instagram Scripts
```bash
sf-ai script "Reel" --platform instagram
# Generates:
# - 30-60 second format
# - Visual-first narrative
# - Text overlay suggestions
# - Trending audio recommendations
```

#### TikTok Scripts
```bash
sf-ai script "Short" --platform tiktok
# Generates:
# - 15-30 second format
# - Immediate hook
# - Fast pacing
# - Trend integration
```

## Content Ideation

### Viral Formulas
```bash
sf-ai ideas --formula "transformation"
# Generates: "I tried X for 30 days"

sf-ai ideas --formula "comparison"
# Generates: "X vs Y: Shocking results"

sf-ai ideas --formula "revelation"
# Generates: "The truth about X"

sf-ai ideas --formula "challenge"
# Generates: "Can you solve this?"
```

### Trend Analysis
```bash
# Get trending topics
sf-ai trends --platform youtube --category tech

# Generate ideas from trends
sf-ai ideas --from-trends --count 20

# Predict viral potential
sf-ai predict "Video Title" --data historical
```

### Content Calendar
```bash
# Generate month of content
sf-ai calendar --month january --videos-per-week 3

# Output:
{
  "week_1": [
    {"day": "Monday", "title": "...", "type": "tutorial"},
    {"day": "Wednesday", "title": "...", "type": "review"},
    {"day": "Friday", "title": "...", "type": "short"}
  ]
}
```

## AI Prompt Engineering

### Thumbnail Prompts
```bash
sf-ai prompt thumbnail --elements "shocked face, bright colors, arrow"
# Output:
"YouTube thumbnail: Shocked expression person pointing at screen,
bright red arrow, neon blue background, high contrast, photorealistic,
ultra detailed, 1920x1080, no text"
```

### B-Roll Prompts
```bash
sf-ai prompt b-roll --scene "coding montage"
# Output:
"Cinematic coding scene: Multiple monitors with code, blue glow,
dark room, keyboard close-up, fast typing, tech aesthetic,
shallow depth of field, 4K quality"
```

## Content Analysis

### Retention Optimization
```bash
sf-ai analyze script.txt --retention
# Reports:
# - Hook strength: 8/10
# - Drop-off points identified
# - Suggested improvements
# - Pattern interrupt locations
```

### SEO Analysis
```bash
sf-ai analyze "My Video" --seo
# Reports:
# - Keyword density
# - Title optimization
# - Description suggestions
# - Tag recommendations
```

## Advanced Features

### Voice Cloning Prep
```bash
# Prepare script for AI voice
sf-ai voice-prep script.txt --style natural
# Adds:
# - Pronunciation guides
# - Emphasis markers
# - Pause indicators
# - Emotion cues
```

### Multi-Language
```bash
# Generate in different languages
sf-ai script "Tutorial" --language spanish
sf-ai translate script.txt --to french
```

### A/B Testing
```bash
# Generate variants for testing
sf-ai variants "Video Title" --count 5
sf-ai variants script.txt --section hook
```

## Integration with Other Tools

### With sf-youtube
```bash
# Complete optimization pipeline
sf-ai script "Project" | sf-youtube optimize
sf-ai ideas --trending | sf-youtube compete
```

### With sf-obs
```bash
# Generate scene descriptions
sf-ai scenes "Tutorial" | sf-obs setup-scenes
```

### With sf-audio
```bash
# Generate voice-over script
sf-ai script "Project" --format voiceover
sf-audio generate-voice script.txt
```

## Templates Library

### Educational Template
```python
structure = {
  "hook": "Question or surprising fact",
  "promise": "What viewer will learn",
  "credibility": "Why trust this info",
  "content": [
    "Concept explanation",
    "Real-world example",
    "Step-by-step guide",
    "Common mistakes"
  ],
  "summary": "Key takeaways",
  "cta": "Apply knowledge prompt"
}
```

### Entertainment Template
```python
structure = {
  "hook": "Cliffhanger or shock",
  "setup": "Context and stakes",
  "rising_action": "Build tension",
  "climax": "Peak moment",
  "resolution": "Outcome",
  "reflection": "What it means",
  "cta": "Engagement prompt"
}
```

## Configuration

`~/.config/studioflow/ai.yml`:
```yaml
api:
  provider: openai  # or anthropic, local
  model: gpt-4
  api_key: ${AI_API_KEY}
  
defaults:
  style: educational
  tone: casual
  length: 10
  platform: youtube
  
optimization:
  viral_factors: true
  seo_keywords: true
  retention_hooks: true
  
prompts:
  custom_system: "You are a viral video expert..."
  temperature: 0.8
  max_tokens: 2000
```

## Best Practices

### Script Writing
1. **Hook in first 3 seconds**
2. **Promise clear value upfront**
3. **Pattern interrupt every 30s**
4. **Multiple CTAs throughout**
5. **End with next video teaser**

### Idea Generation
1. **Mix evergreen and trending**
2. **Target specific problems**
3. **Use emotional triggers**
4. **Create content series**
5. **Repurpose across platforms**

### Optimization
1. **Test multiple versions**
2. **Track performance metrics**
3. **Iterate based on data**
4. **Stay current with trends**
5. **Maintain authenticity**

## Performance Metrics

### Success Indicators
```json
{
  "script_quality": {
    "hook_strength": 9,
    "retention_score": 8.5,
    "cta_effectiveness": 8,
    "seo_optimization": 9.5
  },
  "predicted_performance": {
    "ctr": "8-10%",
    "retention": "55-60%",
    "engagement": "5-7%"
  }
}
```

## Troubleshooting

**"API rate limit exceeded":**
- Reduce request frequency
- Batch operations
- Use local models

**"Script too generic":**
- Add specific context
- Define target audience
- Include unique angle

**"Low viral score":**
- Strengthen hook
- Add emotional triggers
- Improve title
- Check trend alignment

## Related Tools

- `sf-youtube` - Optimize generated content
- `sf-project` - Organize scripts
- `sf-audio` - Convert to voice-over
- `sf-obs` - Record scripted content