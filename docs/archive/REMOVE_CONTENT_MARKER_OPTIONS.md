# Options for Marking Removable Content

## Problem
Currently, segments end automatically at the next `slate` marker. To mark content for removal, we need a way to explicitly end the removable segment before the next content starts.

## Current System
- **START marker:** `slate [commands] done [content]` → segment starts after "done"
- **END marker:** `slate ending done` → closes last segment in sequence
- **STANDALONE marker:** `slate mark done [content]` → creates jump cut
- **Segment boundary:** Segments automatically end at next `slate` marker

## Requirements
1. Mark content to remove without reshooting fixtures
2. Explicitly end removable segments
3. Backwards compatible with existing system
4. Simple to use during recording

---

## Option 1: Reuse `ending` Marker (RECOMMENDED)

### Format
```
slate remove done
[content to remove]
slate ending done
[normal content continues]
slate order one done
[next segment]
```

### Implementation
- Treat `ending` marker as closing ANY segment type (not just sequence end)
- If previous segment has `remove` marker, exclude it from rough cut
- If previous segment is normal, it's the sequence end (current behavior)

### Pros
✅ Uses existing marker type  
✅ No syntax changes  
✅ Backwards compatible  
✅ Can add to existing transcripts/fixtures  
✅ Simple to implement  

### Cons
⚠️ `ending` was conceptually for sequence end (but can work for segment end too)  
⚠️ Slightly ambiguous (but context makes it clear)

### Code Changes
```python
# In extract_segments_from_markers():
# When we encounter END marker, check previous segment's marker type
# If previous marker is "remove", mark segment for exclusion
# Otherwise, it's sequence end (current behavior)
```

---

## Option 2: Extend `ending` to Take Optional Type

### Format
```
slate remove done
[content to remove]
slate ending remove done
[normal content continues]
```

### Implementation
- `ending` can take optional argument: `ending remove`, `ending hook`, etc.
- Parser: if next word after "ending" is not "done", it's a type
- `ending remove` closes remove segment
- `ending` alone closes sequence (backwards compatible)

### Pros
✅ Explicit about what's ending  
✅ Extensible (ending remove, ending hook, etc.)  
✅ Backwards compatible (ending alone still works)  

### Cons
⚠️ More verbose  
⚠️ Requires parser changes  
⚠️ Slightly more complex syntax  

---

## Option 3: New `remove-end` Marker

### Format
```
slate remove done
[content to remove]
slate remove-end done
[normal content continues]
```

### Implementation
- New marker type: `remove-end`
- Only valid after `remove` marker
- Closes the remove segment

### Pros
✅ Very clear and explicit  
✅ Self-documenting  
✅ No ambiguity  

### Cons
⚠️ New marker type (adds complexity)  
⚠️ Requires parser changes  
⚠️ Must be paired correctly (remove → remove-end)  

---

## Option 4: Implicit End (Next Marker Ends Remove)

### Format
```
slate remove done
[content to remove]
slate order one done
[next segment - remove ends here]
```

### Implementation
- `remove` segments automatically end at next marker (any type)
- Next marker's content is normal (not removed)
- Remove segment excludes everything between "remove done" and next "slate"

### Pros
✅ Simplest syntax  
✅ No new markers needed  
✅ Easy to use during recording  

### Cons
⚠️ Less explicit (can't see remove-end marker)  
⚠️ Can't have empty segments between remove and next marker  
⚠️ Must have a next marker (can't end sequence with remove)  

---

## Option 5: Paired Markers (START/END Pattern)

### Format
```
slate remove start done
[content to remove]
slate remove end done
[normal content continues]
```

### Implementation
- `remove start` opens remove segment
- `remove end` closes remove segment
- Parser tracks pairs

### Pros
✅ Very explicit  
✅ Symmetric pattern  
✅ Clear intent  

### Cons
⚠️ More verbose  
⚠️ Requires tracking pairs  
⚠️ More complex parser logic  
⚠️ Two markers instead of one  

---

## Recommendation: **Option 2** (Extend `ending` with Optional Type) + **Hybrid Approach**

### Why Option 1?

1. **Simplicity:** Uses existing marker type, no syntax changes
2. **Backwards Compatible:** Existing `slate ending done` still works as sequence end
3. **No Reshoot Needed:** Can add `ending` markers to existing transcripts/fixtures
4. **Clear Intent:** Context makes it obvious what's being closed
5. **Easy Implementation:** Minimal code changes

### Usage Pattern

```python
# Normal sequence end (current behavior):
slate order one done
[content]
slate ending done  # Closes sequence

# Remove segment (new usage):
slate remove done
[content to remove]
slate ending done  # Closes remove segment
[normal content continues]
slate order one done  # Next segment
```

### Implementation Details

```python
# In extract_segments_from_markers():
# When we find END marker:
# 1. Check if previous segment has "remove" in commands
# 2. If yes, mark segment for exclusion and continue
# 3. If no, it's sequence end (current behavior)

# In rough cut engine:
# Filter out segments marked with remove=True
```

### Edge Cases

1. **Remove at end of sequence:**
   ```
   slate remove done
   [content]
   slate ending done  # Closes remove AND sequence
   ```
   - Solution: Remove segment is excluded, sequence ends

2. **Multiple remove segments:**
   ```
   slate remove done [content] slate ending done
   slate remove done [content] slate ending done
   slate order one done [content]
   ```
   - Solution: All remove segments excluded, normal segment continues

3. **Remove without ending (implicit end):**
   ```
   slate remove done [content]
   slate order one done [normal content]
   ```
   - Solution: Remove segment implicitly ends at next marker (Option 4 fallback)

---

## Implementation Without Reshooting Fixtures

### Approach 1: Add `ending` Markers in Transcripts
- Edit transcript JSON files
- Add `ending` markers after remove content
- Re-run marker detection

### Approach 2: Post-Process Transcripts
- Script to add `ending` markers after `remove` markers
- Modify transcript JSON before marker detection

### Approach 3: Support Both Explicit and Implicit End
- If `remove` segment has explicit `ending` marker → use it
- If `remove` segment has no `ending` → implicitly end at next marker
- Works with existing fixtures (implicit) and new recordings (explicit)

### Recommended: Approach 3 (Hybrid)
- Best of both worlds
- Works with existing fixtures (no reshoot)
- Supports explicit markers for new recordings
- Flexible and backwards compatible

---

## Code Changes Required

### 1. Marker Detection
- No changes needed (already detects `ending` markers)

### 2. Segment Extraction
```python
# In extract_segments_from_markers():
# When END marker found:
# - Check if previous segment's marker has "remove" command
# - If yes, mark segment with remove=True
# - Continue processing (don't stop sequence)
```

### 3. Rough Cut Engine
```python
# Filter segments:
# segments = [s for s in segments if not s.get('remove', False)]
```

### 4. Parser (No Changes Needed)
- `ending` already parsed as END marker type

---

## Example: Full Workflow

```
slate order one done
[content segment 1]
slate remove done
[mistake content to remove]
slate ending done  # Closes remove segment
slate order two done
[content segment 2]
slate ending done  # Closes sequence
```

Result:
- Segment 1: Included in rough cut
- Remove segment: Excluded from rough cut
- Segment 2: Included in rough cut
- Sequence ends after segment 2

