# Segment Ordering Analysis

## Current State

**Question:** Do we respect chronological order but override with scene numbers?

**Current Implementation:**
- Segments are extracted in chronological order (sorted by timestamp)
- No sorting by `scene_number` is currently implemented
- Segments are returned in the order they appear in the video

## The Problem

**Scenario:**
1. Day 1: Record scenes 1, 2, 4, 5 chronologically
2. Day 2: Record scene 3 (inserted between 2 and 4)

**Current Behavior:**
- Segments returned in chronological order: 1, 2, 4, 5, 3
- Scene 3 appears at the end, not between 2 and 4

**Desired Behavior:**
- Segments sorted by scene_number: 1, 2, 3, 4, 5
- Scene 3 appears in correct position

## Optimal Ordering Logic

### Option 1: Scene Number Priority (Recommended)

**Logic:**
1. If `scene_number` is present → Sort by `scene_number` (ascending)
2. If `scene_number` is None → Fall back to chronological order (timestamp)
3. Within same `scene_number` → Sort by `take` (if present), then chronological

**Implementation:**
```python
def sort_segments_for_rough_cut(segments):
    """Sort segments for rough cut assembly"""
    return sorted(
        segments,
        key=lambda s: (
            s["marker_info"].get("scene_number") or float('inf'),  # Scene number first
            s["marker_info"].get("take") or 0,  # Then take number
            s["start"]  # Finally chronological
        )
    )
```

**Benefits:**
- ✅ Explicit control over sequence order
- ✅ Supports shooting out of order
- ✅ Supports inserting scenes
- ✅ Falls back to chronological if no scene number
- ✅ Handles multiple takes of same scene

**Example:**
```
Chronological order: Scene 1 (0:00), Scene 2 (1:00), Scene 4 (2:00), Scene 5 (3:00), Scene 3 (4:00)
Sorted by scene_number: Scene 1, Scene 2, Scene 3, Scene 4, Scene 5
```

### Option 2: Chronological Only

**Logic:**
- Always use chronological order (timestamp)
- Ignore scene numbers for ordering

**Problems:**
- ❌ Can't shoot out of order
- ❌ Can't insert scenes later
- ❌ Scene numbers become meaningless for ordering

### Option 3: Hybrid (Scene Number + Chronological)

**Logic:**
- Sort by scene_number first
- Within same scene_number, sort chronologically
- Segments without scene_number go at end (chronological)

**Benefits:**
- ✅ Scene numbers control order
- ✅ Chronological within same scene
- ✅ Handles segments without scene numbers

**Example:**
```
Scene 1 (0:00)
Scene 1 (0:30) - retake
Scene 2 (1:00)
Scene 1.5 (1:30) - inserted
Scene 3 (2:00)

Sorted:
- Scene 1 (0:00) - first chronologically
- Scene 1 (0:30) - second chronologically
- Scene 1.5 (1:30)
- Scene 2 (1:00)
- Scene 3 (2:00)
```

## Recommendation: Option 1 (Scene Number Priority)

**Why:**
1. **Explicit Control** - Scene numbers give explicit control over sequence
2. **Flexibility** - Supports shooting out of order and inserting scenes
3. **Industry Standard** - Scene numbers are standard in video production
4. **Backwards Compatible** - Falls back to chronological if no scene number

**Implementation Priority:**
1. Sort by `scene_number` (ascending)
2. If same `scene_number`, sort by `take` (ascending)
3. If no `scene_number`, use chronological order (timestamp)
4. Segments without `scene_number` go after numbered scenes (or can be mixed)

## Edge Cases

### Case 1: Mixed Numbered and Unnumbered
```
Scene 1 (0:00)
Unnumbered segment (0:30)
Scene 2 (1:00)
```

**Options:**
- A: Unnumbered segments go at end (after all numbered)
- B: Unnumbered segments maintain chronological position
- **Recommendation:** Option B (maintain chronological position)

### Case 2: Multiple Takes of Same Scene
```
Scene 1 take 1 (0:00)
Scene 1 take 2 (0:30)
Scene 1 take 3 (1:00)
```

**Sorting:**
- By scene_number: 1
- By take: 1, 2, 3
- Result: All takes grouped together, ordered by take number

### Case 3: Decimal Insertions
```
Scene 1 (0:00)
Scene 2 (1:00)
Scene 1.5 (2:00) - inserted later
Scene 1.25 (2:30) - inserted even later
```

**Sorting:**
- By scene_number: 1.0, 1.25, 1.5, 2.0
- Result: Correct order regardless of recording time

## Implementation

**Location:** Should be in rough cut engine or segment extraction

**Code:**
```python
def order_segments_for_rough_cut(segments: List[Dict]) -> List[Dict]:
    """
    Order segments for rough cut assembly.
    
    Priority:
    1. scene_number (ascending)
    2. take (ascending, if same scene_number)
    3. start timestamp (chronological, if no scene_number or same scene/take)
    """
    def sort_key(seg):
        marker_info = seg.get("marker_info", {})
        scene_num = marker_info.get("scene_number")
        take = marker_info.get("take")
        start = seg.get("start", 0)
        
        # If scene_number exists, use it; otherwise use large number to push to end
        scene_sort = scene_num if scene_num is not None else float('inf')
        
        # Take number (0 if not present)
        take_sort = take if take is not None else 0
        
        return (scene_sort, take_sort, start)
    
    return sorted(segments, key=sort_key)
```

## Conclusion

**Optimal Approach:**
- ✅ Sort by `scene_number` first (ascending)
- ✅ Then by `take` (if same scene_number)
- ✅ Then by timestamp (chronological)
- ✅ Segments without `scene_number` use timestamp only

**This allows:**
- Shooting scenes in any order
- Inserting scenes between existing ones
- Multiple takes of same scene
- Backwards compatibility (chronological if no scene number)

