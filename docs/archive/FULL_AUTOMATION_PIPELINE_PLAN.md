# Full Automation Pipeline Plan
## From SD Card Insertion to One-Button Export

**Goal**: Automatically process imported footage so you only need to review/fix the Resolve rough cut, then press one button to export.

---

## Current State Analysis

### ✅ What Already Works

1. **Auto-Import System** (`studioflow/core/auto_import.py`)
   - ✅ udev rule triggers on card insertion
   - ✅ Detects camera type (FX30, ZV-E10)
   - ✅ Copies to ingest pool with verification
   - ✅ Organizes into project structure
   - ✅ Generates proxies (basic)
   - ✅ Creates basic Resolve timeline

2. **Background Services** (`studioflow/core/background_services.py`)
   - ✅ Auto-transcription service
   - ✅ Auto-rough-cut generation
   - ✅ Project watching capability
   - ✅ Parallel processing support

3. **Rough Cut Engine** (`studioflow/core/rough_cut.py`)
   - ✅ Full rough cut generation
   - ✅ Marker detection and processing
   - ✅ Transcript analysis
   - ✅ Multiple cut styles (DOC, EPISODE, INTERVIEW, TUTORIAL)
   - ✅ EDL/FCPXML export

4. **Resolve Integration** (`studioflow/core/resolve_api.py`)
   - ✅ Resolve API wrapper
   - ✅ Timeline creation
   - ✅ Project setup
   - ✅ Media pool organization

### ❌ What's Missing

1. **Integrated Pipeline**
   - ❌ Auto-import doesn't trigger background processing
   - ❌ No automatic transcription after import
   - ❌ No automatic rough cut generation
   - ❌ No automatic Resolve timeline update

2. **Status Tracking**
   - ❌ No job status tracking
   - ❌ No progress notifications
   - ❌ No error recovery

3. **Workflow Orchestration**
   - ❌ No pipeline state machine
   - ❌ No dependency management
   - ❌ No retry logic

4. **Export Automation**
   - ❌ No one-button export from Resolve
   - ❌ No export preset management
   - ❌ No post-export processing

---

## Target Workflow

### User Experience Flow

```
1. Insert SD Card
   ↓
2. Auto-import runs (udev)
   ↓
3. Files copied to project
   ↓
4. Background processing starts automatically:
   - Transcription (parallel)
   - Marker detection
   - Rough cut generation
   - Resolve timeline update
   ↓
5. Notification: "Rough cut ready in Resolve"
   ↓
6. User opens Resolve, reviews/fixes rough cut
   ↓
7. User clicks "Export" button (or runs command)
   ↓
8. Export runs with preset settings
   ↓
9. Post-processing (thumbnails, metadata, etc.)
   ↓
10. Done! ✅
```

---

## Architecture Design

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Import (Existing - via udev)                       │
│ - Detect card, mount, detect camera                          │
│ - Copy files to ingest pool                                  │
│ - Organize into project structure                            │
│ - Generate proxies                                           │
│ - Create basic Resolve timeline                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Transcription (Background Service)                  │
│ - Queue all video files for transcription                    │
│ - Process in parallel (4 workers)                             │
│ - Save transcripts (SRT, JSON, TXT)                          │
│ - Update project manifest                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: Marker Detection (Background Service)               │
│ - Detect audio markers in transcripts                        │
│ - Parse marker commands (naming, order, effects)            │
│ - Extract marker segments                                    │
│ - Save marker data                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: Rough Cut Generation (Background Service)          │
│ - Analyze all clips with transcripts                        │
│ - Generate rough cut plan                                    │
│ - Create segments from markers/transcript                    │
│ - Score and rank segments                                    │
│ - Generate EDL/FCPXML                                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: Resolve Timeline Update (Background Service)        │
│ - Import rough cut EDL/FCPXML                               │
│ - Update timeline with segments                              │
│ - Apply markers as timeline markers                         │
│ - Organize bins by theme/topic                              │
│ - Set up color management                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 6: User Review (Manual)                                │
│ - Open Resolve project                                       │
│ - Review rough cut timeline                                  │
│ - Make adjustments (trim, reorder, add effects)              │
│ - Add transitions, color grade, etc.                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 7: Export (One-Button)                                │
│ - User clicks "Export" or runs command                       │
│ - Load export preset                                         │
│ - Render timeline                                            │
│ - Generate thumbnails                                        │
│ - Create metadata files                                      │
│ - Upload (optional)                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Pipeline Orchestrator (Week 1)

**Goal**: Create a pipeline orchestrator that manages the entire workflow.

**Components**:

1. **PipelineOrchestrator** (`studioflow/core/pipeline.py`)
   ```python
   class PipelineOrchestrator:
       """Orchestrates the full automation pipeline"""
       
       def __init__(self):
           self.stages = [
               ImportStage(),
               TranscriptionStage(),
               MarkerDetectionStage(),
               RoughCutStage(),
               ResolveUpdateStage(),
               ExportStage()
           ]
           self.state = PipelineState()
           self.job_queue = Queue()
       
       def process_import(self, project_path: Path, media_files: List[Path]):
           """Start pipeline after import"""
           job = PipelineJob(project_path, media_files)
           self.job_queue.put(job)
           self._start_processing()
       
       def _start_processing(self):
           """Process jobs through pipeline stages"""
           # Process each stage in order
           # Handle dependencies
           # Track progress
   ```

2. **Pipeline State Management**
   - Track job status per stage
   - Store state in project manifest
   - Handle failures and retries

3. **Integration with AutoImportService**
   - Hook into import completion
   - Trigger pipeline orchestrator
   - Pass project and media files

**Files to Create**:
- `studioflow/core/pipeline.py` - Pipeline orchestrator
- `studioflow/core/pipeline_state.py` - State management
- `tests/test_pipeline.py` - Pipeline tests

**Files to Modify**:
- `studioflow/core/auto_import.py` - Add pipeline trigger
- `scripts/studioflow-card-import.sh` - Ensure pipeline starts

---

### Phase 2: Enhanced Background Services (Week 1-2)

**Goal**: Enhance background services to work seamlessly with pipeline.

**Components**:

1. **Auto-Start Background Services**
   - Start services on import completion
   - Watch project automatically
   - Process files in order

2. **Job Status Tracking**
   - Track transcription jobs
   - Track rough cut jobs
   - Store status in project manifest
   - Provide status API

3. **Error Handling & Recovery**
   - Retry failed jobs
   - Skip corrupted files
   - Log errors
   - Notify user

**Files to Modify**:
- `studioflow/core/background_services.py` - Add auto-start, status tracking
- `studioflow/core/auto_import.py` - Start background services

**Files to Create**:
- `studioflow/core/job_status.py` - Job status tracking
- `tests/test_background_services_integration.py` - Integration tests

---

### Phase 3: Resolve Timeline Integration (Week 2)

**Goal**: Automatically update Resolve timeline with rough cut.

**Components**:

1. **Rough Cut to Resolve Timeline**
   - Import EDL/FCPXML into Resolve
   - Create timeline from rough cut
   - Apply markers as timeline markers
   - Organize bins by theme/topic

2. **Timeline Update Service**
   - Watch for rough cut completion
   - Update Resolve timeline automatically
   - Handle timeline conflicts
   - Preserve user edits

3. **Resolve Project Management**
   - Auto-open project
   - Create/update timelines
   - Manage media pool
   - Set up color management

**Files to Create**:
- `studioflow/core/resolve_timeline_updater.py` - Timeline update service
- `studioflow/core/resolve_rough_cut_importer.py` - EDL/FCPXML importer

**Files to Modify**:
- `studioflow/core/resolve_api.py` - Add timeline update methods
- `studioflow/core/background_services.py` - Add Resolve update stage

---

### Phase 4: Notification System (Week 2)

**Goal**: Notify user when stages complete.

**Components**:

1. **Desktop Notifications**
   - Stage completion notifications
   - Error notifications
   - Progress updates

2. **Status Dashboard**
   - CLI status command
   - Web dashboard (optional)
   - Project manifest viewer

**Files to Create**:
- `studioflow/core/notifications.py` - Notification system
- `studioflow/cli/commands/pipeline_status.py` - Status command

---

### Phase 5: One-Button Export (Week 3)

**Goal**: Simple export from Resolve with one command/button.

**Components**:

1. **Export Preset System**
   - Store export presets (YouTube, Vimeo, etc.)
   - Apply preset to timeline
   - Customizable settings

2. **Export Service**
   - Resolve render queue integration
   - Progress tracking
   - Post-processing (thumbnails, metadata)

3. **CLI Command**
   ```bash
   sf export --preset youtube --timeline "Rough Cut"
   ```

**Files to Create**:
- `studioflow/core/export_service.py` - Export service
- `studioflow/core/export_presets.py` - Preset management
- `studioflow/cli/commands/export_resolve.py` - Export command

**Files to Modify**:
- `studioflow/core/resolve_api.py` - Add export methods

---

### Phase 6: Post-Export Processing (Week 3)

**Goal**: Automatically process exported files.

**Components**:

1. **Thumbnail Generation**
   - Extract thumbnails from video
   - Generate thumbnail grid
   - Create social media thumbnails

2. **Metadata Creation**
   - Generate metadata files
   - Create project summary
   - Export edit decision list

3. **Optional Upload**
   - Upload to YouTube/Vimeo
   - Upload to cloud storage
   - Share links

**Files to Create**:
- `studioflow/core/post_export.py` - Post-export processing
- `studioflow/core/thumbnail_generator.py` - Thumbnail generation

---

## Technical Implementation Details

### Pipeline State Machine

```python
class PipelineStage(Enum):
    IMPORT = "import"
    TRANSCRIPTION = "transcription"
    MARKER_DETECTION = "marker_detection"
    ROUGH_CUT = "rough_cut"
    RESOLVE_UPDATE = "resolve_update"
    READY = "ready"
    EXPORT = "export"
    COMPLETE = "complete"

class PipelineState:
    """Track pipeline state for a project"""
    project_path: Path
    current_stage: PipelineStage
    completed_stages: Set[PipelineStage]
    failed_stages: Dict[PipelineStage, str]
    stage_results: Dict[PipelineStage, Any]
    started_at: datetime
    updated_at: datetime
```

### Integration Points

1. **AutoImportService → PipelineOrchestrator**
   ```python
   # In auto_import.py
   def import_media(...):
       # ... existing import code ...
       
       # Trigger pipeline
       from studioflow.core.pipeline import PipelineOrchestrator
       orchestrator = PipelineOrchestrator()
       orchestrator.process_import(project, imported_videos)
   ```

2. **PipelineOrchestrator → BackgroundServices**
   ```python
   # In pipeline.py
   def _run_transcription_stage(self, job):
       background_services = BackgroundServices()
       background_services.watch_project(job.project_path)
       # Queue transcription jobs
   ```

3. **BackgroundServices → RoughCutEngine**
   ```python
   # In background_services.py
   def _process_rough_cut(self, job):
       engine = RoughCutEngine()
       plan = engine.generate_rough_cut(...)
       # Save EDL/FCPXML
   ```

4. **RoughCutEngine → ResolveTimelineUpdater**
   ```python
   # In pipeline.py
   def _run_resolve_update_stage(self, job):
       updater = ResolveTimelineUpdater()
       updater.import_rough_cut(job.project_path, edl_path)
   ```

---

## Configuration

### Pipeline Configuration

Add to `config/default.yaml`:

```yaml
pipeline:
  auto_start: true  # Start pipeline automatically after import
  stages:
    transcription:
      enabled: true
      parallel_workers: 4
      model: "base"  # Whisper model
    marker_detection:
      enabled: true
    rough_cut:
      enabled: true
      style: "doc"  # doc, episode, interview, tutorial
      use_audio_markers: true
    resolve_update:
      enabled: true
      auto_open: false  # Don't auto-open Resolve
  notifications:
    enabled: true
    desktop: true
    email: false
  export:
    default_preset: "youtube"
    auto_thumbnail: true
    auto_metadata: true
```

---

## Error Handling & Recovery

### Failure Modes

1. **Transcription Failure**
   - Retry with smaller model
   - Skip file and continue
   - Log error

2. **Rough Cut Failure**
   - Fall back to simple timeline
   - Use all footage if analysis fails
   - Log error

3. **Resolve Failure**
   - Skip Resolve update
   - Generate EDL/FCPXML only
   - User can import manually

4. **Export Failure**
   - Retry with different settings
   - Generate error report
   - Notify user

### Recovery Strategy

- **Checkpoint System**: Save state after each stage
- **Resume Capability**: Resume from last successful stage
- **Manual Override**: Allow manual stage execution
- **Error Reporting**: Detailed error logs and reports

---

## User Interface

### CLI Commands

```bash
# Check pipeline status
sf pipeline status [project]

# Manually trigger stage
sf pipeline run --stage transcription [project]

# Export from Resolve
sf export --preset youtube --timeline "Rough Cut"

# View pipeline logs
sf pipeline logs [project]
```

### Status Display

```
Pipeline Status: transcription (75%)
├─ Import: ✅ Complete
├─ Transcription: 🔄 Running (3/4 files)
│  ├─ C0138.MP4: ✅ Complete
│  ├─ C0139.MP4: ✅ Complete
│  ├─ C0140.MP4: 🔄 Processing...
│  └─ C0141.MP4: ⏳ Pending
├─ Marker Detection: ⏳ Waiting
├─ Rough Cut: ⏳ Waiting
└─ Resolve Update: ⏳ Waiting
```

---

## Testing Strategy

### Unit Tests
- Pipeline orchestrator
- Stage execution
- State management
- Error handling

### Integration Tests
- Full pipeline execution
- Background services integration
- Resolve integration
- Export workflow

### End-to-End Tests
- Complete workflow from import to export
- Error recovery scenarios
- Multiple projects
- Concurrent processing

---

## Success Metrics

1. **Automation Coverage**: 90%+ of workflow automated
2. **Processing Time**: < 2x real-time for transcription
3. **Error Rate**: < 5% failure rate
4. **User Satisfaction**: Minimal manual intervention needed

---

## Implementation Timeline

### Week 1: Foundation
- ✅ Pipeline orchestrator
- ✅ State management
- ✅ Integration with auto-import

### Week 2: Processing
- ✅ Enhanced background services
- ✅ Resolve timeline integration
- ✅ Notification system

### Week 3: Export & Polish
- ✅ One-button export
- ✅ Post-export processing
- ✅ Error handling & recovery
- ✅ Documentation

---

## Next Steps

1. **Review this plan** - Confirm approach and priorities
2. **Start Phase 1** - Build pipeline orchestrator
3. **Test incrementally** - Test each stage as it's built
4. **Iterate** - Refine based on usage

---

**Last Updated**: 2025-01-22

