# How Segments End - Complete Guide

## Overview

**Segments end automatically** - you don't need explicit "end" markers. The next marker's "slate" timestamp automatically becomes the end point of the previous segment.

## How It Works

### Automatic Ending

1. **Segment starts** at the `cut_point` of a marker (after "done")
2. **Segment ends** at the next marker's "slate" timestamp (before the next "slate")
3. **Last segment** extends to the end of the video

### Example

```
0:05  slate scene one intro done     → Segment 001 starts
0:10  [Content: "Introduction..."]   → Segment 001 continues
0:20  slate scene two main done      → Segment 001 ENDS at 0:20, Segment 002 starts
0:25  [Content: "Main content..."]   → Segment 002 continues
0:40  slate step one setup done      → Segment 002 ENDS at 0:40, Segment 003 starts
```

**Key Point**: Segment 001 ends at 0:20 (when "slate" is said for scene two), not when scene two's "done" is said.

## Ending Different Types

### Ending a Shot

A "shot" is a segment created by any marker. To end a shot:

**Just start the next shot** - the next marker automatically ends the previous one.

```
slate mark done
[Content for shot 1]
slate effect zoom done          ← Shot 1 ends here (at "slate"), Shot 2 starts
[Content for shot 2]
```

### Ending a Take

A "take" is multiple attempts at the same scene. Each take creates its own segment:

```
slate scene one take one done
[Content for take 1]
slate scene one take two done    ← Take 1 ends here, Take 2 starts
[Content for take 2]
```

**Note**: Takes are grouped under the same scene number but are separate segments.

### Ending a Scene

A "scene" is organized by scene number. To end a scene:

**Start the next scene** - the next scene marker automatically ends the previous scene.

```
slate scene one intro done
[Content for scene 1]
slate scene two main done        ← Scene 1 ends here, Scene 2 starts
[Content for scene 2]
```

### Ending a Sequence

A "sequence" is the entire recording. To end a sequence:

**Just stop recording** - the last segment automatically extends to the end of the video.

```
slate scene one intro done
[Content for scene 1]
slate scene two main done
[Content for scene 2]
[More content...]                ← Scene 2 continues until video ends
[End of video]                   ← Scene 2 ends here automatically
```

## Visual Timeline

```
Timeline: 0:00 ────────────────────────────────────────── 2:00

0:05  [slate] scene one intro [done]
      └─ Segment 001 starts here
      
0:10  [Content: "Introduction content..."]
      
0:20  [slate] scene two main [done]
      └─ Segment 001 ENDS here (at "slate" timestamp)
      └─ Segment 002 starts here
      
0:25  [Content: "Main content..."]
      
0:40  [slate] step one setup [done]
      └─ Segment 002 ENDS here
      └─ Segment 003 starts here
      
0:45  [Content: "Setup step..."]
      
2:00  [End of video]
      └─ Segment 003 ENDS here automatically
```

## Common Patterns

### Pattern 1: Sequential Scenes

```
slate scene one intro done
[Content]
slate scene two main done        ← Scene 1 ends
[Content]
slate scene three conclusion done ← Scene 2 ends
[Content]
[End of video]                  ← Scene 3 ends
```

### Pattern 2: Multiple Takes

```
slate scene one take one done
[Content]
slate scene one take two done    ← Take 1 ends
[Content]
slate apply best done            ← Retroactive: scores take 2 as "best"
slate scene two main done        ← Take 2 ends
[Content]
```

### Pattern 3: Steps Within a Scene

```
slate scene one intro done
[Content]
slate step one setup done        ← Scene 1 continues (same scene, different step)
[Content]
slate step two execute done      ← Step 1 ends
[Content]
slate scene two main done        ← Step 2 ends, Scene 2 starts
[Content]
```

### Pattern 4: Effects and Transitions

```
slate scene one intro done
[Content]
slate effect zoom done           ← Scene 1 ends, effect segment starts
[Content with zoom effect]
slate transition fade done       ← Effect segment ends, transition segment starts
[Content with fade transition]
slate scene two main done        ← Transition segment ends, Scene 2 starts
[Content]
```

## Important Rules

### ✅ DO

- **Start the next segment** to end the current one
- **Let the last segment extend** to the end of the video
- **Use "apply"** for retroactive actions (doesn't end segments)

### ❌ DON'T

- **Don't use "ending"** - it's deprecated
- **Don't try to explicitly end** - segments end automatically
- **Don't worry about sequence end** - the video end handles it

## Edge Cases

### What if there's a gap between segments?

If you have content between markers, that content belongs to the previous segment:

```
slate scene one done
[Content A]
[Silence or pause]
[Content B]
slate scene two done              ← Segment ends here, includes Content A, silence, and Content B
```

### What if you want to skip content?

Use retroactive markers to mark segments to skip:

```
slate scene one done
[Content you want to skip]
slate apply skip done            ← Marks previous segment to skip (doesn't end it)
slate scene two done             ← Scene 1 ends here, Scene 2 starts
```

### What if you want to end early?

You can't explicitly end a segment early. Segments always extend to the next marker. If you need to cut content, use retroactive markers or edit manually.

## Summary

**The Golden Rule**: **The next marker automatically ends the previous segment.**

- No explicit "end" markers needed
- Segments end at the next marker's "slate" timestamp
- Last segment extends to end of video
- Use "apply" for retroactive actions (doesn't end segments)

This makes the workflow simple: just start the next thing, and the previous thing ends automatically!

