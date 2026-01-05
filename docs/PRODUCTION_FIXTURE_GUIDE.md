# Production Fixture Guide

## Overview

The **Production Fixture** is a comprehensive, production-like test footage that simulates real-world YouTube episode recording sessions. It's designed to test the marker system under realistic conditions with many edge cases.

## Why Production Fixture?

### Real-World Testing
- **5-10 minutes** of continuous recording (vs. 30-60 seconds)
- **45+ segments** (vs. 6 segments)
- **15+ retroactive actions** throughout
- **Multiple takes** of same scenes
- **Edge cases** that occur in real recording sessions

### Comprehensive Coverage
- Tests **all marker types** in realistic patterns
- Tests **segment organization** with many segments
- Tests **edge cases** (rapid markers, gaps, complex scenarios)
- Tests **production workflows** (hooks, intros, main content, outros)

## Quick Start

### 1. Get the Script
```bash
python3 scripts/create_production_fixture.py script > production_script.txt
```

### 2. Record the Footage
- Follow the script exactly
- Record **5-10 minutes** (13 minutes ideal)
- Include the **10-second pause** (don't skip it!)
- Do the **rapid markers** section quickly (3 marks in ~4 seconds)

### 3. Save the File
Save as: `tests/fixtures/test_footage/PRODUCTION-FIXTURE-comprehensive-episode.MP4`

### 4. Test It
```bash
python3 test_unified_pipeline_fixtures.py
```

## What It Tests

### Production Patterns
1. **Hook Recording** - 5 takes with scoring (best, skip, good)
2. **Intro Sequence** - With branding and preview steps
3. **Main Content** - Multiple scenes with teaching steps
4. **Transitions** - Between content blocks
5. **Advanced Content** - With demonstrations and effects
6. **Recap Sequence** - Summary and next steps
7. **CTA and Outro** - Multiple takes with scoring

### Edge Cases
1. **Rapid Markers** - 3 marks in ~4 seconds
2. **Long Gaps** - 10+ seconds of silence
3. **Multiple Retroactive Actions** - 4+ "apply" markers on same segment
4. **Decimal Scene Numbers** - Scene 6.5 between Scene 6 and Scene 7
5. **Deprecated Features** - "order" marker (backwards compatible)
6. **Complex Scoring** - Best, good, skip on different takes
7. **All Marker Types** - Effects, transitions, titles, screens, chapters, emotions, energy

## Expected Results

### Segments
- **45+ segments** created
- **Scene 1**: 5 takes (001-005)
- **Scene 11**: 3 takes (042-044)
- **Decimal scenes**: Scene 6.5 sorts correctly
- **Last segment**: Extends to video end

### Retroactive Actions
- **15+ actions** applied
- **Multiple actions** on same segment work
- **Scores** applied correctly (best, good, skip)
- **Hooks, quotes, conclusions** applied correctly

### Organization
- Segments sorted by **scene_number** (primary)
- Takes grouped under **same scene**
- Decimal scenes sort **correctly**
- Chronological order within **same scene/take**

## Validation

After recording, verify:

1. **File**: 5-10 minutes long, named correctly
2. **Content**: All markers spoken clearly
3. **Edge Cases**: Long pause included, rapid markers done quickly
4. **Test Results**: 45+ segments, all markers detected, edge cases pass

## Helper Commands

```bash
# Get the script
python3 scripts/create_production_fixture.py script

# Get validation checklist
python3 scripts/create_production_fixture.py checklist

# Get quick reference
python3 scripts/create_production_fixture.py reference

# Get edge cases summary
python3 scripts/create_production_fixture.py edgecases
```

## Full Specification

See `tests/docs/PRODUCTION_FIXTURE_FOOTAGE.md` for the complete specification with:
- Detailed timeline
- All marker commands
- Expected segment organization
- Edge case descriptions
- Validation checklist

---

**This fixture is production-ready and tests the system under realistic conditions!** 🎥✨

