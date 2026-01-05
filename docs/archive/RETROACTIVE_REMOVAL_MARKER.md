# Retroactive Removal Marker Design

## Problem Statement

When recording, you don't know what content to remove until AFTER you've finished speaking it. You need to mark removal **retroactively** at the end of the segment, not at the beginning.

## Solution: `slate ending <action> done`

### Concept

The `ending` marker serves dual purpose:
1. **Sequence end:** `slate ending done` (no word) → ends the entire sequence
2. **Retroactive action:** `slate ending <word> done` → ends previous segment with action

### Format

```
slate [previous-segment-commands] done
[content - you realize you want to remove this]
slate ending remove done  ← Marks PREVIOUS segment for removal
slate [next-segment-commands] done
[next content]
```

---

## Usage Examples

### Example 1: Remove Previous Segment

```
slate order one done
[speaking content... oh wait, this is a mistake]
slate ending remove done  ← Retroactively marks segment 1 for removal
slate order two done
[good content continues]
```

**Result:**
- Segment 1 (order one): **REMOVED** ❌
- Segment 2 (order two): **Included** ✅

---

### Example 2: Sequence End (No Removal)

```
slate order one done
[content]
slate ending done  ← Sequence end (no word = no action, just end)
```

**Result:**
- Segment 1: **Included** ✅
- Sequence ends

---

### Example 3: Multiple Removes

```
slate order one done
[mistake 1]
slate ending remove done  ← Removes segment 1
slate order two done
[mistake 2]
slate ending remove done  ← Removes segment 2
slate order three done
[good content]
slate ending done  ← Sequence end
```

**Result:**
- Segment 1: **REMOVED** ❌
- Segment 2: **REMOVED** ❌
- Segment 3: **Included** ✅

---

## Implementation

### 1. Parser Changes (marker_commands.py)

**Current:**
```python
# Check for "ending"
if cmd == "ending":
    parsed.ending = True
    i += 1
    continue
```

**Extended:**
```python
# Check for "ending" with optional action word
if cmd == "ending":
    parsed.ending = True
    # Check if next word is an action (before "done")
    if i + 1 < len(normalized):
        next_word = normalized[i + 1]
        # If next word is NOT "done" (or variant), it's an action word
        if next_word not in ["done", "don", "dun", "dunn", "doan", "doone"]:
            parsed.ending_type = next_word  # e.g., "remove", "hook", etc.
            i += 2  # Skip "ending" and action word
        else:
            # Just "ending" with no action (sequence end)
            i += 1
    else:
        # Just "ending" (sequence end)
        i += 1
    continue
```

### 2. Segment Extraction Logic

**When END marker found:**
```python
if marker.marker_type == "end":
    ending_type = marker.parsed_commands.ending_type  # None or "remove", etc.
    
    if ending_type:
        # Retroactive action: mark PREVIOUS segment
        if segments:
            previous_segment = segments[-1]
            
            if ending_type == "remove":
                previous_segment["remove"] = True
                # Still end the segment (it's done)
                previous_segment["end"] = marker.cut_point
            # Future: handle other ending_type values
    else:
        # No action word = sequence end (current behavior)
        if segments:
            segments[-1]["end"] = marker.cut_point
        # Sequence ends here
```

### 3. Rough Cut Engine

**Filter removed segments:**
```python
# Filter out segments marked for removal
included_segments = [s for s in segments if not s.get("remove", False)]
removed_segments = [s for s in segments if s.get("remove", False)]

# Use included_segments for rough cut
```

---

## Testing Strategy (No Reshoot Needed)

### Approach

1. **Load existing fixture transcript**
2. **Programmatically add `ending remove` markers** in transcript JSON
3. **Run marker detection** on modified transcript
4. **Verify** segments are marked correctly

### Test Example

```python
def test_retroactive_remove_marker():
    """Test retroactive removal marking"""
    # Load existing fixture
    transcript_file = Path("tests/fixtures/test_footage/CAMA-C0176-original-markers_transcript.json")
    with open(transcript_file) as f:
        transcript = json.load(f)
    
    # Find a good spot to insert "ending remove" marker
    # (after a segment, before next slate)
    words = transcript["words"]
    
    # Find index after first segment's "done" and before next "slate"
    insert_idx = None
    for i, word in enumerate(words):
        if "done" in word.get("word", "").lower() and i > 10:
            # Found a "done", check if next "slate" is far enough away
            for j in range(i + 1, min(i + 50, len(words))):
                if "slate" in words[j].get("word", "").lower():
                    insert_idx = j  # Insert before this slate
                    break
            if insert_idx:
                break
    
    if insert_idx:
        # Insert "ending remove done" before next slate
        slate_time = words[insert_idx]["start"]
        
        # Create new words
        new_words = (
            words[:insert_idx] +
            [
                {"word": "ending", "start": slate_time - 1.5, "end": slate_time - 1.0},
                {"word": "remove", "start": slate_time - 1.0, "end": slate_time - 0.5},
                {"word": "done", "start": slate_time - 0.5, "end": slate_time - 0.1},
            ] +
            words[insert_idx:]
        )
        
        transcript["words"] = new_words
        
        # Run marker detection
        detector = AudioMarkerDetector()
        markers = detector.detect_markers(transcript)
        
        # Verify END marker has ending_type="remove"
        end_markers = [m for m in markers if m.marker_type == "end"]
        assert len(end_markers) > 0
        assert end_markers[0].parsed_commands.ending_type == "remove"
        
        # Extract segments
        segments = extract_segments_from_markers(markers, transcript, clip_duration=transcript["duration"])
        
        # Verify previous segment marked for removal
        # (segment before the "ending remove" marker)
        assert any(s.get("remove", False) for s in segments)
```

---

## Sequence Ending vs Segment Ending

### Sequence End
```
slate order one done
[content]
slate ending done  ← No word = sequence end only
```

**Behavior:**
- Ends the sequence
- Previous segment included (normal)
- No action taken

### Segment End with Action
```
slate order one done
[content to remove]
slate ending remove done  ← Has word = segment end + action
slate order two done
[more content]
```

**Behavior:**
- Ends previous segment
- Marks previous segment for removal
- Sequence continues (next segment starts)

---

## Benefits of This Approach

1. ✅ **Retroactive:** Mark removal after speaking (natural workflow)
2. ✅ **Flexible:** Can extend to other actions (ending hook, ending quote, etc.)
3. ✅ **Backwards Compatible:** `ending` alone still works as sequence end
4. ✅ **No Reshoot:** Test by adding markers to existing transcripts
5. ✅ **Clear Intent:** Explicit about what's being removed
6. ✅ **Extensible:** Pattern works for future marker types

---

## Summary

**Pattern:**
- `slate ending done` → Sequence end (backwards compatible)
- `slate ending remove done` → End previous segment + mark for removal
- `slate ending <word> done` → End previous segment + action <word>

**Implementation:**
1. Extend parser to detect optional word after "ending"
2. Store ending_type in ParsedCommands
3. Mark previous segment when END marker with ending_type found
4. Filter removed segments in rough cut engine

**Testing:**
- Add markers programmatically to existing fixture transcripts
- Verify logic without reshooting
- Production recordings use new pattern

