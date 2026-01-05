# Audio Markers: Best Practices Guide

## Overview

This guide provides a step-by-step progression for mastering the audio marker system, from simple basics to advanced workflows. Follow this natural learning path to gain familiarity, accelerate your learning, and master the system.

**Note:** This guide focuses on learning progression. For complete reference, see [AUDIO_MARKERS_USER_GUIDE.md](AUDIO_MARKERS_USER_GUIDE.md) and [AUDIO_MARKERS_REFERENCE.md](AUDIO_MARKERS_REFERENCE.md).

---

## Table of Contents

1. [Getting Started (Simple)](#getting-started-simple)
2. [Building Skills (Intermediate)](#building-skills-intermediate)
3. [Mastering the System (Advanced)](#mastering-the-system-advanced)
4. [Quick Reference](#quick-reference)

---

## Getting Started (Simple)

### Goal: Learn the Basics

**Focus:** Understand the fundamental marker structure and create your first segmented video.

### Step 1: Understand the Basic Structure

Every marker follows this pattern:
```
slate [commands] done
```

**What happens:**
- Say "slate" → System starts listening
- Say your commands → System records them
- Say "done" → System stops listening
- Everything after "done" is your content

### Step 2: Your First Marker

**Practice Script:**
```
slate done
[Speak your content here]
slate done
[Speak more content here]
slate done
```

**Result:** Two separate segments created automatically.

### Step 3: Add Organization with "take" and Scene Numbers

**Two Different Concepts:**

1. **"take"** = Multiple attempts at the same scene (take 1, take 2, take 3)
2. **Scene Numbers** = Position in final sequence using decimal numbers (scene 1, scene 1.5, scene 2)

**Practice Script - Multiple Takes:**
```
slate take one done
[First attempt at same scene]
slate apply good done

slate take two done
[Second attempt - better]
slate apply best done

slate take three done
[Third attempt - mistake]
slate apply skip done
```

**Practice Script - Scene Numbers:**
```
slate scene one intro done
[First scene in sequence]
slate apply good done

slate scene two main done
[Second scene]
slate apply good done

# Later: Insert scene between 1 and 2
slate scene one point five transition done
[Scene 1.5 - inserted between scene 1 and 2]
slate apply good done
```

**Why use "take"?**
- Organizes multiple attempts at the same scene
- Helps you compare different versions
- Standard video production terminology
- System automatically tracks which take was selected

**Why use Scene Numbers?**
- Natural ordering (scene 1, scene 2, scene 3)
- Easy insertion with decimals (scene 1.5, scene 1.6)
- Industry standard (scene numbering)
- No separate "order" keyword needed
- Can add optional names (scene one intro, scene one point five middle)

### Step 4: Add Steps for Tutorials

**Practice Script:**
```
slate step one done
[Step 1: Setup instructions]
slate step two done
[Step 2: Main process]
slate step three done
[Step 3: Final steps]
```

**Result:** Three tutorial segments in sequence.

**When to use "step":**
- Tutorial videos
- Step-by-step instructions
- Sequential processes

### Step 5: Mark Important Moments

**Practice Script:**
```
slate order one done
[Regular content]
slate mark done
[Important moment - mark this]
slate order two done
[More regular content]
```

**Result:** The "mark" segment is highlighted for easy finding.

**When to use "mark":**
- Important quotes
- Key moments
- Highlights you want to find later

---

## Building Skills (Intermediate)

### Goal: Use Scoring and Retroactive Actions

**Focus:** Learn to assess quality and mark content for removal.

### Step 6: Score Your Content

**The 4-Level Score System:**
- `skip` (Level 0) - Remove/skip (mistakes, dead air)
- `fair` (Level 1) - Usable backup (not great, but might need)
- `good` (Level 2) - Solid content (include in rough cut)
- `best` (Level 3) - Top tier (only one per sequence)

**Practice Script:**
```
slate take one done
[First take - pretty good]
slate apply good done

slate take two done
[Second take - even better!]
slate apply best done

slate take three done
[Third take - made a mistake]
slate apply skip done
```

**What happens:**
- First segment: Marked as "good"
- Second segment: Marked as "best" (automatically demotes previous "best" to "good")
- Third segment: Marked for removal

**Key Concept:** "apply" applies actions to the **previous** segment.

### Step 7: Mark Content for Removal

**Practice Script:**
```
slate take one done
[Good content - keep this]
slate apply good done

slate take two done
[Oops, made a mistake, need to redo]
slate apply skip done

slate take three done
[Better take - this is the one]
slate apply best done
```

**Result:**
- Segment 1: Good (included)
- Segment 2: Skipped (removed from rough cut)
- Segment 3: Best (included, demotes segment 1 to "good")

### Step 8: Use "fair" for Backup Material

**Practice Script:**
```
slate take one done
[First take - usable but not great]
slate apply fair done

slate take two done
[Second take - much better]
slate apply good done

slate take three done
[Third take - perfect!]
slate apply best done
```

**When to use "fair":**
- Backup material you might need later
- Not great, but usable if needed
- Alternative takes you want to keep as options

### Step 9: Combine Scoring with Other Actions

**Practice Script:**
```
slate order one done
[Important quote]
slate apply good quote done

slate order two done
[Hook content - first 15 seconds]
slate apply best hook done

slate order three done
[Regular content]
slate apply good done
```

**Result:**
- Segment 1: Good + marked as quote
- Segment 2: Best + marked as hook
- Segment 3: Good

**Available Actions:**
- `quote` - Important quote
- `hook` - Hook content (first 15 seconds)
- `remove` / `skip` - Remove content

---

## Mastering the System (Advanced)

### Goal: Use Emotion, Energy, and Full Workflow

**Focus:** Create professional, automated rough cuts with intelligent editing.

### Step 10: Add Emotion Markers

**Common Emotions:**
- `energetic` - High energy, fast-paced, exciting
- `serious` - Dramatic, important, weighty
- `contemplative` - Thoughtful, reflective, calm
- `happy` - Positive, upbeat, cheerful
- `sad` - Melancholic, emotional, somber
- `neutral` - Balanced, informative, straightforward

**Practice Script:**
```
slate shot front emotion energetic done
[High-energy hook content]
slate apply best hook done

slate shot medium emotion serious done
[Important main content]
slate apply good done

slate shot close emotion contemplative done
[Thoughtful conclusion]
slate apply good done
```

**What This Enables:**
- System matches segments by emotion for smooth transitions
- Music automatically selected based on emotion
- Story arc creation based on emotional progression

### Step 11: Add Energy Markers

**Energy Levels:**
- `high` - Fast-paced, dynamic, intense
- `medium` - Balanced, moderate pace
- `low` - Slow, contemplative, relaxed

**Practice Script:**
```
slate shot front emotion energetic energy high done
[Fast-paced hook]
slate apply best hook done

slate shot medium emotion serious energy medium done
[Balanced main content]
slate apply good done

slate shot close emotion contemplative energy low done
[Slow, thoughtful conclusion]
slate apply good done
```

**What This Enables:**
- Automatic speed adjustment (high = slightly faster, low = slightly slower)
- Music tempo matching
- Rhythm creation for pacing

### Step 12: Complete Workflow Example

**Full Recording Script:**
```
slate sequence start done
slate scene intro done

slate shot front emotion energetic energy high hook done
[High-energy hook - first 15 seconds]
slate apply best done

slate shot medium emotion serious energy medium step one done
[Main content step 1]
slate apply good done

slate shot medium step one retake done
[Better take of step 1]
slate apply best done

slate shot close emotion serious energy low quote done
[Important quote - contemplative]
slate apply good done

slate shot wide emotion contemplative energy low done
[Transition - breathing room]
slate apply fair done

slate shot front emotion energetic energy high cta subscribe done
[Outro - high energy call to action]
slate apply best done

slate scene end done
slate sequence end done
```

**What This Creates:**
1. **Automatic Segmentation:** All content split into logical segments
2. **Score-Based Filtering:** Only good/best segments in rough cut (fair as backup)
3. **Emotion Matching:** Smooth transitions between similar emotions
4. **Energy Arc:** High → medium → low → high (natural rhythm)
5. **Music Selection:** Auto-matched to emotion and energy
6. **Story Structure:** Hook → main → quote → transition → outro

### Step 13: Advanced Scoring Workflow

**Multiple Takes with Scoring:**
```
slate shot front take one done
[Take 1 - not great]
slate apply fair done

slate shot front take two done
[Take 2 - better]
slate apply good done

slate shot front take three done
[Take 3 - perfect!]
slate apply best done

slate shot front take four done
[Take 4 - made mistake]
slate apply skip done
```

**Result:**
- System automatically selects "best" (Take 3)
- Keeps "good" (Take 2) as backup
- Removes "skip" (Take 4)
- Keeps "fair" (Take 1) as backup option

**Combining Take and Order:**
```
# Scene 1: Multiple takes, all go in position 1
slate scene intro take one order one done
[First take of intro scene]
slate apply good done

slate scene intro take two order one done
[Second take of intro scene - better]
slate apply best done

# Scene 3: Inserted between scenes 2 and 4
slate scene middle take one order three done
[Middle scene, goes in position 3]
slate apply good done

# Scene 1 again: Another take, still position 1
slate scene intro take three order one done
[Third take of intro scene]
slate apply good done
```

**Result:**
- All takes of scene 1 are in order 1 (position 1)
- System selects best take from order 1
- Scene 3 is inserted in position 3 (between scenes 2 and 4)

### Step 14: Retroactive Actions

**Key Concept:** "apply" always affects the **previous** segment.

**Practice:**
```
slate order one done
[Content segment]
slate apply good done          # Marks PREVIOUS segment (order one) as good

slate order two done
[Another content segment]
slate apply best done          # Marks PREVIOUS segment (order two) as best
                                # Automatically demotes previous "best" to "good"
```

**Why Retroactive?**
- You don't know quality until after you've spoken
- Natural workflow: speak → assess → mark
- No need to predict quality before recording

### Step 15: Combining Multiple Actions

**Practice Script:**
```
slate shot front emotion energetic energy high hook done
[High-energy hook]
slate apply best hook done     # Score + hook

slate shot medium quote done
[Important quote]
slate apply good quote done    # Score + quote

slate shot close done
[Mistake - need to remove]
slate apply skip done          # Remove
```

**Available Combinations:**
- `slate apply good hook done` - Good score + hook
- `slate apply best quote done` - Best score + quote
- `slate apply fair done` - Fair score only
- `slate apply skip done` - Remove/skip

---

## Quick Reference

### Basic Markers

| Marker | Purpose | Example |
|--------|---------|---------|
| `slate done` | Basic segment | `slate done` |
| `slate take one done` | Multiple attempts at same scene | `slate take one done` |
| `slate scene one done` | Scene number (position in sequence) | `slate scene one done` |
| `slate scene one point five done` | Insert scene between 1 and 2 | `slate scene one point five done` |
| `slate scene one intro done` | Scene number with name | `slate scene one intro done` |
| `slate scene one intro take one done` | Scene, take, and name | `slate scene one intro take one done` |
| `slate step one done` | Tutorial steps | `slate step one done` |
| `slate mark done` | Important moment | `slate mark done` |

### Scoring System

| Score | Level | When to Use |
|-------|-------|-------------|
| `skip` | 0 | Mistakes, dead air, remove |
| `fair` | 1 | Backup material, usable but not great |
| `good` | 2 | Solid content, include in rough cut |
| `best` | 3 | Top tier, only one per sequence |

**Usage:** `slate apply [score] done`

### Retroactive Actions

| Action | Purpose | Example |
|--------|---------|---------|
| `apply good done` | Mark previous as good | `slate apply good done` |
| `apply best done` | Mark previous as best | `slate apply best done` |
| `apply skip done` | Remove previous | `slate apply skip done` |
| `apply good hook done` | Good + hook | `slate apply good hook done` |
| `apply best quote done` | Best + quote | `slate apply best quote done` |

### Emotion Markers

| Emotion | When to Use |
|---------|-------------|
| `emotion energetic` | High energy, exciting content |
| `emotion serious` | Important, dramatic content |
| `emotion contemplative` | Thoughtful, reflective content |
| `emotion happy` | Positive, upbeat content |
| `emotion neutral` | Balanced, informative content |

**Usage:** `slate shot front emotion energetic done`

### Energy Markers

| Energy | When to Use |
|--------|-------------|
| `energy high` | Fast-paced, dynamic content |
| `energy medium` | Balanced, moderate pace |
| `energy low` | Slow, contemplative content |

**Usage:** `slate shot front energy high done`

### Combined Example

```
slate shot front emotion energetic energy high hook done
[Content]
slate apply best done
```

---

## Learning Progression Checklist

### Simple (Episodes 1-3)
- [ ] Understand basic marker structure (`slate ... done`)
- [ ] Use `take` for multiple attempts at same scene
- [ ] Use scene numbers for sequence position (scene one, scene one point five)
- [ ] Use `step` for tutorial sequences
- [ ] Use `mark` for important moments
- [ ] Create your first segmented video

### Intermediate (Episodes 4-7)
- [ ] Use `apply good` to score content
- [ ] Use `apply best` to mark top content
- [ ] Use `apply skip` to remove mistakes
- [ ] Use `apply fair` for backup material
- [ ] Combine scoring with `quote` and `hook`
- [ ] Understand retroactive actions

### Advanced (Episodes 8+)
- [ ] Add `emotion` markers to segments
- [ ] Add `energy` markers to segments
- [ ] Combine emotion + energy + scoring
- [ ] Create complete workflow with all markers
- [ ] Understand automatic music selection
- [ ] Understand story arc creation
- [ ] Master retroactive scoring workflow

---

## Common Patterns

### Pattern 1: Multiple Takes
```
slate take one done [Take 1] slate apply good done
slate take two done [Take 2] slate apply best done
slate take three done [Take 3] slate apply skip done
```

### Pattern 1b: Multiple Takes with Scene Numbers
```
slate scene one intro take one done [Scene 1, Take 1] slate apply good done
slate scene one intro take two done [Scene 1, Take 2] slate apply best done
slate scene one point five middle take one done [Scene 1.5, Take 1] slate apply good done
```

### Pattern 2: Tutorial Steps
```
slate step one done [Step 1] slate apply good done
slate step two done [Step 2] slate apply good done
slate step three done [Step 3] slate apply best done
```

### Pattern 3: Hook + Main + Outro
```
slate emotion energetic energy high hook done [Hook] slate apply best done
slate emotion serious energy medium done [Main] slate apply good done
slate emotion energetic energy high cta subscribe done [Outro] slate apply good done
```

### Pattern 4: Quote Highlight
```
slate quote done [Quote] slate apply best quote done
```

### Pattern 5: Remove Mistake
```
slate take one done [Mistake] slate apply skip done
slate take two done [Better] slate apply good done
```

---

## Tips for Success

1. **Start Simple:** Master basics before adding complexity
2. **Practice Regularly:** Use markers in every recording session
3. **Be Consistent:** Use the same patterns for similar content
4. **Score Honestly:** Use "skip" liberally - it saves editing time
5. **Use "fair" Wisely:** Only for backup material you might actually need
6. **One "best" Per Sequence:** Let the system automatically demote previous "best"
7. **Emotion + Energy Together:** They work best when combined
8. **Retroactive is Natural:** Don't try to predict quality - assess after speaking

---

## Troubleshooting

### Problem: Segments not splitting correctly
**Solution:** Make sure you say "slate" clearly and "done" clearly. Check transcript for proper detection.

### Problem: Score not applying
**Solution:** Make sure "apply" comes immediately after "slate" (e.g., `slate apply good done`)

### Problem: Emotion/energy not detected
**Solution:** Make sure you say "emotion" or "energy" as separate words (e.g., `slate shot front emotion energetic done`)

### Problem: Multiple "best" scores
**Solution:** The system automatically demotes previous "best" to "good" when a new "best" is applied. This is correct behavior.

---

## Next Steps

After mastering this system:
1. Explore platform-specific markers (YouTube, Shorts, TikTok)
2. Learn about automatic multicam switching
3. Understand story beat mapping
4. Master thumbnail extraction
5. Create automated rough cuts

See `ADVANCED_MARKER_PROTOCOL.md` for complete reference.

---

## Summary

**Simple:** Basic markers (`slate done`, `order`, `step`, `mark`)
**Intermediate:** Scoring system (`apply good/best/skip/fair`) + retroactive actions
**Advanced:** Emotion + energy + full workflow automation

**Remember:** Start simple, practice regularly, build complexity gradually. The system is designed to grow with your needs.

