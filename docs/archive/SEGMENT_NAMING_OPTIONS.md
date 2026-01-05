# Segment Naming Options

## Requirements
1. Easy to identify with random footage
2. Respect order/step when specified
3. Include chronological order (segment number) if not specified
4. Human-readable and sortable

## Available Information
- Clip name/stem (e.g., `CAMA-C0176-original-markers`)
- Segment number (chronological, 1-based)
- Order (if specified, e.g., `1`, `2`)
- Step (if specified, e.g., `1`, `2`)
- Marker type (`start`, `standalone`, `end`)
- Commands (original commands from marker)

## Naming Options

### Option 1: Segment Number + Order/Step (Current)
**Format:** `segment_{num:03d}_{type}_{order_or_step}.mov`

**Examples:**
- `segment_001_standalone.mov`
- `segment_order_1.mov`
- `segment_step_1.mov`

**Pros:**
- Simple
- Chronological order preserved

**Cons:**
- No clip identifier
- "standalone" doesn't indicate order in sequence
- Mixed format (sometimes has number, sometimes not)

---

### Option 2: Clip Name + Segment Number + Order/Step
**Format:** `{clip_stem}_seg{num:03d}_{order_or_step_info}.mov`

**Examples:**
- `CAMA-C0176-original-markers_seg001_order_1.mov`
- `CAMA-C0176-original-markers_seg002_standalone.mov`
- `CAMA-C0176-original-markers_seg003_step_1.mov`

**Pros:**
- Includes clip identifier
- Always has segment number
- Clear order/step indication

**Cons:**
- Longer filenames

---

### Option 3: Chronological Number First, Then Order/Step
**Format:** `{clip_stem}_seg{num:03d}_order{order}.mov` or `_step{step}.mov` or `_mark{num}.mov`

**Examples:**
- `CAMA-C0176-original-markers_seg001.mov` (standalone, no order/step)
- `CAMA-C0176-original-markers_seg002_order1.mov`
- `CAMA-C0176-original-markers_seg003.mov` (standalone)
- `CAMA-C0176-original-markers_seg004_order2.mov`
- `CAMA-C0176-original-markers_seg005_step1.mov`
- `CAMA-C0176-original-markers_seg006.mov` (standalone)

**Pros:**
- Always has segment number (chronological)
- Optional order/step suffix
- Short and clean

**Cons:**
- Standalone segments just have number (no distinction)

---

### Option 4: Order/Step Priority, Segment Number Fallback
**Format:** `{clip_stem}_order{order:02d}.mov` or `_step{step:02d}.mov` or `_seg{num:03d}.mov`

**Examples:**
- `CAMA-C0176-original-markers_seg001.mov` (standalone)
- `CAMA-C0176-original-markers_order01.mov`
- `CAMA-C0176-original-markers_seg003.mov` (standalone)
- `CAMA-C0176-original-markers_order02.mov`
- `CAMA-C0176-original-markers_step01.mov`
- `CAMA-C0176-original-markers_seg006.mov` (standalone)

**Pros:**
- Order/step segments use meaningful names
- Segment number for standalone
- Sorts well (order/step first, then segments)

**Cons:**
- Mixed naming scheme
- Harder to see chronological order

---

### Option 5: Always Segment Number + Optional Order/Step
**Format:** `{clip_stem}_seg{num:03d}_[order{order}|step{step}].mov`

**Examples:**
- `CAMA-C0176-original-markers_seg001.mov` (standalone, no order/step)
- `CAMA-C0176-original-markers_seg002_order1.mov`
- `CAMA-C0176-original-markers_seg003.mov` (standalone)
- `CAMA-C0176-original-markers_seg004_order2.mov`
- `CAMA-C0176-original-markers_seg005_step1.mov`
- `CAMA-C0176-original-markers_seg006.mov` (standalone)

**Pros:**
- Always has segment number (chronological order)
- Optional order/step suffix when available
- Clean and consistent
- Easy to sort chronologically

**Cons:**
- None significant

---

## Recommendation: **Option 5**

This option provides:
1. ✅ Clip identifier (easy to identify)
2. ✅ Always has segment number (chronological order)
3. ✅ Optional order/step suffix when specified
4. ✅ Clean, consistent format
5. ✅ Easy to sort and identify

### Implementation
```python
# Generate segment filename
clip_stem = test_clip.stem  # e.g., "CAMA-C0176-original-markers"
seg_num = i  # 1-based segment number

if seg["marker_info"].get("order") is not None:
    seg_name = f"{clip_stem}_seg{seg_num:03d}_order{seg['marker_info']['order']}"
elif seg["marker_info"].get("step") is not None:
    seg_name = f"{clip_stem}_seg{seg_num:03d}_step{seg['marker_info']['step']}"
else:
    seg_name = f"{clip_stem}_seg{seg_num:03d}"

output_segment = segments_dir / f"{seg_name}.mov"
```

### Example Output
```
CAMA-C0176-original-markers_seg001.mov
CAMA-C0176-original-markers_seg002_order1.mov
CAMA-C0176-original-markers_seg003.mov
CAMA-C0176-original-markers_seg004.mov
CAMA-C0176-original-markers_seg005_step1.mov
CAMA-C0176-original-markers_seg006.mov
```

