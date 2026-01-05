# StudioFlow Development Guide

Complete guide for extending and contributing to StudioFlow.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Adding New Features](#adding-new-features)
4. [Code Style](#code-style)
5. [Testing](#testing)
6. [Critical Implementation Priorities](#critical-implementation-priorities)
7. [Edge Cases & Solutions](#edge-cases--solutions)
8. [Features to Remove/Simplify](#features-to-removesimplify)
9. [Best Practices](#best-practices)
10. [Contributing](#contributing)

---

## Development Setup

### Prerequisites

```bash
# Python 3.8+
python --version

# pip
pip --version

# git
git --version
```

### Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/studioflow.git
cd studioflow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with debug logging
SF_DEBUG=1 sf new "Test Project"
```

### Development Tools

```bash
# Code formatting
black studioflow/

# Type checking
mypy studioflow/

# Linting
ruff studioflow/

# Pre-commit hooks
pre-commit install
```

---

## Project Structure

```
studioflow/
├── studioflow/              # Main package
│   ├── __init__.py         # Version, exports
│   ├── cli/                # Command-line interface
│   │   ├── main.py        # Entry point
│   │   ├── commands/      # Command modules
│   │   └── workflows/     # Multi-step workflows
│   └── core/              # Business logic
│       ├── project.py     # Project management
│       ├── media.py       # Media operations
│       └── *.py           # Other services
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test data
├── docs/                   # Additional documentation
├── scripts/               # Utility scripts
├── setup.py               # Package configuration
├── requirements.txt       # Production dependencies
└── requirements-dev.txt   # Development dependencies
```

---

## Adding New Features

### 1. Adding a New Command

Create a new command module in `cli/commands/`:

```python
# studioflow/cli/commands/mynewfeature.py
import typer
from rich.console import Console
from typing import Optional

console = Console()
app = typer.Typer()

@app.command()
def process(
    input_file: typer.Argument(..., help="File to process"),
    option: Optional[str] = typer.Option(None, "--option", "-o", help="Optional parameter")
):
    """
    Process a file with my new feature.

    Examples:
        sf mynewfeature process file.mp4
        sf mynewfeature process file.mp4 --option value
    """
    console.print(f"Processing {input_file}...")

    # Your logic here
    from studioflow.core.mynewservice import MyNewService
    service = MyNewService()
    result = service.process(input_file, option)

    console.print(f"[green]✓ Complete![/green] Result: {result}")
    return result
```

Register in `cli/main.py`:

```python
from studioflow.cli.commands import mynewfeature

app.add_typer(mynewfeature.app, name="mynewfeature", help="My new feature")
```

### 2. Adding a Core Service

Create service in `core/`:

```python
# studioflow/core/mynewservice.py
from pathlib import Path
from typing import Dict, Any, Optional

class MyNewService:
    """Service for processing something new"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

    def process(self, file_path: Path, option: Optional[str] = None) -> Dict[str, Any]:
        """
        Process the file and return results.

        Args:
            file_path: Path to input file
            option: Optional processing parameter

        Returns:
            Dictionary with process results
        """
        # Validate input
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Process
        result = {
            "success": True,
            "file": str(file_path),
            "option": option,
            # Add your processing here
        }

        return result
```

### 3. Adding Configuration

Add to config schema:

```python
# studioflow/core/config.py
@dataclass
class MyNewFeatureConfig:
    enabled: bool = True
    setting1: str = "default"
    setting2: int = 42

@dataclass
class Config:
    # ... existing config ...
    mynewfeature: MyNewFeatureConfig = field(default_factory=MyNewFeatureConfig)
```

---

## Code Style

### Python Style Guide

We follow PEP 8 with these additions:

```python
# Imports - grouped and sorted
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.console import Console

from studioflow.core.service import Service

# Type hints - always use them
def process_file(file_path: Path, options: Dict[str, Any]) -> bool:
    """Process a file with given options."""
    pass

# Docstrings - Google style
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Dictionary containing:
            - key1: Description
            - key2: Description

    Raises:
        ValueError: If param2 is negative
    """
    pass

# Error messages - user-friendly
try:
    result = api_call()
except ApiError as e:
    console.print(f"[red]Failed to connect to service: {e}[/red]")
    console.print("[yellow]Tip: Check your API credentials in config[/yellow]")
    raise typer.Exit(1)
```

### Naming Conventions

```python
# Classes - PascalCase
class MediaProcessor:
    pass

# Functions/methods - snake_case
def process_media():
    pass

# Constants - UPPER_SNAKE_CASE
MAX_FILE_SIZE = 1024 * 1024 * 100  # 100MB

# Private methods - leading underscore
def _internal_helper():
    pass
```

---

## Testing

### Test Structure

```python
# tests/unit/test_mynewservice.py
import pytest
from pathlib import Path
from studioflow.core.mynewservice import MyNewService

class TestMyNewService:
    """Test suite for MyNewService"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return MyNewService()

    @pytest.fixture
    def sample_file(self, tmp_path):
        """Create sample file for testing"""
        file = tmp_path / "test.txt"
        file.write_text("test content")
        return file

    def test_process_success(self, service, sample_file):
        """Test successful processing"""
        result = service.process(sample_file)
        assert result["success"] == True
        assert result["file"] == str(sample_file)

    def test_process_missing_file(self, service):
        """Test processing with missing file"""
        with pytest.raises(FileNotFoundError):
            service.process(Path("/nonexistent/file.txt"))
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=studioflow

# Run specific test file
pytest tests/unit/test_mynewservice.py

# Run with verbose output
pytest -v

# Run only marked tests
pytest -m "not slow"
```

---

## Critical Implementation Priorities

### Top 10 Most Impactful Features to Implement

#### 1. Robust Media Import with Verification 🔴 CRITICAL

**Impact:** Prevents data loss and corrupted imports

```python
# Implementation needed in: studioflow/core/media.py
class RobustMediaImporter:
    def import_with_verification(self, source_path: Path, destination: Path):
        """Import with hash verification and corruption detection"""
        
        # Pre-import checks
        if not self._verify_source_accessible(source_path):
            raise MediaSourceError("Cannot access media source")
        
        # Scan for media files
        media_files = self._scan_media_files(source_path)
        
        # Import with verification
        imported = []
        failed = []
        
        for file in track(media_files, description="Importing..."):
            try:
                # Calculate source hash
                source_hash = self._calculate_hash(file)
                
                # Copy with progress
                dest_file = self._copy_with_progress(file, destination)
                
                # Verify copy
                dest_hash = self._calculate_hash(dest_file)
                
                if source_hash != dest_hash:
                    raise VerificationError(f"Hash mismatch for {file}")
                
                # Verify file is readable
                if not self._verify_media_readable(dest_file):
                    raise CorruptedMediaError(f"Cannot read {file}")
                
                imported.append(dest_file)
                
            except Exception as e:
                failed.append((file, str(e)))
                continue
        
        return ImportResult(imported=imported, failed=failed)

# CLI command to add:
sf media import /source --verify --continue-on-error --quarantine-corrupted
```

#### 2. Fallback Video Processing (No Resolve Required) 🔴 CRITICAL

**Impact:** Makes StudioFlow usable without DaVinci Resolve

```python
# Implementation needed in: studioflow/core/video_processor.py
class UniversalVideoProcessor:
    def __init__(self):
        self.backends = {
            'resolve': ResolveBackend(),
            'ffmpeg': FFmpegBackend(),
            'moviepy': MoviePyBackend()
        }
        self.active_backend = None

    def process_video(self, input_path: Path, operations: List[Operation]):
        """Process video with automatic backend selection"""
        
        # Try backends in order of preference
        for backend_name, backend in self.backends.items():
            if backend.is_available():
                self.active_backend = backend
                console.print(f"Using {backend_name} backend")
                break
        else:
            raise NoBackendError("No video processing backend available")
        
        return self.active_backend.process(input_path, operations)
```

#### 3. Resumable Export with Checkpointing 🔴 CRITICAL

**Impact:** Saves hours of re-rendering on failures

```python
# Implementation needed in: studioflow/core/export.py
class ResumableExporter:
    def export_with_checkpoints(self, project: Project, output: Path):
        """Export with ability to resume from failure"""
        
        checkpoint_file = output.with_suffix('.checkpoint')
        
        # Load previous state if exists
        state = self._load_checkpoint(checkpoint_file) or ExportState()
        
        # Segment-based export
        segments = self._split_into_segments(project, segment_duration=60)
        
        for i, segment in enumerate(segments):
            if i < state.last_completed_segment:
                continue  # Skip completed segments
            
            try:
                # Export segment
                segment_file = self._export_segment(segment, i)
                
                # Update checkpoint
                state.completed_segments.append(segment_file)
                state.last_completed_segment = i
                self._save_checkpoint(checkpoint_file, state)
                
            except Exception as e:
                console.print(f"[red]Segment {i} failed: {e}")
                console.print("[yellow]Run export again to resume")
                return False
        
        # Concatenate segments
        self._concatenate_segments(state.completed_segments, output)
        
        # Cleanup
        checkpoint_file.unlink()
        return True
```

#### 4. Smart Duplicate Detection System 🟡 HIGH

**Impact:** Prevents storage waste and confusion

```python
# Implementation needed in: studioflow/core/duplicate_detector.py
class DuplicateDetector:
    def __init__(self):
        self.hash_db = SQLiteHashDB('~/.studioflow/hashes.db')
    
    def check_before_import(self, files: List[Path]) -> Dict[str, Action]:
        """Check files before importing"""
        
        actions = {}
        
        for file in files:
            # Quick check by name and size
            quick_match = self.hash_db.find_by_name_size(
                file.name,
                file.stat().st_size
            )
            
            if quick_match:
                # Deep check with content hash
                file_hash = self._calculate_hash(file)
                
                if quick_match.hash == file_hash:
                    # Exact duplicate
                    actions[file] = self._decide_duplicate_action(file, quick_match)
                else:
                    # Different content, same name
                    actions[file] = Action.RENAME
            else:
                # New file
                actions[file] = Action.IMPORT
        
        return actions
```

#### 5. Automatic Dependency Installation 🟡 HIGH

**Impact:** Eliminates "command not found" errors

```python
# Implementation needed in: studioflow/core/dependencies.py
class DependencyManager:
    def __init__(self):
        self.required_deps = {
            'ffmpeg': {
                'check': 'ffmpeg -version',
                'install': {
                    'darwin': 'brew install ffmpeg',
                    'linux': 'sudo apt install ffmpeg',
                    'win32': self._install_ffmpeg_windows
                }
            },
            # ... more dependencies
        }
    
    def check_and_install(self):
        """Check and install missing dependencies"""
        
        missing = []
        
        for dep, config in self.required_deps.items():
            if not self._check_installed(config['check']):
                missing.append(dep)
        
        if missing:
            console.print(f"[yellow]Missing dependencies: {', '.join(missing)}")
            
            if Confirm.ask("Install missing dependencies?"):
                for dep in missing:
                    self._install_dependency(dep)
            else:
                raise DependencyError("Required dependencies not installed")
```

### Implementation Order & Timeline

**Phase 1: Core Stability (Week 1-2)**
1. Robust Media Import - 3 days
2. Fallback Video Processing - 3 days
3. Automatic Dependencies - 2 days

**Phase 2: Reliability (Week 3-4)**
4. Resumable Export - 3 days
5. Error Recovery System - 2 days
6. Automatic Backup - 2 days

**Phase 3: Quality of Life (Week 5-6)**
7. Smart Duplicate Detection - 2 days
8. Framerate Handling - 2 days
9. Platform Export - 2 days
10. Bandwidth Management - 2 days

---

## Edge Cases & Solutions

### Import & Media Management

#### Problem: Massive Media Import (1TB+)

**Solution:**
```python
class ChunkedImporter:
    def import_large_dataset(self, path: Path, chunk_size: int = 100):
        """Import large media sets in manageable chunks"""
        media_files = self._scan_media(path)
        total_files = len(media_files)
        
        for i in range(0, total_files, chunk_size):
            chunk = media_files[i:i+chunk_size]
            
            # Process chunk with progress
            with Progress() as progress:
                task = progress.add_task("Importing chunk", total=len(chunk))
                
                for file in chunk:
                    self._import_file(file)
                    progress.advance(task)
            
            # Garbage collection between chunks
            gc.collect()
            
            # Allow system to breathe
            time.sleep(0.5)
```

#### Problem: Corrupted File Recovery

**Solution:**
```python
class MediaRecovery:
    def recover_corrupted(self, file_path: Path) -> bool:
        """Attempt to recover corrupted media"""
        strategies = [
            self._try_ffmpeg_recovery,
            self._try_partial_recovery,
            self._try_container_rebuild,
            self._extract_audio_only,
            self._extract_keyframes_only
        ]
        
        for strategy in strategies:
            try:
                if strategy(file_path):
                    console.print(f"[green]Recovered using {strategy.__name__}")
                    return True
            except:
                continue
        
        # Quarantine if unrecoverable
        self._quarantine(file_path)
        return False
```

### Timeline & Editing

#### Problem: Resolve API Connection Failure

**Solution:**
```python
class ResolveConnectionManager:
    def connect_with_fallback(self):
        """Multi-strategy connection approach"""
        strategies = [
            ("Direct API", self._connect_api),
            ("Local Socket", self._connect_socket),
            ("HTTP Bridge", self._connect_http),
            ("File Watch", self._connect_file_watch),
            ("Manual Mode", self._manual_mode)
        ]
        
        for name, method in strategies:
            try:
                connection = method()
                if connection:
                    console.print(f"[green]Connected via {name}")
                    return connection
            except Exception as e:
                console.print(f"[yellow]{name} failed: {e}")
        
        # Fallback to offline mode
        return self._offline_mode()
```

#### Problem: Timeline Framerate Mismatch

**Solution:**
```python
class FramerateHandler:
    def conform_timeline(self, clips: List[Clip], target_fps: float):
        """Smart framerate conforming"""
        strategies = {
            (23.976, 24): self._pulldown_2398_to_24,
            (29.97, 24): self._reverse_telecine,
            (30, 24): self._drop_frames,
            (24, 30): self._add_pulldown,
            (50, 25): self._drop_alternate,
            (60, 30): self._drop_alternate,
            (60, 24): self._complex_pulldown
        }
        
        for clip in clips:
            source_fps = clip.framerate
            
            # Find best conversion strategy
            key = (source_fps, target_fps)
            if key in strategies:
                strategies[key](clip)
            else:
                # Use optical flow for non-standard conversions
                self._optical_flow_retiming(clip, target_fps)
```

### Export & Rendering

#### Problem: Export Crash at 99%

**Solution:**
```python
class ResumableExporter:
    def export_with_checkpoints(self, timeline, output_path):
        """Checkpoint-based resumable export"""
        checkpoint_file = output_path.with_suffix('.checkpoint')
        
        # Load previous progress if exists
        start_frame = 0
        if checkpoint_file.exists():
            checkpoint = self._load_checkpoint(checkpoint_file)
            start_frame = checkpoint['last_frame']
            console.print(f"[yellow]Resuming from frame {start_frame}")
        
        total_frames = timeline.duration * timeline.fps
        chunk_size = 500  # frames
        
        for i in range(start_frame, total_frames, chunk_size):
            end_frame = min(i + chunk_size, total_frames)
            
            # Render chunk
            chunk_file = self._render_chunk(timeline, i, end_frame)
            
            # Save checkpoint
            self._save_checkpoint(checkpoint_file, {
                'last_frame': end_frame,
                'chunks': self._get_completed_chunks()
            })
        
        # Concatenate all chunks
        self._concatenate_chunks(output_path)
```

---

## Features to Remove/Simplify

### 1. Complex Node Graph System for Effects ❌ REMOVE

**Current:** Over-engineered node graph system  
**Replace:** Simple FFmpeg filter chains

```python
# SIMPLE:
class SimpleEffectChain:
    def __init__(self):
        self.effects = []
    
    def add_effect(self, effect_name: str, params: dict):
        self.effects.append((effect_name, params))
    
    def apply(self, video_path: Path) -> Path:
        # Just use FFmpeg filters in sequence
        return apply_ffmpeg_filters(video_path, self.effects)
```

### 2. Abstract Template System Polymorphism ❌ REMOVE

**Current:** Complex inheritance hierarchy  
**Replace:** Simple function-based templates

```python
# SIMPLE:
def apply_template(template_name: str, params: dict):
    templates = {
        'youtube': lambda p: create_youtube_project(p),
        'podcast': lambda p: create_podcast_project(p),
    }
    return templates[template_name](params)
```

### 3. Particle System Animation ❌ REMOVE

**Why:** Not practical for CLI tool, better handled by video editing software

### 4. Multiple Animation Interpolation Types ❌ SIMPLIFY

**Current:** 12 different interpolation types  
**Replace:** Just LINEAR and EASE (covers 99% of cases)

### 5. Custom Shader Support ❌ REMOVE

**Why:** Cannot run shaders from CLI effectively, use built-in FFmpeg filters instead

---

## Best Practices

### 1. Error Handling

```python
# Good - Specific error handling with user guidance
try:
    result = transcribe(file)
except WhisperNotInstalledError:
    console.print("[red]Whisper is not installed[/red]")
    console.print("Install with: pip install openai-whisper")
    raise typer.Exit(1)
except InsufficientMemoryError:
    console.print("[yellow]Not enough memory for this model[/yellow]")
    console.print("Try a smaller model with --model tiny")
    raise typer.Exit(1)

# Bad - Generic error handling
try:
    result = transcribe(file)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
```

### 2. Progress Feedback

```python
# Good - Show progress for long operations
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console
) as progress:
    task = progress.add_task("Processing...", total=len(files))
    
    for file in files:
        process_file(file)
        progress.update(task, advance=1)
```

### 3. Configuration Access

```python
# Good - Use configuration service
from studioflow.core.config import get_config

config = get_config()
api_key = config.youtube.api_key

# Bad - Hardcode values
api_key = "sk-abc123"
```

### 4. Path Handling

```python
# Good - Use pathlib
from pathlib import Path

file_path = Path(user_input).expanduser().resolve()
if not file_path.exists():
    raise FileNotFoundError(f"File not found: {file_path}")

# Bad - String manipulation
file_path = os.path.join(os.path.expanduser(user_input))
```

---

## Contributing

### Pull Request Process

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/studioflow.git
   cd studioflow
   git checkout -b feature/my-new-feature
   ```

2. **Make Changes**
   - Add tests for new functionality
   - Update documentation
   - Follow code style

3. **Test**
   ```bash
   pytest
   black studioflow/
   mypy studioflow/
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "feat: add new feature

   - Detail 1
   - Detail 2

   Closes #123"
   ```

5. **Push and PR**
   ```bash
   git push origin feature/my-new-feature
   # Create PR on GitHub
   ```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

---

**Last Updated**: 2025-01-22  
**Status**: Active Development


