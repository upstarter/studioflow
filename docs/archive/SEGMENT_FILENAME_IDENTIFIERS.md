# Segment Filename Identifier Options

## Current Pattern
**Format:** `{CAMERA}-{CLIP_NUMBER}-{DESCRIPTOR}-{TYPE}_seg{num:03d}_[order|step].mov`

**Example:** `CAMA-C0176-original-markers_seg001.mov`

## Current Components

1. **Camera identifier:** `CAMA`, `CAMB` (A-cam, B-cam)
2. **Clip number:** `C0176`, `C0030` (camera's clip number)
3. **Descriptor:** `original` (source type)
4. **Type:** `markers`, `no-markers` (has markers or not)

## Identifier Options for Middle Part

### Option A: Current (Descriptive Suffix)
**Format:** `{CAMERA}-{CLIP_NUMBER}-{DESCRIPTOR}-{TYPE}`

**Examples:**
- `CAMA-C0176-original-markers`
- `CAMB-C0030-original-markers`
- `CAMA-C0177-original-no-markers`

**Pros:**
- Clear indication of source and content type
- Descriptive and self-documenting
- Easy to filter (all "original", all "markers")

**Cons:**
- Longer filenames
- Requires consistent naming of source files

---

### Option B: Camera Model
**Format:** `{CAMERA}-{CLIP_NUMBER}-{CAMERA_MODEL}`

**Examples:**
- `CAMA-C0176-FX30`
- `CAMB-C0030-ZVE10`
- `CAMA-C0177-FX30`

**Pros:**
- Identifies camera model (useful for multicam)
- Shorter than current
- Technical but clear

**Cons:**
- Need to determine camera model from metadata
- Less descriptive about content type

---

### Option C: Recording Date
**Format:** `{CAMERA}-{CLIP_NUMBER}-{DATE}`

**Examples:**
- `CAMA-C0176-20260104`
- `CAMB-C0030-20260104`
- `CAMA-C0177-20260104`

**Pros:**
- Chronological organization
- Useful for multi-day shoots
- Standard date format

**Cons:**
- All clips from same day have same date
- Doesn't indicate content type

---

### Option D: Just Camera + Clip (Minimal)
**Format:** `{CAMERA}-{CLIP_NUMBER}`

**Examples:**
- `CAMA-C0176`
- `CAMB-C0030`
- `CAMA-C0177`

**Pros:**
- Shortest option
- Clean and simple
- All essential info

**Cons:**
- No context about source or content
- Harder to distinguish processed vs original
- Less descriptive

---

### Option E: Camera + Clip + Date (Recommended)
**Format:** `{CAMERA}-{CLIP_NUMBER}-{DATE}`

**Examples:**
- `CAMA-C0176-20260104`
- `CAMB-C0030-20260104`
- `CAMA-C0177-20260104`

**Pros:**
- Chronological organization
- Standard format
- Clear camera and clip identification
- Moderate length

**Cons:**
- All clips from same day have same date
- Date may not be available from filename (need metadata)

---

### Option F: Camera + Clip + Scene/Take (If Available)
**Format:** `{CAMERA}-{CLIP_NUMBER}-{SCENE}-{TAKE}`

**Examples:**
- `CAMA-C0176-S01-T01`
- `CAMB-C0030-S01-T01`
- `CAMA-C0177-S02-T03`

**Pros:**
- Production-oriented
- Useful for organized shoots
- Clear scene/take tracking

**Cons:**
- Requires scene/take metadata (may not be available)
- More complex
- Not all clips have this info

---

### Option G: Keep Descriptor, Drop Type
**Format:** `{CAMERA}-{CLIP_NUMBER}-{DESCRIPTOR}`

**Examples:**
- `CAMA-C0176-original`
- `CAMB-C0030-original`
- `CAMA-C0177-edited`

**Pros:**
- Shorter than current
- Still indicates source type
- Flexible for different descriptors

**Cons:**
- Loses marker indicator (but segments themselves show if markers exist)

---

### Option H: Camera + Clip + Episode/Project (If Available)
**Format:** `{CAMERA}-{CLIP_NUMBER}-{PROJECT}`

**Examples:**
- `CAMA-C0176-ep01`
- `CAMB-C0030-ep01`
- `CAMA-C0177-ep02`

**Pros:**
- Project/episode organization
- Useful for series or multi-episode content

**Cons:**
- Requires project/episode context
- May not always be available
- Additional metadata needed

---

## Recommendation Matrix

| Use Case | Best Option | Reason |
|----------|-------------|--------|
| **Minimal, clean filenames** | Option D (Camera + Clip) | Shortest, essential info only |
| **Date-based organization** | Option E (Camera + Clip + Date) | Chronological, standard format |
| **Production workflow** | Option F (Camera + Clip + Scene/Take) | Scene/take tracking |
| **Self-documenting** | Option A (Current) | Most descriptive |
| **Balanced (Recommended)** | Option E or Option G | Good balance of info vs length |

---

## Implementation Considerations

### Date Extraction
- From filename: If filename contains date (e.g., `20260104`)
- From metadata: Extract creation date from video file
- From context: Use project/ingest date
- Fallback: Use current date if not available

### Camera Model Detection
- From metadata: EXIF/metadata in video file
- From filename: Pattern matching (FX30, ZVE10, etc.)
- From config: Camera assignment in project config
- Fallback: Use camera identifier (CAMA, CAMB) if model unknown

### Scene/Take Extraction
- From audio markers: "naming" command (when re-enabled)
- From filename: Pattern matching
- From metadata: Custom metadata fields
- Fallback: Not included if not available

---

## Recommended: **Option E** (Camera + Clip + Date)

### Format
```
{CAMERA}-{CLIP_NUMBER}-{DATE}_seg{num:03d}_[order{order}|step{step}].mov
```

### Examples
```
CAMA-C0176-20260104_seg001.mov
CAMA-C0176-20260104_seg002_order1.mov
CAMA-C0176-20260104_seg003.mov
CAMA-C0176-20260104_seg004.mov
CAMA-C0176-20260104_seg005_step1.mov
CAMA-C0176-20260104_seg006.mov
```

### Benefits
1. ✅ Short and clean
2. ✅ Chronological organization
3. ✅ Standard date format (YYYYMMDD)
4. ✅ All essential identification
5. ✅ Easy to filter by date
6. ✅ Works well with file systems

### Date Source Priority
1. Extract from video file metadata (creation date)
2. Parse from original filename if present
3. Use ingest/project date if available
4. Fallback to current date

