"""
StudioFlow Configuration System
Allows users to fully customize their directory structures and workflows
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages user configurations with layered overrides"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.studioflow'
        self.config_file = self.config_dir / 'config.yml'
        self.templates_dir = self.config_dir / 'templates'
        self.storage_profiles_file = self.config_dir / 'storage-profiles.yml'
        
        # Create user config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Load configurations in order of precedence
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load config with precedence: ENV > User > Defaults"""
        
        # 1. Start with built-in defaults
        config = self._get_defaults()
        
        # 2. Override with user config if exists
        if self.config_file.exists():
            with open(self.config_file) as f:
                user_config = yaml.safe_load(f) or {}
                config = self._deep_merge(config, user_config)
        
        # 3. Override with environment variables
        config = self._apply_env_overrides(config)
        
        return config
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Built-in defaults - ships with StudioFlow"""
        return {
            'storage': {
                'profile': 'single',  # Most users have one location
                'base_path': '~/Videos/Projects',
                'archive_path': '~/Videos/Archive',
                'assets_path': '~/Videos/Assets'
            },
            'templates': {
                'default': 'minimal'
            },
            'structure': {
                'dirs': {
                    'footage': 'footage',      # Users can rename these
                    'audio': 'audio',
                    'graphics': 'graphics',
                    'exports': 'exports',
                    'cache': 'cache'
                },
                'files': {
                    'project': 'project.drp',   # Default DaVinci
                    'readme': 'README.md',
                    'metadata': 'metadata.yml'
                }
            },
            'naming': {
                'style': 'kebab',  # kebab-case, snake_case, PascalCase, etc
                'date_format': '%Y-%m-%d',
                'include_date': True
            }
        }
    
    def get_user_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a user-defined template"""
        template_file = self.templates_dir / f"{name}.yml"
        if template_file.exists():
            with open(template_file) as f:
                return yaml.safe_load(f)
        return None
    
    def save_user_template(self, name: str, template: Dict[str, Any]):
        """Save a custom template"""
        template_file = self.templates_dir / f"{name}.yml"
        with open(template_file, 'w') as f:
            yaml.dump(template, f, default_flow_style=False)
    
    def get_storage_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a storage profile configuration"""
        if not self.storage_profiles_file.exists():
            return None
        
        with open(self.storage_profiles_file) as f:
            profiles = yaml.safe_load(f) or {}
            return profiles.get(name)
    
    def _deep_merge(self, base: dict, overlay: dict) -> dict:
        """Deep merge overlay onto base"""
        result = base.copy()
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _apply_env_overrides(self, config: dict) -> dict:
        """Apply environment variable overrides"""
        # STUDIOFLOW_BASE_PATH=/custom/path
        if base_path := os.environ.get('STUDIOFLOW_BASE_PATH'):
            config['storage']['base_path'] = base_path
        
        # STUDIOFLOW_STORAGE_PROFILE=professional
        if profile := os.environ.get('STUDIOFLOW_STORAGE_PROFILE'):
            config['storage']['profile'] = profile
        
        return config


# Example user configurations that users can create:

EXAMPLE_USER_CONFIG = """
# ~/.studioflow/config.yml
# This is YOUR configuration - customize everything!

storage:
  profile: custom
  base_path: /my/video/projects
  archive_path: /my/video/archive
  assets_path: /my/shared/assets

structure:
  dirs:
    # Rename directories to your preference
    footage: "01_RAW_FOOTAGE"      # Some prefer numbered
    audio: "02_AUDIO"
    graphics: "03_GFX"
    exports: "04_EXPORTS"
    cache: ".cache"                 # Hidden cache
    
    # Add your own directories
    color: "05_COLOR_GRADE"
    vfx: "06_VFX"
    documents: "07_DOCS"

naming:
  style: "PascalCase"              # MyVideoProject
  date_format: "%Y%m%d"            # 20240820
  include_date: true
  separator: "_"                   # 20240820_MyVideoProject

templates:
  default: my-custom-template      # Use your template by default
"""

EXAMPLE_STORAGE_PROFILES = """
# ~/.studioflow/storage-profiles.yml
# Define different storage setups you use

# Simple setup - everything in one place
simple:
  base_path: ~/Videos/Projects
  archive_path: ~/Videos/Archive
  assets_path: ~/Videos/Assets

# NAS-based setup
nas:
  base_path: /mnt/nas/active-projects
  archive_path: /mnt/nas/archive
  assets_path: /mnt/nas/shared-assets
  cache_path: /tmp/video-cache    # Keep cache local

# Professional multi-tier setup
professional:
  base_path: /fast-ssd/active
  archive_path: /storage/archive
  assets_path: /storage/library
  cache_path: /scratch/cache
  
  # Advanced: specify different paths for different content
  paths_by_type:
    raw_footage: /storage/raw       # Large files on big drive
    audio: /fast-ssd/audio          # Audio on fast drive
    exports: /fast-ssd/exports      # Exports on fast drive
    
# Laptop + External Drive
portable:
  base_path: ~/Videos/Projects
  archive_path: /Volumes/External/Archive
  assets_path: /Volumes/External/Assets
  cache_path: ~/Library/Caches/StudioFlow
"""

EXAMPLE_CUSTOM_TEMPLATE = """
# ~/.studioflow/templates/my-documentary.yml
# Custom template for documentary projects

name: Documentary Template
description: My personal documentary structure

# Directory structure
directories:
  - interviews/scheduled
  - interviews/completed
  - interviews/transcripts
  - broll/locations
  - broll/establishing
  - broll/detail
  - archival/photos
  - archival/videos
  - archival/documents
  - audio/music
  - audio/sfx
  - audio/voiceover/raw
  - audio/voiceover/processed
  - graphics/titles
  - graphics/maps
  - graphics/infographics
  - exports/rough-cuts
  - exports/review
  - exports/final
  - research/scripts
  - research/notes
  - research/releases

# Files to create
files:
  - path: README.md
    content: |
      # {project_name}
      Documentary Project
      
      Director: {user}
      Created: {date}
      
  - path: research/shot-list.md
    content: |
      # Shot List
      
      ## Interviews
      - [ ] 
      
      ## B-Roll
      - [ ]
      
  - path: metadata.yml
    content: |
      project: {project_name}
      type: documentary
      director: {user}
      created: {date}

# Platform-specific exports
platforms:
  - name: broadcast
    path: exports/broadcast
    specs: "1920x1080 ProRes 422"
  
  - name: web
    path: exports/web  
    specs: "1920x1080 H.264"
    
  - name: archive
    path: exports/archive
    specs: "Original quality ProRes 4444"
"""