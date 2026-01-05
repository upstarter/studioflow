"""
Storage Manager - Handles different storage configurations
Supports single location, NAS, and multi-tier setups
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import shutil

class StorageManager:
    """Manages storage profiles and project locations"""
    
    def __init__(self, config_manager, profile: Optional[str] = None):
        self.config = config_manager
        self.profile_name = profile or config_manager.config.get('storage', {}).get('profile', 'single')
        # Load full storage config, not just profile
        self.storage_config = config_manager.config.get('storage', {})
        self.profile = self._load_profile(self.profile_name)
    
    def _load_profile(self, profile_name: str) -> Dict[str, Any]:
        """Load a storage profile"""
        
        # Check for custom profile
        custom_profile = self.config.get_storage_profile(profile_name)
        if custom_profile:
            return custom_profile
        
        # Built-in profiles
        profiles = {
            'single': {
                'base_path': self.config.config.get('storage', {}).get('base_path', '~/Videos/Projects'),
                'archive_path': self.config.config.get('storage', {}).get('archive_path', '~/Videos/Archive'),
                'assets_path': self.config.config.get('storage', {}).get('assets_path', '~/Videos/Assets')
            },
            'multi-tier': {
                # This would be customized by user
                'base_path': '/mnt/fast/projects',
                'archive_path': '/mnt/storage/archive',
                'assets_path': '/mnt/storage/assets',
                'cache_path': '/mnt/scratch/cache'
            }
        }
        
        return profiles.get(profile_name, profiles['single'])
    
    def get_project_path(self, project_name: Optional[str] = None) -> Path:
        """Get the base path for creating projects"""
        base = self.profile.get('base_path', '.')
        base_path = Path(base).expanduser()
        
        if project_name:
            return base_path / project_name
        return base_path
    
    def get_archive_path(self) -> Path:
        """Get the archive path"""
        archive = self.profile.get('archive_path', '~/Videos/Archive')
        return Path(archive).expanduser()
    
    def get_assets_path(self) -> Path:
        """Get the shared assets path"""
        assets = self.profile.get('assets_path', '~/Videos/Assets')
        return Path(assets).expanduser()
    
    def get_cache_path(self) -> Path:
        """Get the cache/scratch path"""
        cache = self.profile.get('cache_path')
        if cache:
            return Path(cache).expanduser()
        # Default to system temp if no cache specified
        return Path('/tmp/studioflow-cache')
    
    def archive_project(self, project_path: Path) -> Path:
        """Archive a completed project"""
        
        archive_base = self.get_archive_path()
        year = datetime.now().strftime('%Y')
        
        # Create year-based archive structure
        archive_dir = archive_base / year
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine archive name (handle duplicates)
        project_name = project_path.name
        archive_path = archive_dir / project_name
        
        if archive_path.exists():
            # Add timestamp if duplicate
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_path = archive_dir / f"{project_name}_{timestamp}"
        
        # Move or copy based on profile settings
        if self.profile.get('archive_mode') == 'copy':
            shutil.copytree(project_path, archive_path)
        else:
            shutil.move(str(project_path), str(archive_path))
        
        return archive_path
    
    def setup_project_links(self, project_path: Path, template: Dict[str, Any]):
        """Setup symlinks for multi-tier storage - use all optimized partitions"""
        
        # Only for professional-multi-tier profile (Eric's setup)
        if self.profile_name != 'professional-multi-tier':
            return
        
        # 1. Link to content library for shared assets
        content_library = Path(self.storage_config.get('assets_path', '/mnt/content_library')).expanduser()
        if content_library.exists():
            # Create shared assets directories if they don't exist
            for asset_type in ['music', 'sfx', 'graphics/logos', 'luts', 'stock-footage']:
                asset_dir = content_library / asset_type
                asset_dir.mkdir(parents=True, exist_ok=True)
                
                # Link from project to shared library
                if asset_type in ['music', 'sfx', 'luts', 'stock-footage']:
                    link_path = project_path / 'shared' / asset_type
                    link_path.parent.mkdir(parents=True, exist_ok=True)
                    if not link_path.exists():
                        link_path.symlink_to(asset_dir)
        
        # 2. Setup cache directories - use ramdisk for active, SSD for persistent
        # Active render cache goes to ramdisk (ultra-fast, cleared on reboot)
        ramdisk_path = Path('/mnt/video_ramdisk')
        if ramdisk_path.exists():
            # Active timeline renders to ramdisk
            active_cache = ramdisk_path / 'render_cache' / project_path.name
            active_cache.mkdir(parents=True, exist_ok=True)
            
            active_link = project_path / '.active_cache'
            if not active_link.exists():
                active_link.symlink_to(active_cache)
            
            # Export buffer to ramdisk
            export_buffer = ramdisk_path / 'export_buffer' / project_path.name
            export_buffer.mkdir(parents=True, exist_ok=True)
            
            export_link = project_path / '.export_temp'
            if not export_link.exists():
                export_link.symlink_to(export_buffer)
        
        # Persistent cache - Keep on fast NVMe with project for best performance
        # Since /mnt/studio is 4.4 GB/s, better to keep cache local
        cache_dir = project_path / '.cache'
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
        # No symlink - cache stays on fastest storage!
        
        # DaVinci Resolve cache also stays local
        davinci_cache = project_path / 'CacheClip'
        if not davinci_cache.exists():
            davinci_cache.mkdir(parents=True, exist_ok=True)
        
        # 3. Setup downloads staging area
        download_path = Path(self.storage_config.get('downloads_path', '/mnt/download_stage')).expanduser()
        if download_path.exists():
            project_downloads = download_path / project_path.name
            project_downloads.mkdir(parents=True, exist_ok=True)
            
            # Link downloads directory
            downloads_link = project_path / 'downloads'
            if not downloads_link.exists():
                downloads_link.symlink_to(project_downloads)
        
        # 4. Proxies - Keep on FASTEST NVMe with the project!
        # Since /mnt/studio is our fastest drive (4.4 GB/s), keep proxies local
        proxy_dir = project_path / 'proxies'
        if not proxy_dir.exists():
            proxy_dir.mkdir(parents=True, exist_ok=True)
        # No symlink needed - proxies stay on fastest storage with project!