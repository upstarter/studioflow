"""
Simple project templates for StudioFlow
No abstractions, just practical folder structures with smart defaults
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
import json
from datetime import datetime


def create_project(name: str, template: str, base_path: Path) -> Path:
    """Create project with template structure"""

    templates = {
        "youtube": {
            "folders": [
                "01_Media/Video",
                "01_Media/Audio",
                "01_Media/Images",
                "02_Edits",
                "03_Exports",
                "04_Thumbnails"
            ],
            "config": {
                "resolution": "1920x1080",
                "fps": 30,
                "platform": "youtube"
            }
        },
        "podcast": {
            "folders": [
                "01_Audio/Raw",
                "01_Audio/Processed",
                "02_Transcripts",
                "03_Exports"
            ],
            "config": {
                "sample_rate": 48000,
                "target_lufs": -16,
                "platform": "podcast"
            }
        },
        "short": {
            "folders": [
                "01_Media",
                "02_Edits",
                "03_Exports"
            ],
            "config": {
                "resolution": "1080x1920",
                "fps": 30,
                "platform": "tiktok"
            }
        },
        "basic": {
            "folders": [
                "Media",
                "Edits",
                "Exports"
            ],
            "config": {
                "resolution": "1920x1080",
                "fps": 30,
                "platform": "general"
            }
        }
    }

    # Get template or use basic
    template_data = templates.get(template, templates["basic"])

    # Create project directory
    project_path = base_path / name.replace(" ", "_")
    project_path.mkdir(parents=True, exist_ok=True)

    # Create folder structure
    for folder in template_data["folders"]:
        (project_path / folder).mkdir(parents=True, exist_ok=True)

    # Save config with metadata
    config_data = {
        **template_data["config"],
        "project_name": name,
        "template": template,
        "created": datetime.now().isoformat(),
        "version": "1.0"
    }
    config_file = project_path / "project.yaml"
    config_file.write_text(yaml.dump(config_data, default_flow_style=False))

    # Create .studioflow file for project detection
    studioflow_file = project_path / ".studioflow"
    studioflow_file.write_text(json.dumps({
        "type": "project",
        "template": template,
        "created": datetime.now().isoformat()
    }, indent=2))

    # Create README with more helpful info
    readme = project_path / "README.md"
    readme.write_text(f"""# {name}

## Project Structure
- **01_Media/** - Raw footage and assets
- **02_Edits/** - Working files
- **03_Exports/** - Final outputs

## Quick Commands
```bash
# Import media
sf import /path/to/media

# Export for platform
sf export video.mp4 --platform {template_data["config"]["platform"]}

# Upload
sf upload {template_data["config"]["platform"]}
```
""")

    return project_path


def list_templates() -> List[str]:
    """List available templates"""
    return ["youtube", "podcast", "short", "basic"]


def get_template_info(template: str) -> Dict:
    """Get template information"""
    info = {
        "youtube": {
            "name": "YouTube Video",
            "description": "Standard YouTube video project",
            "platform": "youtube",
            "resolution": "1920x1080"
        },
        "podcast": {
            "name": "Podcast",
            "description": "Audio podcast project",
            "platform": "podcast",
            "resolution": "audio only"
        },
        "short": {
            "name": "Short Form",
            "description": "TikTok/Reels/Shorts",
            "platform": "tiktok",
            "resolution": "1080x1920"
        },
        "basic": {
            "name": "Basic Project",
            "description": "Simple video project",
            "platform": "general",
            "resolution": "1920x1080"
        }
    }
    return info.get(template, info["basic"])


def find_project_root(start_path: Path = None) -> Optional[Path]:
    """Find the project root by looking for .studioflow file"""
    if start_path is None:
        start_path = Path.cwd()

    current = start_path
    while current != current.parent:
        if (current / ".studioflow").exists():
            return current
        current = current.parent

    return None


def load_project_config(project_path: Path = None) -> Dict:
    """Load project configuration"""
    if project_path is None:
        project_path = find_project_root()

    if not project_path:
        return {}

    config_file = project_path / "project.yaml"
    if config_file.exists():
        with open(config_file) as f:
            return yaml.safe_load(f) or {}

    return {}


def get_project_folders(project_path: Path = None) -> Dict[str, Path]:
    """Get project folder paths"""
    if project_path is None:
        project_path = find_project_root()

    if not project_path:
        return {}

    folders = {}

    # Common folder patterns
    patterns = {
        "media": ["*Media*", "01_Media", "Media"],
        "edits": ["*Edit*", "02_Edits", "Edits"],
        "exports": ["*Export*", "03_Exports", "Exports"],
        "thumbnails": ["*Thumb*", "04_Thumbnails", "Thumbnails"]
    }

    for key, patterns_list in patterns.items():
        for pattern in patterns_list:
            matches = list(project_path.glob(pattern))
            if matches:
                folders[key] = matches[0]
                break

    return folders


def create_episode(project_path: Path, episode_name: str) -> Path:
    """Create an episode within a project"""
    episode_path = project_path / "Episodes" / episode_name.replace(" ", "_")
    episode_path.mkdir(parents=True, exist_ok=True)

    # Create episode structure
    for folder in ["Media", "Edits", "Exports"]:
        (episode_path / folder).mkdir(exist_ok=True)

    # Episode metadata
    meta_file = episode_path / "episode.yaml"
    meta_file.write_text(yaml.dump({
        "name": episode_name,
        "created": datetime.now().isoformat(),
        "status": "in_progress"
    }))

    return episode_path


def quick_setup(name: str = None) -> Path:
    """Quick project setup with smart defaults"""
    if name is None:
        name = f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Detect platform preference
    platform = "youtube"  # Default

    # Check for existing projects to infer preference
    base_path = Path.home() / "StudioFlow"
    if base_path.exists():
        for project in base_path.iterdir():
            if project.is_dir() and (project / "project.yaml").exists():
                config = load_project_config(project)
                if "platform" in config:
                    platform = config["platform"]
                    break

    # Map platform to template
    template_map = {
        "youtube": "youtube",
        "tiktok": "short",
        "instagram": "short",
        "podcast": "podcast"
    }
    template = template_map.get(platform, "basic")

    return create_project(name, template, base_path)