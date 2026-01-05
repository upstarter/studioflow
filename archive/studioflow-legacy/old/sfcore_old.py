#!/usr/bin/env python3
"""
StudioFlow Core Library
Shared functions for all StudioFlow tools
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configuration
STUDIOFLOW_DIR = Path.home() / ".studioflow"
CURRENT_PROJECT_FILE = STUDIOFLOW_DIR / "current_project"
CONFIG_FILE = STUDIOFLOW_DIR / "config.json"

# Storage tiers
STORAGE_TIERS = {
    "ingest": Path("/mnt/ingest"),
    "studio": Path("/mnt/studio/Projects"),
    "render": Path("/mnt/render"),
    "library": Path("/mnt/library"),
    "archive": Path("/mnt/archive"),
    "nas": Path("/mnt/nas")
}

# Default project structure
PROJECT_STRUCTURE = {
    "01_MEDIA": "Raw footage and imports",
    "02_PROJECTS": "DaVinci Resolve projects",
    "03_RENDERS": "Final exports",
    "04_ASSETS": "Graphics, audio, etc",
    ".studioflow": "Project metadata"
}

class StudioFlowCore:
    """Core functionality for StudioFlow"""

    def __init__(self):
        """Initialize StudioFlow core"""
        self.ensure_config()

    def ensure_config(self):
        """Ensure configuration directory exists"""
        STUDIOFLOW_DIR.mkdir(exist_ok=True)

        # Create default config if not exists
        if not CONFIG_FILE.exists():
            default_config = {
                "youtube_settings": {
                    "resolution": "3840x2160",
                    "fps": 29.97,
                    "audio_lufs": -14.0
                },
                "categories": {
                    "test_clip": {"min": 0, "max": 3},
                    "b_roll": {"min": 10, "max": 30},
                    "a_roll": {"min": 60, "max": float('inf')},
                    "general": {"default": True}
                }
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)

    # Project Management
    def get_current_project(self) -> Optional[Path]:
        """Get the current active project path"""
        if CURRENT_PROJECT_FILE.exists():
            project_path = Path(CURRENT_PROJECT_FILE.read_text().strip())
            if project_path.exists():
                return project_path
        return None

    def set_current_project(self, project_path: Path) -> bool:
        """Set the current active project"""
        if not project_path.exists():
            return False
        CURRENT_PROJECT_FILE.write_text(str(project_path.absolute()))
        return True

    def create_project(self, name: str, template: str = "youtube") -> Path:
        """Create a new project with standard structure"""
        # Sanitize name
        safe_name = f"{datetime.now().strftime('%Y%m%d')}_{name.replace(' ', '_')}"
        project_path = STORAGE_TIERS["studio"] / safe_name

        # Create project structure
        for folder, description in PROJECT_STRUCTURE.items():
            (project_path / folder).mkdir(parents=True, exist_ok=True)

        # Create project metadata
        metadata = {
            "name": name,
            "created": datetime.now().isoformat(),
            "template": template,
            "sessions": []
        }

        metadata_file = project_path / ".studioflow" / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Set as current project
        self.set_current_project(project_path)

        return project_path

    # Media Analysis
    def analyze_clip(self, file_path: Path) -> Dict:
        """Analyze a video clip using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                str(file_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            # Extract key information
            duration = float(data.get('format', {}).get('duration', 0))

            # Find video stream
            video_stream = next(
                (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
                {}
            )

            return {
                'filename': file_path.name,
                'path': str(file_path),
                'duration': duration,
                'width': video_stream.get('width', 0),
                'height': video_stream.get('height', 0),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                'codec': video_stream.get('codec_name', ''),
                'category': self.categorize_clip(file_path.name, duration)
            }
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {
                'filename': file_path.name,
                'path': str(file_path),
                'error': str(e)
            }

    def categorize_clip(self, filename: str, duration: float) -> str:
        """Categorize clip based on duration and filename"""
        # Load categories from config
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        categories = config.get('categories', {})

        # Duration-based categorization
        if duration < 3:
            return "test_clip"
        elif duration >= 60:
            return "a_roll"
        elif 10 <= duration <= 30:
            return "b_roll"
        else:
            return "general"

    # Resolve Integration
    def create_resolve_project(self, project_path: Path) -> bool:
        """Create DaVinci Resolve project for the given project"""
        try:
            # Set environment for Resolve API
            env = os.environ.copy()
            env['RESOLVE_SCRIPT_API'] = '/opt/resolve/Developer/Scripting'
            env['PYTHONPATH'] = f"{env['RESOLVE_SCRIPT_API']}/Modules:{env.get('PYTHONPATH', '')}"

            # Run the resolve project creator
            cmd = [
                '/mnt/projects/studioflow/sf-resolve-create-project',
                str(project_path)
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error creating Resolve project: {e}")
            return False

    # Session Management
    def add_import_session(self, project_path: Path, import_data: Dict) -> Dict:
        """Add an import session to the project"""
        metadata_file = project_path / ".studioflow" / "metadata.json"

        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
        else:
            metadata = {"sessions": []}

        session = {
            "timestamp": datetime.now().isoformat(),
            "clips_imported": import_data.get("clips_imported", 0),
            "duration": import_data.get("total_duration", 0),
            "source": import_data.get("source", "unknown")
        }

        metadata["sessions"].append(session)

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return session

    # Status Reporting
    def get_project_status(self, project_path: Path) -> Dict:
        """Get comprehensive project status"""
        status = {
            "path": str(project_path),
            "name": project_path.name,
            "exists": project_path.exists()
        }

        if not project_path.exists():
            return status

        # Load metadata
        metadata_file = project_path / ".studioflow" / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
                status.update(metadata)

        # Count clips
        clips_file = project_path / ".studioflow" / "clips.json"
        if clips_file.exists():
            with open(clips_file) as f:
                clips = json.load(f)
                if isinstance(clips, dict):
                    clips = clips.get('clips', [])

                status["clips_count"] = len(clips)

                # Count by category
                categories = {}
                for clip in clips:
                    cat = clip.get('category', 'unknown')
                    categories[cat] = categories.get(cat, 0) + 1
                status["categories"] = categories

                # Total duration
                total_duration = sum(clip.get('duration', 0) for clip in clips)
                status["total_duration"] = total_duration

        # Check for Resolve project
        resolve_files = list((project_path / ".studioflow" / "resolve").glob("*.fcpxml")) if (project_path / ".studioflow" / "resolve").exists() else []
        status["resolve_ready"] = len(resolve_files) > 0

        return status

# Singleton instance
core = StudioFlowCore()

# Convenience functions
def get_current_project() -> Optional[Path]:
    """Get current project path"""
    return core.get_current_project()

def set_current_project(project_path: Path) -> bool:
    """Set current project"""
    return core.set_current_project(project_path)

def create_project(name: str, template: str = "youtube") -> Path:
    """Create new project"""
    return core.create_project(name, template)

def analyze_clip(file_path: Path) -> Dict:
    """Analyze video clip"""
    return core.analyze_clip(file_path)

def categorize_clip(filename: str, duration: float) -> str:
    """Categorize clip"""
    return core.categorize_clip(filename, duration)

def create_resolve_project(project_path: Path) -> bool:
    """Create Resolve project"""
    return core.create_resolve_project(project_path)

def add_import_session(project_path: Path, import_data: Dict) -> Dict:
    """Add import session"""
    return core.add_import_session(project_path, import_data)

def get_project_status(project_path: Path) -> Dict:
    """Get project status"""
    return core.get_project_status(project_path)