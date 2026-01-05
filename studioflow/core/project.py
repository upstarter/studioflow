"""
Project Management Core
Handles project lifecycle with modern patterns
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
import json
import shutil

from pydantic import BaseModel, Field
from rich.console import Console

from studioflow.core.config import get_config, Platform


console = Console()


class ProjectMetadata(BaseModel):
    """Project metadata with validation"""
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    modified_at: datetime = Field(default_factory=datetime.now)
    template: str = "youtube"
    platform: Platform = Platform.YOUTUBE
    resolution: str = "3840x2160"
    framerate: float = 29.97
    media_count: int = 0
    total_size_bytes: int = 0
    tags: List[str] = []
    description: str = ""
    status: str = "active"  # active, archived, completed
    project_type: str = "quick"  # quick, episode, doc, film

    @property
    def human_size(self) -> str:
        """Get human-readable size"""
        size = self.total_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


@dataclass
class ProjectResult:
    """Result of project operations"""
    success: bool
    project_path: Optional[Path] = None
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


class Project:
    """Project management with modern patterns"""

    def __init__(self, name: str, path: Optional[Path] = None):
        self.name = name
        self.config = get_config()

        # Set project path - use library if available
        if path:
            self.path = Path(path)
        else:
            # Prefer studio path if it exists
            studio_path = self.config.storage.studio
            if studio_path and studio_path.exists():
                # If studio_path already ends with "PROJECTS", use it directly
                # Otherwise, append "PROJECTS"
                if studio_path.name == "PROJECTS":
                    projects_dir = studio_path
                else:
                    projects_dir = studio_path / "PROJECTS"
                projects_dir.mkdir(parents=True, exist_ok=True)
                self.path = projects_dir / self._sanitize_name(name)
            else:
                self.path = self.config.storage.active / self._sanitize_name(name)

        self.metadata_file = self.path / ".studioflow" / "project.json"
        self.metadata = self._load_metadata()

    def _sanitize_name(self, name: str) -> str:
        """Sanitize project name for filesystem"""
        # Remove invalid characters
        invalid_chars = '<>:"|?*\\/\0'
        for char in invalid_chars:
            name = name.replace(char, '_')

        # Add timestamp if configured
        if "{date}" in self.config.project.naming_pattern:
            date_str = datetime.now().strftime("%Y%m%d")
            name = f"{date_str}_{name}"

        return name.strip()

    def _load_metadata(self) -> ProjectMetadata:
        """Load or create project metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                data = json.load(f)
            return ProjectMetadata(**data)
        else:
            return ProjectMetadata(name=self.name)

    def save_metadata(self):
        """Save project metadata"""
        self.metadata.modified_at = datetime.now()
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata.dict(), f, indent=2, default=str)

    def create(self,
               template: str = "youtube",
               platform: Platform = Platform.YOUTUBE,
               **kwargs) -> ProjectResult:
        """Create new project with structure"""
        try:
            # Check if exists
            if self.path.exists():
                return ProjectResult(
                    success=False,
                    error=f"Project '{self.name}' already exists at {self.path}"
                )

            # Create directory structure
            self.path.mkdir(parents=True, exist_ok=True)

            for folder in self.config.project.folder_structure:
                (self.path / folder).mkdir(exist_ok=True)

            # Set metadata
            self.metadata.template = template
            self.metadata.platform = platform
            self.metadata.resolution = kwargs.get('resolution', self.config.resolve.default_resolution)
            self.metadata.framerate = kwargs.get('framerate', self.config.resolve.default_framerate)

            # Save metadata
            self.save_metadata()

            # Create template-specific files
            self._apply_template(template)

            return ProjectResult(
                success=True,
                project_path=self.path,
                data={"metadata": self.metadata.dict()}
            )

        except Exception as e:
            return ProjectResult(
                success=False,
                error=str(e)
            )

    def _apply_template(self, template: str):
        """Apply project template"""
        templates = {
            "youtube": self._template_youtube,
            "vlog": self._template_vlog,
            "tutorial": self._template_tutorial,
            "shorts": self._template_shorts,
            "multicam": self._template_multicam,
        }

        if template in templates:
            templates[template]()

    def _template_youtube(self):
        """YouTube optimized template"""
        # Create YouTube-specific folders
        (self.path / "06_THUMBNAILS").mkdir(exist_ok=True)
        (self.path / "07_DESCRIPTIONS").mkdir(exist_ok=True)

        # Create description template
        desc_template = """
[VIDEO TITLE]

In this video...

⏰ TIMESTAMPS:
00:00 Intro
00:30 Main Content
05:00 Conclusion

🔗 LINKS:
- Resource 1:
- Resource 2:

📱 SOCIAL:
- Twitter: @
- Instagram: @

🎵 MUSIC:
- Track:
- Artist:

#youtube #video #tags
"""
        (self.path / "07_DESCRIPTIONS" / "template.txt").write_text(desc_template)

    def _template_vlog(self):
        """Vlog template with date-based organization"""
        (self.path / "B_ROLL").mkdir(exist_ok=True)
        (self.path / "TIMELAPSES").mkdir(exist_ok=True)

    def _template_tutorial(self):
        """Tutorial template with screen recordings"""
        (self.path / "SCREEN_RECORDINGS").mkdir(exist_ok=True)
        (self.path / "SLIDES").mkdir(exist_ok=True)
        (self.path / "CODE_SAMPLES").mkdir(exist_ok=True)

    def _template_shorts(self):
        """YouTube Shorts / TikTok template"""
        (self.path / "VERTICAL_MEDIA").mkdir(exist_ok=True)
        (self.path / "HOOKS").mkdir(exist_ok=True)
        (self.path / "CAPTIONS").mkdir(exist_ok=True)

    def _template_multicam(self):
        """Multi-camera template"""
        (self.path / "CAM_A").mkdir(exist_ok=True)
        (self.path / "CAM_B").mkdir(exist_ok=True)
        (self.path / "AUDIO_SYNC").mkdir(exist_ok=True)

    def import_media(self, source_path: Path, organize: bool = True) -> Dict[str, int]:
        """Import media with smart organization"""
        from studioflow.core.media import MediaImporter

        importer = MediaImporter(self)
        result = importer.import_from_path(source_path, organize=organize)

        # Update metadata
        self.metadata.media_count = result['total_files']
        self.metadata.total_size_bytes += result['total_size']
        self.save_metadata()

        return result

    def get_media_stats(self) -> Dict[str, Any]:
        """Get media statistics for project"""
        stats = {
            "total_files": 0,
            "by_type": {},
            "by_category": {},
            "total_size": 0
        }

        media_dir = self.path / "01_MEDIA"
        if not media_dir.exists():
            return stats

        for file in media_dir.rglob("*"):
            if file.is_file():
                stats["total_files"] += 1
                stats["total_size"] += file.stat().st_size

                # Count by extension
                ext = file.suffix.lower()
                stats["by_type"][ext] = stats["by_type"].get(ext, 0) + 1

                # Count by category (folder)
                category = file.parent.name
                stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        return stats

    def archive(self) -> ProjectResult:
        """Archive project to storage"""
        try:
            archive_path = self.config.storage.archive / self.name

            # Move project to archive
            shutil.move(str(self.path), str(archive_path))

            # Update metadata
            self.path = archive_path
            self.metadata.status = "archived"
            self.save_metadata()

            return ProjectResult(
                success=True,
                project_path=archive_path,
                data={"status": "archived"}
            )
        except Exception as e:
            return ProjectResult(
                success=False,
                error=str(e)
            )

    def delete(self, confirm: bool = True) -> ProjectResult:
        """Delete project (with confirmation)"""
        if confirm:
            from rich.prompt import Confirm
            if not Confirm.ask(f"Delete project '{self.name}'?"):
                return ProjectResult(success=False, error="Cancelled by user")

        try:
            shutil.rmtree(self.path)
            return ProjectResult(success=True)
        except Exception as e:
            return ProjectResult(success=False, error=str(e))


class ProjectManager:
    """Manages all projects"""

    def __init__(self):
        self.config = get_config()
        self.projects_dir = self.config.storage.active

    def list_projects(self, include_archived: bool = False) -> List[Project]:
        """List all projects"""
        projects = []

        # Active projects
        if self.projects_dir.exists():
            for path in self.projects_dir.iterdir():
                if path.is_dir() and (path / ".studioflow" / "project.json").exists():
                    projects.append(Project(path.name, path))

        # Archived projects
        if include_archived and self.config.storage.archive:
            archive_dir = self.config.storage.archive
            if archive_dir.exists():
                for path in archive_dir.iterdir():
                    if path.is_dir() and (path / ".studioflow" / "project.json").exists():
                        projects.append(Project(path.name, path))

        return sorted(projects, key=lambda p: p.metadata.modified_at, reverse=True)

    def get_project(self, name: str) -> Optional[Project]:
        """Get project by name"""
        # Check active projects
        project_path = self.projects_dir / name
        if project_path.exists():
            return Project(name, project_path)

        # Check archived projects
        if self.config.storage.archive:
            archive_path = self.config.storage.archive / name
            if archive_path.exists():
                return Project(name, archive_path)

        return None

    def create_project(self, name: str, **kwargs) -> ProjectResult:
        """Create new project"""
        project = Project(name)
        return project.create(**kwargs)

    def get_recent_projects(self, limit: int = 5) -> List[Project]:
        """Get recently modified projects"""
        projects = self.list_projects()
        return projects[:limit]


# Episode/Doc/Film Support (Simplified)

def create_episode(number: int, title: str, **kwargs) -> ProjectResult:
    """
    Create new episode with standard 8-folder structure

    Args:
        number: Episode number (e.g., 1, 2, 3)
        title: Episode title
        **kwargs: Additional metadata (resolution, framerate, etc.)

    Returns:
        ProjectResult with success status and path
    """
    config = get_config()

    # Format episode ID (EP001, EP002, etc.)
    episode_id = f"EP{number:03d}_{title.replace(' ', '_')}"
    episode_path = config.storage.episodes / episode_id

    try:
        if episode_path.exists():
            return ProjectResult(
                success=False,
                error=f"Episode {episode_id} already exists"
            )

        # Create 8-folder structure
        episode_path.mkdir(parents=True, exist_ok=True)
        folders = [
            "00_script",
            "01_footage",
            "02_graphics",
            "03_resolve",
            "04_audio",
            "05_exports",
            "06_transcripts",
            "07_documents"
        ]

        for folder in folders:
            (episode_path / folder).mkdir(exist_ok=True)

        # Create subdirectories for footage
        (episode_path / "01_footage" / "A_ROLL").mkdir(exist_ok=True)
        (episode_path / "01_footage" / "B_ROLL").mkdir(exist_ok=True)
        (episode_path / "01_footage" / "SCREEN_RECORDINGS").mkdir(exist_ok=True)
        (episode_path / "01_footage" / "VFX_RENDERS").mkdir(exist_ok=True)  # Pre-rendered Fusion effects

        # Create subdirectories for resolve
        (episode_path / "03_resolve" / "PROJECT").mkdir(exist_ok=True)
        (episode_path / "03_resolve" / "GRADES").mkdir(exist_ok=True)
        (episode_path / "03_resolve" / "SMART_BINS").mkdir(exist_ok=True)
        (episode_path / "03_resolve" / "TIMELINES").mkdir(exist_ok=True)

        # Create YouTube-specific structure (cross-platform workflow)
        youtube_path = episode_path / "95_YOUTUBE"
        youtube_path.mkdir(exist_ok=True)
        (youtube_path / "01_HOOKS").mkdir(exist_ok=True)      # First 5-15 seconds variants
        (youtube_path / "02_CALLOUTS").mkdir(exist_ok=True)   # Subscribe, links, chapters
        (youtube_path / "03_BROLL_FAST").mkdir(exist_ok=True) # High-energy cutaways
        (youtube_path / "04_REACTION_PUNCHES").mkdir(exist_ok=True)  # Reaction shots
        (youtube_path / "05_SHORTS_EXPORT").mkdir(exist_ok=True)     # Vertical extracts

        # Create graphics subfolders
        (episode_path / "02_graphics" / "TITLES").mkdir(exist_ok=True)
        (episode_path / "02_graphics" / "LOWER_THIRDS").mkdir(exist_ok=True)
        (episode_path / "02_graphics" / "THUMBNAILS").mkdir(exist_ok=True)

        # Create METADATA.json
        metadata = {
            "episode": f"EP{number:03d}",
            "number": number,
            "title": title.replace('_', ' '),
            "safe_title": title.replace(' ', '_'),
            "created": datetime.now().isoformat(),
            "template": "youtube",
            "cameras": ["FX30", "ZV-E10", "OBS"],
            "status": "pre-production",
            "storage": {
                "ingest": str(config.storage.ingest),
                "cache": str(config.storage.cache / episode_id),
                "proxies": str(config.storage.proxy / episode_id),
                "render": str(config.storage.render / "YOUTUBE_READY" / episode_id),
                "archive": str(config.storage.archive / "EPISODES" / str(datetime.now().year))
            },
            "workflow": {
                "proxy_generation": "automatic",
                "color_space": "Rec.709",
                "target_platforms": ["YouTube", "Shorts", "Instagram"],
                "target_resolution": kwargs.get('resolution', "4K"),
                "frame_rate": kwargs.get('framerate', "60fps")
            }
        }

        with open(episode_path / "METADATA.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create CHECKLIST.md
        checklist = """# Production Checklist

## Pre-Production
- [ ] Script written
- [ ] Storyboard/shot list
- [ ] Equipment ready

## Production
- [ ] Footage captured
- [ ] B-roll recorded
- [ ] Audio recorded

## Post-Production
- [ ] Media imported and organized
- [ ] Proxies generated (if needed)
- [ ] Rough cut complete
- [ ] Fusion effects created
- [ ] **VFX Pre-renders** (render Fusion effects to 01_footage/VFX_RENDERS/)
- [ ] Color grading done
- [ ] Audio mixed (-14 LUFS for YouTube)
- [ ] Graphics/lower thirds added
- [ ] Render cache built (Playback > Render Cache > Smart)
- [ ] Final export (use NVIDIA encoder)

## Publishing
- [ ] Thumbnail created (saved to 02_graphics/THUMBNAILS/)
- [ ] Description written
- [ ] Tags added
- [ ] Uploaded to YouTube

## DaVinci Resolve Workflow Notes
- Cache location: /mnt/ingest/ResolveCache
- Proxy location: /mnt/ingest/ProxyMedia
- Render output: /mnt/render/YOUTUBE_READY/
- Pre-render Fusion effects to VFX_RENDERS/ before final export
- Use H.265 NVIDIA encoder for fastest renders
"""
        (episode_path / "CHECKLIST.md").write_text(checklist)

        # Create resolve_config.json
        resolve_config = {
            "project_name": episode_id,
            "database": "YouTube_2025",
            "settings": {
                "timeline_resolution": "3840x2160",
                "timeline_framerate": "60",
                "color_space": "Rec.709",
                "color_science": "DaVinci YRGB Color Managed"
            },
            "paths": {
                "cache": str(config.storage.cache / episode_id),
                "proxy": str(config.storage.proxy / episode_id),
                "optimized": str(config.storage.optimized / episode_id),
                "render": str(config.storage.render / "YOUTUBE_READY" / episode_id)
            },
            "smart_bins": [
                "FX30_Footage",
                "ZV-E10_Footage",
                "Screen_Recordings",
                "Talking_Head",
                "B_Roll",
                "Graphics",
                "Music",
                "Sound_Effects"
            ],
            "timeline_stack": [
                "01_STRINGOUT",      # Raw assembly: keep vs discard
                "02_HOOK_TESTS",     # First 5-15 seconds ONLY
                "03_STRUCTURE_PASS", # Story order locked
                "04_PACING_PASS",    # Energy tightening
                "05_FINAL_YT",       # Ready for export
                "06_SHORTS_CUTS"     # Vertical extracts
            ],
            "export_presets": [
                "YT_HOOK_PROXY_TEST",      # 720p, 8Mbps, fast testing
                "YT_UNLISTED_RETENTION",   # 1080p, 16-20Mbps, retention test
                "YT_FINAL_DELIVERY"        # 4K, 30-45Mbps, public release
            ],
            "marker_colors": {
                "red": "Hook point / attention grab",
                "yellow": "Chapter marker",
                "green": "Keep / approved",
                "blue": "CTA / callout",
                "purple": "Shorts extract point",
                "white": "Review needed"
            }
        }

        with open(episode_path / "03_resolve" / "PROJECT" / "resolve_config.json", 'w') as f:
            json.dump(resolve_config, f, indent=2)

        console.print(f"[green]✓[/green] Created episode: {episode_id}")
        console.print(f"  Location: {episode_path}")

        return ProjectResult(
            success=True,
            project_path=episode_path,
            data={"episode_id": episode_id, "metadata": metadata}
        )

    except Exception as e:
        return ProjectResult(
            success=False,
            error=f"Failed to create episode: {str(e)}"
        )


def create_doc(number: int, title: str, **kwargs) -> ProjectResult:
    """
    Create new documentary with same 8-folder structure

    Args:
        number: Doc number (e.g., 1, 2, 3)
        title: Documentary title
        **kwargs: Additional metadata

    Returns:
        ProjectResult with success status and path
    """
    config = get_config()

    # Format doc ID (DOC001, DOC002, etc.)
    doc_id = f"DOC{number:03d}_{title.replace(' ', '_')}"
    doc_path = config.storage.docs / doc_id

    try:
        if doc_path.exists():
            return ProjectResult(
                success=False,
                error=f"Documentary {doc_id} already exists"
            )

        # Create same 8-folder structure as episodes
        doc_path.mkdir(parents=True, exist_ok=True)
        folders = [
            "00_script",
            "01_footage",
            "02_graphics",
            "03_resolve",
            "04_audio",
            "05_exports",
            "06_transcripts",
            "07_documents"
        ]

        for folder in folders:
            (doc_path / folder).mkdir(exist_ok=True)

        # Add subfolders for documentary footage
        (doc_path / "01_footage" / "INTERVIEWS").mkdir(exist_ok=True)
        (doc_path / "01_footage" / "B_ROLL").mkdir(exist_ok=True)
        (doc_path / "01_footage" / "ARCHIVAL").mkdir(exist_ok=True)
        (doc_path / "01_footage" / "PHOTOS").mkdir(exist_ok=True)
        (doc_path / "01_footage" / "VFX_RENDERS").mkdir(exist_ok=True)  # Pre-rendered Fusion effects

        # Add resolve subfolders
        (doc_path / "03_resolve" / "PROJECT").mkdir(exist_ok=True)
        (doc_path / "03_resolve" / "GRADES").mkdir(exist_ok=True)
        (doc_path / "03_resolve" / "TIMELINES").mkdir(exist_ok=True)

        # Create basic metadata
        metadata = {
            "doc_id": doc_id,
            "number": number,
            "title": title.replace('_', ' '),
            "created": datetime.now().isoformat(),
            "project_type": "documentary",
            "status": "pre-production",
            "storage": {
                "cache": str(config.storage.cache / doc_id),
                "proxies": str(config.storage.proxy / doc_id),
                "archive": str(config.storage.archive / "DOCS" / str(datetime.now().year))
            }
        }

        with open(doc_path / "METADATA.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        console.print(f"[green]✓[/green] Created documentary: {doc_id}")
        console.print(f"  Location: {doc_path}")

        return ProjectResult(
            success=True,
            project_path=doc_path,
            data={"doc_id": doc_id, "metadata": metadata}
        )

    except Exception as e:
        return ProjectResult(
            success=False,
            error=f"Failed to create documentary: {str(e)}"
        )


def create_film(number: int, title: str, **kwargs) -> ProjectResult:
    """
    Create new film project with same 8-folder structure

    Args:
        number: Film number (e.g., 1, 2, 3)
        title: Film title
        **kwargs: Additional metadata

    Returns:
        ProjectResult with success status and path
    """
    config = get_config()

    # Format film ID (FLM001, FLM002, etc.)
    film_id = f"FLM{number:03d}_{title.replace(' ', '_')}"
    film_path = config.storage.films / film_id

    try:
        if film_path.exists():
            return ProjectResult(
                success=False,
                error=f"Film {film_id} already exists"
            )

        # Create same 8-folder structure
        film_path.mkdir(parents=True, exist_ok=True)
        folders = [
            "00_script",
            "01_footage",
            "02_graphics",
            "03_resolve",
            "04_audio",
            "05_exports",
            "06_transcripts",
            "07_documents"
        ]

        for folder in folders:
            (film_path / folder).mkdir(exist_ok=True)

        # Create basic metadata
        metadata = {
            "film_id": film_id,
            "number": number,
            "title": title.replace('_', ' '),
            "created": datetime.now().isoformat(),
            "project_type": "film",
            "status": "pre-production",
            "storage": {
                "cache": str(config.storage.cache / film_id),
                "proxies": str(config.storage.proxy / film_id),
                "archive": str(config.storage.archive / "FILMS" / str(datetime.now().year))
            }
        }

        with open(film_path / "METADATA.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        console.print(f"[green]✓[/green] Created film: {film_id}")
        console.print(f"  Location: {film_path}")

        return ProjectResult(
            success=True,
            project_path=film_path,
            data={"film_id": film_id, "metadata": metadata}
        )

    except Exception as e:
        return ProjectResult(
            success=False,
            error=f"Failed to create film: {str(e)}"
        )