"""
Enhanced Project Generator with rollback and comprehensive error handling
"""

import os
import shutil
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import tempfile
import hashlib
import git

from .validators import ProjectValidator

logger = logging.getLogger(__name__)

class ProjectGeneratorV2:
    """Enhanced project generator with rollback and validation"""
    
    STANDARD_DIRECTORIES = [
        "00_INGEST",
        "01_PROXIES", 
        "02_AUDIO",
        "03_GFX",
        "04_GRADES",
        "05_PROJECT",
        "06_TIMELINES",
        "07_VFX",
        "08_RENDERS",
        "09_DELIVERY",
        "10_DOCUMENTS",
        "11_SMART_BINS"
    ]
    
    TEMPLATES = {
        'standard': {
            'directories': STANDARD_DIRECTORIES,
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
        'commercial': {
            'directories': STANDARD_DIRECTORIES,
            'subdirs': {
                '00_INGEST': ['RAW', 'CONVERTED', 'LOGS', 'CLIENT_ASSETS'],
                '01_PROXIES': ['1080p', 'OFFLINE'],
                '02_AUDIO': ['MUSIC', 'SFX', 'VO', 'STEMS'],
                '03_GFX': ['BRAND', 'SUPERS', 'PACKSHOT', 'ENDFRAME'],
                '09_DELIVERY': ['MASTER', 'BROADCAST', 'SOCIAL', 'CLIENT_REVIEW'],
                '10_DOCUMENTS': ['BRIEF', 'STORYBOARD', 'CONTRACTS', 'FEEDBACK']
            }
        },
        'documentary': {
            'directories': STANDARD_DIRECTORIES,
            'subdirs': {
                '00_INGEST': ['INTERVIEWS', 'BROLL', 'ARCHIVE', 'STILLS'],
                '02_AUDIO': ['INTERVIEWS', 'NARRATION', 'MUSIC', 'AMBIENCE'],
                '06_TIMELINES': ['ASSEMBLY', 'ROUGH_CUT', 'FINE_CUT', 'LOCKED'],
                '10_DOCUMENTS': ['TRANSCRIPTS', 'RESEARCH', 'RELEASES', 'NOTES'],
                '11_SMART_BINS': ['BY_INTERVIEW', 'BY_TOPIC', 'BY_LOCATION', 'SELECTS']
            }
        }
    }
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.created_items = []  # Track what we create for rollback
        self.validation_errors = []
        self.warnings = []
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def validate_inputs(
        self,
        name: str,
        location: Path,
        template: str,
        force: bool = False
    ) -> bool:
        """
        Comprehensive input validation
        Returns: True if all validations pass
        """
        self.validation_errors.clear()
        self.warnings.clear()
        
        # Validate project name
        valid, error = ProjectValidator.validate_project_name(name)
        if not valid:
            self.validation_errors.append(f"Name validation: {error}")
            
            # Try to suggest a sanitized version
            sanitized = ProjectValidator.sanitize_project_name(name)
            self.warnings.append(f"Suggested name: '{sanitized}'")
        
        # Validate location path
        valid, error = ProjectValidator.validate_path(location, must_exist=True)
        if not valid:
            self.validation_errors.append(f"Location validation: {error}")
        
        # Check if project already exists
        project_path = location / name
        if project_path.exists() and not force:
            self.validation_errors.append(
                f"Project '{name}' already exists at {project_path}. Use --force to overwrite."
            )
        
        # Validate template
        valid, error = ProjectValidator.validate_template(template, list(self.TEMPLATES.keys()))
        if not valid:
            self.validation_errors.append(f"Template validation: {error}")
        
        # Check disk space (need at least 100MB for safety)
        valid, error = ProjectValidator.check_disk_space(location, required_mb=100)
        if not valid:
            self.validation_errors.append(f"Disk space: {error}")
        
        # Check for network paths (warning only)
        valid, warning = ProjectValidator.validate_network_path(location)
        if warning:
            self.warnings.append(warning)
        
        return len(self.validation_errors) == 0
    
    @contextmanager
    def rollback_on_error(self):
        """
        Context manager to rollback changes on error
        """
        try:
            yield
        except Exception as e:
            logger.error(f"Error occurred, rolling back: {e}")
            self._rollback()
            raise
    
    def _rollback(self):
        """
        Rollback all created items in reverse order
        """
        logger.info("Starting rollback...")
        
        for item in reversed(self.created_items):
            try:
                if item.exists():
                    if item.is_dir():
                        shutil.rmtree(item)
                        logger.debug(f"Removed directory: {item}")
                    else:
                        item.unlink()
                        logger.debug(f"Removed file: {item}")
            except Exception as e:
                logger.error(f"Failed to rollback {item}: {e}")
        
        self.created_items.clear()
        logger.info("Rollback completed")
    
    def create_project(
        self,
        name: str,
        location: Path,
        template: str = 'standard',
        init_git: bool = True,
        force: bool = False,
        metadata: Optional[Dict] = None
    ) -> Tuple[Optional[Path], Dict[str, Any]]:
        """
        Create project with comprehensive error handling
        Returns: (project_path, creation_report)
        """
        report = {
            'success': False,
            'project_path': None,
            'errors': [],
            'warnings': [],
            'stats': {
                'directories_created': 0,
                'files_created': 0,
                'time_taken': 0
            }
        }
        
        start_time = datetime.now()
        
        # Validate inputs first
        if not self.validate_inputs(name, location, template, force):
            report['errors'] = self.validation_errors
            report['warnings'] = self.warnings
            return None, report
        
        project_path = location / name
        
        # Handle existing project
        if project_path.exists():
            if force:
                if not self.dry_run:
                    logger.info(f"Removing existing project at {project_path}")
                    shutil.rmtree(project_path)
            else:
                report['errors'].append(f"Project already exists: {project_path}")
                return None, report
        
        try:
            with self.rollback_on_error():
                # Create project root
                if not self.dry_run:
                    project_path.mkdir(parents=True, exist_ok=True)
                    self.created_items.append(project_path)
                logger.info(f"Created project root: {project_path}")
                
                # Create metadata directory
                metadata_dir = project_path / '.studioflow'
                if not self.dry_run:
                    metadata_dir.mkdir(exist_ok=True)
                    self.created_items.append(metadata_dir)
                
                # Create directory structure
                dirs_created = self._create_directories(project_path, template)
                report['stats']['directories_created'] = dirs_created
                
                # Create configuration files
                files_created = self._create_config_files(project_path, name, template, metadata)
                report['stats']['files_created'] += files_created
                
                # Create README
                self._create_readme(project_path, name, template)
                report['stats']['files_created'] += 1
                
                # Initialize git if requested
                if init_git:
                    git_valid, git_error = ProjectValidator.validate_git_available()
                    if git_valid:
                        self._initialize_git(project_path)
                        report['stats']['git_initialized'] = True
                    else:
                        report['warnings'].append(f"Git not available: {git_error}")
                
                # Create manifest
                manifest = self._create_manifest(project_path)
                report['stats']['files_created'] += 1
                
                # Create health baseline
                self._create_health_baseline(project_path)
                report['stats']['files_created'] += 1
                
                # Success!
                report['success'] = True
                report['project_path'] = str(project_path)
                report['warnings'] = self.warnings
                
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            report['errors'].append(str(e))
            return None, report
        
        finally:
            elapsed = (datetime.now() - start_time).total_seconds()
            report['stats']['time_taken'] = elapsed
            logger.info(f"Project creation took {elapsed:.2f} seconds")
        
        return project_path, report
    
    def _create_directories(self, project_path: Path, template: str) -> int:
        """
        Create directory structure with tracking
        Returns: number of directories created
        """
        template_config = self.TEMPLATES.get(template, self.TEMPLATES['standard'])
        dirs_created = 0
        
        for directory in template_config['directories']:
            dir_path = project_path / directory
            
            if not self.dry_run:
                dir_path.mkdir(exist_ok=True)
                self.created_items.append(dir_path)
            
            dirs_created += 1
            logger.debug(f"Created directory: {directory}")
            
            # Create subdirectories
            subdirs = template_config.get('subdirs', {}).get(directory, [])
            for subdir in subdirs:
                subdir_path = dir_path / subdir
                
                if not self.dry_run:
                    subdir_path.mkdir(exist_ok=True)
                    self.created_items.append(subdir_path)
                    
                    # Create .gitkeep file
                    gitkeep = subdir_path / '.gitkeep'
                    gitkeep.touch()
                    self.created_items.append(gitkeep)
                
                dirs_created += 1
        
        return dirs_created
    
    def _create_config_files(
        self,
        project_path: Path,
        name: str,
        template: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Create configuration files with validation
        Returns: number of files created
        """
        files_created = 0
        
        # Main config
        config = {
            'project': {
                'name': name,
                'template': template,
                'created': datetime.now().isoformat(),
                'version': '1.0.0',
                'studioflow_version': '0.1.0',
                'metadata': metadata or {}
            },
            'settings': {
                'auto_backup': True,
                'backup_interval_hours': 24,
                'proxy_resolution': '1920x1080',
                'proxy_codec': 'ProRes Proxy',
                'color_space': 'Rec.709',
                'frame_rate': 24,
                'bit_depth': '10-bit',
                'audio_sample_rate': 48000
            },
            'paths': {
                'ingest_watch': str(project_path / '00_INGEST' / 'RAW'),
                'proxy_output': str(project_path / '01_PROXIES'),
                'render_output': str(project_path / '08_RENDERS'),
                'delivery': str(project_path / '09_DELIVERY')
            },
            'monitoring': {
                'check_interval_minutes': 60,
                'alert_on_errors': True,
                'track_disk_usage': True,
                'max_disk_usage_percent': 90,
                'enable_notifications': False
            },
            'performance': {
                'parallel_processing': True,
                'max_workers': 4,
                'gpu_acceleration': False,
                'cache_size_gb': 10
            }
        }
        
        config_path = project_path / '.studioflow' / 'config.yaml'
        if not self.dry_run:
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            self.created_items.append(config_path)
        files_created += 1
        
        # Pipeline config
        pipeline_config = {
            'pipeline': {
                'stages': [
                    {'name': 'ingest', 'auto': True, 'watch_folder': True},
                    {'name': 'validation', 'auto': True, 'check_integrity': True},
                    {'name': 'proxy_generation', 'auto': True, 'parallel': True},
                    {'name': 'scene_detection', 'auto': False, 'ai_enabled': True},
                    {'name': 'transcription', 'auto': False, 'languages': ['en']},
                    {'name': 'color_grading', 'auto': False},
                    {'name': 'quality_check', 'auto': True},
                    {'name': 'delivery', 'auto': False, 'formats': ['mp4', 'mov']}
                ],
                'error_handling': {
                    'retry_attempts': 3,
                    'retry_delay_seconds': 60,
                    'alert_on_failure': True
                }
            }
        }
        
        pipeline_path = project_path / '.studioflow' / 'pipeline.yaml'
        if not self.dry_run:
            with open(pipeline_path, 'w') as f:
                yaml.dump(pipeline_config, f, default_flow_style=False, sort_keys=False)
            self.created_items.append(pipeline_path)
        files_created += 1
        
        return files_created
    
    def _create_readme(self, project_path: Path, name: str, template: str):
        """Create comprehensive README"""
        readme_content = f"""# {name}

## Project Information
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Template**: {template}
- **StudioFlow Version**: 0.1.0
- **Project ID**: {hashlib.sha256(f"{name}{datetime.now()}".encode()).hexdigest()[:8]}

## Directory Structure
```
{name}/
├── 00_INGEST/        # Raw media imports
├── 01_PROXIES/       # Edit-friendly proxies
├── 02_AUDIO/         # Audio workspace
├── 03_GFX/           # Graphics assets
├── 04_GRADES/        # Color workflow
├── 05_PROJECT/       # Project files
├── 06_TIMELINES/     # Edit versions
├── 07_VFX/           # Visual effects
├── 08_RENDERS/       # WIP renders
├── 09_DELIVERY/      # Final outputs
├── 10_DOCUMENTS/     # Documentation
└── 11_SMART_BINS/    # AI organization
```

## Quick Commands
```bash
# Check project health
studioflow-project health .

# Create snapshot
studioflow-project snapshot . --name "before_edit"

# Start watching for new media
studioflow ingest watch .

# Generate proxies
studioflow proxy generate . --parallel

# Run AI scene detection
studioflow ai detect-scenes .
```

## Workflow Status
- [ ] Media ingested
- [ ] Proxies generated
- [ ] Edit completed
- [ ] Color graded
- [ ] Audio mixed
- [ ] VFX completed
- [ ] Client approved
- [ ] Delivered

## Team Members
- Editor: 
- Colorist: 
- Sound: 
- VFX: 

## Important Dates
- Shoot Date: 
- Edit Deadline: 
- Delivery Date: 

## Notes
_Add project-specific notes here..._

## Technical Specifications
- Resolution: 
- Frame Rate: 
- Codec: 
- Color Space: 
- Audio: 

---
*Generated by StudioFlow - Professional Video Production Automation*
"""
        
        readme_path = project_path / 'README.md'
        if not self.dry_run:
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            self.created_items.append(readme_path)
    
    def _initialize_git(self, project_path: Path):
        """Initialize git with comprehensive .gitignore"""
        if self.dry_run:
            return
        
        repo = git.Repo.init(project_path)
        
        gitignore_content = """# StudioFlow Project
# ====================

# System Files
# ------------
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini
*.swp
*.swo
*~

# StudioFlow
# -----------
*.cache
*.tmp
*.log
*.bak
.studioflow/snapshots/
.studioflow/health.log
.studioflow/cache/

# DaVinci Resolve
# ---------------
*.drp-bak
*.dra-bak
CacheClip/
OptimizedMedia/
ProxyMedia/
RenderCache/
.scratch/
*.dr_temp

# Adobe Premiere
# --------------
Adobe Premiere Pro Auto-Save/
Adobe Premiere Pro Preview Files/
*.prproj_bak

# Final Cut Pro
# -------------
**/Render Files/
**/Transcoded Media/
**/Thumbnails/
*.fcpevent/
*.fcpbundle/

# Media Files (customize as needed)
# ----------------------------------
# Comment out extensions you want to track
# *.mov
# *.mp4
# *.avi
# *.mxf
# *.r3d
# *.braw

# Large proxy files (track selectively)
01_PROXIES/**/*.mov
01_PROXIES/**/*.mp4
!01_PROXIES/**/README.md

# Temporary renders
08_RENDERS/DAILIES/
08_RENDERS/REVIEW/
08_RENDERS/TEMP/
08_RENDERS/**/*_temp.*
08_RENDERS/**/*_draft.*

# Keep delivery files
!09_DELIVERY/**/*.mov
!09_DELIVERY/**/*.mp4
!09_DELIVERY/**/MASTER/

# Cache and temp directories
**/cache/
**/temp/
**/tmp/
**/.temp/

# Logs (keep error logs)
*.log
!**/errors.log
!**/critical.log

# Python
# ------
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/

# Node
# ----
node_modules/
npm-debug.log*

# IDE
# ---
.vscode/
.idea/
*.sublime-project
*.sublime-workspace

# Custom excludes
# ---------------
# Add your own excludes below
"""
        
        gitignore_path = project_path / '.gitignore'
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        self.created_items.append(gitignore_path)
        
        # Create .gitattributes for better diff handling
        gitattributes_content = """# StudioFlow Git Attributes
*.drp binary
*.dra binary
*.prproj binary
*.aep binary
*.psd binary
*.ai binary

# Video files
*.mov binary
*.mp4 binary
*.avi binary
*.mxf binary

# Images
*.jpg binary
*.jpeg binary
*.png binary
*.tiff binary
*.exr binary
*.dpx binary

# Audio
*.wav binary
*.aiff binary
*.mp3 binary

# Documents
*.pdf binary
*.doc binary
*.docx binary

# Text files
*.txt text
*.md text
*.yaml text
*.yml text
*.json text
*.xml text
*.edl text
*.srt text
*.vtt text
"""
        
        gitattributes_path = project_path / '.gitattributes'
        with open(gitattributes_path, 'w') as f:
            f.write(gitattributes_content)
        self.created_items.append(gitattributes_path)
        
        # Initial commit
        repo.index.add(['.gitignore', '.gitattributes', 'README.md', '.studioflow/config.yaml'])
        repo.index.commit(f"Initial commit: {project_path.name} project created with StudioFlow")
    
    def _create_manifest(self, project_path: Path) -> Dict:
        """Create detailed project manifest"""
        manifest = {
            'version': '2.0',
            'created': datetime.now().isoformat(),
            'project_id': hashlib.sha256(str(project_path).encode()).hexdigest()[:16],
            'directories': [],
            'files': [],
            'checksums': {},
            'stats': {
                'total_directories': 0,
                'total_files': 0,
                'total_size_bytes': 0
            }
        }
        
        if not self.dry_run:
            for root, dirs, files in os.walk(project_path):
                root_path = Path(root)
                rel_path = root_path.relative_to(project_path)
                
                if not str(rel_path).startswith('.git'):
                    manifest['directories'].append(str(rel_path))
                    manifest['stats']['total_directories'] += 1
                    
                    for file in files:
                        if not file.startswith('.git'):
                            file_path = root_path / file
                            rel_file_path = file_path.relative_to(project_path)
                            
                            file_stat = file_path.stat()
                            manifest['files'].append({
                                'path': str(rel_file_path),
                                'size': file_stat.st_size,
                                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                'permissions': oct(file_stat.st_mode)[-3:]
                            })
                            
                            manifest['stats']['total_files'] += 1
                            manifest['stats']['total_size_bytes'] += file_stat.st_size
                            
                            # Calculate checksum for important files
                            if file_path.suffix in ['.yaml', '.yml', '.json', '.md']:
                                with open(file_path, 'rb') as f:
                                    checksum = hashlib.sha256(f.read()).hexdigest()
                                    manifest['checksums'][str(rel_file_path)] = checksum
            
            manifest_path = project_path / '.studioflow' / 'manifest.json'
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            self.created_items.append(manifest_path)
        
        return manifest
    
    def _create_health_baseline(self, project_path: Path):
        """Create initial health baseline for monitoring"""
        baseline = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'expected_structure': {
                'directories': list(self.STANDARD_DIRECTORIES),
                'critical_files': [
                    '.studioflow/config.yaml',
                    '.studioflow/pipeline.yaml',
                    '.studioflow/manifest.json',
                    'README.md'
                ]
            },
            'thresholds': {
                'max_file_age_days': 365,
                'max_directory_size_gb': 1000,
                'min_free_space_gb': 10,
                'max_temp_files': 100
            },
            'checks': {
                'verify_structure': True,
                'check_permissions': True,
                'scan_corruption': False,  # Expensive, off by default
                'check_naming': True,
                'verify_checksums': True
            }
        }
        
        if not self.dry_run:
            baseline_path = project_path / '.studioflow' / 'health_baseline.json'
            with open(baseline_path, 'w') as f:
                json.dump(baseline, f, indent=2)
            self.created_items.append(baseline_path)