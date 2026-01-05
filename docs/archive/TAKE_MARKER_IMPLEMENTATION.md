# Take Marker Implementation

## Summary

**Changed:** `slate order one done` → `slate take one done`

**Reason:** "Take" is the correct video production terminology for multiple attempts at the same shot. "Order" was ambiguous and not standard industry terminology.

## Implementation

### Code Changes

1. **`marker_commands.py`**: Added "take" parsing alongside "order" (backwards compatible)
   - Both `take` and `order` are recognized
   - Both populate the `order` field (internal storage)
   - "take" is now the recommended keyword

2. **Documentation**: Updated all examples to use "take" instead of "order"

### Backwards Compatibility

- **"order" still works** - existing footage with "order" markers will continue to work
- **"take" is recommended** - new footage should use "take"
- Both keywords produce the same result internally

## Why "Take" is Useful

### 1. Industry Standard Terminology
- Every video professional understands "take"
- Aligns with industry conventions
- Clear semantic meaning

### 2. Organizing Multiple Attempts
```
slate take one done
[First attempt]
slate apply good done

slate take two done
[Second attempt - better]
slate apply best done

slate take three done
[Third attempt - mistake]
slate apply skip done
```

**Benefits:**
- Easy to compare takes
- Track which take was selected
- Organize footage by take number

### 3. Workflow Efficiency
- Quickly identify best take
- Remove unused takes
- Keep backup takes organized
- Understand final edit decisions

### 4. Integration with Scoring
The take number works perfectly with the scoring system:
- Take 1: `apply good` → Keep as backup
- Take 2: `apply best` → Use in final cut
- Take 3: `apply skip` → Remove

System automatically tracks which take was selected based on scores.

## Usage Examples

### Basic Usage
```
slate take one done
[Content]
slate apply good done

slate take two done
[Better content]
slate apply best done
```

### With Other Markers
```
slate shot front take one done
[First take of front shot]
slate apply good done

slate shot front take two done
[Second take of front shot]
slate apply best done
```

### Multiple Takes with Scoring
```
slate take one done [Take 1] slate apply fair done
slate take two done [Take 2] slate apply good done
slate take three done [Take 3] slate apply best done
slate take four done [Take 4] slate apply skip done
```

**Result:**
- Take 3 selected (best)
- Take 2 kept as backup (good)
- Take 1 kept as backup (fair)
- Take 4 removed (skip)

## Migration Guide

### For New Footage
**Use "take" instead of "order":**
- ✅ `slate take one done`
- ❌ `slate order one done` (deprecated)

### For Existing Footage
- Existing "order" markers will continue to work
- No changes needed to existing footage
- Both keywords produce identical results

## Difference from "step"

- **"take"** = Multiple attempts at the same content (take 1, take 2, take 3)
- **"step"** = Sequential steps in a tutorial/process (step 1, step 2, step 3)

**Example:**
```
# Multiple takes of the same hook
slate take one done [Hook attempt 1] slate apply good done
slate take two done [Hook attempt 2] slate apply best done

# Tutorial steps (different content)
slate step one done [Step 1: Setup] slate apply good done
slate step two done [Step 2: Process] slate apply good done
slate step three done [Step 3: Result] slate apply good done
```

## Conclusion

"Take" is the correct terminology and provides clear semantic meaning for multiple attempts at the same content. The implementation maintains backwards compatibility while providing a more professional and intuitive interface.

