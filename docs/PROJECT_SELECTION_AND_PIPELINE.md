# Project Selection & Full Pipeline Implementation

## Optimal Project Selection Methods

### Current State
- `StateManager.current_project` - tracks active project
- `AutoImportService.get_active_project()` - creates date-based projects (`YYYYMMDD_Shoot`)
- `ProjectManager` - manages projects in `config.storage.active`

### Recommended Approach: Priority-Based Selection

**Priority Order:**
1. **SD Card Label/Config** (highest priority)
   - Read project name from SD card label
   - Or read from `.studioflow_project` file on card
   - Format: `PROJECT_NAME` or `EP001_ProjectName`

2. **Active Project** (StateManager)
   - Use `StateManager.current_project` if set
   - User has explicitly selected a project

3. **Date-Based Auto-Create**
   - Create `YYYYMMDD_Shoot` if no project specified
   - Or create `YYYYMMDD_Import` for imports

4. **Interactive Prompt** (fallback)
   - Show recent projects
   - Allow selection or creation

### Implementation Strategy

```python
def determine_target_project(mount_point: Path) -> Optional[Project]:
    """
    Determine which project to use for import
    
    Priority:
    1. SD card label/config file
    2. Active project (StateManager)
    3. Date-based auto-create
    4. Interactive prompt
    """
    # 1. Check SD card for project name
    project_name = read_project_from_card(mount_point)
    if project_name:
        return get_or_create_project(project_name)
    
    # 2. Check active project
    state = StateManager()
    if state.current_project:
        return ProjectManager().get_project(state.current_project)
    
    # 3. Auto-create date-based
    today = datetime.now().strftime("%Y%m%d")
    project_name = f"{today}_Shoot"
    return ProjectManager().create_project(project_name)
```

---

## What I Need to Know

### 1. Project Naming Convention
**Questions:**
- Do you use a specific naming pattern? (e.g., `EP001_Title`, `YYYYMMDD_Shoot`)
- Should projects be created automatically or always require explicit name?
- Do you want to name SD cards with project names?

**Recommendation:**
- Support multiple patterns
- Default: `YYYYMMDD_Shoot` for auto-imports
- Allow custom via SD card label or config file

### 2. Library Path Structure
**Questions:**
- Projects are stored in `/mnt/studio/PROJECTS/` (via `config.storage.active`)
- Projects are organized by name (flat structure, not by type)
- Test outputs go to `/mnt/dev/studioflow/tests/output/`

**Current:**
- Uses `config.storage.active` (defaults to `~/Videos/StudioFlow/Projects/`)
- Uses `config.storage.active` which defaults to `/mnt/studio/PROJECTS/`

**Current:**
- Projects are stored in `/mnt/studio/PROJECTS/` via `config.storage.active`
- Test outputs go to `/mnt/dev/studioflow/tests/output/`
- No separate library path needed

### 3. Processing Priority
**Questions:**
- Should normalization happen during import or after?
- Should transcription be immediate or queued?
- Should rough cut be automatic or on-demand?
- What's the priority order for processing?

**Recommendation:**
- **Phase 1 (Immediate):** Import, Normalize, Proxies
- **Phase 2 (Background):** Transcription, Marker Detection
- **Phase 3 (On-Demand):** Rough Cut, Resolve Setup

### 4. Project Creation Behavior
**Questions:**
- Should it always create a new project or use existing?
- Should it prompt if multiple projects exist?
- Should it auto-create if no project specified?

**Recommendation:**
- Use existing project if found (by name or active)
- Auto-create if none exists
- Prompt only if ambiguous (multiple matches)

### 5. Render Cache & Resolve Setup
**Questions:**
- Should Resolve project be created automatically?
- Should render cache be assembled immediately?
- Should bins be created automatically?

**Recommendation:**
- Create Resolve project after import
- Assemble render cache in background
- Create bins based on media analysis

---

## Full Pipeline Implementation Plan

### Phase 1: Project Selection (Day 1)
**Tasks:**
1. Enhance `AutoImportService` to read project from SD card
2. Integrate with `StateManager` for active project
3. Add date-based auto-create fallback
4. Projects use `/mnt/studio/PROJECTS/` (via `config.storage.active`)

**Files to Modify:**
- `studioflow/core/auto_import.py` - Add project selection logic
- `studioflow/core/config.py` - Add library_path
- `scripts/studioflow-card-import.sh` - Pass project info

### Phase 2: Import & Normalization (Day 1)
**Tasks:**
1. Integrate normalization into import pipeline
2. Normalize audio to -14 LUFS during import
3. Copy to project directory structure
4. Generate proxies in parallel

**Files to Modify:**
- `studioflow/core/auto_import.py` - Add normalization step
- `studioflow/core/unified_import.py` - NEW: Orchestrate pipeline

### Phase 3: Transcription & Markers (Day 2)
**Tasks:**
1. Queue transcription after import
2. Generate JSON transcripts (for markers)
3. Detect audio markers automatically
4. Extract segments with sorting

**Files to Modify:**
- `studioflow/core/unified_import.py` - Add transcription queue
- `studioflow/core/background.py` - Background transcription service

### Phase 4: Rough Cut & Resolve (Day 2)
**Tasks:**
1. Generate rough cut after markers detected
2. Create Resolve project automatically
3. Setup bins and smart bins
4. Import media to Resolve

**Files to Modify:**
- `studioflow/core/unified_import.py` - Add rough cut generation
- `studioflow/core/resolve_api.py` - Auto-create project

### Phase 5: Render Cache (Day 3)
**Tasks:**
1. Assemble render cache
2. Generate optimized media
3. Setup cache structure

**Files to Create:**
- `studioflow/core/render_cache.py` - NEW: Render cache assembly

### Phase 6: Export Integration (Day 3)
**Tasks:**
1. Enhance `sf export all` command
2. Export to all platforms
3. Use project context

**Files to Modify:**
- `studioflow/cli/commands/export.py` - Enhance export command

---

## Implementation Questions

### Critical Questions:

1. **Project Naming:**
   - What naming pattern do you prefer?
   - Should SD cards be labeled with project names?
   - Do you want a config file on SD card (`.studioflow_project`)?

2. **Storage Path:**
   - Projects use `/mnt/studio/PROJECTS/` (via `config.storage.active`)
   - Projects are organized by name (flat structure)
   - Test outputs go to `/mnt/dev/studioflow/tests/output/`

3. **Processing Behavior:**
   - Should everything happen automatically or in phases?
   - Should transcription be immediate or queued?
   - Should rough cut be automatic or on-demand?

4. **Resolve Integration:**
   - Should Resolve project be created automatically?
   - Should it open Resolve after setup?
   - Should bins be auto-populated?

5. **Error Handling:**
   - What should happen if import fails?
   - Should it retry or notify?
   - How should errors be logged?

---

## Recommended Defaults

If you don't specify, I'll implement with these defaults:

1. **Project Selection:**
   - Check SD card label for project name
   - Use active project if set
   - Auto-create `YYYYMMDD_Shoot` if none

2. **Storage Path:**
   - Use `/mnt/studio/PROJECTS/` (via `config.storage.active`)
   - Test outputs go to `/mnt/dev/studioflow/tests/output/`

3. **Processing:**
   - Immediate: Import, Normalize, Proxies
   - Background: Transcription, Markers
   - On-Demand: Rough Cut, Resolve Setup

4. **Resolve:**
   - Auto-create project
   - Auto-create bins
   - Don't auto-open (manual)

5. **Error Handling:**
   - Log all errors
   - Continue on non-critical errors
   - Notify on critical failures

---

## Next Steps

**Please Answer:**
1. Project naming preference
2. Library path confirmation
3. Processing priority preferences
4. Resolve integration preferences

**Then I'll:**
1. Implement project selection logic
2. Build unified import pipeline
3. Integrate all processing steps
4. Test end-to-end workflow


