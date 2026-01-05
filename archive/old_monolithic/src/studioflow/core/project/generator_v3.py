"""
StudioFlow v3 - Production-Ready Generator
Solidified, robust, simple, and ready for real-world use
"""

import os
import shutil
import json
import yaml
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from contextlib import contextmanager
import hashlib
import git
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from .validators import ProjectValidator

logger = logging.getLogger(__name__)
console = Console()

class StudioFlowGenerator:
    """
    Production-ready StudioFlow project generator v3.
    
    Key Features:
    - Auto-discovery of external resources (NAS, stock footage)
    - Global configuration support
    - Smart linking instead of copying
    - Atomic operations with rollback
    - Rich CLI feedback
    - Dry-run mode
    - Profile support
    """
    
    # Templates remain the same but with improved structure
    TEMPLATES = {
        'youtube': {
            'name': 'YouTube Creator',
            'description': 'Optimized for YouTube content creation',
            'directories': {
                '00_PLANNING': ['SCRIPTS', 'RESEARCH', 'STORYBOARDS', 'SCHEDULE'],
                '01_FOOTAGE': ['A_ROLL', 'B_ROLL', 'SCREEN_CAPTURE', 'STOCK'],
                '02_AUDIO': ['MUSIC', 'SFX', 'NARRATION', 'STEMS'],
                '03_GRAPHICS': ['THUMBNAILS', 'OVERLAYS', 'TITLES', 'END_SCREENS'],
                '04_EDITING': ['PROJECT_FILES', 'AUTO_SAVES', 'CACHE'],
                '05_COLOR': ['LUTS', 'GRADES', 'REFERENCE'],
                '06_EXPORTS': ['YOUTUBE', 'SHORTS', 'SOCIAL', 'DRAFTS'],
                '07_ARCHIVE': ['FINAL', 'VERSIONS', 'BACKUPS']
            }
        },
        'production': {
            'name': 'Professional Production',
            'description': 'Industry-standard video production workflow',
            'directories': {
                '00_INGEST': ['RAW', 'TRANSCODED', 'LOGS'],
                '01_PROXIES': ['OFFLINE', 'ONLINE'],
                '02_AUDIO': ['DIALOG', 'MUSIC', 'SFX', 'FOLEY', 'MIX'],
                '03_VFX': ['PLATES', 'COMPS', 'RENDERS'],
                '04_COLOR': ['DAILIES', 'GRADES', 'LUT'],
                '05_EDIT': ['ROUGH', 'FINE', 'LOCKED'],
                '06_DELIVERY': ['MASTER', 'WEB', 'BROADCAST'],
                '07_ARCHIVE': ['PROJECT', 'ASSETS', 'DOCUMENTATION']
            }
        },
        'minimal': {
            'name': 'Minimal Setup',
            'description': 'Simple structure for quick projects',
            'directories': {
                'FOOTAGE': [],
                'AUDIO': [],
                'GRAPHICS': [],
                'EXPORTS': [],
                'PROJECT': []
            }
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None, verbose: bool = False):
        """Initialize with optional global config"""
        self.verbose = verbose
        self.config = self._load_config(config_path)
        self.discovered_resources = {}
        self.created_items = []
        self._setup_logging()
    
    def _load_config(self, config_path: Optional[Path] = None) -> Dict:
        """Load global configuration"""
        default_config = {
            'defaults': {
                'template': 'youtube',
                'auto_discover': True,
                'init_git': True,
                'create_readme': True
            },
            'external_resources': {
                'stock_footage': [],
                'archives': [],
                'templates': []
            },
            'profiles': {}
        }
        
        # Try to load from multiple locations
        config_locations = [
            config_path,
            Path.home() / '.studioflow' / 'config.yaml',
            Path('/etc/studioflow/config.yaml')
        ]
        
        for location in config_locations:
            if location and location.exists():
                try:
                    with open(location, 'r') as f:
                        user_config = yaml.safe_load(f)
                        default_config.update(user_config)
                        if self.verbose:
                            console.print(f"[green]Loaded config from {location}[/green]")
                        break
                except Exception as e:
                    logger.warning(f"Failed to load config from {location}: {e}")
        
        return default_config
    
    def discover_external_resources(self) -> Dict[str, List[str]]:
        """Auto-discover external media resources"""
        discovered = {
            'stock_footage': [],
            'archives': [],
            'active_projects': [],
            'davinci_projects': []
        }
        
        # Common external paths to check
        search_paths = [
            # Standard media paths
            Path('/mnt/media'),
            Path('/media'),
            Path.home() / 'Videos',
            Path.home() / 'Movies',
            # macOS paths
            Path('/Volumes'),
            # Custom paths from config
            *[Path(p) for p in self.config.get('external_resources', {}).get('custom_paths', [])]
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Discovering external resources...", total=len(search_paths))
            
            for path in search_paths:
                progress.advance(task)
                if path.exists():
                    # Check for video production markers
                    if any(marker in path.name.lower() for marker in ['video', 'media', 'footage', 'active']):
                        discovered['stock_footage'].append(str(path))
                    
                    # Check for DaVinci Resolve projects
                    if (path / 'DaVinciProjects').exists():
                        discovered['davinci_projects'].append(str(path))
                    
                    # Check for archives
                    if 'archive' in path.name.lower():
                        discovered['archives'].append(str(path))
                    
                    # Check for active projects (has .prproj, .drp, etc.)
                    project_markers = ['*.prproj', '*.drp', '*.fcpx', '*.aep']
                    for marker in project_markers:
                        if list(path.glob(marker)):
                            discovered['active_projects'].append(str(path))
                            break
        
        self.discovered_resources = discovered
        return discovered
    
    def create_project(
        self,
        name: str,
        location: Union[str, Path] = ".",
        template: str = None,
        profile: str = None,
        auto_discover: bool = None,
        init_git: bool = None,
        dry_run: bool = False,
        force: bool = False,
        link_resources: bool = True
    ) -> Tuple[Optional[Path], Dict[str, Any]]:
        """
        Create a new StudioFlow project with production features
        
        Args:
            name: Project name
            location: Where to create the project
            template: Template to use (youtube, production, minimal)
            profile: Profile name to load settings from
            auto_discover: Auto-discover and link external resources
            init_git: Initialize git repository
            dry_run: Preview without creating
            force: Overwrite existing project
            link_resources: Create symlinks to discovered resources
            
        Returns:
            (project_path, report) tuple
        """
        start_time = datetime.now()
        location = Path(location)
        
        # Load profile if specified
        if profile and profile in self.config.get('profiles', {}):
            profile_config = self.config['profiles'][profile]
            template = template or profile_config.get('template')
            auto_discover = auto_discover if auto_discover is not None else profile_config.get('auto_discover')
            init_git = init_git if init_git is not None else profile_config.get('init_git')
        
        # Use defaults from config
        template = template or self.config['defaults'].get('template', 'youtube')
        auto_discover = auto_discover if auto_discover is not None else self.config['defaults'].get('auto_discover', True)
        init_git = init_git if init_git is not None else self.config['defaults'].get('init_git', True)
        
        # Validate inputs
        validation = self._validate_inputs(name, location, template, force)
        if not validation['valid']:
            return None, validation
        
        clean_name = validation['sanitized_name']
        project_path = location / clean_name
        
        # Auto-discover resources if enabled
        if auto_discover and not dry_run:
            self.discover_external_resources()
        
        # Dry run mode - just show what would be created
        if dry_run:
            return self._dry_run_report(project_path, template, clean_name)
        
        try:
            with self._atomic_operation():
                # Create base structure
                self._create_structure(project_path, template)
                
                # Link external resources if discovered
                if link_resources and self.discovered_resources:
                    self._create_resource_links(project_path, template)
                
                # Create configuration files
                self._create_config_files(project_path, clean_name, template)
                
                # Initialize git if requested
                if init_git:
                    self._init_git_repo(project_path, clean_name)
                
                # Create health baseline
                self._create_health_baseline(project_path)
                
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # Success report
                report = {
                    'success': True,
                    'project_path': str(project_path),
                    'template': template,
                    'time_seconds': elapsed,
                    'directories_created': len([p for p in self.created_items if p.is_dir()]),
                    'files_created': len([p for p in self.created_items if p.is_file()]),
                    'resources_linked': len(self.discovered_resources.get('stock_footage', [])),
                    'git_initialized': init_git
                }
                
                self._print_success_message(project_path, report)
                return project_path, report
                
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            return None, {
                'success': False,
                'error': str(e),
                'suggestion': 'Check permissions and disk space'
            }
    
    def _validate_inputs(self, name: str, location: Path, template: str, force: bool) -> Dict:
        """Validate all inputs"""
        # Name validation
        valid, error = ProjectValidator.validate_project_name(name)
        if not valid:
            return {
                'valid': False,
                'error': error,
                'suggestion': f"Try: '{ProjectValidator.sanitize_project_name(name)}'"
            }
        
        # Template validation
        if template not in self.TEMPLATES:
            return {
                'valid': False,
                'error': f"Unknown template '{template}'",
                'available_templates': list(self.TEMPLATES.keys())
            }
        
        # Location validation
        if not location.exists():
            return {
                'valid': False,
                'error': f"Location does not exist: {location}"
            }
        
        # Check if project exists
        project_path = location / ProjectValidator.sanitize_project_name(name)
        if project_path.exists() and not force:
            return {
                'valid': False,
                'error': f"Project already exists: {project_path}",
                'suggestion': "Use --force to overwrite"
            }
        
        # Disk space check (need at least 100MB)
        valid, error = ProjectValidator.check_disk_space(location, required_mb=100)
        if not valid:
            return {'valid': False, 'error': error}
        
        return {
            'valid': True,
            'sanitized_name': ProjectValidator.sanitize_project_name(name)
        }
    
    @contextmanager
    def _atomic_operation(self):
        """Ensure atomic operations - all or nothing"""
        try:
            yield
        except Exception:
            # Rollback on any error
            console.print("[yellow]Rolling back changes...[/yellow]")
            for item in reversed(self.created_items):
                try:
                    if item.exists():
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                except Exception as e:
                    logger.error(f"Rollback failed for {item}: {e}")
            raise
    
    def _create_structure(self, project_path: Path, template: str):
        """Create directory structure"""
        template_config = self.TEMPLATES[template]
        
        # Create root
        project_path.mkdir(parents=True, exist_ok=True)
        self.created_items.append(project_path)
        
        # Create .studioflow directory
        studioflow_dir = project_path / '.studioflow'
        studioflow_dir.mkdir(exist_ok=True)
        self.created_items.append(studioflow_dir)
        
        # Create template directories
        for main_dir, subdirs in template_config['directories'].items():
            main_path = project_path / main_dir
            main_path.mkdir(exist_ok=True)
            self.created_items.append(main_path)
            
            # Create subdirectories
            for subdir in subdirs:
                sub_path = main_path / subdir
                sub_path.mkdir(exist_ok=True)
                self.created_items.append(sub_path)
                
                # Add .gitkeep to preserve empty directories
                gitkeep = sub_path / '.gitkeep'
                gitkeep.touch()
                self.created_items.append(gitkeep)
    
    def _create_resource_links(self, project_path: Path, template: str):
        """Create symlinks to discovered external resources"""
        links_dir = project_path / '.studioflow' / 'external_links'
        links_dir.mkdir(exist_ok=True)
        self.created_items.append(links_dir)
        
        # Create links based on template
        if template == 'youtube':
            stock_dir = project_path / '01_FOOTAGE' / 'STOCK'
        else:
            stock_dir = project_path / '00_INGEST' / 'STOCK'
        
        # Link stock footage
        for i, stock_path in enumerate(self.discovered_resources.get('stock_footage', [])):
            source = Path(stock_path)
            if source.exists():
                link_name = f"STOCK_{source.name}" if i > 0 else "STOCK_LIBRARY"
                link_path = stock_dir / link_name
                try:
                    link_path.symlink_to(source)
                    self.created_items.append(link_path)
                    
                    # Also create reference in external_links
                    ref_file = links_dir / f"{link_name}.ref"
                    with open(ref_file, 'w') as f:
                        json.dump({
                            'source': str(source),
                            'target': str(link_path),
                            'type': 'stock_footage',
                            'created': datetime.now().isoformat()
                        }, f, indent=2)
                    self.created_items.append(ref_file)
                except Exception as e:
                    logger.warning(f"Could not create link to {source}: {e}")
    
    def _create_config_files(self, project_path: Path, name: str, template: str):
        """Create all configuration files"""
        template_config = self.TEMPLATES[template]
        
        # Main project configuration
        config = {
            'project': {
                'name': name,
                'template': template,
                'created': datetime.now().isoformat(),
                'studioflow_version': '3.0.0',
                'id': hashlib.sha256(f"{name}{datetime.now()}".encode()).hexdigest()[:12]
            },
            'structure': {
                'directories': list(template_config['directories'].keys()),
                'template_name': template_config['name']
            },
            'resources': {
                'external_links': len(self.discovered_resources.get('stock_footage', [])),
                'discovered': self.discovered_resources
            },
            'settings': {
                'auto_backup': True,
                'health_checks': True,
                'version_control': True
            }
        }
        
        config_file = project_path / '.studioflow' / 'project.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        self.created_items.append(config_file)
        
        # Create README
        self._create_readme(project_path, name, template, template_config)
        
        # Create .gitignore
        self._create_gitignore(project_path)
    
    def _create_readme(self, project_path: Path, name: str, template: str, template_config: Dict):
        """Create comprehensive README"""
        readme = f"""# {name}

**Template**: {template_config['name']} - {template_config['description']}
**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**StudioFlow**: v3.0.0

## Directory Structure
```
{name}/
"""
        for main_dir, subdirs in template_config['directories'].items():
            readme += f"├── {main_dir}/\n"
            for subdir in subdirs[:3]:  # Show first 3 subdirs
                readme += f"│   ├── {subdir}/\n"
            if len(subdirs) > 3:
                readme += f"│   └── ... ({len(subdirs)-3} more)\n"
        
        readme += """└── .studioflow/        # Project metadata and configuration
```

## Quick Start

```bash
# Check project health
studioflow health .

# Discover and link external resources
studioflow discover .

# Create delivery package
studioflow deliver .
```

## External Resources
"""
        
        if self.discovered_resources.get('stock_footage'):
            readme += "\n### Linked Stock Footage\n"
            for path in self.discovered_resources['stock_footage']:
                readme += f"- {path}\n"
        
        if self.discovered_resources.get('archives'):
            readme += "\n### Linked Archives\n"
            for path in self.discovered_resources['archives']:
                readme += f"- {path}\n"
        
        readme += """

## Workflow

1. **Import** footage to appropriate directories
2. **Edit** your project using your preferred NLE
3. **Export** to the EXPORTS directory
4. **Archive** completed project

---
*Generated by StudioFlow - Professional Video Production Automation*
"""
        
        readme_file = project_path / 'README.md'
        with open(readme_file, 'w') as f:
            f.write(readme)
        self.created_items.append(readme_file)
    
    def _create_gitignore(self, project_path: Path):
        """Create comprehensive .gitignore"""
        gitignore = """# StudioFlow
.studioflow/cache/
.studioflow/temp/
.studioflow/*.log

# OS Files
.DS_Store
Thumbs.db
desktop.ini

# Video Editing
*.drp-bak
*.dra-bak
CacheClip/
OptimizedMedia/
ProxyMedia/
RenderCache/
VideoPreview/
AudioPreview/

# Adobe
Adobe Premiere Pro Auto-Save/
Adobe After Effects Auto-Save/
*.prproj.lock

# DaVinci Resolve
*.drp.bak
CacheFiles/
.gallery/
.timeline/

# Large Media (customize as needed)
*.mov
*.mp4
*.avi
*.mxf
*.r3d

# Keep exports
!*/EXPORTS/**/*.mp4
!*/DELIVERY/**/*.mov
"""
        
        gitignore_file = project_path / '.gitignore'
        with open(gitignore_file, 'w') as f:
            f.write(gitignore)
        self.created_items.append(gitignore_file)
    
    def _init_git_repo(self, project_path: Path, name: str):
        """Initialize git repository"""
        repo = git.Repo.init(project_path)
        repo.index.add(['README.md', '.gitignore', '.studioflow/project.yaml'])
        repo.index.commit(f"🎬 Initialize StudioFlow project: {name}")
    
    def _create_health_baseline(self, project_path: Path):
        """Create initial health baseline"""
        health = {
            'baseline': {
                'created': datetime.now().isoformat(),
                'directories': len([p for p in self.created_items if p.is_dir()]),
                'files': len([p for p in self.created_items if p.is_file()]),
                'total_size': sum(p.stat().st_size for p in self.created_items if p.is_file()),
                'structure_hash': self._calculate_structure_hash(project_path)
            },
            'checks': {
                'last_check': None,
                'status': 'healthy',
                'issues': []
            }
        }
        
        health_file = project_path / '.studioflow' / 'health.json'
        with open(health_file, 'w') as f:
            json.dump(health, f, indent=2)
        self.created_items.append(health_file)
    
    def _calculate_structure_hash(self, project_path: Path) -> str:
        """Calculate hash of directory structure"""
        structure = []
        for item in sorted(project_path.rglob('*')):
            if '.studioflow' not in str(item) and '.git' not in str(item):
                structure.append(str(item.relative_to(project_path)))
        return hashlib.sha256('\n'.join(structure).encode()).hexdigest()[:16]
    
    def _dry_run_report(self, project_path: Path, template: str, name: str) -> Tuple[None, Dict]:
        """Generate dry-run report"""
        template_config = self.TEMPLATES[template]
        
        report = {
            'success': True,
            'dry_run': True,
            'would_create': {
                'project_path': str(project_path),
                'directories': len(template_config['directories']) + sum(len(v) for v in template_config['directories'].values()),
                'files': 5,  # README, .gitignore, config, health, etc.
                'external_links': len(self.discovered_resources.get('stock_footage', []))
            },
            'discovered_resources': self.discovered_resources,
            'template': template,
            'name': name
        }
        
        # Print dry-run summary
        console.print("\n[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")
        console.print(f"Would create project: [cyan]{name}[/cyan]")
        console.print(f"Location: [dim]{project_path}[/dim]")
        console.print(f"Template: [green]{template_config['name']}[/green]")
        console.print(f"Directories: {report['would_create']['directories']}")
        console.print(f"Files: {report['would_create']['files']}")
        
        if self.discovered_resources:
            console.print("\n[bold]Would link external resources:[/bold]")
            for resource_type, paths in self.discovered_resources.items():
                if paths:
                    console.print(f"  {resource_type}: {len(paths)} location(s)")
        
        return None, report
    
    def _print_success_message(self, project_path: Path, report: Dict):
        """Print success message with next steps"""
        console.print("\n[green bold]✅ Project created successfully![/green bold]\n")
        
        # Create summary table
        table = Table(title=f"Project: {project_path.name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Location", str(project_path))
        table.add_row("Template", report['template'])
        table.add_row("Directories", str(report['directories_created']))
        table.add_row("Files", str(report['files_created']))
        
        if report['resources_linked'] > 0:
            table.add_row("External Resources", f"{report['resources_linked']} linked")
        
        if report['git_initialized']:
            table.add_row("Git", "Initialized ✓")
        
        table.add_row("Time", f"{report['time_seconds']:.2f}s")
        
        console.print(table)
        
        # Next steps
        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  cd {project_path}")
        console.print("  studioflow health .")
        
        if self.discovered_resources:
            console.print("\n[dim]External resources have been linked automatically.[/dim]")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        level = logging.DEBUG if self.verbose else logging.WARNING
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )