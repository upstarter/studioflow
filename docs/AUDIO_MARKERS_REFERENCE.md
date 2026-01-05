# Audio Markers: Complete Reference

Complete technical reference for all audio marker commands and features.

## Marker Structure

All markers follow this pattern:
```
slate [commands] done
```

**Components:**
- `slate` - Start marker (required)
- `[commands]` - One or more commands (optional)
- `done` - End marker (required)
- Content after `done` - Actual video content

---

## Core Commands

### Scene Numbers

**Purpose:** Specify position in final sequence using decimal numbers.

**Syntax:**
```
slate scene [number] [name] done
```

**Examples:**
- `slate scene one done` → Scene 1.0
- `slate scene one point five done` → Scene 1.5
- `slate scene one point two five done` → Scene 1.25
- `slate scene one intro done` → Scene 1.0, name: "intro"
- `slate scene one point five transition done` → Scene 1.5, name: "transition"

**Precision:**
- Supports up to 3 decimal places (0.001 precision)
- Typical usage: 1-2 decimal places
- Complex usage: 2-3 decimal places

**Use Cases:**
- Shooting scenes in sequence
- Shooting out of order
- Inserting scenes between existing ones

### Takes

**Purpose:** Multiple attempts at the same scene.

**Syntax:**
```
slate take [number] done
```

**Examples:**
- `slate take one done` → Take 1
- `slate take two done` → Take 2
- `slate scene one intro take one done` → Scene 1, Take 1

**Use Cases:**
- Multiple attempts at same content
- Comparing different versions
- Tracking which take was selected

### Steps

**Purpose:** Sequential steps in tutorials or processes.

**Syntax:**
```
slate step [number] done
```

**Examples:**
- `slate step one done` → Step 1
- `slate step two done` → Step 2
- `slate shot screen step one done` → Screen recording, Step 1

**Use Cases:**
- Tutorial videos
- Step-by-step instructions
- Sequential processes

### Mark

**Purpose:** Mark important moments.

**Syntax:**
```
slate mark done
```

**Examples:**
- `slate mark done` → Important moment

**Use Cases:**
- Important quotes
- Key moments
- Highlights

---

## Scoring System

### Score Levels

**Purpose:** Assess content quality (4-level system).

**Syntax:**
```
slate apply [score] [actions] done
```

**Score Levels:**
- `skip` (Level 0) - Remove/skip (mistakes, dead air)
- `fair` (Level 1) - Usable backup (not great, but might need)
- `good` (Level 2) - Solid content (include in rough cut)
- `best` (Level 3) - Top tier (only one per sequence)

**Examples:**
- `slate apply skip done` → Remove previous segment
- `slate apply fair done` → Mark previous as backup
- `slate apply good done` → Mark previous as good
- `slate apply best done` → Mark previous as best (demotes previous best)

**Behavior:**
- Retroactive (applies to previous segment)
- Only one "best" per sequence (auto-demotes previous)
- Can combine with other actions

### Combined Actions

**Syntax:**
```
slate apply [score] [action1] [action2] ... done
```

**Available Actions:**
- `hook` - Hook content (first 15 seconds)
- `quote` - Important quote
- `remove` / `skip` - Remove content

**Examples:**
- `slate apply good hook done` → Good + hook
- `slate apply best quote done` → Best + quote
- `slate apply skip done` → Remove

---

## Emotion & Energy Markers

### Emotion

**Purpose:** Set emotional tone of content.

**Syntax:**
```
slate [shot] emotion [type] done
```

**Emotion Types:**
- `energetic` - High energy, fast-paced, exciting
- `serious` - Dramatic, important, weighty
- `contemplative` - Thoughtful, reflective, calm
- `happy` - Positive, upbeat, cheerful
- `sad` - Melancholic, emotional, somber
- `neutral` - Balanced, informative, straightforward

**Examples:**
- `slate shot front emotion energetic done`
- `slate scene one emotion serious done`

**Use Cases:**
- Tone matching for transitions
- Music selection
- Story arc creation

### Energy

**Purpose:** Set energy/pacing level.

**Syntax:**
```
slate [shot] energy [level] done
```

**Energy Levels:**
- `high` - Fast-paced, dynamic, intense
- `medium` - Balanced, moderate pace
- `low` - Slow, contemplative, relaxed

**Examples:**
- `slate shot front energy high done`
- `slate scene one energy medium done`

**Use Cases:**
- Speed adjustment
- Music tempo matching
- Rhythm creation

### Combined

**Examples:**
- `slate shot front emotion energetic energy high done`
- `slate scene one emotion serious energy medium done`

---

## Shot Types

**Purpose:** Specify camera angle or shot type.

**Syntax:**
```
slate shot [type] [commands] done
```

**Common Shot Types:**
- `front` - Front-facing camera
- `close` - Close-up
- `medium` - Medium shot
- `wide` - Wide shot
- `overhead` - Overhead angle
- `screen` - Screen recording

**Examples:**
- `slate shot front done`
- `slate shot screen step one done`
- `slate shot close emotion serious done`

---

## Other Commands

### Hook

**Purpose:** Mark hook content (first 15 seconds).

**Syntax:**
```
slate [commands] hook done
slate apply [score] hook done
```

**Examples:**
- `slate shot front hook done`
- `slate apply best hook done`

### Quote

**Purpose:** Mark important quotes.

**Syntax:**
```
slate [commands] quote done
slate apply [score] quote done
```

**Examples:**
- `slate shot front quote done`
- `slate apply best quote done`

### CTA (Call to Action)

**Purpose:** Mark call-to-action content.

**Syntax:**
```
slate [commands] cta [type] done
```

**Examples:**
- `slate shot front cta subscribe done`
- `slate scene outro cta subscribe done`

### Transition

**Purpose:** Mark transition content.

**Syntax:**
```
slate transition [type] done
```

**Examples:**
- `slate transition done`
- `slate transition fade done`

### Effect

**Purpose:** Mark effect content.

**Syntax:**
```
slate effect [product] [name] done
```

**Examples:**
- `slate effect mtuber intro done`

---

## Marker Types

### START Markers
- Have `take`, `order`, `scene_number`, or `step`
- Create new segments
- Examples: `slate scene one done`, `slate take one done`

### RETROACTIVE Markers
- Have `apply` keyword
- Apply actions to previous segment
- Examples: `slate apply good done`, `slate apply best done`

### END Markers
- Have `ending` alone (no commands)
- Mark sequence end
- Examples: `slate ending done`

### STANDALONE Markers
- Just `mark` or effects/transitions
- Create segments
- Examples: `slate mark done`, `slate transition done`

---

## Complete Examples

### Example 1: Basic Workflow
```
slate scene one intro done
[Scene 1 content]
slate apply good done

slate scene two main done
[Scene 2 content]
slate apply good done

slate scene three outro done
[Scene 3 content]
slate apply good done
```

### Example 2: Multiple Takes
```
slate scene one intro take one done
[Take 1]
slate apply good done

slate scene one intro take two done
[Take 2 - better]
slate apply best done

slate scene one intro take three done
[Take 3 - mistake]
slate apply skip done
```

### Example 3: Shooting Out of Order
```
# Day 1
slate scene one intro done
slate scene two setup done
slate scene four demo done
slate scene five outro done

# Day 2: Insert scene 3
slate scene three middle done
```

**Result:** Ordered as 1 → 2 → 3 → 4 → 5

### Example 4: Complete Workflow
```
slate scene one emotion energetic energy high hook done
[Hook content]
slate apply best done

slate scene two emotion serious energy medium step one done
[Main content step 1]
slate apply good done

slate scene two step one take two done
[Better take of step 1]
slate apply best done

slate scene two point five emotion contemplative energy low done
[Transition]
slate apply fair done

slate scene three emotion energetic energy high cta subscribe done
[Outro]
slate apply good done
```

---

## Implementation Details

### Parsing Logic
- Case-insensitive
- Fuzzy matching for "slate" and "done" variants
- Handles punctuation (strips before checking)
- Supports number words ("one", "two", etc.) and digits ("1", "2", etc.)

### Decimal Parsing
- Supports up to 3 decimal places
- Parses "point" as decimal separator
- Examples: "one point five" → 1.5, "one point two five" → 1.25

### Score Demotion
- When "best" is applied, previous "best" is demoted to "good"
- Only one "best" per sequence
- Automatic demotion logic

### Segment Extraction
- Segments start at first words after "done"
- Segments end at last words before next "slate"
- Padding: 0.2s before, 0.3s after for natural jump cuts

### Segment Ordering

**Sorting Priority:**
1. `scene_number` (ascending) - Explicit sequence order
2. `take` (ascending, if same scene_number) - Multiple attempts
3. `start` timestamp (chronological, if no scene_number or same scene/take)

**Behavior:**
- Scene numbers override chronological order
- Allows shooting scenes out of order
- Allows inserting scenes between existing ones (using decimals)
- Multiple takes of same scene are grouped together
- Segments without scene numbers use chronological order

**Example:**
```
Chronological: Scene 1 (0:00), Scene 2 (1:00), Scene 4 (2:00), Scene 3 (3:00)
Sorted: Scene 1, Scene 2, Scene 3, Scene 4
```

---

## Backwards Compatibility

### Deprecated Commands
- `order` - Use `scene [number]` instead
- `ending [action]` - Use `apply [action]` instead

**Note:** Deprecated commands still work but are not recommended for new footage.

---

## See Also

- `AUDIO_MARKERS_USER_GUIDE.md` - User guide with examples
- `AUDIO_MARKERS_IMPLEMENTATION.md` - Implementation details for developers

