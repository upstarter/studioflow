# CLAUDE.md - Creator AI Studio Development Guide
*Last Updated: September 23, 2024 | Deadline: October 12, 2024*

## 🎯 Current Mission
Build a personal YouTube automation system that works TODAY, not a commercial platform. Focus on tools that immediately improve video creation workflow.

## 🧠 Core Philosophy
- **Use what works** - Don't rebuild working features
- **Quick wins over perfection** - Ship something usable daily
- **Local first** - No deployment complexity
- **Test by using** - Make real videos, not demos

## 📊 What We Have (And Actually Works)

### ✅ StudioFlow (Already Working)
- Auto-import from SD cards
- Whisper transcription
- YouTube upload
- Thumbnail generation
- Silence removal
- **Keep as-is, just add hooks for other services**

### ✅ Creator AI Hub (Partially Working)
- Voice cloning works ($0.02/video with Vast.ai)
- Einstein deepfake demo works
- Phoenix web UI (overcomplicated for now)
- **Extract just the voice/video generation parts**

### ✅ ChainMind Algorithms (Need Integration)
- RetentionScorer - predicts viewer drop-off
- TreeOfThoughts - generates video ideas
- PromptOptimizer - improves titles/descriptions
- **Port as simple Python functions, not full system**

### ✅ Vast Orchestrator (GPU Management)
- Handles Vast.ai GPU rentals
- **Use simplified version - just job submission**

## 🚫 What to IGNORE (For Now)

### Skip These Complexities
- ❌ Phoenix/Elixir web UI (use CLI)
- ❌ Microservices architecture (use functions)
- ❌ Docker/Kubernetes (run locally)
- ❌ Payment systems (not selling yet)
- ❌ Multi-user support (just you)
- ❌ Production deployment (local only)
- ❌ Perfect error handling (fail fast, fix quick)

## 🏗️ Simplified Architecture (What We're Actually Building)

### Option 1: Enhanced CLI Tool (Fastest)
```bash
# Everything through studioflow CLI
sf idea generate "python tutorial"        # Uses TreeOfThoughts
sf script write idea.json                 # Uses LLM + RetentionScorer
sf video create script.txt                # Uses Vast.ai + voice clone
sf youtube optimize video.mp4             # Uses PromptOptimizer
sf youtube upload video.mp4 --auto        # Full automation
```

### Option 2: Simple Python Script (Most Flexible)
```python
# daily_video.py - One script that does everything
from studioflow import YouTube, Transcribe
from chainmind import TreeOfThoughts, RetentionScorer
from creator_hub import VoiceClone, VideoGenerator

def create_daily_video(topic):
    # Generate ideas
    ideas = TreeOfThoughts().generate(topic)

    # Score and pick best
    best_idea = RetentionScorer().pick_best(ideas)

    # Generate script
    script = generate_script(best_idea)

    # Create video (local or Vast.ai)
    if expensive_video:
        video = VastGenerator().create(script)  # $0.50
    else:
        video = SimpleSlideshow().create(script)  # Free

    # Upload
    YouTube().upload(video)
```

### Option 3: Local Web Dashboard (If You Want UI)
```python
# Simple Flask/FastAPI, not Phoenix
from flask import Flask
app = Flask(__name__)

@app.route('/create-video', methods=['POST'])
def create_video():
    # Call the same functions as CLI
    return {"status": "processing", "job_id": 123}

# Run with: python app.py
# Access at: http://localhost:5000
```

## 🎯 Immediate Implementation Plan (Next 7 Days)

### Day 1-2: Core Integration Layer
```python
# studioflow/integrations.py
class CreatorStudio:
    """Simple integration of all our tools"""

    def __init__(self):
        self.studioflow = StudioFlow()  # Existing
        self.ideas = TreeOfThoughts()   # From ChainMind
        self.scorer = RetentionScorer() # From ChainMind
        self.voice = VoiceCloner()      # From Creator Hub
        self.vast = VastClient()        # Simplified

    def make_video(self, topic):
        """One function to rule them all"""
        idea = self.ideas.generate(topic)
        script = self.write_script(idea)
        video = self.create_video(script)
        self.upload(video)
```

### Day 3-4: Port Critical Algorithms
```python
# Port ONLY these from ChainMind:
1. retention_scorer.py -> studioflow/ai/retention.py
2. tree_of_thoughts.py -> studioflow/ai/ideas.py
3. prompt_optimizer.py -> studioflow/ai/optimizer.py

# Simplify them:
- Remove plugin architecture
- Remove abstract base classes
- Just make them functions that work
```

### Day 5-6: Voice & Video Generation
```python
# Extract from Creator Hub:
1. Voice cloning (already works)
2. Simple video generation
3. Vast.ai job submission

# Simplify to:
def clone_voice(sample_audio):
    # Returns voice model

def generate_video(script, voice_model):
    # Returns video file
```

### Day 7: First Full Test
```bash
# Create a real video for your channel
sf studio create "How to automate YouTube with AI"
# Should do everything automatically
```

## 🔧 Technical Simplifications

### Use Simple Data Passing (Not Events)
```python
# Instead of complex event bus:
# BAD: publish_event("script.ready", data)

# GOOD: Just return values
script = generate_script(topic)
video = create_video(script)
```

### Use Files for State (Not Databases)
```python
# Simple JSON files for now
project_dir = Path("~/.studioflow/projects/my_video/")
(project_dir / "idea.json").write_text(json.dumps(idea))
(project_dir / "script.txt").write_text(script)
(project_dir / "metadata.json").write_text(json.dumps(metadata))
```

### Use Subprocess for Integration (Not APIs)
```python
# Call existing tools directly
subprocess.run(["sf", "media", "transcribe", "audio.mp3"])
subprocess.run(["python", "chainmind/generate_idea.py", topic])
```

## 📝 What Needs Design Clarification

### 1. Vast.ai Integration Level
**Question**: How much GPU processing do we actually need?
- Option A: Always use Vast.ai ($0.50/video but slow)
- Option B: Local for simple, Vast for complex
- Option C: Batch overnight on Vast
**Recommendation**: Start with Option B

### 2. Voice Cloning Usage
**Question**: When to use voice cloning?
- Option A: Clone your voice once, use always
- Option B: Different voices for different content
- Option C: Celebrity voices for viral content
**Recommendation**: Option A for consistency

### 3. Automation Level
**Question**: How automated should it be?
- Option A: Fully auto (risky but scalable)
- Option B: Generate drafts, human review
- Option C: Human picks topic, AI does rest
**Recommendation**: Start with C, move to B

### 4. Quality vs Quantity
**Question**: Better to make 1 great or 10 good videos?
- Current capability: 10 good videos/day
- Time for great: 2-3 hours human work
**Recommendation**: 1 great daily, 9 auto experiments

## 🚀 Quick Start Commands (Make These Work First)

```bash
# These should work by Day 7:

# 1. Generate video idea
sf idea "python programming"
# Output: idea.json with 10 concepts

# 2. Write optimized script
sf script idea.json
# Output: script.txt with retention scoring

# 3. Create video
sf video create script.txt --voice "my_voice"
# Output: video.mp4

# 4. Optimize for YouTube
sf youtube optimize video.mp4
# Output: title.txt, description.txt, tags.txt, thumbnail.jpg

# 5. Upload
sf youtube upload video.mp4 --metadata output/
# Output: YouTube URL

# 6. One command for everything
sf studio daily "Python Tutorial"
# Does all above automatically
```

## 🎯 Success Metrics (By Oct 12)

### Must Have (Week 1)
- [ ] Generate 10 video ideas from topic
- [ ] Score scripts for retention
- [ ] Create simple videos locally
- [ ] Auto-upload to YouTube

### Should Have (Week 2)
- [ ] Voice cloning integrated
- [ ] Vast.ai for complex videos
- [ ] Thumbnail A/B testing
- [ ] Basic analytics tracking

### Nice to Have (Week 3)
- [ ] Web dashboard
- [ ] Batch processing
- [ ] Multi-channel support
- [ ] Cost optimization

## 🚨 Common Pitfalls to Avoid

### Don't Over-Engineer
```python
# BAD: AbstractFactoryStrategyPattern
class AbstractVideoGeneratorFactory(ABC):
    @abstractmethod
    def create_generator(self) -> VideoGenerator:
        pass

# GOOD: Just a function
def create_video(script):
    return generate_video_with_ffmpeg(script)
```

### Don't Premature Optimize
```python
# BAD: Caching everything
@cache
@memoize
@redis_cache
def generate_idea(topic):
    # Over-optimized

# GOOD: Just work first
def generate_idea(topic):
    return call_llm(topic)  # Optimize later if slow
```

### Don't Abstract Too Early
```python
# BAD: Generic everything
class MediaProcessor(Protocol):
    def process(self, input: Any) -> Any:
        pass

# GOOD: Specific and clear
def process_youtube_video(video_path: Path) -> Path:
    # Add intro, outro, optimize
    return processed_path
```

## 💡 Key Decisions Needed From You

1. **Primary video type?** (Tutorial/Entertainment/News)
2. **Your voice or AI voices?**
3. **How much daily time to review/approve?**
4. **Local GPU available or always use Vast?**
5. **YouTube channel already exists?**

## 🔥 The ONE Thing That Matters

**By October 12th**: You must be able to type one command and get a YouTube video published automatically that gets >50% retention.

Everything else is nice-to-have.

## 📂 Recommended File Structure

```
/mnt/projects/creator-studio/    # New unified home
├── studioflow/                  # Keep existing
│   └── integrations/           # Add new integrations here
├── algorithms/                  # Ported from ChainMind
│   ├── retention_scorer.py
│   ├── idea_generator.py
│   └── optimizer.py
├── generators/                  # From Creator Hub
│   ├── voice_clone.py
│   ├── video_simple.py
│   └── vast_client.py
├── daily_video.py              # Main automation script
├── config.yaml                 # All settings in one place
└── projects/                   # Working directory
    └── YYYY-MM-DD-video-name/
        ├── idea.json
        ├── script.txt
        ├── video.mp4
        └── metadata.json
```

## 🎬 Next Actions (Do These Now)

1. **Create the unified directory**
   ```bash
   mkdir -p /mnt/projects/creator-studio
   cd /mnt/projects/creator-studio
   ```

2. **Copy working code**
   ```bash
   cp -r /mnt/projects/studioflow/* ./studioflow/
   mkdir algorithms generators
   ```

3. **Write the simplest integration**
   ```python
   # daily_video.py
   import sys
   from pathlib import Path

   def make_video(topic):
       print(f"Making video about: {topic}")
       # Add features one by one

   if __name__ == "__main__":
       make_video(sys.argv[1])
   ```

4. **Test with real video**
   ```bash
   python daily_video.py "Python Tutorial"
   ```

## Remember: Ship Something Today

Don't wait for perfect. Make it work, then make it better.

The goal is to have a tool you USE, not a perfect system you never finish.