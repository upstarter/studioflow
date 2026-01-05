"""
StudioFlow Unified Project Generator
Combines the best of all previous versions: validation + performance + simplicity
"""

import os
import shutil
import json
import yaml
import logging
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import git

from .validators import ProjectValidator

logger = logging.getLogger(__name__)

class StudioFlowGenerator:
    """
    The unified, production-ready StudioFlow project generator.
    
    Features:
    - Comprehensive validation with helpful error messages
    - Rollback on failure for safety
    - Async operations for performance
    - YouTube-optimized templates
    - Bridge compatibility with existing workflows
    """
    
    TEMPLATES = {
        'standard': {
            'name': 'Standard Video Production',
            'description': 'Professional video production workflow',
            'directories': [
                '00_INGEST', '01_PROXIES', '02_AUDIO', '03_GFX',
                '04_GRADES', '05_PROJECT', '06_TIMELINES', '07_VFX',
                '08_RENDERS', '09_DELIVERY', '10_DOCUMENTS', '11_SMART_BINS'
            ],
            'subdirs': {
                '00_INGEST': ['RAW', 'CONVERTED', 'LOGS'],
                '01_PROXIES': ['1080p', '720p', 'OFFLINE'],
                '02_AUDIO': ['MUSIC', 'SFX', 'VO', 'MIXED'],
                '03_GFX': ['LOWER_THIRDS', 'LOGOS', 'ANIMATIONS', 'TEMPLATES'],
                '04_GRADES': ['LUT', 'DPX', 'CDL', 'STILLS'],
                '05_PROJECT': ['RESOLVE', 'BACKUP', 'ARCHIVE'],
                '06_TIMELINES': ['ROUGH', 'FINE', 'LOCKED', 'VERSIONS'],
                '07_VFX': ['PLATES', 'COMPS', 'RENDERS', 'ASSETS'],
                '08_RENDERS': ['DAILIES', 'REVIEW', 'TEMP'],
                '09_DELIVERY': ['MASTER', 'WEB', 'BROADCAST', 'ARCHIVE'],
                '10_DOCUMENTS': ['SCRIPTS', 'NOTES', 'CONTRACTS', 'REPORTS'],
                '11_SMART_BINS': ['BY_SCENE', 'BY_DATE', 'BY_CAMERA', 'FAVORITES']
            }
        },
        'youtube': {
            'name': 'YouTube Content Creation',
            'description': 'Optimized for YouTube creators and content production',
            'directories': [
                '00_PLANNING', '01_FOOTAGE', '02_AUDIO', '03_GRAPHICS',
                '04_EDITING', '05_COLOR', '06_EXPORTS', '07_ASSETS', '08_ARCHIVE'
            ],
            'subdirs': {
                '00_PLANNING': ['SCRIPT', 'RESEARCH', 'NOTES', 'STORYBOARD', 'REFERENCES'],
                '01_FOOTAGE': ['A_CAM', 'B_CAM', 'SCREEN_RECORDING', 'PHONE', 'DRONE', 'STOCK'],
                '02_AUDIO': ['NARRATION', 'MUSIC', 'SFX', 'ROOM_TONE', 'SPONSOR_READS'],
                '03_GRAPHICS': ['THUMBNAILS', 'OVERLAYS', 'TRANSITIONS', 'LOGOS', 'LOWER_THIRDS', 'END_SCREENS'],
                '04_EDITING': ['PROJECT_FILES', 'PROXIES', 'SEQUENCES', 'AUTO_SAVES'],
                '05_COLOR': ['LUTS', 'STILLS', 'GRADES'],
                '06_EXPORTS': ['YOUTUBE', 'SHORTS', 'SOCIAL', 'PODCAST', 'DRAFTS'],
                '07_ASSETS': ['ANALYTICS', 'COMMENTS', 'PRESS_KIT'],
                '08_ARCHIVE': ['FINAL_DELIVERABLES', 'PROJECT_BACKUP']
            }
        },
        'commercial': {
            'name': 'Commercial Production',
            'description': 'Agency and brand content production',
            'directories': [
                '00_BRIEF', '01_FOOTAGE', '02_AUDIO', '03_GRAPHICS', 
                '04_EDIT', '05_COLOR', '06_REVIEW', '07_DELIVERY', '08_ARCHIVE'
            ],
            'subdirs': {
                '00_BRIEF': ['CLIENT_BRIEF', 'STORYBOARD', 'REFERENCES', 'CONTRACTS'],
                '01_FOOTAGE': ['RAW', 'CONVERTED', 'CLIENT_ASSETS', 'STOCK'],
                '02_AUDIO': ['MUSIC', 'SFX', 'VO', 'STEMS'],
                '03_GRAPHICS': ['BRAND', 'SUPERS', 'PACKSHOT', 'ENDFRAME'],
                '06_REVIEW': ['CLIENT_REVIEW', 'INTERNAL_REVIEW', 'FEEDBACK'],
                '07_DELIVERY': ['MASTER', 'BROADCAST', 'SOCIAL', 'CLIENT_VERSIONS']
            }
        },
        'documentary': {
            'name': 'Documentary Production',
            'description': 'Long-form documentary filmmaking',
            'directories': [
                '00_RESEARCH', '01_INTERVIEWS', '02_BROLL', '03_ARCHIVE',
                '04_AUDIO', '05_TRANSCRIPTS', '06_EDIT', '07_GRAPHICS',
                '08_COLOR', '09_DELIVERY', '10_ARCHIVE'
            ],
            'subdirs': {
                '00_RESEARCH': ['BACKGROUND', 'SOURCES', 'CONTACTS', 'RELEASES'],
                '01_INTERVIEWS': ['RAW', 'TRANSCODED', 'NOTES'],
                '02_BROLL': ['ESTABLISHING', 'CUTAWAYS', 'MONTAGE'],
                '03_ARCHIVE': ['HISTORICAL', 'STOCK', 'PHOTOS', 'DOCUMENTS'],
                '05_TRANSCRIPTS': ['RAW', 'EDITED', 'SEARCHABLE'],
                '06_EDIT': ['ASSEMBLY', 'ROUGH_CUT', 'FINE_CUT', 'LOCKED']
            }
        }
    }
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.created_items = []
        self.executor = ThreadPoolExecutor(max_workers=8)
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def create_project(
        self,
        name: str,
        location: Union[str, Path],
        template: str = 'standard',
        init_git: bool = True,
        force: bool = False,
        metadata: Optional[Dict] = None
    ) -> Tuple[Optional[Path], Dict[str, Any]]:
        """
        Create a new StudioFlow project
        
        Args:
            name: Project name (will be sanitized)
            location: Directory where project will be created
            template: Project template (standard, youtube, commercial, documentary)
            init_git: Initialize git repository
            force: Overwrite existing project
            metadata: Additional project metadata
            
        Returns:
            (project_path, report) where report contains success status and details
        """
        location = Path(location)
        
        # Input validation
        validation_result = self._validate_inputs(name, location, template, force)
        if not validation_result['valid']:
            return None, validation_result
        
        # Use sanitized name from validation
        clean_name = validation_result['sanitized_name']
        project_path = location / clean_name
        
        start_time = datetime.now()
        
        try:
            with self._rollback_on_error():
                # Create project structure
                self._create_project_structure(project_path, template)
                
                # Generate configuration
                self._create_configuration(project_path, clean_name, template, metadata)
                
                # Initialize git if requested
                if init_git:
                    self._initialize_git(project_path)
                
                # Create manifest and health baseline
                self._finalize_project(project_path)
                
                # Success!
                elapsed = (datetime.now() - start_time).total_seconds()
                return project_path, {
                    'success': True,
                    'project_path': str(project_path),
                    'template': template,
                    'time_taken': elapsed,
                    'directories_created': self._count_directories(project_path),
                    'git_initialized': init_git
                }
                
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            return None, {
                'success': False,
                'error': str(e),
                'project_path': str(project_path) if project_path else None
            }
    
    def _validate_inputs(
        self, name: str, location: Path, template: str, force: bool
    ) -> Dict[str, Any]:
        """Comprehensive input validation"""
        
        # Validate and sanitize project name
        valid, error = ProjectValidator.validate_project_name(name)
        if not valid:
            sanitized = ProjectValidator.sanitize_project_name(name)
            return {
                'valid': False,
                'error': f"Invalid project name: {error}",
                'suggestion': f"Try: '{sanitized}'"
            }
        
        # Check location
        valid, error = ProjectValidator.validate_path(location, must_exist=True)
        if not valid:
            return {'valid': False, 'error': f"Location error: {error}"}
        
        # Validate template
        if template not in self.TEMPLATES:
            available = ', '.join(self.TEMPLATES.keys())
            return {
                'valid': False, 
                'error': f"Unknown template '{template}'. Available: {available}"
            }
        
        # Check if project exists
        project_path = location / name
        if project_path.exists() and not force:
            return {
                'valid': False,
                'error': f"Project '{name}' already exists. Use --force to overwrite."
            }
        
        # Check disk space
        valid, error = ProjectValidator.check_disk_space(location, required_mb=50)
        if not valid:
            return {'valid': False, 'error': error}
        
        return {
            'valid': True,
            'sanitized_name': ProjectValidator.sanitize_project_name(name),
            'warnings': []
        }
    
    @contextmanager
    def _rollback_on_error(self):
        """Rollback on any error"""
        try:
            yield
        except Exception:
            self._rollback()
            raise
    
    def _rollback(self):
        """Remove all created items in reverse order"""
        logger.info("Rolling back changes...")
        for item in reversed(self.created_items):
            try:
                if item.exists():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            except Exception as e:
                logger.error(f"Failed to rollback {item}: {e}")
        self.created_items.clear()
    
    def _create_project_structure(self, project_path: Path, template: str):
        """Create the directory structure"""
        if self.dry_run:
            return
        
        # Create root directory
        project_path.mkdir(parents=True, exist_ok=True)
        self.created_items.append(project_path)
        
        # Create metadata directory
        metadata_dir = project_path / '.studioflow'
        metadata_dir.mkdir(exist_ok=True)
        self.created_items.append(metadata_dir)
        
        # Create template directories
        template_config = self.TEMPLATES[template]
        for directory in template_config['directories']:
            dir_path = project_path / directory
            dir_path.mkdir(exist_ok=True)
            self.created_items.append(dir_path)
            
            # Create subdirectories
            subdirs = template_config.get('subdirs', {}).get(directory, [])
            for subdir in subdirs:
                subdir_path = dir_path / subdir
                subdir_path.mkdir(exist_ok=True)
                self.created_items.append(subdir_path)
                
                # Add .gitkeep for empty directories
                gitkeep = subdir_path / '.gitkeep'
                gitkeep.touch()
                self.created_items.append(gitkeep)
    
    def _create_configuration(
        self, project_path: Path, name: str, template: str, metadata: Optional[Dict]
    ):
        """Create all configuration files"""
        if self.dry_run:
            return
            
        template_info = self.TEMPLATES[template]
        
        # Main configuration
        config = {
            'project': {
                'name': name,
                'template': template,
                'template_name': template_info['name'],
                'description': template_info['description'],
                'created': datetime.now().isoformat(),
                'version': '2.0.0',
                'studioflow_version': '0.2.0',
                'metadata': metadata or {}
            },
            'settings': self._get_template_settings(template),
            'paths': self._get_template_paths(project_path, template),
            'workflow': self._get_template_workflow(template)
        }
        
        config_path = project_path / '.studioflow' / 'config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        self.created_items.append(config_path)
        
        # Create README
        self._create_readme(project_path, name, template, template_info)
    
    def _get_template_settings(self, template: str) -> Dict:
        """Get template-specific settings"""
        base_settings = {
            'auto_backup': True,
            'backup_interval_hours': 24,
            'health_checks': True,
            'git_auto_commit': False
        }
        
        if template == 'youtube':
            base_settings.update({
                'target_resolution': '1920x1080',
                'target_framerate': 30,
                'export_formats': ['mp4', 'webm'],
                'thumbnail_sizes': ['1280x720', '1920x1080'],
                'social_exports': True
            })
        elif template == 'commercial':
            base_settings.update({
                'target_resolution': '1920x1080',
                'target_framerate': 24,
                'export_formats': ['mov', 'mp4'],
                'broadcast_safe': True,
                'client_review': True
            })
        
        return base_settings
    
    def _get_template_paths(self, project_path: Path, template: str) -> Dict:
        """Get template-specific paths"""
        if template == 'youtube':
            return {
                'footage': str(project_path / '01_FOOTAGE'),
                'audio': str(project_path / '02_AUDIO'),
                'graphics': str(project_path / '03_GRAPHICS'),
                'editing': str(project_path / '04_EDITING'),
                'exports': str(project_path / '06_EXPORTS')
            }
        else:
            # Standard paths for other templates
            return {
                'ingest': str(project_path / '00_INGEST'),
                'proxies': str(project_path / '01_PROXIES'),
                'audio': str(project_path / '02_AUDIO'),
                'graphics': str(project_path / '03_GFX'),
                'delivery': str(project_path / '09_DELIVERY')
            }
    
    def _get_template_workflow(self, template: str) -> Dict:
        """Get template-specific workflow configuration"""
        workflows = {
            'youtube': {
                'stages': [
                    'planning', 'shooting', 'editing', 'review', 'export', 'upload'
                ],
                'checklists': {
                    'pre_production': ['Script written', 'Location scouted', 'Equipment checked'],
                    'post_production': ['Rough cut', 'Color correction', 'Audio mix', 'Graphics added'],
                    'publishing': ['Thumbnail created', 'Description written', 'SEO optimized']
                }
            },
            'standard': {
                'stages': [
                    'ingest', 'proxy', 'edit', 'color', 'audio', 'vfx', 'delivery'
                ]
            }
        }
        return workflows.get(template, workflows['standard'])
    
    def _create_readme(self, project_path: Path, name: str, template: str, template_info: Dict):
        """Create comprehensive README"""
        readme_content = f"""# {name}

**{template_info['name']}** - {template_info['description']}

## Project Details
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Template**: {template} ({template_info['name']})
- **StudioFlow**: v0.2.0

## Directory Structure
```
{name}/
"""
        
        # Add directory structure to README
        template_config = self.TEMPLATES[template]
        for directory in template_config['directories']:
            readme_content += f"├── {directory}/\n"
            subdirs = template_config.get('subdirs', {}).get(directory, [])
            for subdir in subdirs:
                readme_content += f"│   ├── {subdir}/\n"
        
        if template == 'youtube':
            readme_content += """```

## YouTube Workflow
1. **Planning** (`00_PLANNING/`) - Write scripts, research, plan content
2. **Shooting** (`01_FOOTAGE/`) - Record all video content
3. **Audio** (`02_AUDIO/`) - Narration, music, sound effects
4. **Graphics** (`03_GRAPHICS/`) - Thumbnails, overlays, end screens
5. **Editing** (`04_EDITING/`) - Assemble final video
6. **Color** (`05_COLOR/`) - Color correction and grading
7. **Export** (`06_EXPORTS/`) - Render for different platforms

## Quick Commands
```bash
# Check project health
studioflow-project health .

# Export for YouTube
studioflow export youtube .

# Create thumbnail variations
studioflow thumbnail generate .
```

## Production Checklist
- [ ] Script complete
- [ ] All footage captured
- [ ] Audio recorded and synced
- [ ] Thumbnail designed
- [ ] Video edited
- [ ] Color corrected
- [ ] Exported for YouTube
- [ ] Metadata optimized
- [ ] Uploaded and scheduled

## Analytics & Performance
Track your video's performance in `07_ASSETS/ANALYTICS/`
"""
        else:
            readme_content += """```

## Quick Commands
```bash
# Check project health  
studioflow-project health .

# Create snapshot
studioflow-project snapshot .
```
"""
        
        readme_content += f"""
---
*Generated by StudioFlow - Professional Video Production Automation*
"""
        
        readme_path = project_path / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        self.created_items.append(readme_path)
    
    def _initialize_git(self, project_path: Path):
        """Initialize git repository"""
        if self.dry_run:
            return
            
        repo = git.Repo.init(project_path)
        
        # Create comprehensive .gitignore
        gitignore_content = """# StudioFlow Project
.studioflow/cache/
.studioflow/*.log

# System files
.DS_Store
Thumbs.db
*.tmp
*.cache

# Video editing
*.drp-bak
*.dra-bak
CacheClip/
OptimizedMedia/
ProxyMedia/
RenderCache/

# Large media files (customize as needed)
*.mov
*.mp4
*.avi
*.mxf
!06_EXPORTS/**/*.mp4
!07_DELIVERY/**/*.mov
"""
        
        gitignore_path = project_path / '.gitignore'
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        self.created_items.append(gitignore_path)
        
        # Initial commit
        repo.index.add(['.gitignore', 'README.md', '.studioflow/config.yaml'])
        repo.index.commit(f"🎬 Initialize StudioFlow project: {project_path.name}")
    
    def _finalize_project(self, project_path: Path):
        """Create manifest and health baseline"""
        if self.dry_run:
            return
        
        # Create manifest
        manifest = {
            'version': '2.0',
            'created': datetime.now().isoformat(),
            'project_id': hashlib.sha256(str(project_path).encode()).hexdigest()[:12],
            'file_count': len(self.created_items),
            'total_size': sum(item.stat().st_size for item in self.created_items if item.exists() and item.is_file())
        }
        
        manifest_path = project_path / '.studioflow' / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        self.created_items.append(manifest_path)
    
    def _count_directories(self, project_path: Path) -> int:
        """Count created directories"""
        if self.dry_run:
            return 0
        return len([item for item in self.created_items if item.exists() and item.is_dir()])
    
    def list_templates(self) -> Dict[str, Dict]:
        """Get available templates with descriptions"""
        return {
            name: {
                'name': template['name'],
                'description': template['description'],
                'directories': len(template['directories'])
            }
            for name, template in self.TEMPLATES.items()
        }
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)