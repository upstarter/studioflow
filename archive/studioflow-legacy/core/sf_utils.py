#!/usr/bin/env python3
"""
sf_utils.py - Minimal shared utilities for StudioFlow tools

Designed to replace sfcore imports with a lightweight, decoupled approach.
Uses JSON events, environment variables, and simple data structures.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Storage tier paths from environment or defaults
STORAGE_TIERS = {
    "ingest": Path(os.getenv("SF_INGEST_PATH", "/mnt/ingest")),
    "active": Path(os.getenv("SF_ACTIVE_PATH", "/mnt/studio/Projects")),
    "render": Path(os.getenv("SF_RENDER_PATH", "/mnt/render")),
    "library": Path(os.getenv("SF_LIBRARY_PATH", "/mnt/library")),
    "archive": Path(os.getenv("SF_ARCHIVE_PATH", "/mnt/archive")),
    "nas": Path(os.getenv("SF_NAS_PATH", "/mnt/nas"))
}

class JsonEvent:
    """Simple JSON event emitter for inter-tool communication"""
    
    @staticmethod
    def emit(event_type: str, data: Dict[str, Any] = None):
        """Emit JSON event to stdout"""
        event = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        print(json.dumps(event), file=sys.stderr)
    
    @staticmethod
    def success(message: str, data: Dict[str, Any] = None):
        """Emit success event"""
        JsonEvent.emit("success", {"message": message, **(data or {})})
    
    @staticmethod
    def error(message: str, data: Dict[str, Any] = None):
        """Emit error event"""
        JsonEvent.emit("error", {"message": message, **(data or {})})
    
    @staticmethod
    def info(message: str, data: Dict[str, Any] = None):
        """Emit info event"""
        JsonEvent.emit("info", {"message": message, **(data or {})})

class ProjectInfo:
    """Simple project information without coupling"""
    
    def __init__(self, path: Path):
        self.path = Path(path)
        self.name = self.path.name
        
        # Standard directory structure
        self.dirs = {
            "media": self.path / "01_MEDIA",
            "audio": self.path / "02_AUDIO",
            "graphics": self.path / "03_GRAPHICS",
            "footage": self.path / "04_FOOTAGE",
            "edits": self.path / "05_EDITS",
            "exports": self.path / "06_EXPORTS",
            "docs": self.path / "07_DOCS"
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "path": str(self.path),
            "dirs": {k: str(v) for k, v in self.dirs.items()}
        }
    
    @classmethod
    def from_env(cls) -> Optional['ProjectInfo']:
        """Create from environment variable SF_PROJECT_PATH"""
        project_path = os.getenv("SF_PROJECT_PATH")
        if project_path and Path(project_path).exists():
            return cls(Path(project_path))
        return None
    
    @classmethod
    def from_name(cls, name: str) -> Optional['ProjectInfo']:
        """Find project by name in active storage"""
        active_dir = STORAGE_TIERS["active"]
        project_path = active_dir / name
        if project_path.exists():
            return cls(project_path)
        return None

def find_project_path(name_or_path: str) -> Optional[Path]:
    """Find project by name or path"""
    # Try as direct path
    path = Path(name_or_path)
    if path.exists() and path.is_dir():
        return path
    
    # Try in active storage
    active_path = STORAGE_TIERS["active"] / name_or_path
    if active_path.exists():
        return active_path
    
    # Try environment variable
    env_path = os.getenv("SF_PROJECT_PATH")
    if env_path:
        return Path(env_path)
    
    return None

def load_config(config_file: str = "studioflow.yml") -> Dict[str, Any]:
    """Load configuration from YAML or JSON"""
    config_path = Path.home() / ".config" / "studioflow" / config_file
    
    if not config_path.exists():
        # Return defaults
        return {
            "storage_tiers": {k: str(v) for k, v in STORAGE_TIERS.items()},
            "whisper_model": "base",
            "youtube_privacy": "private",
            "obs_port": 4455
        }
    
    # Load based on extension
    if config_path.suffix == ".json":
        with open(config_path) as f:
            return json.load(f)
    elif config_path.suffix in [".yml", ".yaml"]:
        try:
            import yaml
            with open(config_path) as f:
                return yaml.safe_load(f)
        except ImportError:
            # Fall back to JSON
            JsonEvent.error("PyYAML not installed, using defaults")
            return {}
    
    return {}

def pipe_to_tool(tool_name: str, data: Any, **kwargs):
    """Pipe data to another StudioFlow tool via subprocess"""
    import subprocess
    
    # Build command
    cmd = [tool_name]
    for key, value in kwargs.items():
        cmd.append(f"--{key}")
        if value is not None:
            cmd.append(str(value))
    
    # Convert data to JSON if dict
    if isinstance(data, dict):
        input_data = json.dumps(data)
    else:
        input_data = str(data)
    
    # Run tool
    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        JsonEvent.error(f"Failed to pipe to {tool_name}", {"error": str(e)})
        return None

def parse_json_stream(input_stream=sys.stdin) -> List[Dict[str, Any]]:
    """Parse JSON events from input stream"""
    events = []
    for line in input_stream:
        line = line.strip()
        if line:
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                # Not JSON, treat as plain text
                pass
    return events

# Compatibility helpers for migration
class CliHelper:
    """Minimal CLI helper for backward compatibility"""
    
    @staticmethod
    def require_project(name_or_path: str) -> ProjectInfo:
        """Get project info or exit"""
        path = find_project_path(name_or_path)
        if not path:
            JsonEvent.error(f"Project not found: {name_or_path}")
            sys.exit(1)
        return ProjectInfo(path)
    
    @staticmethod
    def get_project_or_none(name_or_path: str) -> Optional[ProjectInfo]:
        """Get project info or None"""
        path = find_project_path(name_or_path)
        return ProjectInfo(path) if path else None

# Alias for compatibility
JsonStream = JsonEvent

if __name__ == "__main__":
    # Test utilities
    print("StudioFlow Utilities Test")
    print("=" * 40)
    
    # Test JSON events
    JsonEvent.success("Test successful", {"tool": "sf_utils"})
    
    # Test project finding
    project = ProjectInfo.from_env()
    if project:
        print(f"Project from env: {project.name}")
    
    # Test config loading
    config = load_config()
    print(f"Config loaded: {list(config.keys())}")
    
    # Show storage tiers
    print("\nStorage Tiers:")
    for tier, path in STORAGE_TIERS.items():
        print(f"  {tier}: {path}")