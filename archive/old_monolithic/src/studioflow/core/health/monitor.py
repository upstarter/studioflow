import json
import yaml
import shutil
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib

class HealthMonitor:
    """Monitor and maintain project health"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.metadata_dir = self.project_path / '.studioflow'
        
        if not self.metadata_dir.exists():
            raise ValueError(f"Not a StudioFlow project: {project_path}")
        
        self.config_path = self.metadata_dir / 'config.yaml'
        self.manifest_path = self.metadata_dir / 'manifest.json'
        self.health_log_path = self.metadata_dir / 'health.log'
    
    def check_health(self, verbose: bool = False) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        report = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'issues': [],
            'stats': {}
        }
        
        self._check_directory_structure(report)
        
        self._check_disk_usage(report)
        
        self._check_config_integrity(report)
        
        self._check_file_integrity(report, verbose)
        
        self._check_git_status(report)
        
        if any(issue['level'] == 'error' for issue in report['issues']):
            report['status'] = 'error'
        elif any(issue['level'] == 'warning' for issue in report['issues']):
            report['status'] = 'warning'
        
        self._log_health_check(report)
        
        return report
    
    def _check_directory_structure(self, report: Dict[str, Any]):
        """Verify expected directories exist"""
        try:
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
            
            expected_dirs = set(manifest.get('directories', []))
            actual_dirs = set()
            
            for root, dirs, _ in os.walk(self.project_path):
                root_path = Path(root)
                if not str(root_path).startswith('.git'):
                    rel_path = root_path.relative_to(self.project_path)
                    actual_dirs.add(str(rel_path))
            
            missing_dirs = expected_dirs - actual_dirs
            extra_dirs = actual_dirs - expected_dirs
            
            if missing_dirs:
                report['issues'].append({
                    'level': 'error',
                    'message': f"Missing directories: {', '.join(missing_dirs)}"
                })
            
            if extra_dirs and len(extra_dirs) > 5:
                report['issues'].append({
                    'level': 'info',
                    'message': f"Found {len(extra_dirs)} additional directories"
                })
            
            report['stats']['directories'] = {
                'expected': len(expected_dirs),
                'actual': len(actual_dirs),
                'missing': len(missing_dirs)
            }
            
        except Exception as e:
            report['issues'].append({
                'level': 'error',
                'message': f"Failed to check directory structure: {e}"
            })
    
    def _check_disk_usage(self, report: Dict[str, Any]):
        """Check disk usage and available space"""
        try:
            disk_usage = shutil.disk_usage(self.project_path)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            max_usage = config.get('monitoring', {}).get('max_disk_usage_percent', 90)
            
            if usage_percent > max_usage:
                report['issues'].append({
                    'level': 'warning',
                    'message': f"Disk usage at {usage_percent:.1f}% (threshold: {max_usage}%)"
                })
            
            project_size = sum(
                f.stat().st_size for f in self.project_path.rglob('*') if f.is_file()
            )
            
            report['stats']['disk'] = {
                'project_size_gb': project_size / (1024**3),
                'disk_usage_percent': usage_percent,
                'free_space_gb': disk_usage.free / (1024**3)
            }
            
        except Exception as e:
            report['issues'].append({
                'level': 'warning',
                'message': f"Failed to check disk usage: {e}"
            })
    
    def _check_config_integrity(self, report: Dict[str, Any]):
        """Verify configuration files are valid"""
        config_files = [
            self.config_path,
            self.metadata_dir / 'pipeline.yaml'
        ]
        
        for config_file in config_files:
            if not config_file.exists():
                report['issues'].append({
                    'level': 'error',
                    'message': f"Missing config file: {config_file.name}"
                })
                continue
            
            try:
                with open(config_file, 'r') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                report['issues'].append({
                    'level': 'error',
                    'message': f"Invalid YAML in {config_file.name}: {e}"
                })
    
    def _check_file_integrity(self, report: Dict[str, Any], verbose: bool):
        """Check for corrupted or missing files"""
        try:
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
            
            missing_files = []
            changed_files = []
            
            for file_info in manifest.get('files', []):
                file_path = self.project_path / file_info['path']
                
                if not file_path.exists():
                    missing_files.append(file_info['path'])
                elif verbose:
                    current_size = file_path.stat().st_size
                    if current_size != file_info['size']:
                        changed_files.append(file_info['path'])
            
            if missing_files:
                report['issues'].append({
                    'level': 'warning',
                    'message': f"Missing {len(missing_files)} files from manifest"
                })
            
            if changed_files and verbose:
                report['issues'].append({
                    'level': 'info',
                    'message': f"{len(changed_files)} files have changed size"
                })
            
            report['stats']['files'] = {
                'total': len(manifest.get('files', [])),
                'missing': len(missing_files),
                'changed': len(changed_files)
            }
            
        except Exception as e:
            report['issues'].append({
                'level': 'warning',
                'message': f"Failed to check file integrity: {e}"
            })
    
    def _check_git_status(self, report: Dict[str, Any]):
        """Check git repository status"""
        git_dir = self.project_path / '.git'
        
        if not git_dir.exists():
            report['issues'].append({
                'level': 'info',
                'message': "Git repository not initialized"
            })
            return
        
        try:
            import git
            repo = git.Repo(self.project_path)
            
            if repo.is_dirty():
                report['issues'].append({
                    'level': 'info',
                    'message': f"Uncommitted changes in repository"
                })
            
            untracked = repo.untracked_files
            if untracked:
                report['issues'].append({
                    'level': 'info',
                    'message': f"{len(untracked)} untracked files"
                })
            
            report['stats']['git'] = {
                'branch': repo.active_branch.name,
                'commits': len(list(repo.iter_commits())),
                'uncommitted': repo.is_dirty(),
                'untracked': len(untracked)
            }
            
        except Exception as e:
            report['issues'].append({
                'level': 'warning',
                'message': f"Failed to check git status: {e}"
            })
    
    def _log_health_check(self, report: Dict[str, Any]):
        """Log health check results"""
        try:
            log_entry = {
                'timestamp': report['timestamp'],
                'status': report['status'],
                'issue_count': len(report['issues']),
                'stats': report['stats']
            }
            
            with open(self.health_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception:
            pass
    
    def create_snapshot(self, name: Optional[str] = None) -> Path:
        """Create a project snapshot"""
        snapshot_dir = self.metadata_dir / 'snapshots'
        snapshot_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_name = f"{timestamp}_{name}" if name else timestamp
        
        snapshot_data = {
            'name': snapshot_name,
            'timestamp': datetime.now().isoformat(),
            'description': name,
            'project_state': {}
        }
        
        with open(self.config_path, 'r') as f:
            snapshot_data['config'] = yaml.safe_load(f)
        
        with open(self.manifest_path, 'r') as f:
            snapshot_data['manifest'] = json.load(f)
        
        health_report = self.check_health(verbose=False)
        snapshot_data['health'] = health_report
        
        try:
            import git
            repo = git.Repo(self.project_path)
            snapshot_data['git'] = {
                'branch': repo.active_branch.name,
                'commit': repo.head.commit.hexsha,
                'dirty': repo.is_dirty()
            }
        except:
            snapshot_data['git'] = None
        
        snapshot_data['file_checksums'] = self._calculate_checksums()
        
        snapshot_file = snapshot_dir / f"{snapshot_name}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        return snapshot_file
    
    def _calculate_checksums(self) -> Dict[str, str]:
        """Calculate checksums for critical files"""
        checksums = {}
        critical_extensions = ['.drp', '.dra', '.yaml', '.json', '.xml']
        
        for ext in critical_extensions:
            for file_path in self.project_path.rglob(f'*{ext}'):
                if not str(file_path).startswith('.git'):
                    rel_path = str(file_path.relative_to(self.project_path))
                    
                    if file_path.stat().st_size < 10 * 1024 * 1024:
                        hasher = hashlib.sha256()
                        with open(file_path, 'rb') as f:
                            hasher.update(f.read())
                        checksums[rel_path] = hasher.hexdigest()
        
        return checksums