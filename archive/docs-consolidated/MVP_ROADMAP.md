# MVP Architecture & Roadmap for Creator Studio

## 🎯 Core Insight: Pipeline + Plugins Pattern

The simplest extensible architecture is a **pipeline with plugin hooks**. Start with a bash script, add Python plugins as needed.

## 📐 MVP Architecture (Ship Today)

### The Core: One Script with Hooks

```bash
#!/bin/bash
# creator-studio.sh - The entire system in one file

# Pipeline stages - each can be overridden by plugins
stage_1_research() {
    echo "Researching: $1"
    # Default: just echo the topic
    # Plugin can override with AI research
}

stage_2_script() {
    echo "Writing script about: $1"
    # Default: template script
    # Plugin can add LLM generation
}

stage_3_video() {
    echo "Creating video"
    # Default: slideshow with text
    # Plugin can add voice, animation
}

stage_4_optimize() {
    echo "Optimizing for YouTube"
    # Default: basic title
    # Plugin can add AI optimization
}

stage_5_publish() {
    echo "Publishing"
    # Default: save locally
    # Plugin can upload to YouTube
}

# Main pipeline
run_pipeline() {
    topic="$1"

    # Each stage outputs to next
    research_output=$(stage_1_research "$topic")
    script_output=$(stage_2_script "$research_output")
    video_output=$(stage_3_video "$script_output")
    optimized_output=$(stage_4_optimize "$video_output")
    stage_5_publish "$optimized_output"
}

# Run it
run_pipeline "$1"
```

### Plugin System: Drop-in Python Scripts

```python
# plugins/01_research.py
import sys
import json

def research(topic):
    """Override default research with AI"""
    # Can import ChainMind algorithms later
    ideas = [f"Idea about {topic}"]
    return json.dumps(ideas)

if __name__ == "__main__":
    topic = sys.argv[1]
    print(research(topic))
```

### Configuration: Simple YAML

```yaml
# config.yaml
pipeline:
  research:
    enabled: true
    plugin: "plugins/01_research.py"
    timeout: 30

  script:
    enabled: true
    plugin: "plugins/02_script.py"
    llm: "ollama"

  video:
    enabled: true
    plugin: "plugins/03_video.py"
    use_vast: false  # Start local

  optimize:
    enabled: true
    plugin: "plugins/04_optimize.py"

  publish:
    enabled: false  # Manual review first
    plugin: "plugins/05_publish.py"
```

## 🚀 Day 1 MVP: Minimum Working System

### Step 1: Create Structure (30 min)
```bash
mkdir -p ~/creator-studio/{plugins,output,temp}
cd ~/creator-studio
```

### Step 2: Core Pipeline (1 hour)
```python
#!/usr/bin/env python3
# creator.py - Minimal working pipeline

import subprocess
import json
from pathlib import Path
from datetime import datetime

class CreatorPipeline:
    def __init__(self):
        self.project_dir = Path.home() / "creator-studio"
        self.output_dir = self.project_dir / "output" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, topic):
        """Main pipeline - each step can be enhanced later"""

        # Step 1: Research (for now, just return topic)
        print(f"[1/5] Researching: {topic}")
        idea = self.research(topic)
        (self.output_dir / "1_idea.json").write_text(json.dumps(idea))

        # Step 2: Script (basic template for now)
        print(f"[2/5] Writing script")
        script = self.write_script(idea)
        (self.output_dir / "2_script.txt").write_text(script)

        # Step 3: Video (text on black background for now)
        print(f"[3/5] Creating video")
        video_path = self.create_video(script)

        # Step 4: Optimize (basic metadata for now)
        print(f"[4/5] Optimizing")
        metadata = self.optimize(video_path, idea)
        (self.output_dir / "4_metadata.json").write_text(json.dumps(metadata))

        # Step 5: Publish (just save for now)
        print(f"[5/5] Ready to publish")
        print(f"\nOutput saved to: {self.output_dir}")

        return self.output_dir

    def research(self, topic):
        """Plugin point: Research enhancement"""
        # Default: simple idea
        # TODO: Add TreeOfThoughts from ChainMind
        return {
            "topic": topic,
            "title": f"How to {topic}",
            "angle": "tutorial"
        }

    def write_script(self, idea):
        """Plugin point: Script generation"""
        # Default: template
        # TODO: Add LLM generation
        # TODO: Add RetentionScorer
        return f"""
Title: {idea['title']}

Introduction:
Welcome to this video about {idea['topic']}.

Main Content:
Today we'll learn about {idea['topic']}.

Conclusion:
Thanks for watching!
        """

    def create_video(self, script):
        """Plugin point: Video generation"""
        # Default: Simple text video using ffmpeg
        # TODO: Add voice synthesis
        # TODO: Add Vast.ai rendering

        video_path = self.output_dir / "3_video.mp4"

        # Create simple video with text
        cmd = [
            "ffmpeg", "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=5",
            "-vf", f"drawtext=text='Created with Creator Studio':x=100:y=100:fontsize=48:fontcolor=white",
            str(video_path)
        ]

        subprocess.run(cmd, capture_output=True)
        return video_path

    def optimize(self, video_path, idea):
        """Plugin point: YouTube optimization"""
        # Default: basic metadata
        # TODO: Add PromptOptimizer from ChainMind
        # TODO: Add thumbnail generation
        return {
            "title": idea['title'],
            "description": f"A video about {idea['topic']}",
            "tags": [idea['topic'], "tutorial", "how to"]
        }

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "Python programming"

    pipeline = CreatorPipeline()
    output = pipeline.run(topic)
    print(f"\n✅ Complete! Check: {output}")
```

### Step 3: Make It Work (30 min)
```bash
# Test it
python3 creator.py "Python automation"

# Should create:
# ~/creator-studio/output/20240923_140000/
#   1_idea.json
#   2_script.txt
#   3_video.mp4
#   4_metadata.json
```

## 🔌 Plugin Enhancement Path (Week 1)

### Day 2: Add StudioFlow Integration
```python
# plugins/studioflow_bridge.py
from studioflow.core.transcription import TranscriptionService
from studioflow.core.youtube_api import YouTubeAPIService

class StudioFlowPlugin:
    def enhance_script(self, script):
        # Use existing StudioFlow features
        return optimize_for_retention(script)

    def publish(self, video_path, metadata):
        # Use StudioFlow's YouTube uploader
        youtube = YouTubeAPIService()
        return youtube.upload_video(video_path, **metadata)
```

### Day 3: Add ChainMind Algorithms
```python
# plugins/ai_enhancement.py
import sys
sys.path.append('/mnt/nas/Archive/Projects/AI_Development/chainmind')

from backend.plugins.tree_of_thoughts import TreeOfThoughts
from backend.plugins.retention_scorer import RetentionScorer

class AIPlugin:
    def research(self, topic):
        # Use TreeOfThoughts for ideas
        tot = TreeOfThoughts()
        return tot.generate_ideas(topic)

    def score_script(self, script):
        # Use RetentionScorer
        scorer = RetentionScorer()
        return scorer.predict_retention(script)
```

### Day 4: Add Voice & Video
```python
# plugins/media_generation.py
class MediaPlugin:
    def add_voice(self, script):
        # Use voice cloning from Creator Hub
        # For now, use system TTS
        subprocess.run(["espeak", script, "-w", "voice.wav"])
        return "voice.wav"

    def create_video_with_voice(self, script, voice):
        # Combine voice with video
        # Later: Use Vast.ai for complex rendering
        pass
```

### Day 5: Add Optimization
```python
# plugins/youtube_optimizer.py
class OptimizerPlugin:
    def optimize_title(self, title):
        # Use PromptOptimizer from ChainMind
        return make_title_viral(title)

    def generate_thumbnail(self, video_path):
        # Use StudioFlow thumbnail generator
        return create_thumbnail(video_path)
```

## 📊 Progressive Enhancement Schedule

| Day | Feature | Complexity | Value |
|-----|---------|------------|-------|
| 1 | Basic pipeline works | ⭐ | Can create simple videos |
| 2 | StudioFlow integration | ⭐⭐ | YouTube upload works |
| 3 | AI research/scripts | ⭐⭐⭐ | Better content |
| 4 | Voice synthesis | ⭐⭐ | More engaging |
| 5 | YouTube optimization | ⭐⭐ | Higher CTR |
| 6 | Vast.ai rendering | ⭐⭐⭐⭐ | Complex videos |
| 7 | Full automation | ⭐⭐⭐ | Hands-free |

## 🎯 Next Claude Session Roadmap

### Session 2: Enhanced Plugins (Oct 1-3)
```markdown
## Goals
1. Port RetentionScorer as standalone module
2. Integrate Ollama for local LLM
3. Add voice cloning
4. Create thumbnail A/B testing

## Deliverables
- plugins/retention_scorer.py
- plugins/llm_local.py
- plugins/voice_clone.py
- plugins/thumbnail_ab.py
```

### Session 3: Automation & Scheduling (Oct 4-6)
```markdown
## Goals
1. Add cron scheduling
2. Trend monitoring
3. Batch processing
4. Analytics tracking

## Deliverables
- scheduler.py (cron-based)
- trend_monitor.py
- batch_processor.py
- analytics.py
```

### Session 4: Web Dashboard (Oct 7-9)
```markdown
## Goals
1. Simple Flask dashboard
2. Job queue visibility
3. Performance metrics
4. Manual override controls

## Deliverables
- web/app.py (Flask)
- web/templates/dashboard.html
- web/api.py
```

### Session 5: Polish & Launch (Oct 10-12)
```markdown
## Goals
1. Error handling
2. Logging system
3. Backup & recovery
4. Channel launch

## Deliverables
- Full system test
- 10 videos published
- Documentation complete
```

## 💡 Why This Architecture Wins

### 1. **Starts Simple**
- Day 1: Working video pipeline
- No complex setup
- No dependencies

### 2. **Grows Naturally**
- Each plugin adds one feature
- Plugins don't affect core
- Can develop in parallel

### 3. **Testable**
- Each stage has clear input/output
- Can test plugins independently
- Can run partial pipelines

### 4. **Flexible**
- Swap plugins anytime
- Mix local/cloud processing
- Enable/disable features via config

### 5. **Debuggable**
- Each stage saves output
- Can inspect at any point
- Clear error messages

## 🚨 Critical Success Factors

### Must Have by End of Day 1
- [ ] Pipeline runs end-to-end
- [ ] Creates actual video file
- [ ] Saves all intermediate outputs
- [ ] Clear next steps

### Must Have by End of Week 1
- [ ] One real video uploaded to YouTube
- [ ] At least 3 plugins working
- [ ] Automated daily run
- [ ] Basic quality metrics

### Must Have by Oct 12
- [ ] 10+ videos published
- [ ] Full automation working
- [ ] Analytics showing improvement
- [ ] Ready for daily use

## 📝 Configuration Management

### Simple ENV File
```bash
# .env
YOUTUBE_API_KEY=xxx
VAST_API_KEY=xxx
OLLAMA_HOST=localhost:11434
OUTPUT_DIR=~/creator-studio/output
ENABLE_UPLOAD=false  # Safety first
```

### Feature Flags
```python
# features.py
FEATURES = {
    'use_ai_research': False,  # Start simple
    'use_voice_clone': False,  # Add later
    'use_vast_gpu': False,     # Add when ready
    'auto_upload': False,      # Manual first
    'use_retention_scorer': False,  # Add day 3
}
```

## 🎬 Day 1 Deliverable

By end of today, you should be able to:

```bash
# Run this command
python3 ~/creator-studio/creator.py "How to use Python"

# And get these files
~/creator-studio/output/20240923_140000/
  ├── 1_idea.json       # Topic research
  ├── 2_script.txt      # Video script
  ├── 3_video.mp4       # Actual video
  └── 4_metadata.json   # YouTube metadata
```

The video will be simple (text on black), but it will be a REAL video you could upload.

## 🔑 The Key Insight

**Don't build a platform. Build a pipeline.**

Pipelines are:
- Linear (easy to understand)
- Composable (plugins add features)
- Observable (see each stage)
- Reliable (failures are obvious)

Everything else (web UI, scheduling, optimization) is just plugins to the pipeline.

Ready to build this? Let's start with creating `creator.py` right now!