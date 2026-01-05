# Audio Markers: User Guide

Complete guide for using audio markers in StudioFlow to automate video editing.

## Quick Start

### Basic Structure
Every marker follows this pattern:
```
slate [commands] done
```

**What happens:**
- Say "slate" → System starts listening
- Say your commands → System records them
- Say "done" → System stops listening
- Everything after "done" is your content

### Your First Marker
```
slate done
[Speak your content here]
slate done
[Speak more content here]
```

**Result:** Two separate segments created automatically.

---

## Core Concepts

### 1. Scene Numbers (Sequence Ordering)

Use scene numbers to specify position in final sequence. Use decimals to insert scenes between existing ones.

**Basic Usage:**
```
slate scene one done
[Scene 1]
slate scene two done
[Scene 2]
slate scene three done
[Scene 3]
```

**Inserting Scenes:**
```
slate scene one done
[Scene 1]
slate scene two done
[Scene 2]

# Later: Insert scene between 1 and 2
slate scene one point five done
[Scene 1.5 - inserted between 1 and 2]
```

**With Names:**
```
slate scene one intro done
slate scene one point five transition done
slate scene two main done
```

**Decimal Precision:**
- 1 decimal: `scene one point five` → 1.5
- 2 decimals: `scene one point two five` → 1.25
- 3 decimals: `scene one point one two five` → 1.125 (rarely needed)

**When to use:** When shooting out of order or inserting scenes later.

**Ordering Behavior:**
- Segments are sorted by `scene_number` first (ascending)
- If same `scene_number`, sorted by `take` (ascending)
- If no `scene_number`, uses chronological order (timestamp)
- This allows shooting scenes in any order - the system will assemble them correctly

### 2. Takes (Multiple Attempts)

Use "take" for multiple attempts at the same scene.

**Basic Usage:**
```
slate take one done
[First attempt]
slate apply good done

slate take two done
[Second attempt - better]
slate apply best done

slate take three done
[Third attempt - mistake]
slate apply skip done
```

**With Scene Numbers:**
```
slate scene one intro take one done
[Scene 1, Take 1]
slate apply good done

slate scene one intro take two done
[Scene 1, Take 2 - better]
slate apply best done
```

**When to use:** When shooting multiple attempts at the same content.

### 3. Steps (Tutorial Sequences)

Use "step" for sequential steps in tutorials or processes.

**Basic Usage:**
```
slate step one done
[Step 1: Setup]
slate apply good done

slate step two done
[Step 2: Process]
slate apply good done

slate step three done
[Step 3: Result]
slate apply good done
```

**When to use:** For tutorials, step-by-step instructions, or sequential processes.

### 4. Scoring System

Use the 4-level score system to assess content quality.

**Score Levels:**
- `skip` (Level 0) - Remove/skip (mistakes, dead air)
- `fair` (Level 1) - Usable backup (not great, but might need)
- `good` (Level 2) - Solid content (include in rough cut)
- `best` (Level 3) - Top tier (only one per sequence)

**Usage:**
```
slate take one done
[First take]
slate apply good done

slate take two done
[Second take - better]
slate apply best done

slate take three done
[Mistake]
slate apply skip done
```

**Key Points:**
- "apply" applies to the **previous** segment
- Only one "best" per sequence (automatically demotes previous "best" to "good")
- System automatically selects best takes

### 5. Emotion & Energy Markers

Add emotion and energy markers for intelligent editing.

**Emotion Types:**
- `energetic` - High energy, fast-paced, exciting
- `serious` - Dramatic, important, weighty
- `contemplative` - Thoughtful, reflective, calm
- `happy` - Positive, upbeat, cheerful
- `sad` - Melancholic, emotional, somber
- `neutral` - Balanced, informative, straightforward

**Energy Levels:**
- `high` - Fast-paced, dynamic, intense
- `medium` - Balanced, moderate pace
- `low` - Slow, contemplative, relaxed

**Usage:**
```
slate shot front emotion energetic energy high done
[High-energy content]
slate apply best done

slate shot medium emotion serious energy medium done
[Serious content]
slate apply good done

slate shot close emotion contemplative energy low done
[Thoughtful content]
slate apply good done
```

**What This Enables:**
- Smooth transitions between similar emotions
- Automatic music selection
- Story arc creation
- Speed adjustment based on energy

---

## Common Patterns

### Pattern 1: Multiple Takes
```
slate take one done [Take 1] slate apply good done
slate take two done [Take 2] slate apply best done
slate take three done [Take 3] slate apply skip done
```

### Pattern 2: Tutorial Steps
```
slate step one done [Step 1] slate apply good done
slate step two done [Step 2] slate apply good done
slate step three done [Step 3] slate apply best done
```

### Pattern 3: Hook + Main + Outro
```
slate scene one emotion energetic energy high hook done [Hook] slate apply best done
slate scene two emotion serious energy medium done [Main] slate apply good done
slate scene three emotion energetic energy high cta subscribe done [Outro] slate apply good done
```

### Pattern 4: Shooting Out of Order
```
# Day 1: Shoot scenes 1, 2, 4, 5
slate scene one intro done
slate scene two setup done
slate scene four demo done
slate scene five outro done

# Day 2: Insert scene 3
slate scene three middle done
```

**Result:** System assembles as 1 → 2 → 3 → 4 → 5

### Pattern 5: Multiple Takes with Scene Numbers
```
slate scene one intro take one done [Scene 1, Take 1] slate apply good done
slate scene one intro take two done [Scene 1, Take 2] slate apply best done
slate scene one point five transition take one done [Scene 1.5, Take 1] slate apply good done
```

---

## Quick Reference

### Basic Markers
| Marker | Purpose | Example |
|--------|---------|---------|
| `slate done` | Basic segment | `slate done` |
| `slate scene one done` | Scene number | `slate scene one done` |
| `slate scene one point five done` | Insert scene | `slate scene one point five done` |
| `slate take one done` | Multiple attempts | `slate take one done` |
| `slate step one done` | Tutorial steps | `slate step one done` |
| `slate mark done` | Important moment | `slate mark done` |

### Scoring
| Score | Level | When to Use |
|-------|-------|-------------|
| `skip` | 0 | Mistakes, dead air, remove |
| `fair` | 1 | Backup material, usable but not great |
| `good` | 2 | Solid content, include in rough cut |
| `best` | 3 | Top tier, only one per sequence |

**Usage:** `slate apply [score] done`

### Emotion & Energy
| Marker | Purpose | Example |
|--------|---------|---------|
| `emotion energetic` | Set emotion | `slate shot front emotion energetic done` |
| `energy high` | Set energy | `slate shot front energy high done` |
| Combined | Both | `slate shot front emotion energetic energy high done` |

### Other Actions
| Action | Purpose | Example |
|--------|---------|---------|
| `hook` | Hook content | `slate apply best hook done` |
| `quote` | Important quote | `slate apply good quote done` |
| `remove` / `skip` | Remove content | `slate apply skip done` |

---

## Learning Progression

### Beginner (Episodes 1-3)
- [ ] Understand basic marker structure (`slate ... done`)
- [ ] Use scene numbers for ordering
- [ ] Use `take` for multiple attempts
- [ ] Use `step` for tutorial sequences
- [ ] Create your first segmented video

### Intermediate (Episodes 4-7)
- [ ] Use scoring system (`apply good`, `apply best`, `apply skip`)
- [ ] Use `apply fair` for backup material
- [ ] Combine scoring with other actions (`hook`, `quote`)
- [ ] Understand retroactive actions
- [ ] Use decimal scene numbers for insertion

### Advanced (Episodes 8+)
- [ ] Add emotion markers
- [ ] Add energy markers
- [ ] Combine emotion + energy + scoring
- [ ] Create complete workflow with all markers
- [ ] Master shooting out of order with scene numbers

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

See `AUDIO_MARKERS_REFERENCE.md` for complete marker reference.

