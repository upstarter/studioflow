# Ultimate Fixture Footage Specification

## Purpose

This document describes the ideal test footage clip to replace the current CAMA/CAMB fixtures. The goal is to create **minimal footage** that comprehensively tests **all audio marker features** with maximum efficiency.

## Target Duration

**30-60 seconds** of footage containing multiple marker sequences to test all features efficiently.

> **Note**: For production-grade testing with edge cases and long-form episodes, see [PRODUCTION_FIXTURE_FOOTAGE.md](PRODUCTION_FIXTURE_FOOTAGE.md) which includes 5-10 minute recordings with 45+ segments.

---

## Marker Features to Test

### 1. START Markers (Create Segments)

#### Scene Numbering (Modern)
- `slate scene one intro done` - Scene 1
- `slate scene two main done` - Scene 2  
- `slate scene two point five transition done` - Scene 2.5 (decimal)

#### Order (Deprecated, Backwards Compatible)
- `slate order three done` - Maps to scene 3

#### Step Numbering
- `slate step one setup done` - Step 1
- `slate step two execute done` - Step 2

#### Take Numbering
- `slate scene one take one done` - Scene 1, Take 1
- `slate scene one take two done` - Scene 1, Take 2 (same scene, different take)

### 2. STANDALONE Markers (Create Segments)

#### Simple Mark
- `slate mark done` - Simple mark point

#### Effects
- `slate effect mtuber intro done` - Product effect
- `slate effect zoom done` - Generic effect

#### Transitions
- `slate transition mtuber fade done` - Product transition
- `slate transition warp done` - Generic transition

#### Other Standalone
- `slate broll screen done` - B-roll marker
- `slate hook coh done` - Hook marker
- `slate title Introduction done` - Title marker
- `slate screen hud done` - Screen marker
- `slate cta subscribe done` - CTA marker
- `slate chapter config done` - Chapter marker
- `slate emotion energetic done` - Emotion marker
- `slate energy high done` - Energy marker

### 3. RETROACTIVE Markers (Don't Create Segments)

#### Apply Actions
- `slate apply best done` - Score previous segment as "best"
- `slate apply good done` - Score previous segment as "good"
- `slate apply skip done` - Mark previous segment to skip
- `slate apply hook done` - Mark previous segment as hook
- `slate apply quote done` - Mark previous segment as quote

#### Apply with Commands (Retroactive)
- `slate apply conclusion done` - Apply "conclusion" to previous segment
- `slate apply best done` - Score previous segment as "best" (same as above, but explicit)

**Note**: The `ending` marker is **DEPRECATED**. Use `apply` for all retroactive actions.
- ❌ Deprecated: `slate ending conclusion done` 
- ✅ Use instead: `slate apply conclusion done`

---

## Recommended Test Sequence

Here's a minimal sequence that tests all features:

```
Time    Marker Command                         Expected Behavior
─────────────────────────────────────────────────────────────────────────
0:00    [Content: "This is our test footage"]  (No marker)
0:05    slate scene one intro done             → Creates segment 001 (START)
0:10    [Content: "Introduction content"]      (Segment 001 continues)
0:15    slate mark done                        → Segment 001 ENDS at 0:15, Creates segment 002 (STANDALONE)
0:20    [Content: "Marked content"]            (Segment 002 continues)
0:25    slate apply best done                  → No segment, scores segment 002 as "best" (RETROACTIVE)
0:30    slate scene two main done              → Segment 002 ENDS at 0:30, Creates segment 003 (START)
0:35    [Content: "Main content"]              (Segment 003 continues)
0:40    slate step one setup done              → Segment 003 ENDS at 0:40, Creates segment 004 (START with step)
0:45    [Content: "Setup step"]                (Segment 004 continues)
0:50    slate step two execute done            → Segment 004 ENDS at 0:50, Creates segment 005 (START with step)
0:55    [Content: "Execute step"]              (Segment 005 continues)
1:00    slate effect zoom done                 → Segment 005 ENDS at 1:00, Creates segment 006 (STANDALONE with effect)
1:05    [Content: "Effect content"]            (Segment 006 continues)
1:10    slate apply conclusion done            → No segment, applies "conclusion" to segment 006 (RETROACTIVE)
1:15    [Content: "Final words"]               (Segment 006 continues - no new segment)
1:20    [Content: "More content"]              (Segment 006 continues - ends naturally at video end)
```

### Expected Segments (6 total)

1. **Segment 001** (scene 1, intro): 0:05 - 0:15 (ends at next marker's "slate" timestamp)
2. **Segment 002** (mark): 0:15 - 0:30 (ends at next marker), **scored "best"** (retroactive)
3. **Segment 003** (scene 2, main): 0:30 - 0:40 (ends at next marker)
4. **Segment 004** (step 1, setup): 0:40 - 0:50 (ends at next marker)
5. **Segment 005** (step 2, execute): 0:50 - 1:00 (ends at next marker)
6. **Segment 006** (effect zoom): 1:00 - end of video, **marked "conclusion"** (retroactive)

**Key Points**:
- Segments end at the **next marker's "slate" timestamp** (not the "done" timestamp)
- The last segment extends to the **end of the video** automatically
- No sequence end marker needed - segments end naturally

---

## Complete Test Coverage Checklist

### ✅ Marker Types
- [x] START marker (scene, order, step, take)
- [x] STANDALONE marker (mark, effect, transition)
- [x] RETROACTIVE marker (apply)

### ✅ Scene Organization
- [x] Scene number (scene one)
- [x] Scene number with name (scene one intro)
- [x] Decimal scene number (scene two point five)
- [x] Order number (DEPRECATED, backwards compatible)
- [x] Step number (step one)
- [x] Take number (take one, take two)

### ✅ Effects & Transitions
- [x] Product effect (effect mtuber intro)
- [x] Generic effect (effect zoom)
- [x] Product transition (transition mtuber fade)
- [x] Generic transition (transition warp)

### ✅ Content Markers
- [x] Mark (mark)
- [x] B-roll (broll screen)
- [x] Hook (hook coh)
- [x] Title (title Introduction)
- [x] Screen (screen hud)
- [x] CTA (cta subscribe)
- [x] Chapter (chapter config)
- [x] Emotion (emotion energetic)
- [x] Energy (energy high)
- [x] Quality (best, select, backup)

### ✅ Retroactive Actions
- [x] Apply score (apply best, apply good, apply skip)
- [x] Apply hook (apply hook)
- [x] Apply quote (apply quote)
- [x] Apply with commands (apply conclusion, apply best)

### ✅ Segment Extraction Logic
- [x] START markers create segments
- [x] STANDALONE markers create segments
- [x] END markers don't create segments
- [x] RETROACTIVE markers don't create segments
- [x] Segments end at next marker's slate timestamp (or end of video)
- [x] Last segment extends to natural end of video (not cut off)
- [x] Retroactive actions apply to previous segment
- [x] Segment sorting (scene_number > take > chronological)
- [x] No sequence end marker needed (segments end naturally)

---

## Filming Instructions

1. **Record 30-60 seconds** of talking head footage
2. **Speak clearly** and pause briefly after each marker command
3. **Say "slate" before each marker command** (for detection)
4. **Say "done" after each marker command** (for boundary detection)
5. **Provide content between markers** (at least 5 seconds per segment)
6. **Use the exact marker commands** from the sequence above
7. **End naturally** - segments end at next marker or end of video (no sequence end marker needed)

### Example Script

```
"This is our test footage for comprehensive audio marker testing.

[Slate] Scene one intro [Done]
This is the introduction content for scene one.

[Slate] Mark [Done]
This is a marked section of content.

[Slate] Apply best [Done]
[Slate] Scene two main [Done]
This is the main content for scene two.

[Slate] Step one setup [Done]
This is the setup step content.

[Slate] Step two execute [Done]
This is the execute step content.

[Slate] Effect zoom [Done]
This content uses the zoom effect.

[Slate] Apply conclusion [Done]
These are the final words. The segment will end naturally at the end of the video."
```

---

## File Naming

**Recommended:** `TEST-FIXTURE-comprehensive-markers.MP4`

- `TEST-FIXTURE` - Clearly identifies as test fixture
- `comprehensive-markers` - Describes content
- `.MP4` - Standard video format

---

## Validation Checklist

After creating the fixture footage, verify:

1. **Transcription Quality**
   - All "slate" words are detected correctly
   - All "done" words are detected correctly
   - Marker commands are transcribed accurately

2. **Marker Detection**
   - All expected markers are detected
   - Marker types are classified correctly (START, STANDALONE, RETROACTIVE, END)
   - Commands are parsed correctly

3. **Segment Extraction**
   - Expected number of segments created (6 in example above)
   - Segments start/end at correct timestamps
   - No segment created for RETROACTIVE markers (apply)
   - Last segment extends to natural end of video (not cut off)

4. **Retroactive Actions**
   - Retroactive scores apply to previous segment
   - Retroactive actions (hook, quote, conclusion) apply to previous segment
   - Use "apply" for all retroactive actions (not "ending")

5. **Segment Sorting**
   - Segments sorted correctly (scene_number > take > chronological)
   - Scene numbers in correct order
   - Takes grouped under same scene

---

## Replacement Strategy

1. **Keep original fixtures** as backup (`CAMA-C0176-original-markers.MP4`, `CAMB-C0030-original-markers.MP4`)
2. **Create new fixture** following this specification
3. **Test new fixture** with existing test suite
4. **Update test expectations** if needed
5. **Document results** in test output

---

## Benefits

- **Minimal footage** (30-60 seconds vs. current 2-3 minute clips)
- **Comprehensive coverage** (all marker features in one clip)
- **Faster tests** (less processing time)
- **Clear test cases** (each marker type tested explicitly)
- **Easy to update** (single fixture file to maintain)

---

## Notes

- Current fixtures (`CAMA-C0176-original-markers.MP4`, `CAMB-C0030-original-markers.MP4`) are ~2-3 minutes each
- New fixture should be ~30-60 seconds with all features
- This reduces test time while increasing coverage
- Single fixture can replace both CAMA and CAMB if designed carefully
- Consider creating separate fixtures if feature sets are too large for one clip

