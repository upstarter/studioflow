# Duplicate Handling - How StudioFlow Handles File Names

**Understanding how StudioFlow distinguishes between duplicates and different takes**

---

## The Key Distinction

StudioFlow makes an important distinction:

1. **Different Takes** = `(1)`, `(2)`, `(3)` → **KEPT** (all analyzed)
2. **Normalized Duplicates** = `_normalized` suffix → **REMOVED** (if original exists)

---

## How It Works

### Different Takes (KEPT)

These are **NOT duplicates** - they're different recordings:

```
CAM_STEP01_Introduction.mp4          ✅ KEPT
CAM_STEP01_Introduction (1).mp4      ✅ KEPT (different take)
CAM_STEP01_Introduction (2).mp4      ✅ KEPT (different take)
CAM_STEP01_Introduction (3).mp4      ✅ KEPT (different take)
```

**Why:** Each `(1)`, `(2)`, `(3)` represents a different recording attempt. The system analyzes all of them and can pick the best one.

### Normalized Duplicates (REMOVED)

These are **actual duplicates** - same content, just normalized audio:

```
CAM_STEP01_Introduction.mp4          ✅ KEPT (original)
CAM_STEP01_Introduction_normalized.mp4  ❌ REMOVED (duplicate with normalized audio)
```

**Why:** The `_normalized` version is created automatically during analysis. If the original exists, we don't need the normalized version as a separate file (the system normalizes on-the-fly).

---

## Current Logic (in `rough_cut.py`)

```python
# Filter out ONLY normalized versions if original exists
# Keep ALL numbered versions (1), (2), etc. - they're different takes!

# Collect all non-normalized files (including numbered versions)
originals = [vf for vf in video_files if "_normalized" not in vf.stem]

# Always include all originals (including numbered versions like (1), (2))
filtered_files.extend(originals)

# For normalized files, only include if original doesn't exist
for vf in video_files:
    if "_normalized" in vf.stem:
        # Check if original exists (without _normalized, regardless of (1), (2))
        # Only include normalized if no original exists
```

---

## Examples

### Example 1: Multiple Takes (All Kept)

**Files:**
```
CAM_HOOK_COH_Contrarian.mp4
CAM_HOOK_COH_Contrarian (1).mp4
CAM_HOOK_COH_Contrarian (2).mp4
```

**Result:** ✅ All 3 files are kept and analyzed. System can pick the best one.

### Example 2: Normalized Duplicate (Removed)

**Files:**
```
CAM_STEP01_Introduction.mp4
CAM_STEP01_Introduction_normalized.mp4
```

**Result:** 
- ✅ `CAM_STEP01_Introduction.mp4` - KEPT
- ❌ `CAM_STEP01_Introduction_normalized.mp4` - REMOVED (duplicate)

### Example 3: Mixed Scenario

**Files:**
```
CAM_STEP01_Introduction.mp4
CAM_STEP01_Introduction (1).mp4
CAM_STEP01_Introduction (2).mp4
CAM_STEP01_Introduction_normalized.mp4
CAM_STEP01_Introduction (1)_normalized.mp4
```

**Result:**
- ✅ `CAM_STEP01_Introduction.mp4` - KEPT (original)
- ✅ `CAM_STEP01_Introduction (1).mp4` - KEPT (different take)
- ✅ `CAM_STEP01_Introduction (2).mp4` - KEPT (different take)
- ❌ `CAM_STEP01_Introduction_normalized.mp4` - REMOVED (duplicate of original)
- ❌ `CAM_STEP01_Introduction (1)_normalized.mp4` - REMOVED (duplicate of take 1)

---

## Best Practices

### ✅ DO: Use Numbered Takes for Retakes

```
# Record multiple attempts
CAM_STEP01_Introduction.mp4          # First attempt
CAM_STEP01_Introduction (1).mp4       # Retake 1
CAM_STEP01_Introduction (2).mp4       # Retake 2
CAM_STEP01_Introduction_BEST.mp4     # Best take (marked)
```

**All will be analyzed, system picks best based on quality scores.**

### ✅ DO: Mark Best Takes

```
CAM_STEP01_Introduction_BEST.mp4     # Highest priority
CAM_STEP01_Introduction (1).mp4       # Backup option
```

**System prioritizes `_BEST` marked files.**

### ❌ DON'T: Manually Create Normalized Files

```
# Don't do this manually:
CAM_STEP01_Introduction.mp4
CAM_STEP01_Introduction_normalized.mp4  # System creates this automatically
```

**The system normalizes audio automatically during analysis. You don't need to create normalized versions manually.**

---

## Import Process

### During Import (`sf import`)

The import process:
1. **Copies files** to project directory
2. **Preserves original names** (including `(1)`, `(2)`, etc.)
3. **Tracks checksums** to prevent duplicate imports from same source

**Numbered takes are preserved as-is.**

### During Analysis (`sf rough-cut`)

The analysis process:
1. **Finds all video files** (including numbered takes)
2. **Filters out `_normalized` duplicates** (if original exists)
3. **Keeps all numbered takes** `(1)`, `(2)`, etc.
4. **Normalizes audio** automatically (creates `_normalized` versions if needed)
5. **Analyzes all kept files**

---

## FAQ

### Q: Will `(1)`, `(2)` break the deduplication?

**A: No!** Numbered takes are intentionally kept. They're not duplicates - they're different recordings.

### Q: What if I have both `(1)` and `_normalized`?

**A:** The system handles it correctly:
- `CAM_STEP01_Introduction (1).mp4` → ✅ KEPT (different take)
- `CAM_STEP01_Introduction (1)_normalized.mp4` → ❌ REMOVED (duplicate of take 1)

### Q: Should I rename files before or after import?

**A:** Either works! But it's easier to rename after import:
1. Import files (keeps original FX30 names)
2. Use `rename_fx30_clips.py` to rename
3. Run `sf rough-cut` (handles everything correctly)

### Q: What about files with both `(1)` and `_BEST`?

**A:** Both markers work together:
- `CAM_STEP01_Introduction (1)_BEST.mp4` → ✅ KEPT (take 1, marked as best)
- System prioritizes `_BEST` files

---

## Summary

**Numbered Takes `(1)`, `(2)`, etc.:**
- ✅ Always kept
- ✅ Treated as different files
- ✅ All analyzed
- ✅ System picks best based on quality

**Normalized Files `_normalized`:**
- ❌ Removed if original exists
- ✅ Created automatically during analysis
- ✅ Don't create manually

**Your workflow is safe!** Use `(1)`, `(2)`, etc. for retakes - they won't be removed as duplicates.



