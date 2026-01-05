# StudioFlow Architecture

## Overview

StudioFlow is a unified CLI tool for automated video production workflows. This document describes the system architecture, design decisions, and technical implementation details.

## Project Mission

StudioFlow automates video production tasks to help content creators focus on creativity rather than repetitive technical work. It provides intelligent automation for transcription, editing, optimization, and publishing.

## Architecture Principles

### 1. Clean Modular CLI
- **Single entry point**: `sf` command
- **Typer-based CLI** with subcommands
- **Core services** separated from CLI layer
- **Type-safe** with full type hints
- **Configuration-driven** with YAML

### 2. Service Pattern
- Business logic in `studioflow/core/` services
- CLI layer in `studioflow/cli/commands/`
- Services are testable independently
- Same service can be used by multiple commands
- CLI changes don't affect business logic

### 3. Simplicity Over Complexity
- Avoid over-engineering
- Use proven tools (FFmpeg, Whisper) rather than rebuilding
- Focus on what works, not theoretical perfection
- Progressive enhancement: start simple, add complexity only when needed

## Technology Stack

### Core Technologies
- **Language**: Python 3.8+
- **CLI Framework**: Typer + Rich
- **AI**: OpenAI Whisper for transcription
- **APIs**: YouTube Data API v3, DaVinci Resolve Python API
- **Video Processing**: FFmpeg
- **Storage**: 6-tier system (ingest → archive)

### Key Dependencies
- `typer` - CLI framework with type safety
- `rich` - Beautiful terminal output
- `pyyaml` - Configuration management
- `openai-whisper` - AI transcription
- `google-api-python-client` - YouTube integration

## Directory Structure

```
studioflow/
├── studioflow/          # Main package
│   ├── cli/            # CLI layer (Typer commands)
│   │   ├── main.py     # Entry point, app setup
│   │   ├── commands/   # Command modules
│   │   └── workflows/  # Multi-step workflows
│   └── core/           # Business logic
│       ├── *.py        # Service modules
│       └── models/     # Data models (future)
├── tests/              # Test suite
├── docs/               # Documentation
└── archive/            # Old code (DO NOT USE)
```

## Design Decisions

### Why Typer?
- **Type safety** at runtime
- **Automatic help** generation
- **Subcommand groups** for organization
- **Rich integration** for beautiful output

### Why Service Pattern?
- **Testability** - Services can be tested independently
- **Reusability** - Same service used by multiple commands
- **Separation** - CLI changes don't affect business logic

### Why YAML Config?
- **Human readable** and editable
- **Hierarchical** structure
- **Standard** in DevOps tools
- **Comments** supported

### Why Not Microservices?
- **Simplicity** - Single tool, not a platform
- **Local-first** - No deployment complexity
- **Performance** - Direct function calls, no network overhead
- **Maintainability** - Easier to understand and debug

## Storage Architecture

### 6-Tier Storage System

StudioFlow uses a flexible storage system that supports both portable defaults (`~/Videos/StudioFlow/*`) and professional mount points (`/mnt/*`):

1. **Ingest** - Raw footage from cameras/SD cards
   - Default: `/mnt/ingest` (StorageTierSystem) or `~/Videos/StudioFlow/Ingest` (config)
2. **Active** - Current working projects
   - Default: `/mnt/studio/PROJECTS` (StorageTierSystem) or `~/Videos/StudioFlow/Projects` (config)
3. **Cache** - Resolve cache files (fast disk preferred)
   - Default: `/mnt/cache` (if configured) or `{active}/.cache`
4. **Proxies** - Proxy media files (fast disk preferred)
   - Default: `/mnt/cache/Proxies` (if configured) or `{active}/.proxies`
5. **Archive** - Completed projects, long-term storage
   - Default: `/mnt/archive` (StorageTierSystem) or `~/Videos/StudioFlow/Archive` (config)

### Project Structure

Active projects are stored in `/mnt/studio/PROJECTS/`:

```
/mnt/studio/PROJECTS/
├── {project_name}/     # Individual project directories
│   ├── 01_Media/      # Original and normalized media
│   ├── 02_Transcription/  # Transcripts
│   ├── 03_Segments/   # Extracted segments
│   └── 04_Timelines/  # Rough cut EDLs
```

Test outputs are stored in `/mnt/dev/studioflow/tests/output/`:

```
tests/output/
├── unified_pipeline/   # Unified import pipeline test outputs
│   ├── projects/      # Full test project structures
│   └── summaries/     # Test summary JSON files
├── e2e_test_runs/     # End-to-end test run outputs (timestamped)
└── legacy/            # Old test projects (for reference)
```

### Path Resolution Logic

The application uses this priority order for path resolution:

1. **User config** (`~/.studioflow/config.yaml`) - Highest priority
2. **Code defaults** (StorageTierSystem) - `/mnt/studio/PROJECTS` for active storage
3. **Config system defaults** - `~/Videos/StudioFlow/*` for other paths

**Example for active storage**:
```python
# In unified_import.py, project.py
active_path = config.storage.active  # Defaults to /mnt/studio/PROJECTS
```

**Example for test outputs**:
```python
# In tests (test_unified_pipeline_fixtures.py, conftest.py)
test_output = Path(__file__).parent / "tests" / "output" / "unified_pipeline"
```

### Cache/Proxy Configuration

Cache and proxy files can be separated from the library for better performance:

- **Default**: Cache and proxies stored inside library directory
- **Optimized**: Configure to use separate fast disk (`/mnt/cache`)
- **Configuration**: Set in `~/.studioflow/config.yaml`:
  ```yaml
  storage:
    active: /mnt/studio/PROJECTS   # Current working projects
    ingest: /mnt/ingest            # SD card dumps
    archive: /mnt/archive          # Completed projects
    cache: /mnt/cache              # Fast disk for cache (optional)
    proxy: /mnt/cache/Proxies      # Proxy files on cache disk (optional)
  ```

**See [User Guide](USER_GUIDE.md) for complete storage paths configuration details.**

## Code Patterns

### Command Structure
```python
# GOOD - Clean command with types and docs
@app.command()
def process(
    file: Path = typer.Argument(..., help="File to process"),
    option: str = typer.Option("default", help="Processing option")
):
    """Process a file with clear documentation."""
    service = ProcessService()
    result = service.process(file, option)
    console.print(f"[green]✓[/green] {result}")
```

### Service Pattern
```python
# GOOD - Separated business logic
class VideoService:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()

    def process(self, video: Path) -> Result:
        # Business logic here
        pass
```

### Error Handling
```python
# GOOD - User-friendly errors
try:
    result = api.call()
except ApiAuthError:
    console.print("[red]Authentication failed[/red]")
    console.print("[yellow]Run 'sf config --set youtube.api_key=KEY'[/yellow]")
    raise typer.Exit(1)
```

## Anti-Patterns to Avoid

### ❌ Never:
- Create new wrapper scripts (sf-* pattern is deprecated)
- Add files to project root (use proper module structure)
- Hardcode paths or credentials
- Mix CLI logic with business logic
- Create monolithic functions (keep them focused)
- Skip type hints or documentation

### ❌ Avoid:
- Global variables or state
- String path manipulation (use pathlib)
- Print statements (use Rich console)
- sys.exit() (use typer.Exit())
- Synchronous I/O for large files
- Tight coupling between modules

## Integration Points

### DaVinci Resolve
- Uses Resolve Python API
- Creates projects with optimized settings
- Syncs timelines and markers
- Exports with platform-specific presets

### YouTube API
- OAuth2 authentication
- Video upload with metadata
- Analytics integration
- Channel management

### Whisper AI
- Local or API-based transcription
- Multiple output formats (SRT, VTT, JSON)
- Chapter generation from transcripts
- Speaker diarization support

## Performance Considerations

### GPU Acceleration
- Whisper transcription uses GPU when available
- FFmpeg hardware encoding support
- Resolve GPU acceleration for exports

### Caching Strategy
- Transcript caching to avoid re-processing
- Media metadata caching
- Configuration caching

### Memory Management
- Streaming for large file operations
- Chunked processing for batch operations
- Lazy loading of heavy modules

## Security

### Credential Management
- API keys stored in config files (needs encryption)
- OAuth tokens for YouTube
- Secure credential storage planned (keyring library)

### Data Privacy
- Local processing preferred
- Optional cloud services
- No data collection without consent

## Testing Strategy

### Current State
- Minimal test coverage (~30%)
- Unit tests for core services
- Integration tests needed

### Target State
- 70%+ code coverage
- Comprehensive integration tests
- CI/CD pipeline
- Performance benchmarks

## Audio Marker System

The Audio Marker System enables hands-free video editing automation by detecting voice commands ("slate" ... "done") during recording to create edit points and apply metadata.

### Architecture

**Core Components**:
1. **`audio_markers.py`** - Marker detection from Whisper transcripts
2. **`marker_commands.py`** - Command parsing and normalization
3. **`rough_cut_markers.py`** - Integration with rough cut engine
4. **`transcript_extraction.py`** - Text extraction for segments

### Marker Detection Workflow

1. **Transcription**: Whisper generates word-level timestamps (JSON format)
2. **Detection**: Scan for "slate" keyword, collect commands until "done" (10s window)
3. **Classification**: Classify as START, END, or STANDALONE based on commands
4. **Cut Point Calculation**: Remove dead space automatically
5. **Segment Extraction**: Create segments from START/END marker pairs

### Marker Types

- **START**: Contains "naming", "order", or "step" commands → Creates segment start
- **END**: Contains "ending" command → Creates segment end
- **STANDALONE**: Just "mark" or effects → Creates jump cut points

### Integration Points

- **Rough Cut Engine**: `create_rough_cut()` accepts `use_audio_markers` flag
- **EDL/FCPXML Export**: Marker metadata (topic, type) included in exports
- **Transcript Service**: JSON output includes flattened `words` array for marker detection

### Design Decisions

- **10-second window**: If "done" not found, use 10s window for commands
- **Fuzzy matching**: Handles variations like "b roll" → "broll"
- **Dead space removal**: Cut points automatically remove silence before/after markers
- **JSON transcript format**: Requires word-level timestamps for marker detection

## Rough Cut System: State of the Art Analysis

### Comparison with Industry Tools

**StudioFlow vs. Descript**:
- ✅ Similar: Text-based editing, transcript-driven cuts
- ✅ Better: Audio marker automation (hands-free during recording)
- ✅ Better: Automatic B-roll matching
- ⚠️ Missing: Real-time collaboration

**StudioFlow vs. Premiere Pro Auto Reframe**:
- ✅ Better: AI-powered content analysis (not just aspect ratio)
- ✅ Better: Thematic organization
- ✅ Better: Narrative arc building
- ⚠️ Missing: Visual analysis (shot composition, color grading)

**StudioFlow vs. Final Cut Pro Magnetic Timeline**:
- ✅ Better: Automatic segment extraction from markers
- ✅ Better: Smart deduplication
- ⚠️ Missing: Advanced color grading integration

**Key Differentiators**:
1. **Audio Marker System** - Unique hands-free automation during recording
2. **Deep Content Analysis** - NLP-powered quote extraction and thematic organization
3. **Narrative Structure** - Automatic story arc building for documentaries
4. **B-Roll Matching** - Intelligent visual-to-audio matching

### Future Enhancements

**Short-term**:
- Visual analysis integration (shot composition, color grading)
- Multi-speaker support (speaker diarization)
- Music beat sync

**Medium-term**:
- Real-time collaboration
- Cloud sync (S3/GCS backup)
- Batch processing queue

**Long-term**:
- Plugin system for third-party extensions
- Web UI for browser-based interface
- ML model training on editor preferences

## Future Architecture Considerations

### Potential Enhancements
1. **Plugin System** - Allow third-party extensions
2. **Web UI** - Browser-based interface
3. **Cloud Sync** - S3/GCS backup support
4. **Batch Processing** - Queue multiple projects
5. **Real-time Collaboration** - Multi-user editing

### Scalability
- Current: Single-user, local processing
- Future: Multi-user, distributed processing
- Architecture designed to support growth

## Development Guidelines

### When Adding Features

**Step 1: Determine Type**
- **Simple command?** → Add to existing command module
- **New domain?** → Create new command module
- **Complex workflow?** → Create workflow module
- **Business logic?** → Create/update core service

**Step 2: Implementation Order**
1. Write core service with tests
2. Add CLI command
3. Update documentation
4. Add integration test
5. Update architecture docs if needed

**Step 3: Code Review Checklist**
- [ ] Type hints on all functions
- [ ] Docstrings with examples
- [ ] Error handling with user guidance
- [ ] Progress feedback for long operations
- [ ] Configuration not hardcoded
- [ ] Tests written
- [ ] Documentation updated

## Known Limitations

1. **YouTube API** requires manual credential setup
2. **Resolve API** needs Resolve running
3. **Storage paths** assume Linux filesystem
4. **No Windows testing** yet
5. **Limited test coverage** (~30%)

## Design Philosophy

### For Users
- **One command** to do common tasks
- **Intelligent defaults** that work
- **Clear feedback** on what's happening
- **Helpful errors** that guide to solution

### For Developers
- **Clean code** over clever code
- **Explicit** over implicit
- **Tested** over "it works on my machine"
- **Documented** over self-documenting

---

**Last Updated**: 2025-01-22  
**Status**: Active Development  
**Version**: 1.0.0


