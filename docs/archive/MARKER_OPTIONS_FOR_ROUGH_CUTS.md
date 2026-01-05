# Marker Options for Automated Rough Cut Creation

## Current Markers (Already Implemented)

### Quality & Selection
- **`best`** - Best take, highest priority
- **`select`** - Selected for rough cut
- **`backup`** - Backup/safety take (low priority)

### Content Organization
- **`order <number>`** - Sequential order in edit
- **`step <number>`** - Tutorial step number
- **`mark`** - Jump cut point marker

### Content Type
- **`type <word>`** - Content type (camera, screen, broll)

### Story Structure
- **`hook <type>`** - Hook types (coh, ch, psh, tph)
- **`cta <action>`** - Call to action (subscribe, etc.)
- **`chapter <name>`** - Chapter/section marker
- **`ending`** - End of content sequence

### Visual/Effects
- **`effect <product> <name>`** - Visual effect
- **`transition <product> <name>`** - Transition effect
- **`screen <type>`** - Screen overlay (hud, etc.)
- **`broll <type>`** - B-roll type

---

## Proposed New Markers for Rough Cut Automation

### 1. Shot Type Markers (Visual Composition)
**Purpose:** Help editor choose best shot coverage (wide/medium/close)

**Format:** `shot <type>`

**Types:**
- `shot wide` - Wide establishing shot
- `shot medium` - Medium shot (most common)
- `shot close` - Close-up
- `shot extreme` - Extreme close-up
- `shot two` - Two-shot (multiple people)
- `shot broll` - B-roll/cutaway

**Use Case:**
```
slate shot wide done
[establishing shot content]
slate shot medium done
[medium shot content]
```

**Rough Cut Benefit:**
- Automatically match shots (wide → medium → close patterns)
- Create natural shot progression
- Identify establishing shots vs. close-ups

---

### 2. Removable/Filler Markers
**Purpose:** Mark content that should be removed (mistakes, dead air, filler)

**Format:** `remove` or `delete` or `filler`

**Use Case:**
```
slate remove done
[this content should be cut out]
slate done
```

**Rough Cut Benefit:**
- Automatically exclude marked content
- Remove mistakes without manual review
- Trim dead air and filler words

**Note:** Could also use negative quality: `quality bad`

---

### 3. Soundbite/Quote Markers
**Purpose:** Mark important quotes or soundbites (high value content)

**Format:** `quote` or `soundbite` or `highlight`

**Use Case:**
```
slate quote done
[this is an important quote that should definitely be included]
slate done
```

**Rough Cut Benefit:**
- Prioritize important quotes in rough cut
- Ensure key soundbites are included
- Build narrative around highlighted quotes

---

### 4. Thumbnail Marker
**Purpose:** Mark moments that would make good thumbnails

**Format:** `thumbnail`

**Use Case:**
```
slate thumbnail done
[good visual moment for thumbnail]
slate done
```

**Rough Cut Benefit:**
- Extract thumbnail frames automatically
- Identify visually compelling moments
- A/B test multiple thumbnail options

---

### 5. Natural Edit Point Marker
**Purpose:** Mark ideal cut points (natural pauses, breaths, sentence ends)

**Format:** `cut` or `edit`

**Use Case:**
```
[content]
slate cut done
[ideal place to cut - natural pause]
[content continues]
```

**Rough Cut Benefit:**
- Identify natural edit points
- Create smooth cuts without jump cuts
- Respect speech rhythm and pacing

**Note:** Could be automatically detected, but manual override useful

---

### 6. Pacing Markers
**Purpose:** Indicate pacing (slow, normal, fast) for tempo matching

**Format:** `pacing <speed>`

**Types:**
- `pacing slow` - Slow, contemplative content
- `pacing normal` - Normal pace
- `pacing fast` - Fast-paced, energetic content

**Use Case:**
```
slate pacing fast done
[energetic, quick content]
slate pacing slow done
[thoughtful, slow content]
```

**Rough Cut Benefit:**
- Match pacing between segments
- Create rhythm in edit
- Speed up/slow down segments appropriately

---

### 7. Story Beat Markers
**Purpose:** Explicitly mark story structure elements

**Format:** `beat <type>`

**Types:**
- `beat hook` - Hook/attention grabber
- `beat intro` - Introduction
- `beat main` - Main content
- `beat transition` - Transition/breathing room
- `beat recap` - Recap/summary
- `beat outro` - Outro/call to action

**Use Case:**
```
slate beat hook done
[hook content]
slate beat main done
[main content]
slate beat outro done
[outro content]
```

**Rough Cut Benefit:**
- Map content to story structure automatically
- Fill story template (hook → intro → main → outro)
- Ensure proper narrative flow

**Note:** Some overlap with existing `hook` and `cta`, but more explicit structure

---

### 8. Emphasis/Highlight Marker
**Purpose:** Mark content that needs emphasis (slow motion, zoom, text overlay)

**Format:** `emphasize` or `highlight`

**Use Case:**
```
slate emphasize done
[important moment that should be emphasized]
slate done
```

**Rough Cut Benefit:**
- Apply effects to important moments
- Create visual emphasis
- Highlight key points

**Note:** Could work with existing `effect` marker

---

### 9. Multicam Sync Marker
**Purpose:** Mark sync points for multicam editing

**Format:** `sync`

**Use Case:**
```
# Camera A:
slate sync done
[content]

# Camera B:
slate sync done
[same moment, different angle]
```

**Rough Cut Benefit:**
- Automatically sync multicam angles
- Create multicam sequences
- Switch between angles at sync points

---

### 10. Removed Segment Marker
**Purpose:** Mark segments that were intentionally removed (for review)

**Format:** `removed` or `cut-out`

**Use Case:**
```
slate removed reason slow done
[content that was cut for being too slow]
slate done
```

**Rough Cut Benefit:**
- Track removed content
- Create "source tape" of removed footage
- Review edits for potential improvements

---

### 11. Tag/Topic Marker
**Purpose:** Tag content with topics or themes (for thematic grouping)

**Format:** `tag <topic>` or `topic <name>`

**Use Case:**
```
slate tag setup done
[content about setup]
slate tag config done
[content about configuration]
```

**Rough Cut Benefit:**
- Group related content thematically
- Create themed sections in edit
- Match B-roll to topics

**Note:** Could work with existing `chapter` marker

---

### 12. Music/Sound Cue Marker
**Purpose:** Mark music transitions or sound design moments

**Format:** `music <action>` or `sound <type>`

**Types:**
- `music start` - Start music here
- `music stop` - Stop music here
- `music fade` - Fade music
- `sound sfx` - Sound effect needed

**Use Case:**
```
slate music start done
[content with music starting]
slate music fade done
[content with music fading]
```

**Rough Cut Benefit:**
- Automatically place music
- Create music-driven edits
- Add sound design cues

---

## Implementation Priority

### High Priority (Most Impact)
1. **`remove` / `delete`** - Immediate time savings
2. **`quote` / `soundbite`** - Ensures important content included
3. **`shot <type>`** - Creates better shot progression
4. **`beat <type>`** - Maps to story structure automatically

### Medium Priority (Nice to Have)
5. **`thumbnail`** - Useful for automation
6. **`cut` / `edit`** - Helps with edit point detection
7. **`tag <topic>`** - Useful for thematic grouping
8. **`pacing <speed>`** - Creates better rhythm

### Low Priority (Advanced)
9. **`sync`** - Multicam-specific
10. **`emphasize`** - Could work with existing `effect`
11. **`music <action>`** - Music-specific workflow
12. **`removed`** - More for review than automation

---

## Marker Combinations

### Example: Comprehensive Workflow
```
slate beat hook shot wide quote done
[wide establishing shot with important quote for hook]

slate beat main order 1 shot medium best done
[main content, first topic, medium shot, best take]

slate shot close emphasize done
[close-up with emphasis effect]

slate beat transition shot broll tag product done
[b-roll transition with product shots]

slate remove done
[mistake - should be cut]

slate beat outro cta subscribe done
[outro with call to action]
```

---

## Integration with Rough Cut Engine

### Current Rough Cut Process:
1. Analyze transcripts
2. Detect natural edit points
3. Extract quotes
4. Match B-roll
5. Create story structure
6. Apply transitions

### With New Markers:
1. **Parse markers** - Extract all marker data
2. **Filter by quality** - Use `best`/`select`/`remove` markers
3. **Map to story beats** - Use `beat <type>` markers
4. **Match shot types** - Use `shot <type>` for progression
5. **Prioritize quotes** - Use `quote` markers for important content
6. **Identify edit points** - Use `cut` markers for natural cuts
7. **Apply effects** - Use `effect`/`emphasize` markers
8. **Group by topics** - Use `tag` markers for thematic grouping
9. **Sync multicam** - Use `sync` markers for multicam edits
10. **Add music cues** - Use `music` markers for audio

---

## Recommended Starting Set

For initial implementation, recommend:
1. **`remove`** - Most immediate value
2. **`quote`** - Ensures important content
3. **`shot <type>`** - Better shot progression
4. **`beat <type>`** - Story structure mapping
5. **`tag <topic>`** - Thematic grouping

These 5 markers would significantly improve rough cut automation while keeping complexity manageable.

