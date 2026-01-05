# Audio Markers: Advanced Features

## Overview

This document covers advanced audio marker features for world-class video editing automation:
1. **Advanced Score System** - 4-level shot assessment with automatic demotion
2. **Emotion & Energy Markers** - Tone matching, rhythm creation, music sync
3. **Platform Auto-Export** - Automatic platform-specific optimization
4. **Powerful Marker Combinations** - Complex workflows with multiple markers

---

## 1. Most Powerful Marker Combinations

### 1.1 Complete Production Workflow

**Full Sequence with All Marker Types:**
```
slate sequence start done
slate scene intro done
slate shot front emotion energetic energy high done
slate step one quote reveal done
[content]
slate apply best done
slate shot overhead action done
[content]
slate apply good done
slate shot front step two done
[content]
slate apply good done
slate scene end done
slate sequence end done
```

**What This Enables:**
- Complete sequence/scene/shot hierarchy
- Score assessment at each level
- Emotion/energy tracking
- Quote identification
- Retroactive score marking
- Action-based cutting points

---

### 1.2 Multicam Automatic Switching

**Multi-Camera Workflow:**
```
slate scene demo done
slate shot front step one done          # CAMA (FX30)
[content]
slate shot overhead step two done       # CAMB (ZV-E10) - auto-switch
[content]
slate shot front step three done        # CAMA - auto-switch back
[content]
slate apply best done                   # Mark previous as best
slate scene end done
```

**What This Enables:**
- Automatic camera switching based on shot names
- Chronological shot progression
- Score marking for best takes
- Seamless multicam assembly

---

### 1.3 Story Structure with Score

**Narrative Arc with Score Assessment:**
```
slate sequence start done
slate scene intro done
slate shot front beat hook emotion energetic done
[hook content]
slate apply good done              # Mark previous as good
slate shot medium beat main step one done
[main content part 1]
slate apply good done                   # Mark previous as good
slate shot close beat main step two done
[main content part 2]
slate apply best done                   # Mark previous as best
slate shot wide beat transition done
[transition]
slate apply good done                   # Mark previous as good
slate shot front beat outro cta subscribe done
[outro]
slate apply good done              # Mark previous as good
slate scene end done
slate sequence end done
```

**What This Enables:**
- Story beat mapping (hook → main → transition → outro)
- Score assessment at each beat
- Shot progression (wide → medium → close)
- Call-to-action placement
- Automatic story structure assembly

---

### 1.4 Tutorial with Score Assessment

**Tutorial Workflow:**
```
slate scene setup done
slate shot screen step one done
[setup step 1]
slate apply good done               # Mark previous as good
slate shot front step two done
[explanation]
slate apply good done                    # Mark previous as good
slate apply best done               # Upgrade previous to best
slate shot screen step three done
[final step]
slate apply good done               # Mark previous as good
slate scene end done
```

**What This Enables:**
- Score-based assessment for each step
- Step-by-step tutorial structure
- Score upgrades (retroactive)
- Screen + talking head coordination

---

### 1.5 Quote-Driven Assembly

**Quote-Focused Workflow:**
```
slate scene interview done
slate shot front quote emotion serious energy medium done
[important quote 1]
slate apply best done              # Mark previous as best
slate shot close quote emotion energetic energy high done
[important quote 2]
slate apply good done              # Mark previous as good
slate shot medium done
[filler content - not great]
slate apply fair done              # Mark previous as fair (backup)
slate shot medium retake done
[better filler content]
slate apply good done              # Mark previous as good
slate shot front quote emotion serious energy low done
[important quote 3 - contemplative]
slate apply best done              # Mark previous as best (demotes previous best)
slate scene end done
```

**What This Enables:**
- Prioritize quotes in rough cut
- Filter out non-quote content
- Emotion tracking for quotes
- Score-based quote selection

---

## 2. Advanced Score System

### 2.1 Score Scale

**Four-Level Score Scale:**
```
slate apply skip done      # Level 0 - Remove/skip
slate apply fair done      # Level 1 - Usable but not great (backup)
slate apply good done      # Level 2 - Good quality (solid content)
slate apply best done      # Level 3 - Top tier (only one)
```

**Implementation:**
```python
SCORE_SCALE = {
    "skip": 0,      # Remove/skip
    "fair": 1,      # Usable but not great (backup material)
    "good": 2,      # Good quality (solid content)
    "best": 3       # Top tier (only one)
}

# Score levels are recognized when used after "apply"
# No keyword needed - level word alone works
# Examples:
#   slate apply fair done             → score: "fair"
#   slate apply good done             → score: "good"
#   slate apply best done             → score: "best"
#   slate apply good hook done        → score: "good" + hook: True
```

---

### 2.2 Score Recognition Logic

**Parser Implementation:**
```python
# Known score levels
SCORE_LEVELS = ["skip", "fair", "good", "best"]

def process_retroactive_actions(actions):
    """Process actions collected after 'apply' keyword"""
    for action in actions:
        if action in SCORE_LEVELS:
            # This is a score level
            segment["score"] = action
            segment["score_level"] = SCORE_SCALE[action]
        elif action == "hook":
            segment["hook"] = True
        elif action == "quote":
            segment["quote"] = True
        # ... process other actions
```

**Usage Examples:**
```
slate apply fair done                   # Score only (backup)
slate apply good done                    # Score only (solid)
slate apply best hook done               # Score + hook
slate apply good quote done              # Score + quote
slate apply skip done                    # Remove/skip
```

---

### 2.3 Score Promotion/Demotion

**Retroactive Score Changes:**
```
slate shot front step one done
[content]
slate apply good done                   # Mark previous as good
slate apply best done                   # Upgrade previous to best (demotes previous best)
```

**Automatic Demotion Logic:**
- When `best` is applied, previous `best` is demoted to `good`
- Score can only increase (upgrade) or decrease (downgrade)
- Only one segment can have `best` score at a time

**Implementation:**
```python
def apply_score_promotion(segments, marker):
    """Apply score with automatic demotion"""
    action_type = marker.parsed_commands.retroactive_actions
    
    for action in action_type:
        if action in SCORE_LEVELS:
            previous_segment = find_segment_before_marker(segments, marker)
            
            # Apply score to previous segment
            previous_segment["score"] = action
            previous_segment["score_level"] = SCORE_SCALE[action]
            
            # If "best", demote previous "best"
            if action == "best":
                for seg in segments:
                    if seg != previous_segment and seg.get("score") == "best":
                        seg["score"] = "good"  # Demote to next level
                        seg["score_level"] = SCORE_SCALE["good"]
```

**Score Decision Guide:**
- **skip**: Mistakes, dead air, filler - definitely remove
- **fair**: Usable but not great - backup material, might need later
- **good**: Solid content - include in rough cut
- **best**: Top tier - highest priority, only one per sequence

---

### 2.4 Score-Based Filtering

**Rough Cut Assembly Rules:**
```python
def filter_by_score(segments, min_score=2):
    """Filter segments by score threshold"""
    return [
        s for s in segments 
        if s.get("score_level", 0) >= min_score
        and not s.get("remove", False)
    ]

def select_best_takes(segments):
    """Select only 'best' score segments"""
    return [s for s in segments if s.get("score") == "best"]

def score_based_ordering(segments):
    """Order segments by score (best first)"""
    return sorted(
        segments,
        key=lambda s: s.get("score_level", 0),
        reverse=True
    )
```

---

## 2.5 Emotion & Energy Markers

### 2.5.1 Emotion Markers

**Purpose:** Capture the emotional tone of content for matching, pacing, and story arc creation.

**Usage:**
```
slate shot front emotion energetic done
slate shot close emotion serious done
slate shot medium emotion contemplative done
slate shot wide emotion happy done
```

**Common Emotion Types:**
- `energetic` - High energy, fast-paced, exciting
- `serious` - Dramatic, important, weighty
- `contemplative` - Thoughtful, reflective, calm
- `happy` - Positive, upbeat, cheerful
- `sad` - Melancholic, emotional, somber
- `neutral` - Balanced, informative, straightforward

**How Emotion Markers Are Used:**

1. **Matching Segments by Tone**
   ```python
   def match_emotion_transitions(segments):
       """Group segments with similar emotion for smooth transitions"""
       # Group by emotion
       emotion_groups = {}
       for seg in segments:
           emotion = seg.get("emotion", "neutral")
           if emotion not in emotion_groups:
               emotion_groups[emotion] = []
           emotion_groups[emotion].append(seg)
       
       # Create transitions between emotion groups
       # Avoid jarring jumps (serious → energetic needs transition)
   ```

2. **Story Arc Creation**
   ```python
   def build_emotional_arc(segments):
       """Build emotional progression through story"""
       # Example arc: contemplative → serious → energetic → contemplative
       # Match emotion to story beats:
       # - Hook: energetic (grab attention)
       # - Main: serious (important content)
       # - Transition: contemplative (breathing room)
       # - Outro: energetic (call to action)
   ```

3. **Music Selection**
   ```python
   def match_music_to_emotion(emotion):
       """Match music tracks to emotion"""
       music_map = {
           "energetic": "upbeat_tracks",
           "serious": "dramatic_tracks",
           "contemplative": "ambient_tracks",
           "happy": "positive_tracks"
       }
       return music_map.get(emotion, "neutral_tracks")
   ```

4. **Filtering by Tone**
   ```python
   def filter_by_emotion(segments, target_emotion):
       """Extract segments with specific emotion"""
       return [s for s in segments if s.get("emotion") == target_emotion]
   
   # Example: Extract all "energetic" segments for high-energy cut
   energetic_segments = filter_by_emotion(segments, "energetic")
   ```

5. **Transition Selection**
   ```python
   def select_transition(prev_emotion, next_emotion):
       """Select transition based on emotion change"""
       if prev_emotion == next_emotion:
           return "cut"  # Same emotion = quick cut
       elif (prev_emotion == "serious" and next_emotion == "energetic"):
           return "fade"  # Dramatic change = fade
       elif (prev_emotion == "contemplative" and next_emotion == "serious"):
           return "dissolve"  # Smooth transition
       else:
           return "cut"  # Default
   ```

---

### 2.5.2 Energy Markers

**Purpose:** Capture the energy/pacing level for rhythm creation, tempo matching, and speed adjustment.

**Usage:**
```
slate shot front energy high done
slate shot medium energy medium done
slate shot close energy low done
```

**Energy Levels:**
- `high` - Fast-paced, dynamic, intense
- `medium` - Balanced, moderate pace
- `low` - Slow, contemplative, relaxed

**How Energy Markers Are Used:**

1. **Creating Rhythm**
   ```python
   def build_energy_arc(segments):
       """Build energy progression for rhythm"""
       # Example arc: high → medium → low → high
       # Creates natural rhythm and pacing
       # High energy = fast cuts, low energy = longer shots
   ```

2. **Speed Adjustment**
   ```python
   def adjust_speed_by_energy(segment):
       """Adjust playback speed based on energy"""
       energy = segment.get("energy", "medium")
       speed_map = {
           "high": 1.1,    # Slightly speed up (10%)
           "medium": 1.0,  # Normal speed
           "low": 0.95     # Slightly slow down (5%)
       }
       return speed_map.get(energy, 1.0)
   ```

3. **Music Sync**
   ```python
   def match_music_tempo(energy):
       """Match music tempo to energy level"""
       tempo_map = {
           "high": "fast_tempo_tracks",    # 120+ BPM
           "medium": "moderate_tempo_tracks",  # 90-120 BPM
           "low": "slow_tempo_tracks"      # <90 BPM
       }
       return tempo_map.get(energy, "moderate_tempo_tracks")
   ```

4. **Edit Point Selection**
   ```python
   def select_edit_points(segments):
       """Select edit points based on energy"""
       for seg in segments:
           energy = seg.get("energy", "medium")
           if energy == "high":
               # Quick cuts, fast pacing
               seg["cut_style"] = "fast"
               seg["max_duration"] = 5.0  # Shorter segments
           elif energy == "low":
               # Longer shots, slower pacing
               seg["cut_style"] = "slow"
               seg["max_duration"] = 15.0  # Longer segments
           else:
               # Balanced pacing
               seg["cut_style"] = "normal"
               seg["max_duration"] = 10.0
   ```

5. **Platform Optimization**
   ```python
   def optimize_for_platform(segments, platform):
       """Optimize energy levels for platform"""
       if platform == "shorts" or platform == "tiktok":
           # Prefer high-energy segments
           return [s for s in segments if s.get("energy") == "high"]
       elif platform == "youtube":
           # Mix energy levels for variety
           return segments  # Include all
   ```

---

### 2.5.3 Combined Emotion & Energy Usage

**Example Workflow:**
```
slate shot front emotion energetic energy high done
[high-energy, energetic content]
slate apply best done

slate shot medium emotion serious energy medium done
[serious, medium-energy content]
slate apply good done

slate shot close emotion contemplative energy low done
[contemplative, low-energy content]
slate apply fair done
```

**Rough Cut Engine Processing:**
```python
def process_emotion_energy(segments):
    """Process segments with emotion and energy markers"""
    
    # 1. Group by emotion/energy similarity
    similar_segments = group_by_emotion_energy(segments)
    
    # 2. Create energy arc: high → medium → low
    energy_arc = build_energy_arc(segments)
    
    # 3. Match music to energy levels
    music_tracks = []
    for seg in segments:
        music = match_music_tempo(seg.get("energy"))
        music_tracks.append(music)
    
    # 4. Adjust pacing based on energy
    for seg in segments:
        seg["speed"] = adjust_speed_by_energy(seg)
    
    # 5. Select transitions based on emotion changes
    transitions = []
    for i in range(len(segments) - 1):
        prev_emotion = segments[i].get("emotion")
        next_emotion = segments[i + 1].get("emotion")
        transition = select_transition(prev_emotion, next_emotion)
        transitions.append(transition)
    
    return {
        "segments": segments,
        "energy_arc": energy_arc,
        "music_tracks": music_tracks,
        "transitions": transitions
    }
```

**Benefits:**
- **Smooth Transitions**: Match emotion/energy for natural flow
- **Rhythm Creation**: Build energy arcs for pacing
- **Music Sync**: Auto-match music to content tone
- **Platform Optimization**: Filter by energy for platform-specific cuts
- **Story Arc**: Build emotional progression through narrative

---

## 3. Platform Auto-Export Capabilities

### 3.1 Platform-Specific Markers

**Platform Identification:**
```
slate platform youtube done            # YouTube long-form
slate platform shorts done             # YouTube Shorts
slate platform tiktok done             # TikTok
slate platform instagram done          # Instagram Reel
slate platform twitter done            # Twitter/X
```

**Vertical/Horizontal Markers:**
```
slate vertical done                    # Good for vertical/shorts
slate horizontal done                   # Good for landscape/long-form
slate square done                       # Good for Instagram square
```

**Thumbnail Markers:**
```
slate thumbnail done                   # Thumbnail-worthy moment
slate thumbnail <type> done            # thumbnail hook, thumbnail main, etc.
```

---

### 3.2 Hook Extraction

**Hook Identification:**
```
slate hook done                        # General hook
slate hook <type> done                 # hook coh, hook ch, hook psh, etc.
slate beat hook done                   # Story beat hook
slate platform shorts hook done        # Shorts-specific hook
```

**Auto-Extraction Logic:**
```python
def extract_hooks(segments, platform="youtube"):
    """Extract hook segments for platform"""
    hooks = []
    
    for segment in segments:
        # Check for hook markers
        if segment.get("hook") or segment.get("beat") == "hook":
            # Platform-specific duration limits
            duration_limits = {
                "youtube": 15,      # First 15 seconds
                "shorts": 3,        # First 3 seconds
                "tiktok": 3,
                "instagram": 3
            }
            
            max_duration = duration_limits.get(platform, 15)
            if segment["duration"] <= max_duration:
                hooks.append(segment)
    
    return hooks
```

---

### 3.3 Automatic Platform Versions

**Multi-Platform Export Workflow:**
```python
def create_platform_versions(rough_cut, platforms=["youtube", "shorts", "tiktok"]):
    """Create platform-specific versions automatically"""
    
    versions = {}
    
    for platform in platforms:
        # Extract platform-specific segments
        segments = filter_platform_segments(rough_cut.segments, platform)
        
        # Apply platform-specific rules
        if platform == "youtube":
            version = create_youtube_version(segments)
        elif platform == "shorts":
            version = create_shorts_version(segments)
        elif platform == "tiktok":
            version = create_tiktok_version(segments)
        
        versions[platform] = version
    
    return versions

def filter_platform_segments(segments, platform):
    """Filter segments by platform markers"""
    filtered = []
    
    for segment in segments:
        # Check platform markers
        if segment.get("platform") == platform:
            filtered.append(segment)
        elif platform == "shorts" and segment.get("vertical"):
            filtered.append(segment)
        elif platform == "youtube" and segment.get("horizontal"):
            filtered.append(segment)
        # Default: include if no platform specified
        elif not segment.get("platform"):
            filtered.append(segment)
    
    return filtered
```

---

### 3.4 Thumbnail Generation

**Thumbnail Extraction:**
```python
def extract_thumbnail_frames(segments):
    """Extract thumbnail-worthy frames from segments"""
    thumbnails = []
    
    for segment in segments:
        if segment.get("thumbnail"):
            # Extract frame at segment start or best moment
            frame_time = segment.get("start", 0)
            
            # If thumbnail type specified, use that
            thumbnail_type = segment.get("thumbnail_type", "general")
            
            thumbnails.append({
                "segment": segment,
                "time": frame_time,
                "type": thumbnail_type,
                "file": extract_frame(segment["file"], frame_time)
            })
    
    return thumbnails
```

---

### 3.5 Platform-Specific Optimization

**YouTube Long-Form:**
- Extract hook (first 15 seconds)
- Full story structure (hook → intro → main → outro)
- Chapter markers
- Thumbnail extraction
- 16:9 aspect ratio
- Target duration: 10-30 minutes

**YouTube Shorts:**
- Extract hook (first 3 seconds)
- Vertical format (9:16)
- Fast-paced editing
- Target duration: 15-60 seconds
- Auto-create from long-form or standalone

**TikTok:**
- Vertical format (9:16)
- Hook extraction
- Fast cuts
- Target duration: 15-60 seconds
- Music sync

**Instagram Reels:**
- Vertical format (9:16)
- Square option (1:1)
- Hook extraction
- Target duration: 15-90 seconds

---

### 3.6 Auto-Export Pipeline

**Complete Export Workflow:**
```python
def auto_export_pipeline(rough_cut, export_config):
    """Automatically create all platform versions"""
    
    results = {}
    
    # 1. Extract platform-specific segments
    platform_segments = {}
    for platform in export_config["platforms"]:
        platform_segments[platform] = filter_platform_segments(
            rough_cut.segments, 
            platform
        )
    
    # 2. Create platform-specific rough cuts
    platform_cuts = {}
    for platform, segments in platform_segments.items():
        platform_cuts[platform] = create_platform_cut(
            segments,
            platform,
            export_config
        )
    
    # 3. Extract thumbnails
    thumbnails = extract_thumbnail_frames(rough_cut.segments)
    
    # 4. Export all versions
    exports = {}
    for platform, cut in platform_cuts.items():
        exports[platform] = export_platform_version(
            cut,
            platform,
            export_config["output_dir"] / platform
        )
    
    # 5. Generate thumbnails
    thumbnail_files = []
    for thumb in thumbnails:
        thumbnail_files.append(export_thumbnail(thumb, export_config["output_dir"]))
    
    return {
        "exports": exports,
        "thumbnails": thumbnail_files,
        "platform_cuts": platform_cuts
    }
```

---

## 4. Implementation Examples

### 4.1 Complete Workflow Example

**Recording Script:**
```
slate sequence start done
slate scene intro done
slate shot front emotion energetic energy high platform youtube hook done
[hook content - first 15 seconds]
slate apply best done                   # Mark previous as best
slate shot medium step one emotion serious energy medium done
[main content step 1]
slate apply good done                   # Mark previous as good
slate shot medium step one retake done
[better take of step 1]
slate apply best done                   # Upgrade previous to best (demotes previous best)
slate shot close quote emotion serious energy low done
[important quote - contemplative]
slate apply good done                   # Mark previous as good
slate shot wide beat transition emotion contemplative energy low done
[transition - breathing room]
slate apply fair done                   # Mark previous as fair (backup)
slate shot front beat outro emotion energetic energy high cta subscribe done
[outro - high energy call to action]
slate apply best done                   # Mark previous as best (demotes previous best)
slate scene end done
slate sequence end done
```

**Automated Output:**
1. **YouTube Long-Form**: Full sequence with hook, main, quote, transition, outro
2. **YouTube Shorts**: Hook extraction (first 3 seconds) + quote highlight
3. **Thumbnails**: Extract from hook and quote segments
4. **Score Filtering**: Only good/best segments in final cut (fair as backup)
5. **Story Structure**: Automatic beat mapping (hook → main → transition → outro)

---

### 4.2 Score Assessment Example

**Score-Based Workflow:**
```
slate shot front step one done
[content]
slate apply good done                   # Mark previous as good
slate apply best done              # Upgrade previous to best
[content]
slate apply best done                   # Upgrade to best (demotes previous best)
```

**Scoring:**
- Step 1: Initially `good` (score_level: 2)
- After `apply best`: Upgraded to `best` (score_level: 3)
- Previous `best` (if any) demoted to `good`

**Decision Logic:**
- If score is `best` → Include in rough cut (highest priority)
- If score is `good` → Include in rough cut (solid content)
- If score is `fair` → Include if needed (backup material)
- If score is `skip` → Exclude from rough cut

---

### 4.3 Platform Export Example

**Input:**
```
slate platform youtube hook done
[YouTube hook]
slate platform shorts hook done
[Shorts hook]
slate platform youtube main done
[Main content]
slate platform shorts main done
[Shorts main]
```

**Output:**
- **YouTube Version**: Hook + Main (long-form)
- **Shorts Version**: Hook + Main (vertical, 15-60 seconds)
- **Thumbnails**: From hook segments
- **Automatic**: No manual editing needed

---

## 5. Summary

### Key Features

1. **Powerful Marker Combinations**
   - Complete sequence/scene/shot hierarchy
   - Score + emotion + energy + story beats
   - Retroactive score marking
   - Multicam automatic switching

2. **Advanced Score System**
   - Four-level score scale (skip → fair → good → best)
   - Score levels used directly after "apply" (no keyword needed)
   - Score promotion/demotion
   - Score-based filtering and ordering
   - Emotion markers for tone matching and story arcs
   - Energy markers for rhythm creation and pacing

3. **Platform Auto-Export**
   - Platform-specific markers
   - Automatic version creation
   - Hook extraction
   - Thumbnail generation
   - Platform-specific optimization

### Benefits

- **Time Savings**: 80-90% reduction in editing time
- **Consistency**: Automated quality across all platforms
- **Scalability**: Create multiple platform versions automatically
- **Intelligence**: Story structure and score-based assembly

---

## Score System Quick Reference

### Score Levels (used after "apply")
- `slate apply skip done`      → Score: 0 (remove/skip)
- `slate apply fair done`      → Score: 1 (usable backup)
- `slate apply good done`      → Score: 2 (good quality)
- `slate apply best done`      → Score: 3 (top tier)

### Combining with Other Commands
- `slate apply good hook done`         → Score + hook
- `slate apply best quote done`        → Score + quote
- `slate apply fair done`              → Backup material
- `slate apply skip done`              → Remove/skip (same as remove)

### Score Recognition
- Score levels are recognized by checking against known list: `["skip", "fair", "good", "best"]`
- No "score" keyword needed when used after "apply"
- Can be combined with other retroactive actions

### Emotion & Energy Markers
- `slate shot front emotion energetic done` → Sets emotional tone
- `slate shot front energy high done` → Sets energy/pacing level
- Used for: tone matching, rhythm creation, music sync, transition selection
- Common emotions: energetic, serious, contemplative, happy, sad, neutral
- Energy levels: high, medium, low

---

## Next Steps

1. Implement score scale parser
2. Add score recognition in retroactive actions
3. Build platform export pipeline
4. Create thumbnail extraction
5. Test with real footage

