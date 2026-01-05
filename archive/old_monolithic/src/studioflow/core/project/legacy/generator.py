import os
import shutil
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import git

class ProjectGenerator:
    """Generate standardized video project structures"""
    
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
    
    def __init__(self):
        self.created_paths: List[Path] = []
        
    def create_project(
        self,
        name: str,
        location: Path,
        template: str = 'standard',
        init_git: bool = True,
        force: bool = False
    ) -> Path:
        """Create a complete project structure"""
        project_path = location / name
        
        if project_path.exists():
            if force:
                shutil.rmtree(project_path)
            else:
                raise FileExistsError(f"Project already exists: {project_path}")
        
        project_path.mkdir(parents=True, exist_ok=True)
        self.created_paths.append(project_path)
        
        metadata_dir = project_path / '.studioflow'
        metadata_dir.mkdir(exist_ok=True)
        
        self._create_directories(project_path, template)
        
        self._create_config_files(project_path, name, template)
        
        self._create_readme(project_path, name, template)
        
        if init_git:
            self._initialize_git(project_path)
        
        self._create_manifest(project_path)
        
        return project_path
    
    def _create_directories(self, project_path: Path, template: str):
        """Create directory structure based on template"""
        template_config = self.TEMPLATES.get(template, self.TEMPLATES['standard'])
        
        for directory in template_config['directories']:
            dir_path = project_path / directory
            dir_path.mkdir(exist_ok=True)
            self.created_paths.append(dir_path)
            
            subdirs = template_config.get('subdirs', {}).get(directory, [])
            for subdir in subdirs:
                subdir_path = dir_path / subdir
                subdir_path.mkdir(exist_ok=True)
                self.created_paths.append(subdir_path)
                
                (subdir_path / '.gitkeep').touch()
    
    def _create_config_files(self, project_path: Path, name: str, template: str):
        """Create project configuration files"""
        config = {
            'project': {
                'name': name,
                'template': template,
                'created': datetime.now().isoformat(),
                'version': '1.0.0',
                'studioflow_version': '0.1.0'
            },
            'settings': {
                'auto_backup': True,
                'backup_interval_hours': 24,
                'proxy_resolution': '1920x1080',
                'proxy_codec': 'ProRes Proxy',
                'color_space': 'Rec.709',
                'frame_rate': 24
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
                'max_disk_usage_percent': 90
            }
        }
        
        config_path = project_path / '.studioflow' / 'config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        pipeline_config = {
            'pipeline': {
                'stages': [
                    {'name': 'ingest', 'auto': True, 'watch_folder': True},
                    {'name': 'proxy_generation', 'auto': True, 'parallel': True},
                    {'name': 'scene_detection', 'auto': False, 'ai_enabled': True},
                    {'name': 'transcription', 'auto': False, 'languages': ['en']},
                    {'name': 'color_grading', 'auto': False},
                    {'name': 'delivery', 'auto': False, 'formats': ['mp4', 'mov']}
                ]
            }
        }
        
        pipeline_path = project_path / '.studioflow' / 'pipeline.yaml'
        with open(pipeline_path, 'w') as f:
            yaml.dump(pipeline_config, f, default_flow_style=False, sort_keys=False)
    
    def _create_readme(self, project_path: Path, name: str, template: str):
        """Create project README file"""
        readme_content = f"""# {name}

## Project Information
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Template**: {template}
- **StudioFlow Version**: 0.1.0

## Directory Structure
- `00_INGEST/` - Raw media imports and conversion
- `01_PROXIES/` - Edit-friendly proxy media
- `02_AUDIO/` - Audio workspace and assets
- `03_GFX/` - Graphics and motion design assets
- `04_GRADES/` - Color grading workflow files
- `05_PROJECT/` - DaVinci Resolve project files
- `06_TIMELINES/` - Edit versions and timelines
- `07_VFX/` - Visual effects work
- `08_RENDERS/` - Work-in-progress renders
- `09_DELIVERY/` - Final deliverables
- `10_DOCUMENTS/` - Project documentation
- `11_SMART_BINS/` - AI-organized content bins

## Quick Commands
```bash
# Check project health
studioflow-project health .

# Create a snapshot
studioflow-project snapshot .

# Start auto-ingest
studioflow ingest watch .

# Generate proxies
studioflow proxy generate .
```

## Notes
Add project-specific notes here...
"""
        
        readme_path = project_path / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)
    
    def _initialize_git(self, project_path: Path):
        """Initialize git repository"""
        repo = git.Repo.init(project_path)
        
        gitignore_content = """# StudioFlow Project
*.cache
*.tmp
*.log
*.bak
.DS_Store
Thumbs.db

# DaVinci Resolve
*.drp
*.dra
CacheClip/
OptimizedMedia/
ProxyMedia/
RenderCache/

# Media files (add specific ones as needed)
*.mov
*.mp4
*.avi
*.mxf
*.r3d
*.braw

# Proxy files
01_PROXIES/**/*.mov
01_PROXIES/**/*.mp4

# Renders (keep only finals)
08_RENDERS/DAILIES/
08_RENDERS/REVIEW/
08_RENDERS/TEMP/

# Keep delivery files
!09_DELIVERY/**/*.mov
!09_DELIVERY/**/*.mp4
"""
        
        gitignore_path = project_path / '.gitignore'
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        
        repo.index.add(['.gitignore', 'README.md', '.studioflow/config.yaml'])
        repo.index.commit(f"Initial commit: {project_path.name} project created")
    
    def _create_manifest(self, project_path: Path):
        """Create project manifest file"""
        manifest = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'directories': [],
            'files': []
        }
        
        for root, dirs, files in os.walk(project_path):
            root_path = Path(root)
            rel_path = root_path.relative_to(project_path)
            
            if not str(rel_path).startswith('.git'):
                manifest['directories'].append(str(rel_path))
                
                for file in files:
                    if not file.startswith('.git'):
                        file_path = root_path / file
                        manifest['files'].append({
                            'path': str(file_path.relative_to(project_path)),
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat()
                        })
        
        manifest_path = project_path / '.studioflow' / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)