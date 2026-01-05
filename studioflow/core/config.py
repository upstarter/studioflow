"""
Configuration Management with Pydantic Validation
Modern config system with type safety and validation
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from enum import Enum
import os
import yaml

from pydantic import BaseModel, Field, validator, DirectoryPath, FilePath
from pydantic_settings import BaseSettings


class Platform(str, Enum):
    """Supported platforms"""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    VIMEO = "vimeo"


class StorageConfig(BaseModel):
    """Storage tier configuration"""
    ingest: Path = Field(default_factory=lambda: Path.home() / "Videos" / "StudioFlow" / "Ingest")
    active: Path = Field(default_factory=lambda: Path.home() / "Videos" / "StudioFlow" / "Projects")
    render: Path = Field(default_factory=lambda: Path.home() / "Videos" / "StudioFlow" / "Render")
    archive: Path = Field(default_factory=lambda: Path.home() / "Videos" / "StudioFlow" / "Archive")
    library: Optional[Path] = Field(default_factory=lambda: Path("/mnt/library/PROJECTS") if Path("/mnt/library/PROJECTS").exists() else (Path("/mnt/library") if Path("/mnt/library").exists() else None))
    nas: Optional[Path] = None

    # Content-type specific paths
    episodes: Optional[Path] = None
    films: Optional[Path] = None
    docs: Optional[Path] = None

    # Cache paths
    cache: Optional[Path] = None
    proxy: Optional[Path] = None
    optimized: Optional[Path] = None

    @validator("*", pre=True)
    def expand_paths(cls, v):
        """Expand environment variables and ~ in paths"""
        if isinstance(v, str):
            v = os.path.expandvars(os.path.expanduser(v))
            return Path(v)
        return v

    def ensure_dirs(self):
        """Create storage directories if they don't exist"""
        for field_name, path in self:
            if path and not path.exists():
                path.mkdir(parents=True, exist_ok=True)


class ResolveConfig(BaseModel):
    """DaVinci Resolve configuration"""
    install_path: Path = Path("/opt/resolve")
    api_path: Optional[Path] = None
    enabled: bool = True
    default_framerate: float = 29.97
    default_resolution: str = "3840x2160"
    color_space: str = "Rec.709"

    @validator("api_path", always=True)
    def set_api_path(cls, v, values):
        """Auto-detect API path if not set"""
        if v is None and "install_path" in values:
            api_path = values["install_path"] / "Developer" / "Scripting"
            if api_path.exists():
                return api_path
        return v


class ProjectConfig(BaseModel):
    """Project defaults configuration"""
    default_template: str = "youtube"
    folder_structure: List[str] = [
        "01_MEDIA",
        "02_AUDIO",
        "03_GRAPHICS",
        "04_PROJECTS",
        "05_RENDERS",
        ".studioflow"
    ]
    naming_pattern: str = "{date}_{name}_{type}"
    auto_categorize: bool = True


class MediaConfig(BaseModel):
    """Media import configuration"""
    extensions: List[str] = [".mp4", ".mov", ".avi", ".mkv", ".mxf"]
    image_extensions: List[str] = [".jpg", ".png", ".tiff", ".bmp"]
    audio_extensions: List[str] = [".wav", ".mp3", ".aac", ".m4a"]

    # Categorization rules (in seconds)
    test_clip_max: int = 3
    b_roll_min: int = 10
    b_roll_max: int = 30
    a_roll_min: int = 60

    verify_checksums: bool = True
    skip_duplicates: bool = True
    parallel_copy: bool = True
    preserve_structure: bool = False


class YouTubeConfig(BaseModel):
    """YouTube specific configuration"""
    upload_defaults: Dict[str, Any] = {
        "privacy": "private",
        "category": "28",  # Science & Technology
        "language": "en",
        "embeddable": True,
        "publicStatsViewable": True
    }
    thumbnail_template: Optional[str] = None
    description_template: Optional[str] = None
    tags_template: List[str] = []
    optimal_length_minutes: int = 10
    schedule_time: str = "14:00"  # 2 PM
    schedule_days: List[str] = ["tuesday", "thursday"]


class Config(BaseSettings):
    """Main StudioFlow configuration"""

    # User settings
    user_name: str = Field(default_factory=lambda: os.getenv("USER", "user"))
    notifications: bool = True
    theme: str = "auto"

    # Component configs
    storage: StorageConfig = Field(default_factory=StorageConfig)
    resolve: ResolveConfig = Field(default_factory=ResolveConfig)
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    media: MediaConfig = Field(default_factory=MediaConfig)
    youtube: YouTubeConfig = Field(default_factory=YouTubeConfig)

    # Advanced settings
    log_level: str = "INFO"
    telemetry: bool = False
    auto_update: bool = True
    plugins_enabled: List[str] = []

    model_config = {
        "env_prefix": "STUDIOFLOW_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Allow extra fields from old configs
    }


class ConfigManager:
    """Manages configuration loading, saving, and migration"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".studioflow"
        self.config_file = self.config_dir / "config.yaml"
        self.config_dir.mkdir(exist_ok=True)

        # Load or create config
        self.config = self._load_config()

    def _load_config(self) -> Config:
        """Load config from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    data = yaml.safe_load(f)
                return Config(**data) if data else Config()
            except Exception as e:
                print(f"Error loading config: {e}")
                return self._create_default()
        else:
            return self._create_default()

    def _create_default(self) -> Config:
        """Create and save default configuration"""
        config = Config()
        self.save(config)
        return config

    def save(self, config: Optional[Config] = None):
        """Save configuration to file"""
        config = config or self.config

        # Convert to dict and save
        data = config.dict(exclude_unset=False)

        # Convert Path objects to strings for YAML compatibility
        data = self._paths_to_strings(data)

        with open(self.config_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _paths_to_strings(self, obj):
        """Recursively convert Path objects to strings"""
        from pathlib import Path

        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._paths_to_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._paths_to_strings(item) for item in obj]
        else:
            return obj

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot notation"""
        parts = key.split('.')
        value = self.config.dict()

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set config value by dot notation"""
        parts = key.split('.')
        data = self.config.dict()

        # Navigate to the parent
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set the value
        current[parts[-1]] = value

        # Recreate config and save
        self.config = Config(**data)
        self.save()

    def all(self) -> Dict[str, Any]:
        """Get all config as dict"""
        return self.config.dict()

    def migrate_from_legacy(self, legacy_path: Path):
        """Migrate from old sfconfig.py format"""
        # Implementation for migrating old config
        pass

    def validate(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []

        # Check storage paths
        for name, path in self.config.storage:
            if path and not path.exists():
                issues.append(f"Storage path '{name}' does not exist: {path}")

        # Check Resolve installation
        if self.config.resolve.enabled:
            if not self.config.resolve.install_path.exists():
                issues.append(f"DaVinci Resolve not found at: {self.config.resolve.install_path}")

        return issues

    def setup_wizard(self):
        """Interactive setup wizard for first-time configuration"""
        from rich.console import Console
        from rich.prompt import Prompt, Confirm

        console = Console()
        console.print("[bold cyan]StudioFlow Setup Wizard[/bold cyan]\n")

        # Get user preferences
        storage_root = Prompt.ask(
            "Where should StudioFlow store projects?",
            default=str(Path.home() / "Videos" / "StudioFlow")
        )

        use_resolve = Confirm.ask("Do you use DaVinci Resolve?", default=True)

        if use_resolve:
            resolve_path = Prompt.ask(
                "Where is DaVinci Resolve installed?",
                default="/opt/resolve"
            )
            self.config.resolve.install_path = Path(resolve_path)
            self.config.resolve.enabled = True

        # Set storage paths
        storage_root = Path(storage_root)
        self.config.storage.ingest = storage_root / "Ingest"
        self.config.storage.active = storage_root / "Projects"
        self.config.storage.render = storage_root / "Render"
        self.config.storage.archive = storage_root / "Archive"

        # Create directories
        self.config.storage.ensure_dirs()

        # Save configuration
        self.save()

        console.print("\n[green]✅ Configuration saved![/green]")
        console.print(f"Config file: [cyan]{self.config_file}[/cyan]")

        return self.config


# Singleton instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> Config:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance.config


def reload_config():
    """Reload configuration from disk"""
    global _config_instance
    _config_instance = ConfigManager()
    return _config_instance.config