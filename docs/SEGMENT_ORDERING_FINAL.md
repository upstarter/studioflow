# Segment Ordering: Final Implementation

## Answer to Your Question

**Q: Do we respect chronological order but override with scene numbers?**

**A: Yes, exactly!** Scene numbers override chronological order for rough cut assembly.

## How It Works

### Sorting Priority

1. **Scene Number** (ascending) - Primary sort key
2. **Take** (ascending) - Secondary sort key (if same scene_number)
3. **Timestamp** (chronological) - Tertiary sort key (if no scene_number or same scene/take)

### Example Scenario

**Recording Order (Chronological):**
```
0:00  - Scene 1
1:00  - Scene 2
2:00  - Scene 4
3:00  - Scene 5
4:00  - Scene 3 (inserted later)
5:00  - Scene 1.5 (inserted between 1 and 2)
```

**Rough Cut Order (Sorted by scene_number):**
```
Scene 1
Scene 1.5
Scene 2
Scene 3
Scene 4
Scene 5
```

## Is This Optimal?

**Yes, this is optimal!** Here's why:

### ✅ Benefits

1. **Flexible Shooting** - Record scenes in any order
2. **Easy Insertions** - Add scenes between existing ones using decimals
3. **Multiple Takes** - All takes of same scene grouped together
4. **Backwards Compatible** - Chronological order if no scene number
5. **Industry Standard** - Scene numbering is standard in video production

### ✅ Use Cases Supported

1. **Sequential Recording** - Record 1, 2, 3, 4, 5 → Works perfectly
2. **Out of Order** - Record 1, 2, 4, 5, then 3 → Sorted correctly
3. **Insertions** - Record 1, 2, then insert 1.5 → Placed correctly
4. **Multiple Takes** - Record take 1, take 2, take 3 → Grouped by scene, ordered by take

### ✅ Edge Cases Handled

- **Unnumbered segments** - Use chronological order (go to end)
- **Mixed numbered/unnumbered** - Numbered first, then unnumbered chronologically
- **Multiple takes** - Grouped by scene, ordered by take number
- **Decimal insertions** - Correctly ordered (1, 1.25, 1.5, 2)

## Implementation

**Code Location:** `studioflow/core/audio_markers.py`

**Function:** `_sort_segments_for_rough_cut()`

**Sort Key:**
```python
(scene_number or inf, take or 0, start_timestamp)
```

**Result:**
- Scene numbers control order
- Takes are grouped within scenes
- Chronological order for unnumbered segments

## Real-World Example

**Day 1: Record main scenes**
```
slate scene one intro done
slate scene two main done
slate scene four demo done
slate scene five outro done
```

**Day 2: Insert missing scene**
```
slate scene three middle done  # Goes between 2 and 4
```

**Day 3: Add transition**
```
slate scene one point five transition done  # Goes between 1 and 2
```

**Day 4: Retake scene 1**
```
slate scene one intro take two done  # Groups with scene 1, take 1
```

**Final Rough Cut Order:**
1. Scene 1, Take 1
2. Scene 1, Take 2
3. Scene 1.5 (transition)
4. Scene 2
5. Scene 3
6. Scene 4
7. Scene 5

## Conclusion

**This is optimal because:**
- ✅ Scene numbers give explicit control
- ✅ Supports all real-world workflows
- ✅ Backwards compatible
- ✅ Industry standard approach
- ✅ Handles all edge cases

**No changes needed** - the current implementation is optimal for your use case!


