#!/usr/bin/env python3
"""
StudioFlow Core Library (v2.0)
Shared functions for all StudioFlow tools with configuration support
"""

import json
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Import configuration system
try:
    from sfconfig import get_config, get_categorization_rules, get_project_settings, get_studio_projects, get_username
except ImportError:
    # Fallback for old system
    print("Warning: Configuration system not available, using defaults")

    def get_config():
        class FallbackConfig:
            def studio_projects(self): return Path("/mnt/studio/Projects")
            def ingest_dir(self): return Path("/mnt/ingest")
            def username(self): return "eric"
        return FallbackConfig()

    def get_categorization_rules(): return {"test_clip_max": 3, "b_roll_min": 10, "b_roll_max": 30, "a_roll_min": 60}
    def get_project_settings(): return {"resolution": "3840x2160", "framerate": 29.97}
    def get_studio_projects(): return Path("/mnt/studio/Projects")
    def get_username(): return "eric"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StudioFlowCore:
    """Core functionality for StudioFlow with configuration support"""

    def __init__(self):
        """Initialize StudioFlow core"""
        self.config = get_config()
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure required directories exist"""
        try:
            # Create config directory
            config_dir = Path.home() / ".studioflow"
            config_dir.mkdir(exist_ok=True)

            # Create project directories
            for attr in ['studio_projects', 'ingest_dir', 'archive_dir']:
                if hasattr(self.config, attr):
                    path = getattr(self.config, attr)
                    path.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.warning(f"Could not create directories: {e}")

    # Project Management
    def get_current_project(self) -> Optional[Path]:
        """Get the current active project path"""
        current_project_file = Path.home() / ".studioflow" / "current_project"

        if current_project_file.exists():
            try:
                project_path = Path(current_project_file.read_text().strip())
                if project_path.exists():
                    return project_path
            except Exception as e:
                logger.warning(f"Error reading current project: {e}")

        return None

    def set_current_project(self, project_path: Path) -> bool:
        """Set the current active project"""
        if not project_path.exists():
            logger.error(f"Project path does not exist: {project_path}")
            return False

        try:
            current_project_file = Path.home() / ".studioflow" / "current_project"
            current_project_file.write_text(str(project_path.absolute()))
            logger.info(f"Set current project: {project_path}")
            return True
        except Exception as e:
            logger.error(f"Error setting current project: {e}")
            return False

    def create_project(self, name: str, template: str = "youtube") -> Path:
        """Create a new project with standard structure"""
        try:
            # Sanitize name
            safe_name = f"{datetime.now().strftime('%Y%m%d')}_{name.replace(' ', '_')}"
            project_path = self.config.studio_projects / safe_name

            # Get project settings from config
            project_settings = get_project_settings()
            folder_structure = project_settings.get('folder_structure', [
                "01_MEDIA", "02_PROJECTS", "03_RENDERS", "04_ASSETS", ".studioflow"
            ])

            # Create project structure
            for folder in folder_structure:
                (project_path / folder).mkdir(parents=True, exist_ok=True)

            # Create project metadata
            metadata = {
                "name": name,
                "created": datetime.now().isoformat(),
                "template": template,
                "settings": project_settings,
                "sessions": []
            }

            metadata_file = project_path / ".studioflow" / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Initialize empty clips file
            clips_file = project_path / ".studioflow" / "clips.json"
            clips_file.write_text("[]")

            # Set as current project
            self.set_current_project(project_path)

            logger.info(f"Created project: {project_path}")
            return project_path

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise

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

            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            data = json.loads(result.stdout)

            # Extract key information
            duration = float(data.get('format', {}).get('duration', 0))

            # Find video stream
            video_stream = next(
                (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
                {}
            )

            # Calculate fps safely
            fps = 0
            if 'r_frame_rate' in video_stream:
                try:
                    num, den = video_stream['r_frame_rate'].split('/')
                    fps = float(num) / float(den) if float(den) != 0 else 0
                except:
                    fps = 0

            return {
                'filename': file_path.name,
                'path': str(file_path),
                'duration': duration,
                'width': video_stream.get('width', 0),
                'height': video_stream.get('height', 0),
                'fps': fps,
                'codec': video_stream.get('codec_name', ''),
                'category': self.categorize_clip(file_path.name, duration)
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout analyzing {file_path}")
            return {'filename': file_path.name, 'path': str(file_path), 'error': 'Analysis timeout'}
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {'filename': file_path.name, 'path': str(file_path), 'error': str(e)}

    def categorize_clip(self, filename: str, duration: float) -> str:
        """Categorize clip based on duration and filename using config rules"""
        try:
            rules = get_categorization_rules()

            if duration < rules['test_clip_max']:
                return "test_clip"
            elif duration >= rules['a_roll_min']:
                return "a_roll"
            elif rules['b_roll_min'] <= duration <= rules['b_roll_max']:
                return "b_roll"
            else:
                return "general"

        except Exception as e:
            logger.warning(f"Error categorizing clip: {e}")
            # Fallback to hardcoded rules
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
        if not self.config.resolve_enabled:
            logger.info("Resolve integration disabled in config")
            return False

        try:
            # Set environment for Resolve API
            env = os.environ.copy()
            api_path = str(self.config.resolve_api_path)
            env['RESOLVE_SCRIPT_API'] = api_path
            env['PYTHONPATH'] = f"{api_path}/Modules:{env.get('PYTHONPATH', '')}"

            # Get the current studioflow directory dynamically
            studioflow_dir = Path(__file__).parent

            # Run the resolve project creator
            cmd = [
                str(studioflow_dir / 'sf-resolve-create-project'),
                str(project_path)
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                logger.info("Resolve project created successfully")
                return True
            else:
                logger.error(f"Resolve project creation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Timeout creating Resolve project")
            return False
        except Exception as e:
            logger.error(f"Error creating Resolve project: {e}")
            return False

    # Session Management
    def add_import_session(self, project_path: Path, import_data: Dict) -> Dict:
        """Add an import session to the project"""
        try:
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
                "source": import_data.get("source", "unknown"),
                "user": get_username()
            }

            metadata["sessions"].append(session)

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Added import session: {session['clips_imported']} clips")
            return session

        except Exception as e:
            logger.error(f"Error adding import session: {e}")
            return {}

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

        try:
            # Load metadata
            metadata_file = project_path / ".studioflow" / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    status.update(metadata)

            # Count clips - try both possible filenames
            clips_data = []
            for clips_filename in ['clips.json', 'clips_metadata.json']:
                clips_file = project_path / ".studioflow" / clips_filename
                if clips_file.exists():
                    with open(clips_file) as f:
                        clips_data = json.load(f)
                        if isinstance(clips_data, dict):
                            clips_data = clips_data.get('clips', [])
                    break

            if clips_data:
                status["clips_count"] = len(clips_data)

                # Count by category
                categories = {}
                for clip in clips_data:
                    cat = clip.get('category', 'unknown')
                    categories[cat] = categories.get(cat, 0) + 1
                status["categories"] = categories

                # Total duration
                total_duration = sum(clip.get('duration', 0) for clip in clips_data)
                status["total_duration"] = total_duration

            # Check for Resolve project
            resolve_dir = project_path / ".studioflow" / "resolve"
            if resolve_dir.exists():
                resolve_files = list(resolve_dir.glob("*.fcpxml")) + list(resolve_dir.glob("*.xml"))
                status["resolve_ready"] = len(resolve_files) > 0
            else:
                status["resolve_ready"] = False

        except Exception as e:
            logger.warning(f"Error getting project status: {e}")

        return status

    def find_studioflow_install_dir(self) -> Path:
        """Find StudioFlow installation directory"""
        # Try to find it relative to this file
        current_dir = Path(__file__).parent.resolve()

        # Common locations to check
        possible_dirs = [
            current_dir,  # Current directory
            Path("/opt/studioflow"),
            Path("/usr/local/share/studioflow"),
            Path.home() / ".local/share/studioflow"
        ]

        for dir_path in possible_dirs:
            if (dir_path / "sf").exists():
                return dir_path

        # Default to current directory
        return current_dir

# Create singleton instance
core = StudioFlowCore()

# Convenience functions for backward compatibility
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