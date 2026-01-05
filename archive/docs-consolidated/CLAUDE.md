# CLAUDE.md - StudioFlow AI Assistant Context

## 🎯 Project Mission

StudioFlow is a **unified CLI tool** for automated video production workflows. It replaces manual tasks with intelligent automation, focusing on content creator needs: viral growth, quality output, and efficient workflows.

## 📌 Current State (2024)

### Architecture: Clean Modular CLI
- **Single entry point**: `sf` command
- **Typer-based CLI** with subcommands
- **Core services** separated from CLI layer
- **Type-safe** with full type hints
- **Configuration-driven** with YAML

### Technology Stack
- **Language**: Python 3.8+
- **CLI Framework**: Typer + Rich
- **AI**: OpenAI Whisper, GPT integration ready
- **APIs**: YouTube Data API v3, DaVinci Resolve Python API
- **Storage**: 6-tier system (ingest → archive)

### Key Features Implemented
✅ **Whisper Transcription** - Full implementation with SRT/VTT/JSON output
✅ **YouTube API** - Upload, metadata, analytics
✅ **Viral Optimization** - CTR prediction, psychological triggers
✅ **Resolve Profiles** - FX30 camera, YouTube optimization
✅ **Project Management** - Templates, metadata tracking
✅ **Media Import** - Smart categorization, deduplication

## 🚨 IMPORTANT: What NOT to Do

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

## ✅ ALWAYS Follow These Patterns

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

## 🏗️ Architecture Decisions

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

## 📁 Directory Structure

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
├── docs/               # Documentation (this file)
└── archive/            # Old code (DO NOT USE)
```

## 🎯 When Adding Features

### Step 1: Determine Type
- **Simple command?** → Add to existing command module
- **New domain?** → Create new command module
- **Complex workflow?** → Create workflow module
- **Business logic?** → Create/update core service

### Step 2: Implementation Order
1. Write core service with tests
2. Add CLI command
3. Update COMMANDS.md
4. Add integration test
5. Update this file if architecture changes

### Step 3: Code Review Checklist
- [ ] Type hints on all functions
- [ ] Docstrings with examples
- [ ] Error handling with user guidance
- [ ] Progress feedback for long operations
- [ ] Configuration not hardcoded
- [ ] Tests written
- [ ] Documentation updated

## 🔥 Current Priorities

### High Priority
1. **Testing**: Need comprehensive test suite
2. **CI/CD**: GitHub Actions for automated testing
3. **Documentation**: Video tutorials, examples
4. **Error Recovery**: Better error messages and recovery

### Medium Priority
1. **Plugin System**: Allow third-party extensions
2. **Web UI**: Browser-based interface
3. **Cloud Sync**: S3/GCS backup support
4. **Batch Processing**: Queue multiple projects

### Low Priority
1. **Mobile App**: Companion app for monitoring
2. **AI Chat**: Natural language commands
3. **Analytics Dashboard**: View channel analytics

## 💡 Design Philosophy

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

## 🚀 Quick Command Reference

```bash
# Most important commands
sf new "Project"                    # Create project
sf media transcribe video.mp4       # AI transcription
sf youtube optimize "Topic"         # Viral optimization
sf youtube upload video.mp4         # Direct upload
sf resolve profiles                 # Export settings

# Check implementation
grep -r "def.*" studioflow/cli/commands/  # All commands
grep -r "class.*Service" studioflow/core/ # All services
```

## 🐛 Known Issues

1. **YouTube API** requires manual credential setup
2. **Resolve API** needs Resolve running
3. **Storage paths** assume Linux filesystem
4. **No Windows testing** yet

## 📝 Notes for Future Claudes

### What Works Well
- Typer CLI structure is solid
- Service pattern is clean
- Rich output looks great
- Type hints help a lot

### What Needs Improvement
- Test coverage (~30%)
- Error messages could be clearer
- Some commands need progress bars
- Configuration validation weak

### Don't Change
- Overall architecture (it's good!)
- Module structure
- Service pattern
- CLI command structure

### Feel Free to Improve
- Add more tests
- Better error handling
- Performance optimizations
- Documentation examples

---

**Last Updated**: 2024
**Status**: Active Development
**Version**: 1.0.0

Remember: This is a tool for creators. Every feature should make their life easier, their content better, or their growth faster. If it doesn't do one of those, it doesn't belong here.