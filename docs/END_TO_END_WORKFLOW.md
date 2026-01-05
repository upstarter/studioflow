# End-to-End Workflow: SD Card to Ready-to-Edit

## What Happens When You Insert an SD Card

### Current Implementation Status

#### ✅ **Step 1: Auto-Detection** (IMPLEMENTED)
**Location:** `scripts/99-studioflow-import.rules` + `scripts/studioflow-card-import.sh`

**What Happens:**
1. udev rule detects SD card insertion (USB or built-in slot)
2. Triggers `studioflow-card-import.sh` script
3. Script detects camera type (FX30, ZV-E10, etc.)
4. Verifies it's a video card (checks for M4ROOT/CLIP structure)

**Status:** ✅ Working

---

#### ✅ **Step 2: Auto-Ingest** (IMPLEMENTED)
**Location:** `studioflow/core/auto_import.py` → `AutoImportService.import_media()`

**What Happens:**
1. Finds all media files on card
2. Copies to ingest pool: `/mnt/nas/Scratch/Ingest/{date}/`
3. Verifies file integrity (checksums)
4. Organizes by camera type (FX30, ZV-E10)

**Status:** ✅ Working

**Current Path:** `/mnt/nas/Scratch/Ingest/{date}/`
**Expected Path:** `/mnt/library/PROJECTS/{project_name}/01_Media/Original/`

**⚠️ Gap:** Files go to ingest pool, not directly to project

---

#### ⚠️ **Step 3: Normalization** (PARTIAL)
**Location:** `studioflow/core/ffmpeg.py` → `FFmpegProcessor.normalize_audio()`

**What Happens:**
- Audio normalization to -14 LUFS (YouTube standard)
- Codec conversion (if needed)

**Status:** ⚠️ Function exists but not integrated into auto-import

**⚠️ Gap:** Normalization happens separately, not during auto-import

---

#### ⚠️ **Step 4: Project Creation** (PARTIAL)
**Location:** `studioflow/core/project.py` → `Project.create()`

**What Happens:**
- Creates project structure
- Sets up folders (01_Media, 02_Transcription, etc.)

**Status:** ⚠️ Works but not automatically triggered by auto-import

**Current Path:** Uses `config.storage.active` (defaults to `~/StudioFlow/Projects/`)
**Expected Path:** `/mnt/library/PROJECTS/{project_name}/`

**⚠️ Gap:** 
- Auto-import doesn't create project automatically
- Path doesn't match `/mnt/library/PROJECTS/`

---

#### ✅ **Step 5: Proxy Generation** (IMPLEMENTED)
**Location:** `studioflow/core/auto_import.py` → `AutoImportService.generate_proxy()`

**What Happens:**
1. Generates proxies in parallel (up to 4 concurrent)
2. Saves to project proxy directory
3. Skips if proxy already exists

**Status:** ✅ Working (if project exists)

**⚠️ Gap:** Only works if project is already created

---

#### ⚠️ **Step 6: Transcription** (PARTIAL)
**Location:** `studioflow/core/transcription.py` → `TranscriptionService.transcribe()`

**What Happens:**
- Generates SRT subtitles
- Generates JSON with word-level timestamps (for audio markers)

**Status:** ⚠️ Function exists but not integrated into auto-import

**⚠️ Gap:** Transcription happens separately, not during auto-import

---

#### ⚠️ **Step 7: Audio Marker Detection** (PARTIAL)
**Location:** `studioflow/core/audio_markers.py` → `AudioMarkerDetector.detect_markers()`

**What Happens:**
- Detects "slate" and "done" markers
- Extracts segments
- Sorts by scene_number

**Status:** ⚠️ Function exists but not integrated into auto-import

**⚠️ Gap:** Marker detection happens separately, not during auto-import

---

#### ⚠️ **Step 8: Rough Cut Generation** (PARTIAL)
**Location:** `studioflow/core/rough_cut.py` → `RoughCutEngine.create_rough_cut()`

**What Happens:**
- Creates rough cut from segments
- Exports EDL/FCPXML for Resolve

**Status:** ⚠️ Function exists but not integrated into auto-import

**⚠️ Gap:** Rough cut generation happens separately via `sf rough-cut` command

---

#### ⚠️ **Step 9: Resolve Project Setup** (PARTIAL)
**Location:** `studioflow/core/resolve_api.py` → `ResolveDirectAPI.create_project()`

**What Happens:**
- Creates Resolve project
- Sets up bins and smart bins
- Configures color space (S-Log3 for FX30)

**Status:** ⚠️ Function exists but not integrated into auto-import

**⚠️ Gap:** Resolve project creation happens separately

---

#### ⚠️ **Step 10: Render Cache** (NOT IMPLEMENTED)
**What Should Happen:**
- Assemble render cache
- Optimize media for Resolve

**Status:** ❌ Not implemented

**⚠️ Gap:** No render cache assembly

---

#### ✅ **Step 11: Multi-Platform Export** (IMPLEMENTED)
**Location:** `studioflow/cli/commands/publish.py` → `publish.all()`

**What Happens:**
- Renders for YouTube, Instagram, TikTok, Twitter
- Platform-specific settings (resolution, bitrate, etc.)

**Status:** ✅ Working (but requires manual command: `sf publish all`)

**⚠️ Gap:** Not automatic, requires manual command

---

## Complete Workflow: What Should Happen

### Ideal Flow

```
1. Insert SD Card
   ↓
2. Auto-detect (udev rule)
   ↓
3. Auto-import to project
   ↓
4. Normalize audio (-14 LUFS)
   ↓
5. Create/use project in /mnt/library/PROJECTS/
   ↓
6. Generate proxies
   ↓
7. Transcribe (SRT + JSON)
   ↓
8. Detect audio markers
   ↓
9. Extract segments
   ↓
10. Generate rough cut
   ↓
11. Create Resolve project
   ↓
12. Setup bins & smart bins
   ↓
13. Assemble render cache
   ↓
14. Ready for timeline review
   ↓
15. One command: sf export all → exports to all platforms
```

---

## Current Reality vs. Expected

### ✅ What Works Now:
1. SD card auto-detection
2. Media import to ingest pool
3. Proxy generation (if project exists)
4. Multi-platform export (manual command)

### ⚠️ What's Missing:
1. **Automatic project creation** from auto-import
2. **Path configuration** to `/mnt/library/PROJECTS/`
3. **Normalization** during import
4. **Transcription** during import
5. **Audio marker detection** during import
6. **Rough cut generation** during import
7. **Resolve project setup** during import
8. **Render cache assembly**
9. **Fully automated pipeline** (all steps in sequence)

---

## How to Use Current System

### Manual Workflow (Current State):

```bash
# 1. Insert SD card (auto-detects, copies to ingest)
# Wait for notification or check: tail -f /var/log/studioflow-import.log

# 2. Create project
sf new "My Episode" --template youtube

# 3. Import from ingest pool to project
sf media import /mnt/nas/Scratch/Ingest/2026-01-04/

# 4. Normalize audio
sf normalize audio /path/to/project/01_Media/Original/

# 5. Transcribe
sf media transcribe /path/to/video.mp4

# 6. Generate rough cut (with audio markers)
sf rough-cut --audio-markers /path/to/project/01_Media/Original/

# 7. Create Resolve project
sf resolve create "My Episode"

# 8. Export to all platforms
sf publish all
```

---

## What Needs to Be Built

### 1. Unified Auto-Import Pipeline
**File:** `studioflow/core/unified_import.py` (NEW)

**Functionality:**
- Orchestrates all steps in sequence
- Creates project automatically
- Normalizes during import
- Transcribes during import
- Detects markers during import
- Generates rough cut
- Sets up Resolve project

### 2. Configuration for Library Path
**File:** `studioflow/core/config.py` (UPDATE)

**Change:**
- Add `library_path` to config
- Default to `/mnt/library/PROJECTS/`
- Use for all project creation

### 3. Render Cache Assembly
**File:** `studioflow/core/render_cache.py` (NEW)

**Functionality:**
- Assemble render cache
- Optimize media for Resolve
- Generate optimized media files

### 4. One-Command Export
**File:** `studioflow/cli/commands/export.py` (UPDATE)

**Enhancement:**
- `sf export all` command
- Exports to all platforms automatically
- Uses project context

---

## Recommendation

**Current Status:** ~40% Complete

**What Works:**
- SD card detection ✅
- Media import ✅
- Proxy generation ✅
- Export (manual) ✅

**What's Missing:**
- Unified pipeline ❌
- Automatic project creation ❌
- Normalization integration ❌
- Transcription integration ❌
- Marker detection integration ❌
- Rough cut automation ❌
- Resolve setup automation ❌
- Render cache ❌

**Next Steps:**
1. Build unified import pipeline
2. Integrate normalization
3. Integrate transcription
4. Integrate marker detection
5. Integrate rough cut generation
6. Integrate Resolve setup
7. Build render cache assembly
8. Test end-to-end

**Estimated Effort:** 2-3 days to build complete pipeline

