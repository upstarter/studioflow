"""
StudioFlow Workflow Bridge - Seamlessly integrates with existing video production setups
Marketing promise: "Keep your workflow, gain superpowers"
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import hashlib
from ...core.patterns import WorkflowPatterns

class WorkflowBridge:
    """
    Intelligently bridges existing directory structures with StudioFlow's organization.
    Instead of forcing reorganization, we create smart mappings and virtual views.
    """
    
    def __init__(self):
        self.discovered_assets = {}
        self.path_mappings = {}
        self.storage_locations = []
        
    def discover_existing_structure(self, root_path: Path) -> Dict[str, Any]:
        """
        Auto-discovers and analyzes existing video production directory structure.
        Returns intelligent suggestions without requiring any changes.
        """
        discovery = {
            'root': str(root_path),
            'detected_type': 'unknown',
            'assets': {
                'projects': [],
                'stock_footage': [],
                'templates': [],
                'archives': [],
                'active_edits': []
            },
            'storage_stats': {},
            'workflow_patterns': [],
            'integration_score': 0
        }
        
        # Use comprehensive patterns from patterns module
        patterns = WorkflowPatterns()
        
        # Smart pattern detection using comprehensive patterns
        for root, dirs, files in os.walk(root_path):
            root_path_obj = Path(root)
            depth = len(root_path_obj.relative_to(root_path).parts)
            
            # Don't go too deep for performance
            if depth > 3:
                dirs.clear()
                continue
            
            # Detect workflow type based on project files
            detected_type = patterns.detect_workflow_type(root_path_obj)
            if detected_type != 'generic_video' and detected_type != discovery['detected_type']:
                discovery['detected_type'] = detected_type
                discovery['workflow_patterns'].append({
                    'type': detected_type,
                    'location': str(root_path_obj),
                    'confidence': 0.9 if depth <= 2 else 0.7
                })
            
            # Categorize directories
            dir_categories = patterns.categorize_directory(root_path_obj.name)
            
            # Detect stock footage libraries
            if patterns.is_stock_directory(root_path_obj.name):
                discovery['assets']['stock_footage'].append({
                    'path': str(root_path_obj),
                    'size_gb': self._get_dir_size_gb(root_path_obj),
                    'file_count': len(list(root_path_obj.glob('**/*'))),
                    'categories': dir_categories
                })
            
            # Detect source media directories
            if patterns.is_source_media_directory(root_path_obj.name):
                discovery['assets']['active_edits'].append({
                    'path': str(root_path_obj),
                    'type': 'source_media',
                    'categories': dir_categories
                })
            
            # Detect project directories
            if 'project' in dir_categories or 'edit' in dir_categories:
                for subdir in dirs:
                    project_path = root_path_obj / subdir
                    if self._looks_like_project(project_path):
                        discovery['assets']['projects'].append({
                            'name': subdir,
                            'path': str(project_path),
                            'modified': datetime.fromtimestamp(
                                project_path.stat().st_mtime
                            ).isoformat(),
                            'categories': patterns.categorize_directory(subdir)
                        })
            
            # Check for archive directories
            if 'backup' in dir_categories:
                discovery['assets']['archives'].append({
                    'path': str(root_path_obj),
                    'size_gb': self._get_dir_size_gb(root_path_obj)
                })
        
        # Calculate integration score (0-100)
        score = 0
        if discovery['workflow_patterns']:
            score += 30
        if discovery['assets']['projects']:
            score += 30
        if discovery['assets']['stock_footage']:
            score += 20
        score += min(20, len(discovery['workflow_patterns']) * 5)
        
        discovery['integration_score'] = min(100, score)
        
        # Detected type is already set by patterns.detect_workflow_type()
        if discovery['detected_type'] == 'unknown' and discovery['assets']['projects']:
            discovery['detected_type'] = 'generic_video'
        
        return discovery
    
    def create_bridge_config(
        self,
        existing_root: Path,
        studioflow_project: Path,
        discovery: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Creates a bridge configuration that maps existing structure to StudioFlow.
        This is the SECRET SAUCE - no copying, just intelligent linking.
        """
        if discovery is None:
            discovery = self.discover_existing_structure(existing_root)
        
        bridge_config = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'mode': 'bridge',  # Can be 'bridge', 'hybrid', or 'migrate'
            'existing_root': str(existing_root),
            'studioflow_project': str(studioflow_project),
            'mappings': {
                # Map StudioFlow directories to existing locations
                '00_INGEST': [],
                '01_PROXIES': [],
                '02_AUDIO': [],
                '03_GFX': [],
                '04_GRADES': [],
                '05_PROJECT': [],
                '06_TIMELINES': [],
                '07_VFX': [],
                '08_RENDERS': [],
                '09_DELIVERY': [],
                '10_DOCUMENTS': [],
                '11_SMART_BINS': []
            },
            'symlinks': [],
            'watch_folders': [],
            'exclusions': [],
            'storage_pools': []
        }
        
        # Intelligent mapping based on discovery
        for footage in discovery['assets'].get('stock_footage', []):
            bridge_config['mappings']['00_INGEST'].append({
                'type': 'symlink',
                'source': footage['path'],
                'target': 'STOCK_LIBRARY',
                'read_only': True
            })
        
        # Map active projects
        for project in discovery['assets'].get('projects', []):
            bridge_config['mappings']['05_PROJECT'].append({
                'type': 'reference',
                'source': project['path'],
                'name': project['name'],
                'sync': 'bidirectional'
            })
        
        # Add storage pools for distributed assets
        bridge_config['storage_pools'] = [
            {
                'name': 'primary',
                'path': str(existing_root),
                'type': 'nas' if 'nas' in str(existing_root).lower() else 'local',
                'priority': 1,
                'usage': 'active'
            },
            {
                'name': 'studioflow',
                'path': str(studioflow_project),
                'type': 'local',
                'priority': 2,
                'usage': 'cache,proxy,temp'
            }
        ]
        
        return bridge_config
    
    def apply_bridge(
        self,
        bridge_config: Dict[str, Any],
        dry_run: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Applies the bridge configuration, creating symlinks and mappings.
        This is non-destructive - existing structure remains untouched.
        """
        actions = []
        studioflow_project = Path(bridge_config['studioflow_project'])
        
        for rf_dir, mappings in bridge_config['mappings'].items():
            for mapping in mappings:
                if mapping['type'] == 'symlink':
                    source = Path(mapping['source'])
                    target = studioflow_project / rf_dir / mapping['target']
                    
                    action = {
                        'type': 'create_symlink',
                        'source': str(source),
                        'target': str(target),
                        'status': 'pending'
                    }
                    
                    if not dry_run:
                        try:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            if target.exists():
                                target.unlink()
                            target.symlink_to(source)
                            action['status'] = 'completed'
                        except Exception as e:
                            action['status'] = 'failed'
                            action['error'] = str(e)
                    
                    actions.append(action)
                
                elif mapping['type'] == 'reference':
                    # Create a reference file instead of symlink
                    ref_file = studioflow_project / rf_dir / f"{mapping['name']}.ref"
                    
                    action = {
                        'type': 'create_reference',
                        'source': mapping['source'],
                        'reference': str(ref_file),
                        'status': 'pending'
                    }
                    
                    if not dry_run:
                        try:
                            ref_file.parent.mkdir(parents=True, exist_ok=True)
                            ref_data = {
                                'source': mapping['source'],
                                'sync': mapping.get('sync', 'none'),
                                'created': datetime.now().isoformat()
                            }
                            with open(ref_file, 'w') as f:
                                json.dump(ref_data, f, indent=2)
                            action['status'] = 'completed'
                        except Exception as e:
                            action['status'] = 'failed'
                            action['error'] = str(e)
                    
                    actions.append(action)
        
        # Save bridge configuration
        if not dry_run:
            bridge_file = studioflow_project / '.studioflow' / 'bridge.yaml'
            bridge_file.parent.mkdir(parents=True, exist_ok=True)
            with open(bridge_file, 'w') as f:
                yaml.dump(bridge_config, f, default_flow_style=False)
        
        return actions
    
    def create_workspace_profile(
        self,
        name: str,
        paths: Dict[str, Union[str, List[str]]]
    ) -> Dict[str, Any]:
        """
        Creates a reusable workspace profile for common setups.
        Example: 'nas_workflow', 'cloud_hybrid', 'local_only'
        """
        profile = {
            'name': name,
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'paths': {
                'stock_footage': paths.get('stock_footage', []),
                'project_templates': paths.get('project_templates', []),
                'render_output': paths.get('render_output', './08_RENDERS'),
                'archive': paths.get('archive', []),
                'watch_folders': paths.get('watch_folders', []),
                'cache': paths.get('cache', '/tmp/studioflow_cache')
            },
            'rules': {
                'auto_proxy': paths.get('auto_proxy', True),
                'preserve_originals': paths.get('preserve_originals', True),
                'sync_to_cloud': paths.get('sync_to_cloud', False),
                'deduplicate': paths.get('deduplicate', True)
            },
            'storage_tiers': [
                {
                    'name': 'hot',
                    'paths': paths.get('hot_storage', []),
                    'usage': 'active_edit,cache,proxy'
                },
                {
                    'name': 'warm',
                    'paths': paths.get('warm_storage', []),
                    'usage': 'recent_projects,templates'
                },
                {
                    'name': 'cold',
                    'paths': paths.get('cold_storage', []),
                    'usage': 'archive,backup'
                }
            ]
        }
        
        # Save profile for reuse
        profile_dir = Path.home() / '.studioflow' / 'profiles'
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        profile_file = profile_dir / f"{name}.yaml"
        with open(profile_file, 'w') as f:
            yaml.dump(profile, f, default_flow_style=False)
        
        return profile
    
    def suggest_optimizations(
        self,
        existing_root: Path
    ) -> List[Dict[str, Any]]:
        """
        Analyzes existing structure and suggests optimizations.
        This showcases StudioFlow's intelligence without being pushy.
        """
        suggestions = []
        discovery = self.discover_existing_structure(existing_root)
        
        # Check for duplicate files
        seen_hashes = {}
        duplicates = []
        
        for root, _, files in os.walk(existing_root):
            for file in files:
                file_path = Path(root) / file
                if file_path.stat().st_size > 100 * 1024 * 1024:  # Only check files > 100MB
                    file_hash = self._get_file_hash(file_path, quick=True)
                    if file_hash in seen_hashes:
                        duplicates.append({
                            'original': seen_hashes[file_hash],
                            'duplicate': str(file_path),
                            'size_mb': file_path.stat().st_size / (1024 * 1024)
                        })
                    else:
                        seen_hashes[file_hash] = str(file_path)
        
        if duplicates:
            total_waste = sum(d['size_mb'] for d in duplicates)
            suggestions.append({
                'type': 'deduplication',
                'severity': 'medium',
                'message': f"Found {len(duplicates)} duplicate files wasting {total_waste:.1f} MB",
                'action': 'StudioFlow can manage these with hardlinks',
                'savings': f"{total_waste:.1f} MB"
            })
        
        # Check for missing proxy organization
        has_raw_footage = any('raw' in str(p).lower() for p in Path(existing_root).rglob('*'))
        has_proxies = any('prox' in str(p).lower() for p in Path(existing_root).rglob('*'))
        
        if has_raw_footage and not has_proxies:
            suggestions.append({
                'type': 'proxy_generation',
                'severity': 'high',
                'message': 'No proxy structure detected for raw footage',
                'action': 'StudioFlow can auto-generate and manage proxies',
                'benefit': '10x faster editing performance'
            })
        
        # Check for backup strategy
        if not any('backup' in str(p).lower() for p in Path(existing_root).iterdir()):
            suggestions.append({
                'type': 'backup_strategy',
                'severity': 'high',
                'message': 'No backup structure detected',
                'action': 'StudioFlow can implement 3-2-1 backup strategy',
                'benefit': 'Protect against data loss'
            })
        
        return suggestions
    
    def _looks_like_project(self, path: Path) -> bool:
        """Heuristic to determine if a directory is a video project"""
        patterns = WorkflowPatterns()
        
        # Check for project files
        for app_name, extensions in patterns.get_project_file_extensions().items():
            for ext in extensions:
                if list(path.glob(f'*{ext}')):
                    return True
        
        # Check for video files
        video_extensions = patterns.get_all_video_extensions()
        for ext in list(video_extensions)[:10]:  # Check first 10 for performance
            if list(path.glob(f'*{ext}')):
                return True
        
        # Check for common project directory patterns
        dir_categories = patterns.categorize_directory(path.name)
        if any(cat in ['project', 'edit', 'source_media'] for cat in dir_categories):
            return True
        
        return False
    
    def _get_dir_size_gb(self, path: Path) -> float:
        """Get directory size in GB"""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except:
            pass
        return total / (1024 ** 3)
    
    def _get_file_hash(self, file_path: Path, quick: bool = True) -> str:
        """Get file hash for deduplication detection"""
        hasher = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                if quick:
                    # Just hash first and last MB for speed
                    hasher.update(f.read(1024 * 1024))
                    f.seek(-1024 * 1024, 2)
                    hasher.update(f.read(1024 * 1024))
                else:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
        except:
            return ""
        
        return hasher.hexdigest()