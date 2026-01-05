"""
Version Manager - Git wrapper for non-technical users
Provides simple version control without Git knowledge
"""

import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import json

class VersionManager:
    """User-friendly version control powered by Git"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.git_dir = project_path / '.git'
        
        # Initialize if needed
        if not self.git_dir.exists():
            self._init_repo()
    
    def _init_repo(self):
        """Initialize git repo silently"""
        subprocess.run(['git', 'init'], 
                      cwd=self.project_path,
                      capture_output=True)
        
        # Set up user if not configured
        self._ensure_git_config()
        
        # Initial commit
        self.save_version("Project created")
    
    def _ensure_git_config(self):
        """Ensure git has user config"""
        try:
            # Check if user.name is set
            result = subprocess.run(['git', 'config', 'user.name'],
                                  cwd=self.project_path,
                                  capture_output=True, text=True)
            if not result.stdout.strip():
                # Set default for StudioFlow
                subprocess.run(['git', 'config', 'user.name', 'StudioFlow User'],
                             cwd=self.project_path, capture_output=True)
                subprocess.run(['git', 'config', 'user.email', 'user@studioflow.local'],
                             cwd=self.project_path, capture_output=True)
        except:
            pass
    
    # ============================================
    # USER-FRIENDLY METHODS (No Git knowledge needed)
    # ============================================
    
    def save_version(self, description: str = None) -> bool:
        """
        Save current project state (git commit)
        
        What users see: "Save Version"
        What happens: git add -A && git commit
        """
        try:
            # Stage all changes
            subprocess.run(['git', 'add', '-A'], 
                         cwd=self.project_path,
                         capture_output=True, check=True)
            
            # Create meaningful commit message
            if not description:
                description = "Quick save"
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            message = f"{description} ({timestamp})"
            
            # Commit
            result = subprocess.run(['git', 'commit', '-m', message],
                                  cwd=self.project_path,
                                  capture_output=True, text=True)
            
            return 'nothing to commit' not in result.stdout
        except:
            return False
    
    def auto_save(self) -> bool:
        """
        Auto-save with timestamp (for background saves)
        
        What users see: "Auto-saved"
        What happens: git commit with timestamp
        """
        return self.save_version(f"Auto-save")
    
    def save_milestone(self, name: str, notes: str = "") -> bool:
        """
        Save important milestone (git tag)
        
        What users see: "Save Milestone: First Draft Complete"
        What happens: git tag -a "first-draft" -m "notes"
        """
        try:
            # First commit current changes
            self.save_version(f"Milestone: {name}")
            
            # Create tag
            tag_name = name.lower().replace(' ', '-')
            subprocess.run(['git', 'tag', '-a', tag_name, '-m', notes or name],
                         cwd=self.project_path,
                         capture_output=True, check=True)
            return True
        except:
            return False
    
    def get_versions(self, limit: int = 50) -> List[Dict]:
        """
        Get version history (git log)
        
        What users see: "Version History"
        What happens: git log parsing
        """
        try:
            result = subprocess.run([
                'git', 'log', 
                '--format=%H|%s|%ad|%an',
                '--date=relative',
                f'-{limit}'
            ], cwd=self.project_path, capture_output=True, text=True)
            
            versions = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    versions.append({
                        'id': parts[0][:8],  # Short hash
                        'description': parts[1],
                        'time': parts[2],
                        'author': parts[3],
                        'full_id': parts[0]
                    })
            return versions
        except:
            return []
    
    def restore_version(self, version_id: str) -> bool:
        """
        Restore to previous version (git checkout)
        
        What users see: "Restore to: 2 hours ago"
        What happens: git checkout {commit}
        """
        try:
            # Save current state first
            self.save_version("Before restore")
            
            # Checkout the version
            subprocess.run(['git', 'checkout', version_id, '.'],
                         cwd=self.project_path,
                         capture_output=True, check=True)
            
            # Create a new commit for the restore
            self.save_version(f"Restored to: {version_id[:8]}")
            return True
        except:
            return False
    
    def compare_versions(self, version1: str = 'HEAD', version2: str = 'HEAD~1') -> Dict:
        """
        Compare two versions (git diff)
        
        What users see: "Compare with yesterday"
        What happens: git diff --stat
        """
        try:
            result = subprocess.run([
                'git', 'diff', '--stat', version2, version1
            ], cwd=self.project_path, capture_output=True, text=True)
            
            stats = {
                'files_changed': 0,
                'insertions': 0,
                'deletions': 0,
                'files': []
            }
            
            lines = result.stdout.strip().split('\n')
            for line in lines[:-1]:  # Skip summary line
                if '|' in line:
                    file_name = line.split('|')[0].strip()
                    stats['files'].append(file_name)
                    stats['files_changed'] += 1
            
            # Parse summary line
            if lines:
                summary = lines[-1]
                if 'insertion' in summary:
                    stats['insertions'] = int(summary.split('insertion')[0].split()[-1])
                if 'deletion' in summary:
                    stats['deletions'] = int(summary.split('deletion')[0].split()[-1])
            
            return stats
        except:
            return {}
    
    def create_branch(self, name: str) -> bool:
        """
        Create alternate version (git branch)
        
        What users see: "Create Alternative Edit"
        What happens: git checkout -b {branch}
        """
        try:
            branch_name = name.lower().replace(' ', '-')
            subprocess.run(['git', 'checkout', '-b', branch_name],
                         cwd=self.project_path,
                         capture_output=True, check=True)
            return True
        except:
            return False
    
    def list_alternatives(self) -> List[str]:
        """
        List alternative edits (git branch)
        
        What users see: "Alternative Edits"
        What happens: git branch listing
        """
        try:
            result = subprocess.run(['git', 'branch'],
                                  cwd=self.project_path,
                                  capture_output=True, text=True)
            
            branches = []
            for line in result.stdout.strip().split('\n'):
                branch = line.strip().replace('* ', '')
                if branch and branch != 'main' and branch != 'master':
                    branches.append(branch)
            return branches
        except:
            return []
    
    def switch_alternative(self, name: str) -> bool:
        """
        Switch to alternative edit (git checkout)
        
        What users see: "Switch to: Director's Cut"
        What happens: git checkout {branch}
        """
        try:
            subprocess.run(['git', 'checkout', name],
                         cwd=self.project_path,
                         capture_output=True, check=True)
            return True
        except:
            return False
    
    def archive_project(self, output_path: Path) -> bool:
        """
        Create project archive (git bundle)
        
        What users see: "Archive Project"
        What happens: git bundle with all history
        """
        try:
            bundle_file = output_path / f"{self.project_path.name}.bundle"
            subprocess.run(['git', 'bundle', 'create', str(bundle_file), '--all'],
                         cwd=self.project_path,
                         capture_output=True, check=True)
            
            # Also create metadata file
            metadata = {
                'project_name': self.project_path.name,
                'archived': datetime.now().isoformat(),
                'versions': len(self.get_versions(limit=999)),
                'size': bundle_file.stat().st_size
            }
            
            metadata_file = output_path / f"{self.project_path.name}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True
        except:
            return False