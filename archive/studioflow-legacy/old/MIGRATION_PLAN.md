# StudioFlow /mnt/studio Migration Plan

## Current State Analysis

### ✅ What's Working
1. **Core StudioFlow**: `/mnt/projects/studioflow/` - Clean, only contains SF tools
2. **Active Projects**: `/mnt/studio/Projects/` - Being backed up every 15 min
3. **Ingest Pipeline**: `/mnt/ingest/Camera/Pool/` - Auto-import working

### ⚠️ Issues Found

#### Backup Coverage Gaps
Currently backed up in restic-active:
- ✅ `/mnt/studio/Projects`
- ✅ `/mnt/studio/Templates`
- ✅ `/mnt/studio/Export`
- ✅ `/mnt/studio/Camera`
- ✅ `/mnt/studio/captures`
- ✅ `/mnt/studio/Studio/Active`
- ✅ `/mnt/studio/Studio/Templates`
- ✅ `/mnt/studio/Studio/Library`
- ✅ `/mnt/studio/Studio/Tools`

NOT backed up:
- ❌ `/mnt/studio/Cache` - OK (temporary files)
- ❌ `/mnt/studio/CacheClip` - OK (Resolve cache)
- ❌ `/mnt/studio/OptimizedMedia` - OK (can regenerate)
- ❌ `/mnt/studio/ProxyMedia` - OK (can regenerate)

#### Legacy Paths in StudioFlow
Found 6 references to old paths:
1. `/mnt/archive/Projects` - Should be `/mnt/studio/Projects`
2. `/mnt/resolve/Projects` - Should be `/mnt/studio/Projects`

## Migration Actions

### 1. Clean Legacy Directories
```bash
# Archive has empty Projects folder - can remove
rm -rf /mnt/archive/Projects/.gallery
rmdir /mnt/archive/Projects

# Resolve mount point deprecated - projects moved to studio
# Keep /mnt/resolve for Resolve database only
```

### 2. Update StudioFlow Paths
Files to update:
- `/mnt/projects/studioflow/archive/old_monolithic/src/studioflow/extensions/ai_creator.py`
- `/mnt/projects/studioflow/sfcore.py` (check STORAGE_TIERS)
- Any config files referencing old paths

### 3. Storage Tier Updates
Current STORAGE_TIERS should be:
```python
STORAGE_TIERS = {
    "ingest": Path("/mnt/ingest"),           # SD card dumps
    "active": Path("/mnt/studio/Projects"),   # Current edits (UPDATED)
    "render": Path("/mnt/render"),           # Exports
    "library": Path("/mnt/library"),         # Reusable assets
    "archive": Path("/mnt/archive"),         # Long-term
    "studio": Path("/mnt/studio"),           # Studio workspace (NEW)
    "nas": Path("/mnt/nas")                 # Network/backup
}
```

### 4. Backup Configuration
No changes needed - restic-active already covers important directories.
Cache directories correctly excluded.

### 5. Directory Structure Standard

```
/mnt/
├── ingest/          # Temporary imports
│   └── Camera/Pool/ # Auto-import target
├── studio/          # MAIN WORKSPACE
│   ├── Projects/    # Active DaVinci projects
│   ├── Templates/   # Project templates
│   ├── Export/      # Rendered outputs
│   ├── Camera/      # Organized footage
│   ├── captures/    # Screenshots
│   ├── Studio/      # Creative workspace
│   ├── Cache/       # Temporary (not backed up)
│   ├── CacheClip/   # Resolve cache (not backed up)
│   ├── OptimizedMedia/ # Generated (not backed up)
│   └── ProxyMedia/  # Generated (not backed up)
├── render/          # Encoding workspace
├── library/         # Asset library
├── archive/         # Long-term storage
├── projects/        # StudioFlow only
│   └── studioflow/
└── nas/            # Network backup

```

## Implementation Script

See `/mnt/projects/studioflow/migrate-studio.sh`