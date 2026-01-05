# StudioFlow Architecture Analysis & Optimization Plan

## Current System Analysis

### Components
1. **cf-card-import** (/home/eric/bin/)
   - Triggered by udev rules on SD card insertion
   - Imports to /mnt/ingest with date-based folders
   - Uses rsync --ignore-existing for deduplication
   - Calls sf-ingest after import

2. **sf-ingest** (/mnt/projects/studioflow/)
   - Analyzes video files with ffprobe
   - Categorizes by duration (test_clip, a_roll, b_roll, general)
   - Creates clips_metadata.json
   - Calls sf-project-manager to track sessions

3. **sf-project-manager** (/mnt/projects/studioflow/)
   - Creates project directories
   - Tracks import sessions
   - Not well integrated with other tools

4. **sf-resolve-project-generator** (/mnt/projects/studioflow/)
   - Generates FCPXML/EDL files
   - Duplicates categorization logic from sf-ingest
   - Not automatically triggered

5. **sf-resolve-create-project** (/mnt/projects/studioflow/)
   - Uses Resolve Python API
   - Creates projects with bins and imports media
   - Requires manual execution

### Issues
- **Fragmented workflow**: Multiple manual steps required
- **Duplicate logic**: Categorization in multiple places
- **No "current project" concept**: User must specify project each time
- **Manual Resolve creation**: Not triggered automatically
- **Scattered configuration**: No central config

## Optimal Architecture Design

### Core Concepts
1. **Current Project File**: `/home/eric/.studioflow/current_project`
   - Points to active project directory
   - All tools reference this automatically

2. **Unified Project Command**: `sf`
   ```bash
   sf new "Project Name"     # Create and set as current
   sf current               # Show current project
   sf import               # Manual import from SD
   sf resolve              # Create/update Resolve project
   sf status              # Show project status
   ```

3. **Automatic Pipeline**
   ```
   SD Card Insert → cf-card-import → sf-orchestrator
                                           ↓
                                    [Import Media]
                                           ↓
                                    [Analyze Clips]
                                           ↓
                                 [Update Project Metadata]
                                           ↓
                                 [Generate Resolve Files]
                                           ↓
                                 [Create Resolve Project]
                                           ↓
                                    [Notify User]
   ```

### Consolidated Components

#### 1. sf (Master Command)
```bash
#!/bin/bash
# Unified StudioFlow command
# Located at: /usr/local/bin/sf
```

#### 2. sf-core (Python Library)
```python
# Shared functions for all tools
- get_current_project()
- set_current_project()
- analyze_clip()
- categorize_clip()
- create_resolve_project()
```

#### 3. sf-orchestrator
```python
# Main pipeline orchestrator
- Triggered by cf-card-import
- Reads current project
- Runs full pipeline
- Creates Resolve project
```

### Workflow

#### Initial Setup (Once)
```bash
# Create new project and set as current
$ sf new "Creator AI Hub Episode 2"
✓ Created project: /mnt/studio/Projects/20250922_Creator_AI_Hub_Episode_2
✓ Set as current project
✓ Ready for media import
```

#### Automatic Import (SD Card)
```
[Insert SD Card]
↓
✓ Detected SD card
✓ Importing 45 clips to current project
✓ Analyzing clips...
  - 6 test clips (< 3s)
  - 3 A-roll clips (> 60s)
  - 28 B-roll clips (10-30s)
  - 8 general clips
✓ Creating Resolve project...
✓ Project ready in DaVinci Resolve
✓ Timeline: Main_Edit_4K30_YouTube
```

#### Manual Commands
```bash
$ sf status
Current Project: Creator AI Hub Episode 2
Location: /mnt/studio/Projects/20250922_Creator_AI_Hub_Episode_2
Clips: 45 (3 A-roll, 28 B-roll, 6 test, 8 general)
Duration: 13:26
Resolve: Project created

$ sf resolve  # Force recreate Resolve project
✓ Updating Resolve project...
```

## Implementation Plan

### Phase 1: Core Infrastructure
1. Create `/home/eric/.studioflow/` config directory
2. Implement `sf` master command
3. Create `sf-core.py` library with shared functions

### Phase 2: Consolidation
1. Merge sf-ingest logic into sf-orchestrator
2. Remove duplicate categorization code
3. Integrate sf-resolve-create-project

### Phase 3: Automation
1. Update cf-card-import to call sf-orchestrator
2. Auto-detect current project
3. Auto-create Resolve project

### Phase 4: Polish
1. Add progress notifications
2. Error handling and recovery
3. Project templates (YouTube, Instagram, TikTok)

## Benefits
1. **One command setup**: `sf new "Project Name"`
2. **Zero-touch import**: Insert SD card → Done
3. **Automatic Resolve setup**: Project ready to edit
4. **Consistent categorization**: Single source of truth
5. **Minimal human input**: Only creative decisions remain

## Technical Details

### File Structure
```
/mnt/projects/studioflow/
├── sf                      # Master command (symlink to /usr/local/bin/)
├── sf-core.py             # Shared library
├── sf-orchestrator        # Main pipeline
├── sf-resolve-api.py      # Resolve API functions
└── templates/             # Project templates
    ├── youtube.json
    ├── instagram.json
    └── tiktok.json

/home/eric/.studioflow/
├── config.json           # Global config
├── current_project       # Path to current project
└── projects.json        # Project history
```

### Project Structure
```
/mnt/studio/Projects/[Project_Name]/
├── .studioflow/
│   ├── metadata.json     # Project metadata
│   ├── clips.json        # Analyzed clips
│   ├── sessions.json     # Import sessions
│   └── resolve/
│       ├── project.drp   # Resolve project
│       └── timeline.fcpxml
├── 01_MEDIA/            # Imported footage
├── 02_PROJECTS/         # Resolve projects
├── 03_RENDERS/          # Exports
└── 04_ASSETS/           # Graphics, audio, etc.
```

## Next Steps
1. Build sf master command
2. Create sf-core.py library
3. Implement sf-orchestrator
4. Update cf-card-import
5. Test end-to-end workflow