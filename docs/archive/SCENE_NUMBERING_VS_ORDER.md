# Scene Numbering vs Order: Analysis

## User's Insight

**Question:** Do we need both "order" and "scene"? Could we just use decimal scene numbers?

**Suggestion:** Use scene numbers with decimals for insertion:
- `scene 1` (first scene)
- `scene 1.5` (inserted between scene 1 and 2)
- `scene 2` (second scene)
- `scene 1.6` (inserted between scene 1.5 and 1.7)
- `scene 1.7` (inserted between scene 1.6 and 2)

## Analysis

### Current State
- "scene" is used with names: `slate scene intro done`
- "order" is used separately: `slate order one done`
- Both can be combined: `slate scene intro order one done`

### Proposed Change
- Use scene numbers directly: `slate scene one done`, `slate scene one point five done`
- Decimal numbers for insertion: `slate scene one point five done`
- Eliminate separate "order" keyword

## Comparison

### Option 1: Keep Both (Current)
```
slate scene intro order one done
slate scene middle order three done
slate scene outro order five done
```

**Pros:**
- Named scenes (intro, middle, outro)
- Explicit ordering separate from naming

**Cons:**
- Two keywords to manage
- Redundant information
- More complex

### Option 2: Decimal Scene Numbers (Proposed)
```
slate scene one intro done
slate scene one point five middle done
slate scene two outro done
```

**Pros:**
- Single keyword (scene)
- Natural ordering (1, 1.5, 2)
- Easy insertion with decimals
- Simpler mental model
- Industry standard (scene numbers)

**Cons:**
- Need to parse decimal numbers ("one point five")
- Slightly longer to say

### Option 3: Hybrid (Scene Number + Name)
```
slate scene one intro done
slate scene one point five middle done
slate scene two outro done
```

**Pros:**
- Scene number for ordering
- Optional name for identification
- Best of both worlds

**Cons:**
- Still need to parse decimals

## Recommendation: Option 3 (Hybrid)

Use scene numbers with optional names:
- `slate scene one done` - Scene 1, no name
- `slate scene one intro done` - Scene 1, named "intro"
- `slate scene one point five done` - Scene 1.5, no name
- `slate scene one point five middle done` - Scene 1.5, named "middle"

**Benefits:**
1. **Natural ordering** - Scene numbers determine sequence
2. **Easy insertion** - Use decimals (1.5, 1.6, 1.7)
3. **Optional naming** - Can name scenes for clarity
4. **Eliminates "order"** - No separate keyword needed
5. **Industry standard** - Scene numbers are standard in video production

## Implementation

### Parse Scene Numbers
- Integer: `scene one` → scene_number: 1
- Decimal: `scene one point five` → scene_number: 1.5
- With name: `scene one intro` → scene_number: 1, scene_name: "intro"
- Decimal with name: `scene one point five middle` → scene_number: 1.5, scene_name: "middle"

### Ordering Logic
- Sort by scene_number (1, 1.5, 2, 2.3, etc.)
- Scene number determines position in final sequence
- No need for separate "order" keyword

## Examples

### Example 1: Sequential Scenes
```
slate scene one intro done
[Scene 1]
slate apply good done

slate scene two main done
[Scene 2]
slate apply good done

slate scene three outro done
[Scene 3]
slate apply good done
```

### Example 2: Insert Scene Between 1 and 2
```
slate scene one intro done
[Scene 1]
slate apply good done

slate scene two main done
[Scene 2]
slate apply good done

# Later: Insert scene between 1 and 2
slate scene one point five transition done
[Scene 1.5 - inserted between 1 and 2]
slate apply good done
```

### Example 3: Multiple Insertions
```
slate scene one done
slate scene one point five done
slate scene one point six done
slate scene one point seven done
slate scene two done
```

**Result:** Ordered as 1 → 1.5 → 1.6 → 1.7 → 2

### Example 4: Multiple Takes with Scene Numbers
```
slate scene one intro take one done
[Scene 1, Take 1]
slate apply good done

slate scene one intro take two done
[Scene 1, Take 2]
slate apply best done

slate scene one point five transition take one done
[Scene 1.5, Take 1]
slate apply good done
```

## Migration

### From "order" to Scene Numbers
**Before:**
```
slate scene intro order one done
slate scene middle order three done
```

**After:**
```
slate scene one intro done
slate scene three middle done
```

### Backwards Compatibility
- Keep "order" as deprecated alias
- Map "order" to scene_number if scene_number not set
- Gradually migrate to scene numbers

## Conclusion

**Yes, we can eliminate "order" by using decimal scene numbers!**

This is:
- ✅ Simpler (one keyword instead of two)
- ✅ More intuitive (scene numbers are standard)
- ✅ More flexible (easy insertion with decimals)
- ✅ Industry standard (scene numbering is common)

**Recommendation:** Implement scene number parsing with decimal support, eliminate "order" keyword.

