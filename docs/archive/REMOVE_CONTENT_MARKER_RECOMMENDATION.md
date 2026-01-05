# Recommended Solution: Hybrid Approach (Implicit + Explicit Ends)

## Goal
Maximum flexibility while working with existing fixtures and enabling best practices for new recordings.

---

## Recommended: **Option 2 (Extend `ending`) + Hybrid Approach**

### Concept: Support Both Implicit and Explicit Ends

**Implicit End (works with existing fixtures):**
```
slate remove done
[content to remove]
slate order one done  ← Remove ends here automatically
```

**Explicit End (best practice, requires reshoot):**
```
slate remove done
[content to remove]
slate ending remove done  ← Explicit end marker
slate order one done
```

---

## Why This Is Best for Flexibility

### 1. **Extensible for Future Needs**
- `slate ending done` → Sequence end (backwards compatible)
- `slate ending remove done` → Ends remove segment
- `slate ending hook done` → Could end hook segment
- `slate ending quote done` → Could end quote segment
- `slate ending <any-type> done` → Extensible pattern

### 2. **Works With Existing Fixtures**
- No reshoot needed initially (implicit end works)
- Existing fixtures continue to work
- Can add explicit ends later if needed

### 3. **Best Practice for New Recordings**
- Explicit ends are clearer and more maintainable
- Better for complex workflows
- Self-documenting

### 4. **Flexibility Matrix**

| Scenario | Implicit End | Explicit End |
|----------|-------------|--------------|
| Simple remove | ✅ Works | ✅ Works (clearer) |
| Complex sequences | ⚠️ Works but ambiguous | ✅ Best |
| Multiple remove segments | ⚠️ Works | ✅ Much clearer |
| Remove at sequence end | ⚠️ Ambiguous | ✅ Clear |
| Future marker types | ⚠️ Limited | ✅ Fully extensible |

---

## Implementation

### Phase 1: Add `remove` Command (Works Now)
1. Add `remove` to parser (simple boolean flag)
2. Remove segments use implicit end (end at next marker)
3. Filter remove segments in rough cut engine
4. ✅ Works with existing fixtures immediately

### Phase 2: Extend `ending` Parser (Optional, for Best Practice)
1. Parse `ending <type>` pattern
2. If `ending` followed by word before `done` → it's a type
3. Store ending type in marker
4. Use explicit end when present, fallback to implicit
5. ✅ Enables explicit ends for new recordings

---

## Parser Changes

### Current Parser (marker_commands.py)
```python
# Check for "ending"
if cmd == "ending":
    parsed.ending = True
    i += 1
    continue
```

### Extended Parser (Option 2)
```python
# Check for "ending" with optional type
if cmd == "ending":
    parsed.ending = True
    # Check if next word is a type (before "done")
    if i + 1 < len(normalized):
        next_word = normalized[i + 1]
        if next_word not in ["done", "don", "dun"]:  # Not "done" yet
            parsed.ending_type = next_word  # e.g., "remove", "hook", etc.
            i += 2  # Skip "ending" and type
        else:
            i += 1  # Just "ending", no type
    else:
        i += 1
    continue
```

---

## Segment Extraction Logic

```python
# When END marker found:
if marker.marker_type == "end":
    ending_type = marker.parsed_commands.ending_type  # None or "remove", etc.
    
    if ending_type:
        # Explicit end for specific segment type
        # Find previous segment of that type and close it
        for seg in reversed(segments):
            if seg["marker_info"].get("type") == ending_type:
                seg["end"] = marker.cut_point
                seg["explicit_end"] = True
                break
    else:
        # Implicit end (sequence end or implicit segment end)
        if segments:
            segments[-1]["end"] = marker.cut_point
```

---

## Usage Examples

### Example 1: Simple Remove (Implicit End)
```
slate order one done
[content segment 1]
slate remove done
[mistake content]
slate order two done  ← Remove ends here (implicit)
[content segment 2]
```

### Example 2: Explicit Remove End
```
slate order one done
[content segment 1]
slate remove done
[mistake content]
slate ending remove done  ← Explicit end
slate order two done
[content segment 2]
```

### Example 3: Multiple Remove Segments (Explicit is Better)
```
slate order one done
[content]
slate remove done
[mistake 1]
slate ending remove done  ← Clear end
slate remove done
[mistake 2]
slate ending remove done  ← Clear end
slate order two done
[content]
```

### Example 4: Remove at Sequence End (Explicit is Better)
```
slate order one done
[content]
slate remove done
[final mistake]
slate ending remove done  ← Explicit end
slate ending done  ← Sequence end
```

---

## Recommendation Summary

**For Maximum Flexibility: Option 2 (Extend `ending`) + Hybrid**

1. **Phase 1 (Now):** Add `remove` command, use implicit ends
   - Works with existing fixtures
   - No reshoot needed
   - Quick to implement

2. **Phase 2 (Later):** Extend `ending` parser for explicit ends
   - Best practice for new recordings
   - Maximum flexibility
   - Self-documenting

3. **Benefits:**
   - ✅ Works now (implicit)
   - ✅ Best practice later (explicit)
   - ✅ Maximum flexibility
   - ✅ Extensible for future markers
   - ✅ No breaking changes

---

## If Reshooting Is Acceptable

If you're willing to reshoot fixtures for best practice:

1. **Implement Option 2 fully (extended `ending` parser)**
2. **Reshoot fixtures with explicit ends**
3. **Result:**
   - Cleanest implementation
   - Most flexible
   - Best for long-term
   - Clear and maintainable

**Format for new fixtures:**
```
slate order one done
[content]
slate remove done
[mistake]
slate ending remove done  ← Explicit end
slate order two done
[content]
```

