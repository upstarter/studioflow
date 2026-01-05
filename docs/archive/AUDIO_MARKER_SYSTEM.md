# Audio Marker Editing System - Complete Guide

**The ultimate hands-free video editing automation system using voice commands during recording.**

---

## Quick Start

**One Rule**: Always end marker commands with "done"

```
SLATE "naming setup mark order one done"
"...content..."
SLATE "ending mark cta subscribe done"
```

That's it! The system automatically:
- Detects markers in your transcript
- Removes dead space between markers and content
- Creates edit points at optimal locations
- Generates complete EDL/timeline with all metadata

---

## Core Design

### Marker Word: "slate"

**Why "slate"**:
- Short (1 syllable)
- Industry standard (film/TV term)
- Very unique (unlikely in normal speech)
- High transcription accuracy (95-99%)

### Command Completion: "done"

**Always end commands with "done"**:
- No pause detection needed
- No complex fallbacks
- Clear and unambiguous
- 10-second safety window if "done" is forgotten (gives time to think)

---

## Marker Types

### 1. START Marker
**Syntax**: `SLATE "commands done"` at the START of speaking

**Example**:
```
SLATE "naming setup mark order one step five done"
"...first we need to install Python..."
```

**Cut placement**: Cut at start of actual speech after "done" (removes dead space)

---

### 2. END Marker
**Syntax**: `SLATE "ending commands done"` at the END of speaking

**Example**:
```
"...and that's how you configure it"
SLATE "ending mark cta subscribe done"
```

**Cut placement**: Cut at end of last content word BEFORE marker (removes dead space)

---

### 3. STANDALONE Marker (Jump Cut)
**Syntax**: `SLATE "mark done"` within a segment

**Example**:
```
"...so step one is done" SLATE "mark done" "...now step two..."
```

**Cut placement**: Cut at start of next speech after "done" (removes dead space)

---

## Command Reference

### START Marker Commands
- `naming <name>` - Name this segment
- `mark` - Create edit point
- `order <number>` - Sequence position
- `step <number>` - Step number
- `type <type>` - Clip type (camera, screen, broll)
- `best` / `select` / `backup` - Quality markers
- `hook <type>` - Hook type (coh, ch, psh, etc.)
- `title <text>` - Title text
- `title <type> <text>` - Title with type (lower third, full screen, etc.)
- `effect <product> <name>` - MotionVFX effect (mtuber, mdocumentary, etc.)
- `screen <type>` - Screen type (hud, stinger)

### END Marker Commands
- `ending` - REQUIRED: Signals end marker
- `mark` - Create edit point
- `order <number>` - Sequence position (confirms/clarifies)
- `step <number>` - Step number (confirms/clarifies)
- `cta <type>` - Call-to-action (subscribe, link)
- `chapter <name>` - Create chapter marker
- `broll <type>` - Match B-roll (screen, product, etc.)
- `title <text>` - Title text
- `effect <product> <name>` - MotionVFX effect
- `transition <product> <name>` - MotionVFX transition
- `warp` / `dissolve` / `fade` - Generic transitions
- `screen <type>` - Screen type (hud, stinger)

### STANDALONE Marker Commands
- `mark` - Create jump cut point
- `effect <product> <name>` - MotionVFX effect
- `transition <product> <name>` - MotionVFX transition

---

## Command Parsing

### Fuzzy Matching

The system handles transcription variations automatically:
- `broll` / `b roll` / `b-roll` → all normalize to `broll`
- `cta` / `c t a` / `see t a` → all normalize to `cta`
- Similar handling for all commands

### "mark" Ambiguity Resolution

- **"mark" with other commands** → command flag
  - `SLATE "naming setup mark order one done"` → "mark" is a flag

- **"mark" alone** → jump cut point
  - `SLATE "mark done"` → jump cut point

---

## Cut Placement (Removes Dead Space)

### START Marker
- **Cut at start of actual speech after "done"**
- Removes all dead space between "done" and when you start speaking

**Example**:
```
SLATE "naming setup done" [silence 2s] "...first we install..."
```
→ Cut at start of "first" (removes 2s of dead space)

### END Marker
- **Cut at end of last content word BEFORE marker**
- Removes any dead space before "slate"

**Example**:
```
"...install Python" [silence 1s] SLATE "ending done"
```
→ Cut at end of "Python" (removes 1s of dead space)

### STANDALONE Marker
- **Cut at start of next speech after "done"**
- Removes all dead space between "done" and next content

**Example**:
```
"...step one" [silence 0.5s] SLATE "mark done" [silence 1s] "...now step two"
```
→ Cut at start of "now" (removes 1s of dead space)

**Note**: If cut too close, can always extend clips in timeline

---

## Complete Workflow Example

```
[Start Recording]

SLATE "naming setup mark order one step five done"
"...first we need to install Python. Let me show you how..."

SLATE "ending mark cta subscribe done"

SLATE "naming config mark order two step six done"
"...now let's configure the settings. Click here" 
SLATE "mark done"
"...then click there" 
SLATE "mark done"
"...and we're done"

SLATE "ending mark chapter config done"

[End Recording]
```

**Result**:
- Segment 1: Name="setup", Order=1, Step=5, CTA=subscribe
- Segment 2: Name="config", Order=2, Step=6, Chapter="config", with 2 jump cuts
- All dead space automatically removed
- Ready-to-edit EDL with all metadata

---

## Complete Workflow Example

```
[Start Recording]

SLATE "naming setup mark order one step five done"
"...first we need to install Python. Let me show you how..."

SLATE "ending mark cta subscribe done"

SLATE "naming config mark order two step six done"
"...now let's configure the settings. Click here" 
SLATE "mark done"
"...then click there" 
SLATE "mark done"
"...and we're done"

SLATE "ending mark chapter config done"

[End Recording]
```

**Result**:
- Segment 1: Name="setup", Order=1, Step=5, CTA=subscribe
- Segment 2: Name="config", Order=2, Step=6, Chapter="config", with 2 jump cuts
- All dead space automatically removed
- Ready-to-edit EDL with all metadata

---

## Implementation Algorithm

```python
def detect_markers(transcript: Dict) -> List[AudioMarker]:
    """Detect all markers - simple and straightforward"""
    markers = []
    words = transcript["words"]
    
    i = 0
    while i < len(words):
        if words[i]["word"].lower() == "slate":
            slate_time = words[i]["start"]
            commands = []
            done_found = False
            
            # Collect words until "done"
            j = i + 1
            while j < len(words):
                word = words[j]["word"].lower()
                if word == "done":
                    done_found = True
                    break
                commands.append(words[j]["word"])
                j += 1
            
            if done_found:
                done_time = words[j]["end"]
                parsed = parse_commands(commands)
                marker_type = classify_marker_type(parsed)
                cut_point = calculate_cut_point(marker_type, slate_time, done_time, transcript)
                
                markers.append(AudioMarker(
                    timestamp=slate_time,
                    marker_type=marker_type,
                    commands=commands,
                    cut_point=cut_point
                ))
                i = j + 1
            else:
                # 10-second time window fallback
                cutoff_time = slate_time + 10.0
                commands = []
                j = i + 1
                while j < len(words) and words[j]["start"] <= cutoff_time:
                    commands.append(words[j]["word"])
                    j += 1
                
                if commands:
                    done_time = words[j-1]["end"] if j > i+1 else slate_time + 10.0
                    parsed = parse_commands(commands)
                    marker_type = classify_marker_type(parsed)
                    cut_point = calculate_cut_point(marker_type, slate_time, done_time, transcript)
                    
                    markers.append(AudioMarker(
                        timestamp=slate_time,
                        marker_type=marker_type,
                        commands=commands,
                        cut_point=cut_point
                    ))
                
                i = j
    
    return markers

def calculate_cut_point(marker_type: str, slate_time: float, done_time: float, 
                        transcript: Dict) -> float:
    """Calculate where to make the cut - remove dead space"""
    
    if marker_type == "start":
        # Cut at start of actual speech after "done"
        words_after_done = [w for w in transcript["words"] 
                           if w["start"] > done_time]
        return words_after_done[0]["start"] if words_after_done else done_time
    
    elif marker_type == "end":
        # Cut at end of last content word BEFORE marker
        words_before = [w for w in transcript["words"] 
                       if w["end"] < slate_time]
        return words_before[-1]["end"] if words_before else slate_time
    
    else:  # standalone
        # Cut at start of next speech after "done"
        words_after_done = [w for w in transcript["words"] 
                           if w["start"] > done_time]
        return words_after_done[0]["start"] if words_after_done else done_time + 0.5
```

---

## Integration with Rough Cut System

The audio marker system integrates with the existing rough cut engine:

1. **Transcribe video** with Whisper (word-level timestamps)
2. **Detect markers** in transcript
3. **Extract segments** from START/END marker pairs
4. **Apply metadata** from marker commands
5. **Generate EDL** with all edit points and metadata

**Result**: Fully automated rough cut with:
- Named segments
- Auto-sequencing
- Jump cuts at optimal points
- B-roll matching
- Chapter markers
- CTAs
- Effects and transitions
- All dead space removed

---

## Benefits Over Filename-Based System

### Old Approach (Filename Convention)
- Requires pre-naming files before import
- Limited metadata (filename only)
- No within-clip automation
- Manual organization required

### New Approach (Audio Markers)
- Mark during recording (hands-free)
- Rich metadata (commands, timing, context)
- Within-clip automation (jump cuts, effects)
- Automatic organization
- Works with any filename

**Best Practice**: Use both! Filename convention for organization, audio markers for automation.

---

## Summary

**One Rule**: Always end with "done"

**Three Marker Types**:
1. START: `SLATE "commands done"` → Cut at start of speech
2. END: `SLATE "ending commands done"` → Cut at end of content
3. STANDALONE: `SLATE "mark done"` → Cut at start of next speech

**Key Features**:
- Removes dead space automatically
- Fuzzy command matching (handles transcription variations)
- Rich metadata encoding
- Complete automation

**That's it!** Simple, powerful, hands-free editing automation.

---

## Design Rationale

### Why "slate"?
- Short (1 syllable) - easy to say
- Industry standard (film/TV term)
- Very unique (unlikely in normal speech)
- Distinctive phonemes (/s/, /l/, /t/)
- High transcription accuracy (95-99%)

### Why "done"?
- Short (1 syllable) - easy to say
- Clear and unambiguous
- Easy to remember
- High transcription accuracy
- 10-second safety window if forgotten (gives time to think)

### Why Remove Dead Space?
- Professional videos have no dead air
- Automatic cleanup saves manual work
- Can always extend clips in timeline if cut too close
- Better final output quality

---

## Background & Research

### Why Audio Markers?

Audio markers provide a **universal control system** for 100% automated editing. Instead of manually organizing files or using complex filename conventions, you can mark everything during recording with simple voice commands.

**Key Benefits**:
- **Hands-free**: No need to stop recording or use external tools
- **Rich metadata**: Commands encode names, order, steps, CTAs, chapters, effects
- **Within-clip automation**: Jump cuts, B-roll matching, transitions all automated
- **Works with any filename**: Filename convention becomes organizational tool only

### Marker Word Selection

**"slate" was chosen because**:
- Short (1 syllable) - easy to say
- Industry standard (film/TV term)
- Very unique (unlikely in normal speech)
- Distinctive phonemes (/s/, /l/, /t/)
- High transcription accuracy (95-99%)

**Alternatives considered**:
- "mark" - Too common in speech ("bookmark", "landmark")
- "cue" - Good but less standard
- "dot" - Might appear in speech ("dot com")

### Command Completion: "done"

**"done" was chosen because**:
- Short (1 syllable) - easy to say
- Clear and unambiguous
- Easy to remember
- High transcription accuracy
- 10-second safety window if forgotten (gives time to think)

### Jump Cut Marking

For continuous talking head footage, audio markers solve the problem of marking edit points without:
- Getting up and shaking the camera (disrupts flow)
- Stopping/starting recording (loses continuity)
- Manual timecode notes (tedious)

**Solution**: Say `SLATE "mark done"` during recording to create jump cut points automatically.

---

## Implementation Status

**Status**: Design approved, ready for implementation

**See**: [Audio Marker Implementation Plan](AUDIO_MARKER_IMPLEMENTATION_PLAN.md) for complete implementation roadmap

