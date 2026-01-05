"""
DaVinci Resolve Direct API Integration
Connects to running Resolve instance for real automation

Requires: Resolve running with scripting enabled
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .config import get_config

# Add Resolve scripting module path
def get_resolve_script_path() -> str:
    """Get Resolve scripting path from config"""
    config = get_config()
    api_path = config.resolve.api_path or config.resolve.install_path / "Developer" / "Scripting" / "Modules"
    return str(api_path)

RESOLVE_SCRIPT_PATH = get_resolve_script_path()
if RESOLVE_SCRIPT_PATH not in sys.path:
    sys.path.append(RESOLVE_SCRIPT_PATH)


def get_resolve():
    """Get connection to running Resolve instance"""
    try:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp("Resolve")
        if resolve is None:
            raise ConnectionError(
                "Could not connect to DaVinci Resolve. "
                "Please ensure Resolve is running and scripting is enabled."
            )
        return resolve
    except ImportError as e:
        config = get_config()
        raise ImportError(
            f"DaVinciResolveScript not found at {RESOLVE_SCRIPT_PATH}. "
            f"Resolve installation path: {config.resolve.install_path}. "
            f"Please verify Resolve is installed and the API path is correct."
        ) from e


@dataclass
class FX30ProjectSettings:
    """Optimized settings for Sony FX30 S-Log3 workflow"""

    # Timeline settings
    timeline_resolution_width: str = "3840"
    timeline_resolution_height: str = "2160"
    timeline_framerate: str = "24"

    # Color Management - FX30 S-Log3 optimized
    color_science: str = "davinciYRGBColorManagedv2"
    input_color_space: str = "S-Gamut3.Cine/S-Log3"
    timeline_color_space: str = "DaVinci Wide Gamut/Intermediate"
    output_color_space: str = "Rec.709 Gamma 2.4"

    # Working folders - will be set from config
    cache_path: str = ""
    proxy_path: str = ""
    working_folder: str = ""

    # Render cache
    render_cache_format: str = "DNxHR SQ"
    optimized_media_format: str = "DNxHR SQ"


class ResolveDirectAPI:
    """Direct Resolve API for automated project creation"""

    def __init__(self):
        self.resolve = get_resolve()
        self.project_manager = None
        self.project = None
        self.media_pool = None

        if self.resolve:
            self.project_manager = self.resolve.GetProjectManager()

    def is_connected(self) -> bool:
        """Check if connected to Resolve"""
        return self.resolve is not None and self.project_manager is not None

    def create_project(self, name: str, settings: FX30ProjectSettings = None, library_path: Path = None) -> bool:
        """
        Create new project with optimized settings
        
        Args:
            name: Project name
            settings: Project settings (defaults to FX30ProjectSettings)
            library_path: Optional library base path (uses config if not provided)
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to DaVinci Resolve. Call is_connected() first.")

        config = get_config()
        
        if settings is None:
            settings = FX30ProjectSettings()
            
            # Get library path from config if not provided
            if library_path is None:
                library_path = config.storage.library or config.storage.active or Path.home() / "Videos" / "StudioFlow" / "Library"
            
            # Set paths from library or use defaults
            if library_path.exists():
                settings.cache_path = str(library_path / "CACHE")
                settings.proxy_path = str(library_path / "PROXIES")
                settings.working_folder = str(library_path / "PROJECTS")
            else:
                # Use config storage paths as fallback
                cache_dir = config.storage.cache or config.storage.active / "CACHE"
                proxy_dir = config.storage.proxy or config.storage.active / "PROXIES"
                projects_dir = config.storage.active / "PROJECTS"
                
                settings.cache_path = str(cache_dir)
                settings.proxy_path = str(proxy_dir)
                settings.working_folder = str(projects_dir)

        # Check if project exists
        try:
            existing = self.project_manager.LoadProject(name)
            if existing:
                print(f"Project '{name}' already exists. Loading...")
                self.project = existing
            else:
                print(f"Creating project: {name}")
                self.project = self.project_manager.CreateProject(name)

            if not self.project:
                raise RuntimeError(f"Failed to create/load project '{name}'")
        except Exception as e:
            raise RuntimeError(f"Error creating Resolve project '{name}': {e}") from e

        self.media_pool = self.project.GetMediaPool()

        # Apply project settings
        self._apply_project_settings(settings)

        return True

    def _apply_project_settings(self, settings: FX30ProjectSettings):
        """Apply all project settings"""

        # Timeline format
        self.project.SetSetting("timelineResolutionWidth", settings.timeline_resolution_width)
        self.project.SetSetting("timelineResolutionHeight", settings.timeline_resolution_height)
        self.project.SetSetting("timelineFrameRate", settings.timeline_framerate)

        # Color management
        self.project.SetSetting("colorScienceMode", settings.color_science)
        self.project.SetSetting("separateColorSpaceAndGamma", "1")

        # For color managed workflow
        self.project.SetSetting("colorSpaceInput", settings.input_color_space)
        self.project.SetSetting("colorSpaceTimeline", settings.timeline_color_space)
        self.project.SetSetting("colorSpaceOutput", settings.output_color_space)

        # Working folders
        self.project.SetSetting("cacheFolder", settings.cache_path)
        
        # Set working folder for project files
        if hasattr(settings, 'working_folder'):
            self.project.SetSetting("workingFolder", settings.working_folder)

        # Render cache format
        self.project.SetSetting("optimizedMediaFormat", settings.optimized_media_format)
        self.project.SetSetting("renderCacheFormat", settings.render_cache_format)

        print("Applied FX30 S-Log3 optimized settings")

    def create_bin_structure(self, structure: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standard bin structure for documentary/YouTube workflow"""

        if structure is None:
            structure = self._get_default_bin_structure()

        if not self.media_pool:
            print("ERROR: No media pool available")
            return {}

        root = self.media_pool.GetRootFolder()
        bins = {"root": root}

        def create_bins_recursive(parent_folder, bin_dict: Dict, parent_path: str = ""):
            for name, content in bin_dict.items():
                # Create the bin
                new_bin = self.media_pool.AddSubFolder(parent_folder, name)
                if new_bin:
                    bin_path = f"{parent_path}/{name}" if parent_path else name
                    bins[bin_path] = new_bin
                    print(f"  Created bin: {bin_path}")

                    # Create sub-bins if nested structure
                    if isinstance(content, dict) and content:
                        create_bins_recursive(new_bin, content, bin_path)

        print("Creating bin structure...")
        create_bins_recursive(root, structure)

        return bins

    def _get_default_bin_structure(self) -> Dict[str, Any]:
        """Default documentary/YouTube bin structure"""
        return {
            "01_MEDIA": {
                "A_ROLL": {},
                "B_ROLL": {},
                "ARCHIVAL": {},
                "SCREEN_REC": {},
                "VFX_RENDERS": {}
            },
            "02_AUDIO": {
                "MUSIC": {},
                "SFX": {},
                "VO": {}
            },
            "03_GRAPHICS": {
                "TITLES": {},
                "LOWER_THIRDS": {},
                "OVERLAYS": {}
            },
            "04_TIMELINES": {
                "01_STRINGOUT": {},
                "02_HOOK_TESTS": {},
                "03_STRUCTURE": {},
                "04_PACING": {},
                "05_FINAL": {},
                "06_SHORTS": {}
            },
            "05_GRADES": {},
            "_SELECTS": {},
            "_ARCHIVE": {}
        }

    def import_media(self, media_paths: List[Path], target_bin: str = None) -> List[Any]:
        """Import media files into project"""
        if not self.media_pool:
            return []

        # Convert paths to strings
        path_strings = [str(p) for p in media_paths if p.exists()]

        if not path_strings:
            print("No valid media paths to import")
            return []

        # Set target folder if specified
        if target_bin:
            root = self.media_pool.GetRootFolder()
            # Navigate to target bin
            target_folder = self._find_bin(root, target_bin)
            if target_folder:
                self.media_pool.SetCurrentFolder(target_folder)

        print(f"Importing {len(path_strings)} files...")
        clips = self.media_pool.ImportMedia(path_strings)

        if clips:
            print(f"Successfully imported {len(clips)} clips")

        return clips or []

    def _find_bin(self, folder, bin_path: str):
        """Find bin by path like '01_MEDIA/A_ROLL'"""
        parts = bin_path.split("/")
        current = folder

        for part in parts:
            subfolders = current.GetSubFolderList()
            found = None
            for subfolder in subfolders:
                if subfolder.GetName() == part:
                    found = subfolder
                    break
            if found:
                current = found
            else:
                return None

        return current

    def create_timeline(self, name: str, clips: List[Any] = None) -> Any:
        """Create timeline with optional clips"""
        if not self.media_pool:
            return None

        if clips:
            timeline = self.media_pool.CreateTimelineFromClips(name, clips)
        else:
            timeline = self.media_pool.CreateEmptyTimeline(name)

        if timeline:
            print(f"Created timeline: {name}")

        return timeline

    def create_timeline_stack(self) -> Dict[str, Any]:
        """Create standard timeline stack for YouTube workflow"""
        timelines = {}

        timeline_names = [
            "01_STRINGOUT",
            "02_HOOK_TESTS",
            "03_STRUCTURE_PASS",
            "04_PACING_PASS",
            "05_FINAL",
            "06_SHORTS_CUTS"
        ]

        print("Creating timeline stack...")
        for name in timeline_names:
            tl = self.create_timeline(name)
            if tl:
                timelines[name] = tl

        return timelines

    def setup_render_presets(self):
        """Create YouTube-optimized render presets"""
        # Note: Render presets must be created via Resolve UI
        # This documents what should be set up
        presets = {
            "YouTube_4K": {
                "format": "MP4",
                "codec": "H.264",
                "encoder": "NVIDIA",
                "resolution": "3840x2160",
                "bitrate": 45000,
                "audio": "AAC 320kbps"
            },
            "YouTube_Master": {
                "format": "QuickTime",
                "codec": "H.265",
                "encoder": "NVIDIA",
                "resolution": "3840x2160",
                "quality": "Best",
                "audio": "AAC 320kbps"
            },
            "Hook_Test": {
                "format": "MP4",
                "codec": "H.264",
                "resolution": "1280x720",
                "bitrate": 8000,
                "audio": "AAC 160kbps"
            },
            "Shorts_Vertical": {
                "format": "MP4",
                "codec": "H.264",
                "resolution": "1080x1920",
                "bitrate": 20000,
                "audio": "AAC 256kbps"
            }
        }

        print("Render presets to create manually in Resolve:")
        for name, settings in presets.items():
            print(f"  {name}: {settings['resolution']} {settings['codec']}")

        return presets

    def apply_input_color_space(self, clip, color_space: str = "S-Gamut3.Cine/S-Log3"):
        """Apply input color space to a clip"""
        if clip:
            clip.SetClipProperty("Input Color Space", color_space)

    def get_project_info(self) -> Dict[str, Any]:
        """Get current project information"""
        if not self.project:
            return {}

        return {
            "name": self.project.GetName(),
            "resolution": f"{self.project.GetSetting('timelineResolutionWidth')}x{self.project.GetSetting('timelineResolutionHeight')}",
            "framerate": self.project.GetSetting("timelineFrameRate"),
            "color_science": self.project.GetSetting("colorScienceMode"),
            "timeline_count": self.project.GetTimelineCount(),
            "media_pool_clips": self._count_media_pool_clips()
        }

    def _count_media_pool_clips(self) -> int:
        """Count clips in media pool"""
        if not self.media_pool:
            return 0

        root = self.media_pool.GetRootFolder()
        return len(root.GetClipList())

    def setup_stock_library(self) -> int:
        """
        Create _STOCK_LIBRARY bin with NAS media imported.
        User should drag this to Power Bins for persistence across projects.
        """
        if not self.media_pool:
            return 0

        root = self.media_pool.GetRootFolder()

        # Check if already exists
        existing = root.GetSubFolderList()
        for folder in existing:
            if folder.GetName() == "_STOCK_LIBRARY":
                print("_STOCK_LIBRARY already exists")
                return 0

        stock_bin = self.media_pool.AddSubFolder(root, "_STOCK_LIBRARY")
        if not stock_bin:
            print("Could not create _STOCK_LIBRARY bin")
            return 0

        print("Creating _STOCK_LIBRARY (drag to Power Bins for persistence)...")

        # Use PowerBinsConfig for optimal structure
        from .power_bins_config import PowerBinsConfig
        power_bin_config = PowerBinsConfig()
        structure = power_bin_config.get_structure()
        
        # Flatten structure for stock library (simpler structure)
        stock_categories = {}
        for category, subcategories in structure.items():
            for subcat_name, subcat_path in subcategories.items():
                # Use category/subcategory as key
                stock_categories[f"{category}_{subcat_name}"] = subcat_path

        total_imported = 0
        for name, path in stock_categories.items():
            sub_bin = self.media_pool.AddSubFolder(stock_bin, name)
            if sub_bin and path.exists():
                # Find media files
                files = []
                for ext in ["*.mp3", "*.wav", "*.mp4", "*.mov", "*.png", "*.jpg", "*.jpeg"]:
                    files.extend(path.glob(ext))
                    files.extend(path.glob(ext.upper()))

                if files:
                    self.media_pool.SetCurrentFolder(sub_bin)
                    imported = self.media_pool.ImportMedia([str(f) for f in files])
                    count = len(imported) if imported else 0
                    total_imported += count
                    print(f"  ✓ {name}: {count} files")
                else:
                    print(f"  ⚠ {name}: (empty or path not found: {path})")
            else:
                print(f"  ✓ {name}: bin created")

        # Reset to root
        self.media_pool.SetCurrentFolder(root)

        print(f"\nTotal stock assets: {total_imported}")
        print("TIP: Drag _STOCK_LIBRARY to Power Bins for use in all projects")

        return total_imported


def create_documentary_project(
    project_name: str,
    media_dir: Path = None,
    settings: FX30ProjectSettings = None,
    setup_stock_library: bool = True,
    library_path: Path = None
) -> Dict[str, Any]:
    """
    One-command documentary project setup optimized for library workflow

    Usage:
        from studioflow.core.resolve_api import create_documentary_project
        result = create_documentary_project("DOC002_Dad", Path("/path/to/footage"))
        
    Args:
        library_path: Base library path (uses config if not provided)
    """
    
    # Auto-detect library path if not provided
    if library_path is None:
        from studioflow.core.config import get_config
        config = get_config()
        library_path = config.storage.library or Path.home() / "Videos" / "StudioFlow" / "Library"

    api = ResolveDirectAPI()

    if not api.is_connected():
        return {"error": "Could not connect to Resolve. Is it running?"}

    # Create project with FX30 settings and library paths
    if not api.create_project(project_name, settings, library_path):
        return {"error": "Failed to create project"}

    # Create bin structure
    bins = api.create_bin_structure()

    # Create timeline stack
    timelines = api.create_timeline_stack()

    # Import media if directory provided
    imported_clips = []
    if media_dir and media_dir.exists():
        # Find all video files
        video_files = list(media_dir.glob("**/*.mp4")) + \
                      list(media_dir.glob("**/*.MP4")) + \
                      list(media_dir.glob("**/*.mov")) + \
                      list(media_dir.glob("**/*.MOV"))

        if video_files:
            imported_clips = api.import_media(video_files, "01_MEDIA/ARCHIVAL")

    # Setup stock library from NAS
    stock_imported = 0
    if setup_stock_library:
        stock_imported = api.setup_stock_library()

    # Get project info
    info = api.get_project_info()

    return {
        "success": True,
        "project_name": project_name,
        "bins_created": len(bins),
        "timelines_created": len(timelines),
        "clips_imported": len(imported_clips),
        "stock_library_clips": stock_imported,
        "project_info": info
    }


# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create Resolve project via API")
    parser.add_argument("name", help="Project name")
    parser.add_argument("--media", "-m", help="Media directory to import", type=Path)
    parser.add_argument("--info", "-i", action="store_true", help="Show current project info")

    args = parser.parse_args()

    if args.info:
        api = ResolveDirectAPI()
        if api.is_connected():
            print(json.dumps(api.get_project_info(), indent=2))
    else:
        result = create_documentary_project(args.name, args.media)
        print(json.dumps(result, indent=2))
