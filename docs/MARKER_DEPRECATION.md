# Marker Deprecation Guide

## Deprecated: "ending" Marker

The `ending` marker has been **deprecated** in favor of using `apply` for all retroactive actions.

### What Changed

**Before (Deprecated):**
- `slate ending conclusion done` - Apply "conclusion" to previous segment
- `slate ending best done` - Score previous segment as "best"
- `slate ending done` - Mark sequence end (no longer needed)

**Now (Use This):**
- `slate apply conclusion done` - Apply "conclusion" to previous segment
- `slate apply best done` - Score previous segment as "best"
- No sequence end marker needed - segments end naturally at next marker or end of video

### Why the Change?

1. **Consistency**: All retroactive actions now use `apply`
2. **Simplicity**: No need for a separate "ending" marker
3. **Natural Flow**: Segments end naturally at the next marker or end of video

### Backwards Compatibility

The `ending` marker still works but will show a deprecation warning:
- `ending` with commands → treated as `apply` (retroactive)
- `ending` alone → does nothing (no longer marks sequence end)

### Migration Guide

**Old Code:**
```
slate ending conclusion done
slate ending best done
slate ending done
```

**New Code:**
```
slate apply conclusion done
slate apply best done
(no marker needed - segments end naturally)
```

### Workarounds Removed

The following workarounds have been removed/cleaned up:

1. **"ending" as sequence end** - No longer needed, segments end naturally
2. **"ending" with commands** - Use "apply" instead
3. **END marker type** - No longer used, only RETROACTIVE, START, and STANDALONE

### Testing

When creating test fixtures:
- ✅ Use `slate apply conclusion done` (not `slate ending conclusion done`)
- ✅ Use `slate apply best done` (not `slate ending best done`)
- ✅ Don't use `slate ending done` - segments end naturally

### Code Changes

- `marker_commands.py`: Added deprecation warning for "ending"
- `audio_markers.py`: "ending" alone no longer creates "end" marker type
- `ULTIMATE_FIXTURE_FOOTAGE.md`: Updated to use "apply" instead of "ending"

