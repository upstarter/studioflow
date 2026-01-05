# StudioFlow Development Guide 🔧

Guide for extending and contributing to StudioFlow.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Adding New Features](#adding-new-features)
- [Code Style](#code-style)
- [Testing](#testing)
- [Best Practices](#best-practices)
- [Performance Guidelines](#performance-guidelines)
- [Contributing](#contributing)

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

    @pytest.mark.parametrize("option,expected", [
        ("option1", "result1"),
        ("option2", "result2"),
    ])
    def test_process_options(self, service, sample_file, option, expected):
        """Test processing with different options"""
        result = service.process(sample_file, option=option)
        assert result["processed"] == expected
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

### Test Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_video():
    """Provide sample video file path"""
    return Path(__file__).parent / "fixtures" / "sample.mp4"

@pytest.fixture
def mock_youtube_api(monkeypatch):
    """Mock YouTube API calls"""
    def mock_upload(*args, **kwargs):
        return {"success": True, "id": "test123"}

    monkeypatch.setattr(
        "studioflow.core.youtube_api.YouTubeAPIService.upload_video",
        mock_upload
    )
```

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

# Bad - No feedback
for file in files:
    process_file(file)
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

## Performance Guidelines

### 1. Lazy Loading

```python
# Good - Import heavy modules only when needed
def transcribe_audio(file: Path):
    """Transcribe audio file"""
    # Import here to avoid loading at startup
    import whisper
    model = whisper.load_model("base")
    return model.transcribe(str(file))

# Bad - Import at module level
import whisper  # Loads model even if not used
```

### 2. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param: str) -> Dict:
    """Cache results of expensive operations"""
    # This result will be cached
    return perform_calculation(param)
```

### 3. Streaming Large Files

```python
# Good - Process in chunks
def process_large_file(file_path: Path):
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            process_chunk(chunk)

# Bad - Load entire file
def process_large_file(file_path: Path):
    data = file_path.read_bytes()  # Could be GB of data!
    process_data(data)
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

Example:
```
feat(youtube): add chapter extraction from transcripts

- Parse timestamps from Whisper output
- Generate YouTube-formatted chapters
- Add --chapters flag to transcribe command

Closes #456
```

---

## Debug Mode

Enable debug logging:

```bash
# Environment variable
export SF_DEBUG=1
sf new "Test"

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

Debug output locations:
- `~/.studioflow/logs/` - Application logs
- `~/.studioflow/debug/` - Debug dumps
- Console with `SF_DEBUG=1`

---

## Release Process

1. **Update Version**
   ```python
   # studioflow/__init__.py
   __version__ = "1.2.0"
   ```

2. **Update Changelog**
   ```markdown
   # CHANGELOG.md
   ## [1.2.0] - 2024-01-20
   ### Added
   - New feature X
   ### Fixed
   - Bug Y
   ```

3. **Tag Release**
   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```

4. **Build and Publish**
   ```bash
   python setup.py sdist bdist_wheel
   twine upload dist/*
   ```

---

**Happy coding!** 🚀

For questions, open an issue on GitHub or reach out to the team.