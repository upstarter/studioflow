#!/usr/bin/env python3
"""
StudioFlow Configuration System
Handles loading and managing user configuration
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

class StudioFlowConfig:
    """Configuration manager for StudioFlow"""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration"""
        self.config_dir = config_dir or Path.home() / ".studioflow"
        self.config_file = self.config_dir / "config.yaml"
        self.default_config_file = self._find_default_config()

        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)

        # Load configuration
        self._config = self._load_config()

    def _find_default_config(self) -> Path:
        """Find the default config file"""
        # Try multiple locations for default config
        possible_locations = [
            Path(__file__).parent / "config" / "default.yaml",
            Path("/opt/studioflow/config/default.yaml"),
            Path("/usr/local/share/studioflow/config/default.yaml"),
            Path.home() / ".local/share/studioflow/config/default.yaml"
        ]

        for location in possible_locations:
            if location.exists():
                return location

        # Fallback: create minimal default
        return self._create_minimal_default()

    def _create_minimal_default(self) -> Path:
        """Create a minimal default config"""
        minimal_config = {
            "user": {"name": os.getenv("USER", "user")},
            "paths": {
                "studio_projects": str(Path.home() / "Videos" / "StudioFlow" / "Projects"),
                "ingest": str(Path.home() / "Videos" / "StudioFlow" / "Ingest"),
                "archive": str(Path.home() / "Videos" / "StudioFlow" / "Archive")
            },
            "project": {
                "resolution": "3840x2160",
                "framerate": 29.97
            },
            "categorization": {
                "test_clip_max": 3,
                "b_roll_min": 10,
                "b_roll_max": 30,
                "a_roll_min": 60
            }
        }

        # Save to config directory
        default_path = self.config_dir / "default.yaml"
        with open(default_path, 'w') as f:
            yaml.dump(minimal_config, f, indent=2)

        return default_path

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_file.exists():
            self._create_user_config()

        try:
            with open(self.config_file) as f:
                config = yaml.safe_load(f)

            # Expand environment variables
            return self._expand_variables(config)

        except Exception as e:
            print(f"Warning: Error loading config: {e}")
            print("Using default configuration")
            return self._get_default_config()

    def _expand_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Expand environment variables in config values"""
        def expand_value(value):
            if isinstance(value, str):
                # Replace ${VAR} with environment variable
                import re
                def replace_var(match):
                    var_name = match.group(1)
                    return os.getenv(var_name, match.group(0))

                return re.sub(r'\$\{([^}]+)\}', replace_var, value)
            elif isinstance(value, dict):
                return {k: expand_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [expand_value(item) for item in value]
            else:
                return value

        return expand_value(config)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        try:
            with open(self.default_config_file) as f:
                return yaml.safe_load(f)
        except:
            return self._create_minimal_default_dict()

    def _create_minimal_default_dict(self) -> Dict[str, Any]:
        """Create minimal default config as dict"""
        return {
            "user": {"name": os.getenv("USER", "user")},
            "paths": {
                "studio_projects": str(Path.home() / "Videos" / "Projects"),
                "ingest": str(Path.home() / "Videos" / "Ingest")
            },
            "project": {"resolution": "3840x2160", "framerate": 29.97},
            "categorization": {"test_clip_max": 3, "a_roll_min": 60}
        }

    def _create_user_config(self):
        """Create user configuration file from default"""
        try:
            if self.default_config_file.exists():
                shutil.copy2(self.default_config_file, self.config_file)
                print(f"Created config file: {self.config_file}")
            else:
                # Create minimal config
                config = self._create_minimal_default_dict()
                with open(self.config_file, 'w') as f:
                    yaml.dump(config, f, indent=2)
                print(f"Created minimal config: {self.config_file}")
        except Exception as e:
            print(f"Warning: Could not create config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'paths.studio_projects')"""
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self._config

        # Navigate to parent
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set value
        config[keys[-1]] = value

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self._config, f, indent=2)
            print(f"Configuration saved to: {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")

    @property
    def username(self) -> str:
        """Get username"""
        return self.get('user.name', os.getenv('USER', 'user'))

    @property
    def studio_projects(self) -> Path:
        """Get studio projects directory"""
        path = self.get('paths.studio_projects', str(Path.home() / "Videos" / "Projects"))
        return Path(path).expanduser().resolve()

    @property
    def ingest_dir(self) -> Path:
        """Get ingest directory"""
        path = self.get('paths.ingest', str(Path.home() / "Videos" / "Ingest"))
        return Path(path).expanduser().resolve()

    @property
    def archive_dir(self) -> Path:
        """Get archive directory"""
        path = self.get('paths.archive', str(Path.home() / "Videos" / "Archive"))
        return Path(path).expanduser().resolve()

    @property
    def resolve_api_path(self) -> Path:
        """Get Resolve API path"""
        path = self.get('resolve.api_path', '/opt/resolve/Developer/Scripting')
        return Path(path)

    @property
    def resolve_enabled(self) -> bool:
        """Check if Resolve integration is enabled"""
        return self.get('resolve.enabled', True)

    def get_categorization_rules(self) -> Dict[str, float]:
        """Get clip categorization rules"""
        return {
            'test_clip_max': self.get('categorization.test_clip_max', 3),
            'b_roll_min': self.get('categorization.b_roll_min', 10),
            'b_roll_max': self.get('categorization.b_roll_max', 30),
            'a_roll_min': self.get('categorization.a_roll_min', 60)
        }

    def get_project_settings(self) -> Dict[str, Any]:
        """Get default project settings"""
        return {
            'resolution': self.get('project.resolution', '3840x2160'),
            'framerate': self.get('project.framerate', 29.97),
            'template': self.get('project.template', 'YouTube 4K30'),
            'folder_structure': self.get('project.folder_structure', [
                "01_MEDIA", "02_PROJECTS", "03_RENDERS", "04_ASSETS", ".studioflow"
            ])
        }

    def validate(self) -> bool:
        """Validate configuration"""
        errors = []

        # Check required paths exist or can be created
        for path_key in ['studio_projects', 'ingest_dir', 'archive_dir']:
            path = getattr(self, path_key)
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create {path_key} at {path}: {e}")

        # Check Resolve API if enabled
        if self.resolve_enabled:
            api_path = self.resolve_api_path
            if not api_path.exists():
                print(f"Warning: Resolve API path not found: {api_path}")
                print("Resolve integration may not work")

        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    def print_config(self):
        """Print current configuration"""
        print("StudioFlow Configuration:")
        print(f"  Config file: {self.config_file}")
        print(f"  Username: {self.username}")
        print(f"  Projects: {self.studio_projects}")
        print(f"  Ingest: {self.ingest_dir}")
        print(f"  Archive: {self.archive_dir}")
        print(f"  Resolve: {'Enabled' if self.resolve_enabled else 'Disabled'}")

        rules = self.get_categorization_rules()
        print("  Categorization:")
        print(f"    Test clips: < {rules['test_clip_max']}s")
        print(f"    B-roll: {rules['b_roll_min']}-{rules['b_roll_max']}s")
        print(f"    A-roll: > {rules['a_roll_min']}s")

# Global config instance
_config = None

def get_config() -> StudioFlowConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = StudioFlowConfig()
    return _config

def reload_config():
    """Reload configuration from file"""
    global _config
    _config = None
    return get_config()

# Convenience functions
def get_studio_projects() -> Path:
    return get_config().studio_projects

def get_username() -> str:
    return get_config().username

def get_categorization_rules() -> Dict[str, float]:
    return get_config().get_categorization_rules()

def get_project_settings() -> Dict[str, Any]:
    return get_config().get_project_settings()

if __name__ == "__main__":
    # Test configuration system
    config = get_config()
    config.print_config()

    if config.validate():
        print("\n✅ Configuration is valid")
    else:
        print("\n❌ Configuration has errors")