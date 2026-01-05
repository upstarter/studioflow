"""
Performance-optimized project generator using parallel operations
"""

import os
import json
import yaml
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing

from .generator_v2 import ProjectGeneratorV2


class OptimizedProjectGenerator(ProjectGeneratorV2):
    """
    Performance-optimized version of project generator
    Uses async I/O and parallel processing for speed
    """
    
    def __init__(self, dry_run: bool = False, verbose: bool = False, max_workers: Optional[int] = None):
        super().__init__(dry_run, verbose)
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) * 2)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    async def create_project_async(
        self,
        name: str,
        location: Path,
        template: str = 'standard',
        init_git: bool = True,
        force: bool = False,
        metadata: Optional[Dict] = None
    ) -> Tuple[Optional[Path], Dict]:
        """
        Async version of project creation for better performance
        """
        # Validation is still synchronous (fast)
        if not self.validate_inputs(name, location, template, force):
            return None, {
                'success': False,
                'errors': self.validation_errors,
                'warnings': self.warnings
            }
        
        project_path = location / name
        
        # Handle existing project
        if project_path.exists():
            if force:
                if not self.dry_run:
                    await self._remove_directory_async(project_path)
            else:
                return None, {
                    'success': False,
                    'errors': [f"Project exists: {project_path}"]
                }
        
        start_time = datetime.now()
        
        try:
            # Create base structure in parallel
            await asyncio.gather(
                self._create_project_root_async(project_path),
                self._prepare_templates_async(template)
            )
            
            # Create all directories and files in parallel
            tasks = [
                self._create_directories_parallel(project_path, template),
                self._create_all_config_files_async(project_path, name, template, metadata),
                self._create_readme_async(project_path, name, template)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for errors
            for result in results:
                if isinstance(result, Exception):
                    raise result
            
            # Git and manifest creation (sequential for safety)
            if init_git:
                await self._initialize_git_async(project_path)
            
            manifest = await self._create_manifest_async(project_path)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            return project_path, {
                'success': True,
                'project_path': str(project_path),
                'warnings': self.warnings,
                'stats': {
                    'time_taken': elapsed,
                    'directories_created': results[0],
                    'files_created': results[1] + 1  # +1 for README
                }
            }
            
        except Exception as e:
            self._rollback()
            return None, {
                'success': False,
                'errors': [str(e)]
            }
    
    async def _create_project_root_async(self, project_path: Path):
        """Create project root directory asynchronously"""
        if not self.dry_run:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: project_path.mkdir(parents=True, exist_ok=True)
            )
            self.created_items.append(project_path)
            
            # Create metadata directory
            metadata_dir = project_path / '.studioflow'
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: metadata_dir.mkdir(exist_ok=True)
            )
            self.created_items.append(metadata_dir)
    
    async def _prepare_templates_async(self, template: str):
        """Pre-process templates for faster access"""
        # This could load templates from disk if they were external
        pass
    
    async def _create_directories_parallel(self, project_path: Path, template: str) -> int:
        """Create all directories in parallel using thread pool"""
        template_config = self.TEMPLATES.get(template, self.TEMPLATES['standard'])
        
        # Prepare all directory paths
        dir_tasks = []
        for directory in template_config['directories']:
            dir_path = project_path / directory
            dir_tasks.append((dir_path, None))
            
            # Add subdirectories
            subdirs = template_config.get('subdirs', {}).get(directory, [])
            for subdir in subdirs:
                subdir_path = dir_path / subdir
                dir_tasks.append((subdir_path, subdir_path / '.gitkeep'))
        
        # Create all directories in parallel
        if not self.dry_run:
            loop = asyncio.get_event_loop()
            tasks = []
            
            for dir_path, gitkeep_path in dir_tasks:
                tasks.append(loop.run_in_executor(
                    self.executor,
                    self._create_directory_with_gitkeep,
                    dir_path,
                    gitkeep_path
                ))
            
            await asyncio.gather(*tasks)
        
        return len(dir_tasks)
    
    def _create_directory_with_gitkeep(self, dir_path: Path, gitkeep_path: Optional[Path]):
        """Create directory and optional .gitkeep file"""
        dir_path.mkdir(parents=True, exist_ok=True)
        self.created_items.append(dir_path)
        
        if gitkeep_path:
            gitkeep_path.touch()
            self.created_items.append(gitkeep_path)
    
    async def _create_all_config_files_async(
        self,
        project_path: Path,
        name: str,
        template: str,
        metadata: Optional[Dict]
    ) -> int:
        """Create all config files in parallel"""
        if self.dry_run:
            return 2
        
        # Prepare config data
        configs = self._prepare_config_data(project_path, name, template, metadata)
        
        # Write all configs in parallel
        tasks = []
        for file_path, data in configs.items():
            tasks.append(self._write_yaml_async(file_path, data))
        
        await asyncio.gather(*tasks)
        return len(tasks)
    
    def _prepare_config_data(
        self,
        project_path: Path,
        name: str,
        template: str,
        metadata: Optional[Dict]
    ) -> Dict[Path, Dict]:
        """Prepare all configuration data"""
        configs = {}
        
        # Main config
        configs[project_path / '.studioflow' / 'config.yaml'] = {
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
        
        # Pipeline config
        configs[project_path / '.studioflow' / 'pipeline.yaml'] = {
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
        
        # Health baseline
        configs[project_path / '.studioflow' / 'health_baseline.json'] = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'expected_structure': {
                'directories': list(self.STANDARD_DIRECTORIES)
            }
        }
        
        return configs
    
    async def _write_yaml_async(self, file_path: Path, data: Dict):
        """Write YAML file asynchronously"""
        # Convert to YAML string first
        if file_path.suffix == '.json':
            content = json.dumps(data, indent=2)
        else:
            content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        
        # Write asynchronously
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(content)
        
        self.created_items.append(file_path)
    
    async def _create_readme_async(self, project_path: Path, name: str, template: str):
        """Create README file asynchronously"""
        if self.dry_run:
            return
        
        content = self._generate_readme_content(name, template)
        
        async with aiofiles.open(project_path / 'README.md', 'w') as f:
            await f.write(content)
        
        self.created_items.append(project_path / 'README.md')
    
    def _generate_readme_content(self, name: str, template: str) -> str:
        """Generate README content (same as parent class)"""
        return f"""# {name}

## Project Information
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Template**: {template}
- **StudioFlow Version**: 0.1.0

## Directory Structure
See `.studioflow/manifest.json` for complete structure.

## Quick Commands
```bash
studioflow-project health .
studioflow-project snapshot .
```

---
*Generated by StudioFlow*
"""
    
    async def _initialize_git_async(self, project_path: Path):
        """Initialize git repository asynchronously"""
        if self.dry_run:
            return
        
        # Git operations in executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._initialize_git_sync,
            project_path
        )
    
    def _initialize_git_sync(self, project_path: Path):
        """Synchronous git initialization (called in executor)"""
        import git
        
        repo = git.Repo.init(project_path)
        
        # Create .gitignore
        gitignore_path = project_path / '.gitignore'
        gitignore_path.write_text(self._get_gitignore_content())
        self.created_items.append(gitignore_path)
        
        # Create .gitattributes
        gitattributes_path = project_path / '.gitattributes'
        gitattributes_path.write_text(self._get_gitattributes_content())
        self.created_items.append(gitattributes_path)
        
        # Initial commit
        repo.index.add(['.gitignore', '.gitattributes', 'README.md'])
        repo.index.commit("Initial commit: StudioFlow project")
    
    def _get_gitignore_content(self) -> str:
        """Get gitignore content"""
        return """# StudioFlow
*.cache
*.tmp
*.log
.DS_Store
Thumbs.db

# Media
*.mov
*.mp4
*.avi
*.mxf

# Keep delivery
!09_DELIVERY/**/*.mov
!09_DELIVERY/**/*.mp4
"""
    
    def _get_gitattributes_content(self) -> str:
        """Get gitattributes content"""
        return """# Binary files
*.mov binary
*.mp4 binary
*.jpg binary
*.png binary
*.psd binary

# Text files
*.txt text
*.md text
*.yaml text
*.json text
"""
    
    async def _create_manifest_async(self, project_path: Path) -> Dict:
        """Create manifest file asynchronously"""
        if self.dry_run:
            return {}
        
        # Gather file information in parallel
        loop = asyncio.get_event_loop()
        manifest = await loop.run_in_executor(
            self.executor,
            self._generate_manifest,
            project_path
        )
        
        # Write manifest
        manifest_path = project_path / '.studioflow' / 'manifest.json'
        async with aiofiles.open(manifest_path, 'w') as f:
            await f.write(json.dumps(manifest, indent=2))
        
        self.created_items.append(manifest_path)
        return manifest
    
    def _generate_manifest(self, project_path: Path) -> Dict:
        """Generate manifest data"""
        manifest = {
            'version': '2.0',
            'created': datetime.now().isoformat(),
            'directories': [],
            'files': []
        }
        
        for root, dirs, files in os.walk(project_path):
            root_path = Path(root)
            if not str(root_path).startswith('.git'):
                rel_path = root_path.relative_to(project_path)
                manifest['directories'].append(str(rel_path))
                
                for file in files:
                    if not file.startswith('.git'):
                        file_path = root_path / file
                        manifest['files'].append({
                            'path': str(file_path.relative_to(project_path)),
                            'size': file_path.stat().st_size
                        })
        
        return manifest
    
    async def _remove_directory_async(self, path: Path):
        """Remove directory asynchronously"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            lambda: shutil.rmtree(path)
        )
    
    def create_project_sync(self, *args, **kwargs):
        """Synchronous wrapper for async project creation"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.create_project_async(*args, **kwargs)
            )
        finally:
            loop.close()
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)