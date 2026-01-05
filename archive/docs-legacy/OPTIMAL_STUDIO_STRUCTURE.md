# Optimal Studio Workflow Structure

## Current Disk Layout Analysis

### Fast NVMe (nvme2n1) - Production Drive
- `/mnt/studio` (700GB) - DaVinci Resolve projects
- `/mnt/ingest` (600GB) - Camera imports
- `/mnt/render` (563GB) - Final exports

### Storage NVMe (nvme0n1p4)
- `/mnt/library` (1.6TB) - Stock footage, music, templates

### RAID Archive (md0)
- `/mnt/archive` (3.7TB) - Completed projects

## 🎯 Proposed Structure: `/mnt/studio`

Instead of `/mnt/Episodes`, use **`/mnt/studio`** because:
- Not limited to episodic content
- Professional terminology
- Covers all creative work
- Clear purpose

## Optimal Directory Organization

```
/mnt/studio/                    # Main creative workspace (on nvme2n1p2 with resolve)
├── active/                     # Current projects in production
│   └── YYYYMMDD_Project_Name/  # Each active project
│       ├── 01_SOURCE/          # Raw materials
│       │   ├── footage/        # Camera files
│       │   ├── audio/          # Audio recordings
│       │   ├── screen/         # Screen captures
│       │   └── ai_generated/   # AI outputs (Runway, Veo, Luma)
│       ├── 02_WORKING/         # Work in progress
│       │   ├── projects/       # DaVinci/Premiere project files
│       │   ├── proxies/        # Proxy media
│       │   ├── cache/          # Working cache
│       │   └── temp/           # Temporary files
│       ├── 03_CREATIVE/        # Creative assets
│       │   ├── graphics/       # Titles, overlays
│       │   ├── music/          # Project-specific music
│       │   ├── effects/        # VFX, transitions
│       │   └── thumbnails/     # Thumbnail designs
│       ├── 04_OUTPUT/          # Final deliverables
│       │   ├── masters/        # Master exports
│       │   ├── youtube/        # Platform-specific (1080p/4K)
│       │   ├── shorts/         # Vertical 9:16
│       │   └── social/         # Other platforms
│       └── 05_DOCS/            # Documentation
│           ├── scripts/        # Episode scripts
│           ├── notes/          # Production notes
│           └── metadata/       # Titles, descriptions, tags
│
├── templates/                  # Reusable project templates
│   ├── youtube_standard/
│   ├── tutorial_series/
│   ├── product_review/
│   └── documentary/
│
├── library/                    # Shared resources
│   ├── music/                 # Licensed music library
│   ├── sfx/                   # Sound effects
│   ├── graphics/              # Logos, overlays
│   ├── luts/                  # Color grading LUTs
│   └── presets/               # Effect presets
│
└── tools/                     # Automation & utilities
    ├── scripts/               # Automation scripts
    ├── workflows/             # Documented workflows
    └── checklists/            # Production checklists
```

## Directory Purposes (Simplified)

### Keep in `/mnt/studio/`:
- `Projects/` - ONLY DaVinci Resolve .drp files and databases
- `Cache/` - DaVinci's internal cache (exclude from backups)

### Keep in `/mnt/ingest/`:
- Raw camera dumps from SD cards
- Temporary holding before organizing into projects

### Keep in `/mnt/render/`:
- Final exports before distribution
- YouTube upload queue
- Archive preparation

### Move to `/mnt/studio/`:
- All active project work
- Templates and presets
- Production tools and scripts
- Creative assets

### Keep in `/mnt/archive/`:
- Completed projects (moved from studio/active)
- Historical versions
- Client deliverables

### Keep in `/mnt/library/`:
- Stock footage
- Music licenses
- Purchased assets
- Reference materials

## Migration Strategy

### Phase 1: Structure Creation
```bash
# Create new structure
sudo mkdir -p /mnt/studio/{active,templates,library,tools}
sudo chown -R eric:eric /mnt/studio
```

### Phase 2: Template Setup
```bash
# Create standard templates
/mnt/studio/templates/
├── youtube_episode/
├── tutorial/
├── product_review/
└── social_short/
```

### Phase 3: Project Migration
- Current: `/mnt/studio/Projects/20250920_Creator_Ai_Hub_2026_Ai_Video_Tools/`
- New: `/mnt/studio/active/20250920_Creator_Ai_Hub_2026_Ai_Video_Tools/`

## Workflow Benefits

### 1. Clear Lifecycle
- **Ingest** → `/mnt/ingest/` (temporary)
- **Organize** → `/mnt/studio/active/PROJECT/01_SOURCE/`
- **Edit** → Work in `/mnt/studio/active/PROJECT/`
- **Export** → `/mnt/studio/active/PROJECT/04_OUTPUT/`
- **Deliver** → `/mnt/render/` (for upload)
- **Archive** → `/mnt/archive/` (completed)

### 2. Separation of Concerns
- **Source files** - Never modified, always preserved
- **Working files** - Proxies, cache, temporary
- **Creative assets** - Reusable across projects
- **Output files** - Platform-optimized exports
- **Documentation** - Scripts, notes, metadata

### 3. Backup Optimization
- `01_SOURCE/` - Critical, never changes (backup once)
- `02_WORKING/cache/` - Exclude from backups
- `03_CREATIVE/` - Important, version controlled
- `04_OUTPUT/` - Can be regenerated but backup anyway
- `05_DOCS/` - Small but critical

### 4. Performance Optimization
- Keep active projects on fast NVMe
- Proxies in working directory
- Cache local to project
- Archive to RAID when complete

## StudioFlow Integration

Update StudioFlow paths:
```python
STORAGE_TIERS = {
    "ingest": Path("/mnt/ingest"),           # Camera dumps
    "active": Path("/mnt/studio/active"),    # Active projects
    "resolve": Path("/mnt/studio/Projects"), # DaVinci files
    "render": Path("/mnt/render"),           # Final exports
    "library": Path("/mnt/studio/library"),  # Shared assets
    "archive": Path("/mnt/archive"),         # Long-term
    "nas": Path("/mnt/nas")                  # Network backup
}
```

## Naming Convention

Maintain strict naming for projects:
- Format: `YYYYMMDD_Descriptive_Project_Name`
- Example: `20250920_Creator_Ai_Hub_Tutorial`
- No spaces in folder names
- Use underscores as separators

## Automation Scripts

### Project Creation
```bash
sf-project create "Project Name" --template youtube
# Creates in /mnt/studio/active/
```

### Project Archival
```bash
sf-project archive "Project Name"
# Moves from /mnt/studio/active/ to /mnt/archive/
```

### Template Management
```bash
sf-project save-template "Project Name" --name "template_name"
# Saves structure as reusable template
```

## Benefits Over Current System

1. **Cleaner** - One main location for all creative work
2. **Scalable** - Templates for different content types
3. **Efficient** - Clear separation of source/work/output
4. **Backup-friendly** - Organized for incremental backups
5. **Archive-ready** - Easy to move completed projects
6. **Tool-agnostic** - Works with any editing software

## Implementation Priority

1. ✅ Create `/mnt/studio/` structure
2. ✅ Set up templates
3. ✅ Migrate current project
4. ✅ Update StudioFlow paths
5. ✅ Create automation scripts
6. ✅ Document workflows
7. ✅ Update backup scripts