# StudioFlow Hardcoded Values Audit

## 🔴 Critical Hardcoded Values (Must Fix Immediately)

### Username References
- `cf-card-import:10` → `NOTIFY_USER="eric"`
- `cf-card-import:40` → `/home/eric/.config/studioflow/active_project.json`
- `cf-card-mount-helper:23,35` → `/home/eric/bin/cf-card-import`

### Installation Paths
- `install.sh:18` → `INSTALL_DIR="/mnt/projects/studioflow"`
- Multiple files → `sys.path.insert(0, '/mnt/projects/studioflow')`
- `sf:153` → `["/mnt/projects/studioflow/sf-resolve-project-generator", str(project)]`

### Storage Paths
- `sfcore.py:20` → `"studio": Path("/mnt/studio/Projects")`
- `sfcore.py:19` → `"ingest": Path("/mnt/ingest")`
- `sf:173,202` → `Path("/mnt/studio/Projects")`
- `sf-project:82,194,215,330` → `Path("/mnt/studio/Projects")`
- `cf-card-import:8` → `POOL_DIR="/mnt/ingest/Camera/Pool"`

### Application Paths
- `sfcore.py:110` → `env['RESOLVE_SCRIPT_API'] = '/opt/resolve/Developer/Scripting'`
- `sf-resolve-create-project:8` → `find /opt -name "DaVinciResolveScript.py"`

## 🟡 Hardcoded Settings (Should Configure)

### Categorization Rules
- `sfcore.py:78` → `if duration < 3: return "test_clip"`
- `sfcore.py:80` → `elif duration >= 60: return "a_roll"`
- `sfcore.py:82` → `elif 10 <= duration <= 30: return "b_roll"`

### Project Structure
- `sfcore.py:30` → Fixed folder names: `"01_MEDIA", "02_PROJECTS", etc.`

### Resolve Settings
- `sf-resolve-create-project:32` → `"timelineResolutionWidth", "3840"`
- `sf-resolve-create-project:33` → `"timelineResolutionHeight", "2160"`
- `sf-resolve-create-project:34` → `"timelineFrameRate", "29.97"`

### Import Settings
- `cf-card-import:65` → rsync include patterns hardcoded
- `sf-resolve-project-generator:78` → Fixed marker positions

## 🟢 Cosmetic Hardcoded (Low Priority)

### Default Names
- `sf-resolve-create-project:92` → `"Main_Edit_4K30_YouTube"`
- `sf-resolve-project-generator:164` → `"YouTube 4K30 Optimized"`

### Log Paths
- `cf-card-import:9` → `LOG_FILE="/var/log/cf-card-import.log"`

## Impact Analysis

### For Sharing Tool
**Blocker Issues:**
- Won't work on any system without user "eric"
- Won't work unless installed at `/mnt/projects/studioflow`
- Won't work without exact mount point structure

**Estimated Users Affected:** 100% (all other users)

### For Your Use
**Current Impact:** Low (works for you)
**Future Impact:** High (hard to modify settings)

## Fix Priority

### Phase 1 (This Week) - Sharing Blockers
1. **Username**: Replace "eric" with `$USER` or config
2. **Home Paths**: Use `~/.studioflow` instead of `/home/eric/`
3. **Install Location**: Make configurable

### Phase 2 (Next Week) - Core Paths
4. **Storage Tiers**: Move to config file
5. **App Paths**: Auto-detect or configure
6. **Import Settings**: Make configurable

### Phase 3 (Later) - Advanced Settings
7. **Categorization Rules**: User-defined thresholds
8. **Project Structure**: Customizable folders
9. **Default Names**: Template system

## Configuration System Design

```yaml
# ~/.studioflow/config.yaml
user:
  name: ${USER}
  notification_enabled: true

paths:
  install_dir: /opt/studioflow
  studio_projects: ~/Videos/Projects
  ingest: ~/Videos/Ingest
  archive: ~/Videos/Archive

resolve:
  install_path: /opt/resolve
  api_path: /opt/resolve/Developer/Scripting

categorization:
  test_clip_max_seconds: 3
  b_roll_min_seconds: 10
  b_roll_max_seconds: 30
  a_roll_min_seconds: 60

project:
  default_template: youtube_4k30
  folder_structure:
    - "01_MEDIA"
    - "02_PROJECTS"
    - "03_RENDERS"
    - "04_ASSETS"
    - ".studioflow"

import:
  file_extensions: [".MP4", ".MOV", ".AVI", ".MXF"]
  skip_duplicates: true
  verify_checksums: true
```

## Implementation Plan

### 1. Create Config Loader (sfcore.py)
```python
import yaml
from pathlib import Path
import os

class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".studioflow"
        self.config_file = self.config_dir / "config.yaml"
        self.load_config()

    def load_config(self):
        if not self.config_file.exists():
            self.create_default_config()

        with open(self.config_file) as f:
            self.data = yaml.safe_load(f)

    @property
    def studio_projects(self):
        return Path(self.data['paths']['studio_projects']).expanduser()

    @property
    def username(self):
        return self.data['user']['name']
```

### 2. Update All Scripts
Replace hardcoded values with config lookups:
```python
# Before
projects_dir = Path("/mnt/studio/Projects")

# After
config = Config()
projects_dir = config.studio_projects
```

### 3. Add Setup Command
```bash
sf setup  # Interactive configuration wizard
```

## Testing Strategy

### Before Changes
1. Document current behavior
2. Create test projects
3. Verify imports work

### During Changes
1. Test each file as it's updated
2. Verify config loading works
3. Test with different config values

### After Changes
1. Test fresh installation
2. Test on different user account
3. Test with non-standard paths

## Risk Mitigation

### Backup Current State
```bash
cp -r /mnt/projects/studioflow /mnt/projects/studioflow.backup
```

### Gradual Migration
1. Add config system alongside hardcoded values
2. Test both paths work
3. Remove hardcoded values once confident

### Fallback Strategy
If config fails, fall back to sensible defaults:
```python
def get_projects_dir():
    try:
        return config.studio_projects
    except:
        return Path.home() / "Videos" / "Projects"
```

## Success Criteria

### Must Have
- [ ] Works for any username
- [ ] Works on different install locations
- [ ] Easy configuration via file
- [ ] Backward compatible for your setup

### Nice to Have
- [ ] Interactive setup wizard
- [ ] Config validation
- [ ] Multiple config profiles
- [ ] Environment variable overrides

## Timeline

**Day 1-2**: Create config system
**Day 3-4**: Update core files (sfcore.py, sf, sf-orchestrator)
**Day 5-6**: Update bash scripts (cf-card-import)
**Day 7**: Testing and documentation

**Total Effort**: ~1 week focused work