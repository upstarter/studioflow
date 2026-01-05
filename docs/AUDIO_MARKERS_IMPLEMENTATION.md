# Audio Markers: Implementation Guide

Technical implementation guide for developers working on the audio marker system.

## Architecture Overview

The audio marker system consists of three main components:

1. **Marker Detection** (`audio_markers.py`) - Detects markers from transcripts
2. **Command Parsing** (`marker_commands.py`) - Parses commands into structured data
3. **Segment Extraction** (`audio_markers.py`) - Extracts segments from markers

## Core Components

### AudioMarkerDetector

**Location:** `studioflow/core/audio_markers.py`

**Responsibilities:**
- Detect "slate" and "done" keywords in transcripts
- Handle Whisper transcription variations
- Classify marker types (START, END, RETROACTIVE, STANDALONE)
- Calculate cut points with padding

**Key Methods:**
- `detect_markers()` - Main detection method
- `_classify_marker_type()` - Classify marker type
- `_calculate_cut_point()` - Calculate precise cut points
- `extract_segments_from_markers()` - Extract segments

### MarkerCommandParser

**Location:** `studioflow/core/marker_commands.py`

**Responsibilities:**
- Parse commands between "slate" and "done"
- Normalize commands (case-insensitive, fuzzy matching)
- Extract structured data (scene numbers, takes, scores, etc.)
- Handle decimal number parsing

**Key Methods:**
- `parse()` - Main parsing method
- `parse_number()` - Parse integer numbers
- `parse_decimal_number()` - Parse decimal numbers (up to 3 places)
- `normalize_word()` - Normalize words for fuzzy matching

### ParsedCommands

**Location:** `studioflow/core/marker_commands.py`

**Data Structure:**
```python
@dataclass
class ParsedCommands:
    # Organization
    take: Optional[int] = None
    order: Optional[int] = None  # Deprecated
    step: Optional[int] = None
    scene_number: Optional[float] = None
    scene_name: Optional[str] = None
    
    # Scoring
    retroactive_actions: List[str] = field(default_factory=list)
    score: Optional[str] = None
    score_level: Optional[int] = None
    
    # Emotion & Energy
    emotion: Optional[str] = None
    energy: Optional[str] = None
    
    # Other commands
    mark: bool = False
    hook: Optional[str] = None
    # ... etc
```

## Key Features

### 1. Scene Number Parsing

**Implementation:**
- Supports integers: `scene one` → 1.0
- Supports decimals: `scene one point five` → 1.5
- Supports up to 3 decimal places: `scene one point one two five` → 1.125
- Optional names: `scene one intro` → number: 1.0, name: "intro"

**Code:**
```python
def parse_decimal_number(self, words: List[str], start_idx: int) -> tuple[Optional[float], int]:
    # Parses up to 3 decimal places
    # Handles "one point two five" → 1.25
```

### 2. Score System

**Implementation:**
- 4-level system: skip (0), fair (1), good (2), best (3)
- Retroactive (applies to previous segment)
- Automatic demotion (only one "best" per sequence)

**Code:**
```python
SCORE_LEVELS = ["skip", "fair", "good", "best"]
SCORE_SCALE = {
    "skip": 0,
    "fair": 1,
    "good": 2,
    "best": 3
}
```

### 3. Fuzzy Matching

**Implementation:**
- Handles Whisper transcription variations
- Strips punctuation before checking
- Case-insensitive

**Variants:**
- "slate": ["slate", "state", "slait", "slayt", "sleight"]
- "done": ["done", "don", "dun", "dunn", "doan", "doone"]

### 4. Cut Point Calculation

**Implementation:**
- Removes dead space between "slate" and "done"
- Adds padding for natural jump cuts
- PADDING_BEFORE = 0.2s (200ms before first content word)
- PADDING_AFTER = 0.3s (300ms after last content word)

## Data Flow

```
Transcript (Whisper JSON)
    ↓
AudioMarkerDetector.detect_markers()
    ↓
List[AudioMarker]
    ↓
MarkerCommandParser.parse() (for each marker)
    ↓
ParsedCommands
    ↓
extract_segments_from_markers()
    ↓
List[Segment] (with marker_info)
```

## Segment Structure

```python
{
    "start": float,  # Cut point start
    "end": float,    # Cut point end
    "words": List[Dict],  # Whisper word objects
    "text": str,     # Full text
    "marker_info": {
        "type": str,  # "start", "end", "retroactive", "standalone"
        "take": Optional[int],
        "scene_number": Optional[float],
        "scene_name": Optional[str],
        "step": Optional[int],
        "emotion": Optional[str],
        "energy": Optional[str],
        "score": Optional[str],
        "score_level": Optional[int],
        # ... etc
    }
}
```

## Marker Type Classification

**Rules:**
1. **RETROACTIVE**: Has `apply` or `ending` with commands
2. **END**: Has `ending` alone (no commands)
3. **START**: Has `take`, `order`, `scene_number`, or `step`
4. **STANDALONE**: Just `mark` or effects/transitions

## Retroactive Actions

**Implementation:**
- Actions after "apply" are collected
- Score levels are extracted from actions
- Applied to previous segment in `extract_segments_from_markers()`

**Code:**
```python
if marker.marker_type == "retroactive":
    previous_segment = segments[-1]
    # Apply score, actions, etc.
```

## Backwards Compatibility

**Deprecated Features:**
- `order` - Maps to `scene_number` if scene number not set
- `ending [action]` - Treated as `apply [action]`

**Migration:**
- Old footage with "order" still works
- New footage should use scene numbers

## Testing

**Key Test Files:**
- `tests/test_audio_markers_segments.py` - Segment extraction
- `tests/test_audio_markers_integration.py` - Full integration
- `tests/test_marker_commands.py` - Command parsing
- `tests/test_audio_markers_permutations.py` - Edge cases

## Future Enhancements

**Planned:**
- Platform-specific markers (YouTube, Shorts, TikTok)
- Automatic multicam switching
- Story beat mapping
- Thumbnail extraction

**See:** `ADVANCED_MARKER_PROTOCOL.md` for advanced features

## Code Locations

- **Core Logic:** `studioflow/core/audio_markers.py`
- **Command Parsing:** `studioflow/core/marker_commands.py`
- **Tests:** `tests/test_audio_markers_*.py`
- **Documentation:** `docs/AUDIO_MARKERS_*.md`

## See Also

- `AUDIO_MARKERS_USER_GUIDE.md` - User-facing guide
- `AUDIO_MARKERS_REFERENCE.md` - Complete reference
- `ADVANCED_MARKER_PROTOCOL.md` - Advanced features

