# Scene Numbering Guide

## Overview

Use **scene numbers** (with optional decimal points) to specify position in the final sequence. This eliminates the need for a separate "order" keyword.

## Basic Usage

### Integer Scene Numbers
```
slate scene one done
[Scene 1]
slate apply good done

slate scene two done
[Scene 2]
slate apply good done

slate scene three done
[Scene 3]
slate apply good done
```

**Result:** Scenes ordered as 1 → 2 → 3

### Decimal Scene Numbers (Insertion)

Insert scenes between existing scenes using decimals:

```
slate scene one done
[Scene 1]
slate apply good done

slate scene two done
[Scene 2]
slate apply good done

# Later: Insert scene between 1 and 2
slate scene one point five done
[Scene 1.5 - inserted between 1 and 2]
slate apply good done
```

**Result:** Scenes ordered as 1 → 1.5 → 2

### Multiple Insertions

You can insert multiple scenes with different decimal values:

```
slate scene one done
slate scene one point five done
slate scene one point six done
slate scene one point seven done
slate scene two done
```

**Result:** Ordered as 1 → 1.5 → 1.6 → 1.7 → 2

## Scene Names (Optional)

Add optional names to scenes for clarity:

### Scene Number Only
```
slate scene one done
```

### Scene Number + Name
```
slate scene one intro done
slate scene one point five transition done
slate scene two main done
```

**Benefits:**
- Scene number determines order
- Name helps identify scene content
- Both stored separately

## Combining with Takes

Use scene numbers with takes for multiple attempts:

```
slate scene one intro take one done
[Scene 1, Take 1]
slate apply good done

slate scene one intro take two done
[Scene 1, Take 2 - better]
slate apply best done

slate scene one point five transition take one done
[Scene 1.5, Take 1]
slate apply good done
```

**Result:**
- Scene 1: Multiple takes, best selected
- Scene 1.5: Single take
- Final order: Scene 1 (best take) → Scene 1.5

## Real-World Examples

### Example 1: Shooting Out of Order

**Day 1: Shoot scenes 1, 2, 4, 5**
```
slate scene one intro done
[Scene 1]
slate apply good done

slate scene two setup done
[Scene 2]
slate apply good done

slate scene four demo done
[Scene 4]
slate apply good done

slate scene five outro done
[Scene 5]
slate apply good done
```

**Day 2: Insert scene 3 between 2 and 4**
```
slate scene three middle done
[Scene 3 - inserted between 2 and 4]
slate apply good done
```

**Result:** System assembles as 1 → 2 → 3 → 4 → 5

### Example 2: Multiple Insertions

**Initial shoot:**
```
slate scene one done
slate scene two done
slate scene three done
```

**Later additions:**
```
slate scene one point five done  # Between 1 and 2
slate scene two point five done  # Between 2 and 3
slate scene one point two five done  # Between 1.5 and 2 (1.25)
```

**Result:** Ordered as 1 → 1.25 → 1.5 → 2 → 2.5 → 3

### Example 3: Complex Workflow

```
# Scene 1: Multiple takes
slate scene one intro take one done
slate apply good done
slate scene one intro take two done
slate apply best done

# Scene 1.5: Inserted transition
slate scene one point five transition done
slate apply good done

# Scene 2: Main content
slate scene two main done
slate apply good done

# Scene 1.6: Another insertion
slate scene one point six broll done
slate apply good done
```

**Result:**
- Scene 1: Best take selected
- Scene 1.5: Transition
- Scene 1.6: B-roll
- Scene 2: Main content
- Final order: 1 → 1.5 → 1.6 → 2

## How to Say Decimal Numbers

When recording, say decimal numbers naturally:

- `scene one point five` → 1.5
- `scene two point three` → 2.3
- `scene one point two five` → 1.25
- `scene three point one four` → 3.14

**Note:** The system parses "point" as the decimal separator.

## Migration from "order"

### Before (using "order")
```
slate scene intro order one done
slate scene middle order three done
```

### After (using scene numbers)
```
slate scene one intro done
slate scene three middle done
```

**Benefits:**
- One keyword instead of two
- Natural ordering (scene numbers)
- Easy insertion (decimals)
- Industry standard

## Best Practices

1. **Start with integers** - Use scene 1, 2, 3 for initial shoot
2. **Use decimals for insertions** - Add 1.5, 1.6, etc. when inserting
3. **Add names for clarity** - `scene one intro` is clearer than `scene one`
4. **Be consistent** - Use same pattern throughout project
5. **Use takes for multiple attempts** - `scene one take one`, `scene one take two`

## Summary

- **Scene numbers** = Position in sequence (1, 1.5, 2, etc.)
- **Scene names** = Optional identifier (intro, main, outro)
- **Takes** = Multiple attempts at same scene
- **No "order" needed** - Scene number handles ordering

This approach is simpler, more intuitive, and aligns with industry standards!

