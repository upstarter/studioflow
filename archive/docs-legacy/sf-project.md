# sf-project - Project Creation & Management

## Overview
`sf-project` is the core tool for creating and managing video production projects. It follows a convention-over-configuration approach, automatically organizing projects with industry-standard directory structures.

## Installation
```bash
sf-project  # Direct command
sf project  # Via master command
sfnew       # Alias (after sourcing .bashrc)
```

## Commands

### create
Create a new video project with automatic organization.

```bash
sf-project create "My YouTube Video"
sf-project create "Tutorial" --template tutorial
sf-project create "Review" --template minimal --no-git
```

**Options:**
- `-t, --template` - Project template (youtube, tutorial, comparison, minimal, raw)
- `--no-git` - Skip git repository initialization

**What it creates:**
- Date-prefixed project directory (YYYYMMDD_Project_Name)
- Template-based folder structure
- `.sf/project.json` metadata file
- README.md with task checklist
- Git repository with .gitignore
- DaVinci Resolve project placeholder (.drp file)

### list
List all projects, sorted by creation date.

```bash
sf-project list
sf-project list --json  # Output as JSON for scripting
```

**Output:**
- Project name with template type
- Creation date
- Status (active/archived)

### info
Get detailed information about a project.

```bash
sf-project info "My YouTube Video"
sf-project info 20250914_Tutorial  # Using full name
```

**Shows:**
- Full project path
- Creation timestamp
- Template used
- Storage size
- File count

### remove
Move a project to trash (recoverable).

```bash
sf-project remove "Old Project"
sf-project remove "Test" --force  # Skip confirmation
```

## Templates

### youtube (default)
Professional YouTube video structure:
```
01_FOOTAGE/A_ROLL      - Main camera footage
01_FOOTAGE/B_ROLL      - Supporting footage
02_AUDIO/MUSIC         - Background music
02_AUDIO/SFX           - Sound effects
02_AUDIO/VO            - Voice over
03_GRAPHICS/TITLES     - Title cards
03_GRAPHICS/OVERLAYS   - Graphics overlays
03_GRAPHICS/THUMBNAILS - YouTube thumbnails
04_EDIT/TIMELINE       - Project files
04_EDIT/CACHE          - Working cache
05_EXPORT/DRAFTS       - Test exports
05_EXPORT/FINAL        - Final renders
05_EXPORT/SHORTS       - Short-form versions
06_ASSETS/LUTS         - Color grading
06_ASSETS/TEMPLATES    - Reusable elements
07_DOCS/SCRIPT         - Video script
07_DOCS/NOTES          - Production notes
```

### tutorial
Optimized for educational content:
```
01_CAPTURES/SCREEN     - Screen recordings
01_CAPTURES/STEPS      - Step-by-step shots
02_NARRATION           - Voice narration
03_GRAPHICS            - Educational graphics
04_EDIT                - Timeline/project
05_EXPORT              - Final outputs
```

### comparison
For comparing tools/products:
```
01_CAPTURES/TOOL_A     - First tool captures
01_CAPTURES/TOOL_B     - Second tool captures
01_CAPTURES/TOOL_C     - Third tool captures
02_GRIDS               - Comparison grids
03_ANALYSIS            - Analysis data
04_EDIT                - Timeline
05_EXPORT              - Final video
```

### minimal
Basic three-folder structure:
```
FOOTAGE                - Raw footage
EDIT                   - Project files
EXPORT                 - Final outputs
```

### raw
Empty project with no predefined structure.

## Project Metadata

Each project contains `.sf/project.json`:
```json
{
  "name": "My YouTube Video",
  "created": "2025-09-14T10:30:00",
  "template": "youtube",
  "status": "active",
  "options": {
    "git": true
  }
}
```

## Event System

Projects emit JSON events for automation:
```json
{
  "timestamp": "2025-09-14T10:30:00",
  "project": "20250914_My_YouTube_Video",
  "type": "created",
  "data": {
    "template": "youtube"
  }
}
```

## Integration Examples

### With other SF tools:
```bash
# Create project and set up recording
sf-project create "Tutorial" && sf-obs setup "Tutorial"

# Create project and generate script
sf-project create "Review" && sf-ai script "Review"
```

### In scripts:
```bash
# Get most recent project
PROJECT=$(sf-project list --json | jq -r '.projects[0].name')

# Batch operations
sf-project list --json | jq -r '.projects[].name' | while read proj; do
  sf-storage move "$proj" archive
done
```

## Best Practices

1. **Use descriptive names** - They become directory names and are searchable
2. **Choose appropriate templates** - Saves setup time
3. **One project per video** - Keeps things organized
4. **Archive completed projects** - Use `sf-storage move` when done
5. **Regular commits** - Projects auto-initialize git

## Troubleshooting

**Project already exists:**
- Projects are date-prefixed, so same-day duplicates are prevented
- Use a different name or wait until tomorrow

**Permission denied:**
- Ensure `/mnt/studio/Projects/` is writable
- Check disk space with `sf-storage status`

**Git initialization failed:**
- Git is optional, use `--no-git` to skip
- Install git: `sudo apt install git`

## Configuration

Projects use the shared configuration in `~/.config/studioflow/config.yml`:
```yaml
defaults:
  template: youtube
  git: true
```

## Related Tools

- `sf-storage` - Move projects between storage tiers
- `sf-capture` - Capture screenshots into projects
- `sf-obs` - Configure OBS for project recording
- `sf-resolve` - Set up DaVinci Resolve projects