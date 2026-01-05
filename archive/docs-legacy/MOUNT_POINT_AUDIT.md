# StudioFlow Mount Point Audit & Recommendations

## 🔍 Current Configuration vs Reality

### StudioFlow Configured Paths (sfcore.py)
```python
STORAGE_TIERS = {
    "ingest": Path("/mnt/ingest"),           # ✅ EXISTS
    "active": Path("/mnt/studio/Projects"),  # ❌ WRONG - should be /mnt/studio/Projects
    "render": Path("/mnt/render"),           # ✅ EXISTS
    "library": Path("/mnt/library"),         # ✅ EXISTS
    "archive": Path("/mnt/archive"),         # ✅ EXISTS
    "nas": Path("/mnt/nas")                  # ✅ EXISTS
}
```

### Actual Mount Points Available
```
/mnt/
├── ingest/     ✅ Camera/SD card ingest (EXISTS)
├── studio/     ✅ Main production drive (EXISTS)
│   └── Projects/ ⚠️ (subdirectory, not direct mount)
├── render/     ✅ Render output drive (EXISTS)
├── library/    ✅ Asset library (EXISTS)
├── archive/    ✅ Long-term storage (EXISTS)
├── nas/        ✅ Network storage (EXISTS)
├── scratch/    🆕 Fast scratch space (NOT USED)
├── projects/   🆕 Code projects (NOT VIDEO)
└── ai_workspace/ 🆕 AI workspace (NOT USED)
```

## 🐛 Issues Found

### 1. **CRITICAL: Wrong Active Projects Path**
**Current**: `Path("/mnt/studio/Projects")`
**Should be**: `Path("/mnt/studio/Projects")`
**Problem**: Missing `/Projects` subdirectory in path

### 2. **Inconsistent Project Locations**
- sf-project creates in: `/mnt/studio/Projects/`
- sfcore.py points to: `/mnt/resolve/Projects` (doesn't exist!)
- OBS recordings go to: User's Videos folder

### 3. **Unused Mount Points**
- `/mnt/scratch/` - Perfect for temp renders
- `/mnt/ai_workspace/` - Could store AI models
- `/mnt/video_scratch/` - Could use for cache

### 4. **Missing Resolve Path**
- Code references `/mnt/resolve/` in multiple places
- This path doesn't exist!
- Should use `/mnt/studio/` instead

## 🔧 Required Fixes

### Fix 1: Update sfcore.py
```python
# CURRENT (WRONG)
STORAGE_TIERS = {
    "active": Path("/mnt/resolve/Projects"),  # ❌
}

# SHOULD BE
STORAGE_TIERS = {
    "active": Path("/mnt/studio/Projects"),   # ✅
}
```

### Fix 2: Create Missing Symlinks
```bash
# Option A: Create symlink for compatibility
sudo ln -s /mnt/studio /mnt/resolve

# Option B: Update all code to use /mnt/studio
```

### Fix 3: Utilize Scratch Space
```python
# Add to sfcore.py
STORAGE_TIERS = {
    # ... existing ...
    "scratch": Path("/mnt/scratch"),      # Fast temp space
    "ai_cache": Path("/mnt/ai_workspace"), # AI models/cache
}
```

## 📊 Storage Tier Analysis

| Tier | Path | Purpose | Status | Size |
|------|------|---------|--------|------|
| **Ingest** | `/mnt/ingest` | Camera dumps | ✅ Working | XFS |
| **Active** | `/mnt/studio/Projects` | Current projects | ❌ Wrong path | BTRFS |
| **Render** | `/mnt/render` | Final exports | ✅ Working | XFS |
| **Library** | `/mnt/library` | Reusable assets | ✅ Working | BTRFS |
| **Archive** | `/mnt/archive` | Long-term | ✅ Working | XFS RAID1 |
| **NAS** | `/mnt/nas` | Network backup | ✅ Working | NFS |
| **Scratch** | `/mnt/scratch` | Temp files | 🆕 Unused | tmpfs |

## 🚀 Recommended Improvements

### 1. Fix Path Configuration
```python
# Updated sfcore.py
STORAGE_TIERS = {
    "ingest": Path("/mnt/ingest"),
    "active": Path("/mnt/studio/Projects"),  # FIXED
    "render": Path("/mnt/render"),
    "library": Path("/mnt/library"),
    "archive": Path("/mnt/archive"),
    "nas": Path("/mnt/nas"),
    "scratch": Path("/mnt/scratch"),        # NEW
    "ai_cache": Path("/mnt/ai_workspace")   # NEW
}

# Add resolve compatibility
RESOLVE_ROOT = Path("/mnt/studio")  # DaVinci Resolve base
```

### 2. Optimize Storage Usage

#### Use Scratch for Temp Files
```python
# For temporary renders/proxies
TEMP_RENDER = STORAGE_TIERS["scratch"] / "render_temp"
PROXY_CACHE = STORAGE_TIERS["scratch"] / "proxy"
```

#### Use AI Workspace for Models
```python
# Store Whisper models, AI cache
WHISPER_MODELS = Path("/mnt/ai_workspace/whisper_models")
AI_CACHE = Path("/mnt/ai_workspace/cache")
```

### 3. Add Configuration File
Create `~/.config/studioflow/paths.yaml`:
```yaml
storage_tiers:
  ingest: /mnt/ingest
  active: /mnt/studio/Projects
  render: /mnt/render
  library: /mnt/library
  archive: /mnt/archive
  nas: /mnt/nas
  scratch: /mnt/scratch

obs:
  recording_path: /mnt/studio/Projects/Current

resolve:
  project_path: /mnt/studio/Projects
  cache_path: /mnt/scratch/resolve_cache

ai:
  models: /mnt/ai_workspace/models
  cache: /mnt/ai_workspace/cache
```

### 4. Create Helper Script
```bash
#!/bin/bash
# sf-check-paths - Verify all paths exist

echo "Checking StudioFlow paths..."

PATHS=(
  "/mnt/ingest"
  "/mnt/studio/Projects"
  "/mnt/render"
  "/mnt/library"
  "/mnt/archive"
  "/mnt/nas"
  "/mnt/scratch"
)

for path in "${PATHS[@]}"; do
  if [ -d "$path" ]; then
    echo "✅ $path exists"
  else
    echo "❌ $path missing"
  fi
done
```

## 🎯 Action Items

### Immediate (Fix Breaking Issues)
1. [ ] Update sfcore.py to use `/mnt/studio/Projects` instead of `/mnt/resolve/Projects`
2. [ ] Create symlink: `ln -s /mnt/studio /mnt/resolve` for compatibility
3. [ ] Test all sf-* commands with correct paths

### Short-term (Optimize)
4. [ ] Add scratch and ai_workspace to STORAGE_TIERS
5. [ ] Configure OBS to record to `/mnt/studio/Projects/Current`
6. [ ] Set DaVinci cache to `/mnt/scratch`

### Long-term (Improve)
7. [ ] Create paths.yaml configuration
8. [ ] Add path validation on startup
9. [ ] Auto-create missing directories
10. [ ] Add storage space monitoring

## 🔍 Testing Commands

```bash
# Test project creation
sf-project create "Test Project"
ls -la /mnt/studio/Projects/*Test*

# Test OBS recording path
sf-obs status | grep recording_path

# Test storage status
sf-storage status

# Check all paths
find /mnt/projects/studioflow -name "*.py" -exec grep -l "/mnt/resolve" {} \;
```

## Conclusion

The main issue is that StudioFlow references `/mnt/resolve/Projects` which doesn't exist. It should use `/mnt/studio/Projects`. Additionally, we're not utilizing the fast scratch space or AI workspace that could improve performance.

The fix is simple but critical for StudioFlow to work properly.