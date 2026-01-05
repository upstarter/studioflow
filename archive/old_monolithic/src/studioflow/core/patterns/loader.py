"""
Pattern Loader - Loads and merges custom patterns with defaults
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .workflow import WorkflowPatterns

class PatternLoader:
    """Loads custom patterns and merges with defaults"""
    
    def __init__(self, custom_config_path: Optional[Path] = None):
        self.base_patterns = WorkflowPatterns()
        self.custom_patterns = {}
        
        # Try to load from multiple locations
        config_paths = [
            custom_config_path,
            Path.home() / '.studioflow' / 'custom_patterns.yaml',
            Path.cwd() / 'studioflow_patterns.yaml',
            Path('/etc/studioflow/patterns.yaml'),
        ]
        
        for path in config_paths:
            if path and path.exists():
                self.load_custom_patterns(path)
                break
    
    def load_custom_patterns(self, config_path: Path) -> None:
        """Load custom patterns from YAML file"""
        try:
            with open(config_path, 'r') as f:
                self.custom_patterns = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load custom patterns from {config_path}: {e}")
    
    def get_merged_patterns(self) -> Dict[str, Any]:
        """Merge custom patterns with base patterns"""
        merged = {
            'file_extensions': dict(self.base_patterns.FILE_EXTENSIONS),
            'directory_patterns': dict(self.base_patterns.DIRECTORY_PATTERNS),
            'production_patterns': dict(self.base_patterns.PRODUCTION_PATTERNS),
            'language_variants': dict(self.base_patterns.LANGUAGE_VARIANTS),
            'studio_patterns': dict(self.base_patterns.STUDIO_PATTERNS),
        }
        
        # Merge custom patterns if loaded
        if self.custom_patterns:
            # Add custom extensions
            if 'custom_extensions' in self.custom_patterns:
                for category, extensions in self.custom_patterns['custom_extensions'].items():
                    if category not in merged['file_extensions']:
                        merged['file_extensions'][category] = []
                    merged['file_extensions'][category].extend(extensions)
            
            # Add custom directories
            if 'custom_directories' in self.custom_patterns:
                for category, patterns in self.custom_patterns['custom_directories'].items():
                    if category not in merged['directory_patterns']:
                        merged['directory_patterns'][category] = []
                    merged['directory_patterns'][category].extend(patterns)
            
            # Add language patterns
            if 'language_patterns' in self.custom_patterns:
                merged['language_variants'].update(self.custom_patterns['language_patterns'])
            
            # Add studio workflows
            if 'studio_workflows' in self.custom_patterns:
                merged['studio_patterns'].update(self.custom_patterns['studio_workflows'])
        
        return merged
    
    def is_ignored(self, path: Path) -> bool:
        """Check if path should be ignored based on custom patterns"""
        if not self.custom_patterns or 'ignore_patterns' not in self.custom_patterns:
            return False
        
        ignore = self.custom_patterns['ignore_patterns']
        
        # Check directory ignores
        if path.is_dir() and 'directories' in ignore:
            for pattern in ignore['directories']:
                if pattern in str(path):
                    return True
        
        # Check file ignores
        if path.is_file() and 'files' in ignore:
            for pattern in ignore['files']:
                if path.match(pattern):
                    return True
        
        return False
    
    def get_categorization_rules(self) -> Dict[str, list]:
        """Get custom categorization rules"""
        if self.custom_patterns and 'categorization_rules' in self.custom_patterns:
            return self.custom_patterns['categorization_rules']
        return {}
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance settings from config"""
        defaults = {
            'max_scan_depth': 4,
            'skip_large_dirs': True,
            'parallel_scanning': True,
            'cache_discoveries': True
        }
        
        if self.custom_patterns and 'performance' in self.custom_patterns:
            defaults.update(self.custom_patterns['performance'])
        
        return defaults