"""
Creator Studio Manager - Integrates with optimized NVMe storage layout
Designed for YouTube content creators with professional camera workflows
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import shutil
from datetime import datetime
import re

class CreatorStudioManager:
    """Manages the complete Creator Studio storage architecture"""

    # Storage tier definitions based on our NVMe layout
    STORAGE_TIERS = {
        'ingest': {
            'path': Path('/mnt/ingest'),
            'purpose': 'Camera dumps and immediate imports',
            'size': '600GB',
            'filesystem': 'XFS'
        },
        'resolve': {
            'path': Path('/mnt/resolve'),
            'purpose': 'DaVinci Resolve cache and proxy media',
            'size': '700GB',
            'filesystem': 'XFS'
        },
        'render': {
            'path': Path('/mnt/render'),
            'purpose': 'Export outputs ready for upload',
            'size': '563GB',
            'filesystem': 'XFS'
        },
        'library': {
            'path': Path('/mnt/library'),
            'purpose': 'Working projects and reusable assets',
            'size': '1.5TB',
            'filesystem': 'BTRFS'
        },
        'archive': {
            'path': Path('/mnt/archive'),
            'purpose': 'Long-term redundant storage',
            'size': '3.6TB',
            'filesystem': 'XFS-RAID1'
        }
    }

    def __init__(self):
        self.verify_storage_layout()
        self.episode_counter = self._get_episode_counter()

    def verify_storage_layout(self) -> bool:
        """Verify all storage tiers are mounted and accessible"""
        missing = []
        for tier, config in self.STORAGE_TIERS.items():
            if not config['path'].exists():
                missing.append(tier)

        if missing:
            raise RuntimeError(f"Missing storage tiers: {missing}")
        return True

    def _get_episode_counter(self) -> int:
        """Get the next episode number"""
        episodes_dir = self.STORAGE_TIERS['library']['path'] / 'EPISODES'
        if not episodes_dir.exists():
            return 1

        existing = [d.name for d in episodes_dir.iterdir() if d.is_dir()]
        episode_nums = []
        for name in existing:
            match = re.match(r'EP(\d+)_', name)
            if match:
                episode_nums.append(int(match.group(1)))

        return max(episode_nums, default=0) + 1

    def create_episode(self,
                      title: str,
                      template: str = 'youtube',
                      cameras: List[str] = None) -> Path:
        """Create a new episode with complete structure"""

        # Format episode name
        ep_num = f"EP{self.episode_counter:03d}"
        safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title)
        episode_name = f"{ep_num}_{safe_title}"

        # Create episode directory
        episode_path = self.STORAGE_TIERS['library']['path'] / 'EPISODES' / episode_name

        # Episode structure
        structure = {
            '00_script': 'Scripts, notes, outlines',
            '01_footage': 'Episode-specific raw footage',
            '02_graphics': 'Custom graphics and overlays',
            '03_resolve': 'DaVinci Resolve project files',
            '04_audio': 'Voiceover, music selections',
            '05_exports': 'Draft versions and iterations'
        }

        # Create directories
        episode_path.mkdir(parents=True, exist_ok=True)
        for dir_name, purpose in structure.items():
            dir_path = episode_path / dir_name
            dir_path.mkdir(exist_ok=True)

            # Add README for each directory
            readme = dir_path / 'README.md'
            readme.write_text(f"# {dir_name}\n\n{purpose}\n")

        # Create metadata
        metadata = {
            'episode': ep_num,
            'title': title,
            'created': datetime.now().isoformat(),
            'template': template,
            'cameras': cameras or ['FX30', 'ZV-E10'],
            'status': 'pre-production',
            'storage_tiers': {
                'ingest': str(self.STORAGE_TIERS['ingest']['path']),
                'cache': str(self.STORAGE_TIERS['resolve']['path']),
                'output': str(self.STORAGE_TIERS['render']['path'])
            }
        }

        metadata_file = episode_path / 'METADATA.json'
        metadata_file.write_text(json.dumps(metadata, indent=2))

        # Link common assets from STOCK library
        self._link_stock_assets(episode_path, template)

        # Create resolve project structure
        self._setup_resolve_project(episode_path, episode_name)

        # Update episode counter
        self.episode_counter += 1

        return episode_path

    def _link_stock_assets(self, episode_path: Path, template: str):
        """Create symbolic links to reusable assets"""
        stock_path = self.STORAGE_TIERS['library']['path'] / 'STOCK'

        # Ensure STOCK directory exists
        stock_dirs = ['intros', 'outros', 'transitions', 'overlays', 'music', 'graphics']
        for dir_name in stock_dirs:
            (stock_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Link common assets based on template
        if template == 'youtube':
            links = {
                'intros/standard_intro.mov': '02_graphics/intro.mov',
                'outros/subscribe_cta.mov': '02_graphics/outro.mov'
            }

            for source, dest in links.items():
                source_file = stock_path / source
                dest_file = episode_path / dest

                # Create placeholder if source doesn't exist
                if not source_file.exists():
                    source_file.parent.mkdir(parents=True, exist_ok=True)
                    source_file.write_text(f"# Placeholder for {source}\n")

                # Create symlink if destination doesn't exist
                if not dest_file.exists():
                    dest_file.symlink_to(source_file)

    def _setup_resolve_project(self, episode_path: Path, project_name: str):
        """Setup DaVinci Resolve project structure"""
        resolve_dir = episode_path / '03_resolve'

        # Create Resolve database structure
        resolve_structure = {
            'CacheClip': 'Resolve cache clips',
            'Proxy': 'Proxy media files',
            'Render': 'Render cache'
        }

        for dir_name, purpose in resolve_structure.items():
            dir_path = resolve_dir / dir_name
            dir_path.mkdir(exist_ok=True)

        # Create project info file
        project_info = {
            'name': project_name,
            'database': 'YouTube_2025',
            'cache_location': str(self.STORAGE_TIERS['resolve']['path']),
            'proxy_location': str(self.STORAGE_TIERS['resolve']['path'] / 'ProxyMedia'),
            'render_location': str(self.STORAGE_TIERS['render']['path'])
        }

        info_file = resolve_dir / 'project_info.json'
        info_file.write_text(json.dumps(project_info, indent=2))

    def ingest_footage(self, source_path: Path, camera: str = None) -> Path:
        """Smart ingest from SD card or camera"""

        # Detect camera from file naming
        if not camera:
            camera = self._detect_camera(source_path)

        # Create dated ingest folder
        date_str = datetime.now().strftime('%Y-%m-%d')
        ingest_dir = self.STORAGE_TIERS['ingest']['path'] / f"{date_str}_{camera}"
        ingest_dir.mkdir(parents=True, exist_ok=True)

        # Copy or move files
        if source_path.is_dir():
            shutil.copytree(source_path, ingest_dir / source_path.name, dirs_exist_ok=True)
        else:
            shutil.copy2(source_path, ingest_dir)

        # Sort into quality tiers
        self._sort_by_quality(ingest_dir, camera)

        return ingest_dir

    def _detect_camera(self, path: Path) -> str:
        """Detect camera from file naming patterns"""
        name = path.name.upper()

        if 'FX30' in name or 'XAVC' in name:
            return 'FX30'
        elif 'ZV' in name or 'E10' in name:
            return 'ZV-E10'
        elif 'OBS' in name or 'SCREEN' in name:
            return 'OBS'
        else:
            return 'UNKNOWN'

    def _sort_by_quality(self, ingest_dir: Path, camera: str):
        """Sort footage by quality into B-roll library"""
        b_roll = self.STORAGE_TIERS['library']['path'] / 'B_ROLL'

        # Determine quality tier
        if camera == 'FX30':
            # Check for XAVC-I (high quality)
            for file in ingest_dir.rglob('*.MXF'):
                quality_dir = b_roll / 'by_quality' / '4k_hero'
                quality_dir.mkdir(parents=True, exist_ok=True)
                # Create link instead of copy to save space
                link_path = quality_dir / file.name
                if not link_path.exists():
                    link_path.symlink_to(file)

        # Sort by topic
        topic_dir = b_roll / 'by_topic' / self._get_topic(camera)
        topic_dir.mkdir(parents=True, exist_ok=True)

        # Sort by date
        date_dir = b_roll / 'by_date' / datetime.now().strftime('%Y-%m')
        date_dir.mkdir(parents=True, exist_ok=True)

    def _get_topic(self, camera: str) -> str:
        """Map camera to typical content topic"""
        mapping = {
            'FX30': 'ai_tools',
            'ZV-E10': 'talking_head',
            'OBS': 'coding'
        }
        return mapping.get(camera, 'general')

    def archive_episode(self, episode_name: str) -> Path:
        """Archive completed episode to RAID storage"""
        source = self.STORAGE_TIERS['library']['path'] / 'EPISODES' / episode_name

        if not source.exists():
            raise ValueError(f"Episode {episode_name} not found")

        # Create archive structure
        year = datetime.now().year
        quarter = f"Q{(datetime.now().month - 1) // 3 + 1}"

        archive_path = self.STORAGE_TIERS['archive']['path'] / str(year) / quarter / f"{episode_name}_COMPLETE"
        archive_path.mkdir(parents=True, exist_ok=True)

        # Copy entire episode
        shutil.copytree(source, archive_path, dirs_exist_ok=True)

        # Update metadata
        metadata_file = archive_path / 'METADATA.json'
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
            metadata['archived'] = datetime.now().isoformat()
            metadata['archive_path'] = str(archive_path)
            metadata_file.write_text(json.dumps(metadata, indent=2))

        return archive_path

    def get_storage_status(self) -> Dict[str, Any]:
        """Get current storage usage across all tiers"""
        status = {}

        for tier, config in self.STORAGE_TIERS.items():
            path = config['path']
            if path.exists():
                # Get disk usage
                stat = shutil.disk_usage(path)
                status[tier] = {
                    'total': stat.total,
                    'used': stat.used,
                    'free': stat.free,
                    'percent': (stat.used / stat.total) * 100,
                    'human_total': f"{stat.total / (1024**3):.1f}GB",
                    'human_used': f"{stat.used / (1024**3):.1f}GB",
                    'human_free': f"{stat.free / (1024**3):.1f}GB"
                }

        return status