# StudioFlow Cleanup Audit

## Files to DELETE (Redundant/Legacy)

### Demo/Test Files
- `ai_wizard_demo.py` - OLD demo file
- `debug_dynamic.py` - Debug test
- `demo_smart_wizard.py` - Another demo
- `sf-ingest-test` - Test duplicate of sf-ingest

### Duplicate Project Tools (Multiple versions doing same thing)
- `sf-project.bak` - Backup file
- `sf-project-episodes` - Duplicate functionality
- `sf-project-improved` - Another duplicate
- `sf-project-simple` - Yet another duplicate
- Keep only: **sf-project** (consolidate best features)

### Redundant AI Tools
- `sf-ai-enhanced` - Duplicate of sf-ai
- Keep only: **sf-ai**

### Obsolete Workflow Tools
- `sf-wizard` - Complex wizard, not needed with new automation
- `sf-fusion` - Unclear purpose, appears unused
- `sf-workflow` - Being replaced by new orchestrator

### Duplicate Resolve Tools
- `sf-resolve-orchestrator` - OLD version, being replaced
- Keep: **sf-resolve-create-project** and **sf-resolve-project-generator**

### Old Documentation
- `EXAMPLES.md` - Outdated examples
- `FAQ.md` - Old FAQ
- `MIGRATION_PLAN.md` - Migration complete
- `migrate-studio.sh` - Migration complete

### Miscellaneous
- `obscore.py` - OBS core, should be integrated into sf-obs
- `install-full.sh` - Old installer
- Keep only: **install.sh**

## Files to CONSOLIDATE

### Core Library (NEW: sf-core.py)
Merge common functions from:
- Clip analysis from `sf-ingest`
- Project management from `sf-project-manager`
- Media utilities from `sf-media`
- Archive functions from `sf-archive`

### Main Tools to Keep & Improve

1. **sf** (NEW) - Master command
   - Create from scratch
   - Manage all sub-commands

2. **sf-orchestrator** (NEW) - Main pipeline
   - Merge logic from sf-ingest
   - Integrate sf-resolve-create-project
   - Handle complete automation

3. **sf-capture** - Keep as is (screenshot tool)

4. **sf-audio** - Keep as is (transcription)

5. **sf-youtube** - Keep as is (optimization)

6. **sf-obs** - Keep, integrate obscore.py

7. **sf-storage** - Keep as is (tier management)

## New Simplified Structure

```
/mnt/projects/studioflow/
├── sf                          # Master command
├── sf-core.py                  # Shared library
├── sf-orchestrator             # Main automation
├── tools/
│   ├── sf-capture              # Screenshot tool
│   ├── sf-audio                # Audio processing
│   ├── sf-youtube              # YouTube optimization
│   ├── sf-obs                  # OBS control
│   └── sf-storage              # Storage management
├── config/
│   └── templates/
│       ├── youtube.json
│       ├── instagram.json
│       └── tiktok.json
├── docs/
│   └── README.md               # Single comprehensive doc
└── install.sh                  # Single installer
```

## Current Working Tools Chain

### What's Actually Working Now:
1. **cf-card-import** → Imports media from SD card
2. **sf-ingest** → Analyzes and categorizes clips
3. **sf-project-manager** → Tracks sessions
4. **sf-resolve-create-project** → Creates Resolve projects

### What to Build:
1. **sf** master command
2. **sf-orchestrator** to tie everything together
3. **Current project** tracking system

## Summary

### Delete (24 files):
- 4 demo/test files
- 5 duplicate project tools
- 1 duplicate AI tool
- 3 obsolete workflow tools
- 1 old resolve tool
- 4 old documentation files
- 2 misc files
- 1 old installer
- archive/ directory
- __pycache__/ directory

### Keep & Improve (8 tools):
- sf-capture
- sf-audio
- sf-youtube
- sf-obs
- sf-storage
- sf-resolve-create-project
- sf-resolve-project-generator
- sf-ingest (merge into orchestrator)

### Create New (3 files):
- sf (master command)
- sf-core.py (shared library)
- sf-orchestrator (main pipeline)

This will reduce from ~30 files to ~12 files with clear purpose and no duplication.