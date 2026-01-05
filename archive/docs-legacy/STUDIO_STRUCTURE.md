# Studio Workspace Structure

## Overview
The creative studio workspace is organized across specialized mount points, each optimized for specific workflows in video production.

## Mount Points

### `/mnt/studio/` (700GB NVMe)
**Purpose**: Main creative workspace for all projects
- **Was**: `/mnt/studio/` (renamed for clarity)
- **Contains**: All active projects, DaVinci Resolve data, templates
- **Filesystem**: XFS optimized for balanced I/O

#### Directory Structure:
```
/mnt/studio/
├── Projects/           # All creative projects (StudioFlow managed)
│   ├── YYYYMMDD_Project_Name/   # Individual projects
│   ├── Current/        # Symlinks to active projects
│   ├── Templates/      # Project templates
│   └── Test/           # Test/experimental projects
├── Studio/             # Additional workspace organization
│   ├── Active/         # Currently working projects
│   ├── Templates/      # Reusable templates
│   ├── Library/        # Shared resources
│   └── Tools/          # Scripts and utilities
├── Cache/              # DaVinci Resolve cache
├── CacheClip/          # Resolve clip cache
├── OptimizedMedia/     # Resolve optimized media
├── ProxyMedia/         # Resolve proxy files
├── Camera/             # Camera imports (if using Resolve)
├── Export/             # Quick exports
└── captures/           # Screen captures

```

### `/mnt/ingest/` (600GB NVMe)
**Purpose**: Temporary holding for camera dumps
- **Workflow**: SD card → ingest → organize into projects
- **Filesystem**: XFS optimized for fast writes

### `/mnt/render/` (563GB NVMe)
**Purpose**: Final export destination
- **Workflow**: Export from editor → render → upload
- **Filesystem**: XFS with largeio for sequential writes

### `/mnt/library/` (1.6TB NVMe)
**Purpose**: Stock footage, music, permanent assets
- **Content**: Licensed music, SFX, graphics, LUTs
- **Filesystem**: BTRFS with zstd compression

### `/mnt/archive/` (3.7TB RAID1)
**Purpose**: Long-term storage of completed projects
- **Content**: Finished projects moved from studio
- **Filesystem**: XFS on RAID1 for redundancy

## Workflow

### 1. Project Creation
```bash
sf-project create "My YouTube Video" --current
# Creates: /mnt/studio/Projects/YYYYMMDD_My_Youtube_Video/
```

### 2. Camera Import
```bash
# SD card → /mnt/ingest/
# Then organize into project
mv /mnt/ingest/*.mp4 /mnt/studio/Projects/*/01_FOOTAGE/
```

### 3. Editing
- Work in `/mnt/studio/Projects/YYYYMMDD_Project_Name/`
- DaVinci Resolve cache in `/mnt/studio/Cache/`
- Proxies in `/mnt/studio/ProxyMedia/`

### 4. Export
```bash
# Render to /mnt/render/
# Then upload or distribute
```

### 5. Archive
```bash
# Move completed project
mv /mnt/studio/Projects/YYYYMMDD_Old_Project /mnt/archive/
```

## Backup Strategy

### High Frequency (Every 15 minutes)
- `/mnt/studio/Projects/` - Active projects
- `/mnt/studio/Studio/Active/` - Current work

### Daily
- `/mnt/library/` - Asset library
- `/mnt/projects/` - StudioFlow code

### On Change
- `/mnt/ingest/` - When camera footage arrives

### Excluded from Backup
- `/mnt/studio/Cache*` - Regeneratable
- `/mnt/studio/OptimizedMedia/` - Regeneratable
- `/mnt/studio/ProxyMedia/` - Regeneratable
- `/mnt/render/` - Temporary exports

## StudioFlow Integration

StudioFlow manages projects in `/mnt/studio/Projects/` with:
- Automatic naming: `YYYYMMDD_Project_Name`
- Template-based structure
- Git initialization
- Metadata tracking

### Configuration
```python
STORAGE_TIERS = {
    "ingest": Path("/mnt/ingest"),
    "active": Path("/mnt/studio/Projects"),
    "render": Path("/mnt/render"),
    "library": Path("/mnt/library"),
    "archive": Path("/mnt/archive"),
    "nas": Path("/mnt/nas")
}
```

## Performance Optimization

### Mount Options (fstab)
```
/mnt/studio:   noatime,nodiratime,inode64
/mnt/ingest:   noatime,nodiratime,inode64
/mnt/render:   noatime,nodiratime,inode64,largeio
/mnt/library:  compress=zstd:1,autodefrag
/mnt/archive:  noatime,nodiratime,inode64,largeio
```

### Best Practices
1. Keep active projects in `/mnt/studio/Projects/`
2. Use `/mnt/ingest/` only temporarily
3. Export to `/mnt/render/` for upload
4. Archive completed work to `/mnt/archive/`
5. Store reusable assets in `/mnt/library/`

## Space Management

### Current Usage
- `/mnt/studio`: 695GB free of 700GB
- `/mnt/ingest`: 596GB free of 600GB
- `/mnt/render`: 559GB free of 563GB
- `/mnt/library`: 1.6TB free of 1.6TB
- `/mnt/archive`: 3.6TB free of 3.7TB

### Cleanup Commands
```bash
# Clear old renders
rm -rf /mnt/render/old_*

# Clear Resolve cache
rm -rf /mnt/studio/Cache/*

# Clear ingest after organizing
rm -rf /mnt/ingest/*
```

## Migration from Old Structure

If you had projects in `/mnt/studio/`, they're now in `/mnt/studio/` after the rename. All paths have been updated in:
- System fstab
- Backup scripts
- StudioFlow configuration
- Documentation

No data was moved - only the mount point name changed from "resolve" to "studio" to better reflect its purpose as a general creative workspace.