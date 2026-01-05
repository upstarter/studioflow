"""
Validators for StudioFlow - Ensure project creation is safe and valid
"""

import re
import os
from pathlib import Path
from typing import Optional, Tuple

class ProjectValidator:
    """Validate project creation parameters"""
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, Optional[str]]:
        """Validate project name"""
        
        # Check for empty name
        if not name or not name.strip():
            return False, "Project name cannot be empty"
        
        # Check length
        if len(name) > 255:
            return False, "Project name too long (max 255 characters)"
        
        # Check for invalid characters
        invalid_chars = r'[<>:"|?*\\]' if os.name == 'nt' else r'[<>:"|?*]'
        if re.search(invalid_chars, name):
            return False, f"Project name contains invalid characters: {invalid_chars}"
        
        # Check for reserved names (Windows)
        if os.name == 'nt':
            reserved = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                       'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                       'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
            if name.upper() in reserved:
                return False, f"'{name}' is a reserved name on Windows"
        
        return True, None
    
    @staticmethod
    def validate_path(path: Path) -> Tuple[bool, Optional[str]]:
        """Validate project path"""
        
        # Check if parent exists
        if not path.parent.exists():
            return False, f"Parent directory does not exist: {path.parent}"
        
        # Check if we have write permissions
        if not os.access(path.parent, os.W_OK):
            return False, f"No write permission for: {path.parent}"
        
        # Check if path already exists
        if path.exists():
            # Check if it's empty
            if path.is_dir() and any(path.iterdir()):
                return False, f"Directory already exists and is not empty: {path}"
        
        # Check available space (require at least 100MB)
        try:
            stat = os.statvfs(path.parent)
            free_space = stat.f_bavail * stat.f_frsize
            if free_space < 100 * 1024 * 1024:  # 100MB
                return False, f"Insufficient disk space (less than 100MB available)"
        except:
            # Can't check space, proceed anyway
            pass
        
        return True, None
    
    @staticmethod
    def validate_template(template: str, available_templates: list) -> Tuple[bool, Optional[str]]:
        """Validate template name"""
        
        if not template:
            return False, "Template name cannot be empty"
        
        # Check if template exists
        if template not in available_templates:
            similar = ProjectValidator._find_similar_template(template, available_templates)
            if similar:
                return False, f"Template '{template}' not found. Did you mean '{similar}'?"
            else:
                return False, f"Template '{template}' not found. Available: {', '.join(available_templates)}"
        
        return True, None
    
    @staticmethod
    def _find_similar_template(name: str, templates: list) -> Optional[str]:
        """Find similar template name for suggestions"""
        name_lower = name.lower()
        for template in templates:
            if name_lower in template.lower() or template.lower() in name_lower:
                return template
        return None
    
    @staticmethod
    def validate_additions(additions: list, available_options: dict) -> Tuple[bool, Optional[str]]:
        """Validate addition options"""
        
        if not additions:
            return True, None
        
        invalid = []
        for add in additions:
            if add not in available_options:
                invalid.append(add)
        
        if invalid:
            return False, f"Invalid additions: {', '.join(invalid)}. Available: {', '.join(available_options.keys())}"
        
        return True, None
    
    @staticmethod
    def validate_all(name: str, path: Path, template: str, 
                    available_templates: list, additions: list = None,
                    available_options: dict = None) -> Tuple[bool, Optional[str]]:
        """Validate all parameters at once"""
        
        # Validate name
        valid, error = ProjectValidator.validate_name(name)
        if not valid:
            return False, error
        
        # Validate path
        valid, error = ProjectValidator.validate_path(path)
        if not valid:
            return False, error
        
        # Validate template
        valid, error = ProjectValidator.validate_template(template, available_templates)
        if not valid:
            return False, error
        
        # Validate additions if provided
        if additions and available_options:
            valid, error = ProjectValidator.validate_additions(additions, available_options)
            if not valid:
                return False, error
        
        return True, None