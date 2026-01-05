"""
Input validators and sanitizers for StudioFlow
"""

import re
import os
from pathlib import Path
from typing import Optional, Tuple

class ProjectValidator:
    """Validates and sanitizes project inputs"""
    
    # Invalid characters for project names
    INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
    
    # Reserved names on various systems
    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
        'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
        'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
        '.', '..', 'lost+found'
    }
    
    # Maximum path lengths for different systems
    MAX_PATH_LENGTH = {
        'windows': 260,
        'macos': 1024,
        'linux': 4096
    }
    
    @classmethod
    def validate_project_name(cls, name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate project name for filesystem compatibility
        Returns: (is_valid, error_message)
        """
        if not name or name.strip() == '':
            return False, "Project name cannot be empty"
        
        # Check length
        if len(name) > 255:
            return False, "Project name too long (max 255 characters)"
        
        if len(name) < 2:
            return False, "Project name too short (min 2 characters)"
        
        # Check for invalid characters
        if re.search(cls.INVALID_CHARS, name):
            return False, f"Project name contains invalid characters"
        
        # Check for reserved names
        if name.upper() in cls.RESERVED_NAMES:
            return False, f"'{name}' is a reserved system name"
        
        # Check for leading/trailing spaces or dots
        if name != name.strip():
            return False, "Project name cannot have leading or trailing spaces"
        
        if name.startswith('.') or name.endswith('.'):
            return False, "Project name cannot start or end with a dot"
        
        # Check for only dots or spaces
        if set(name) <= {'.', ' '}:
            return False, "Project name cannot consist only of dots and spaces"
        
        return True, None
    
    @classmethod
    def sanitize_project_name(cls, name: str) -> str:
        """
        Sanitize project name to make it filesystem-safe
        """
        # Remove invalid characters
        sanitized = re.sub(cls.INVALID_CHARS, '_', name)
        
        # Replace multiple underscores with single
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        
        # Replace spaces with underscores (optional, but cleaner)
        sanitized = sanitized.replace(' ', '_')
        
        # Ensure it's not a reserved name
        if sanitized.upper() in cls.RESERVED_NAMES:
            sanitized = f"{sanitized}_project"
        
        # Ensure minimum length
        if len(sanitized) < 2:
            sanitized = f"project_{sanitized}"
        
        # Truncate if too long
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized
    
    @classmethod
    def validate_path(cls, path: Path, must_exist: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate a filesystem path
        """
        try:
            path = Path(path).resolve()
            
            # Check if path exists when required
            if must_exist and not path.exists():
                return False, f"Path does not exist: {path}"
            
            # Check if we have write permissions
            if must_exist:
                test_file = path / '.studioflow_test'
                try:
                    test_file.touch()
                    test_file.unlink()
                except PermissionError:
                    return False, f"No write permission for: {path}"
                except Exception as e:
                    return False, f"Cannot write to path: {str(e)}"
            
            # Check path length
            if len(str(path)) > cls.MAX_PATH_LENGTH.get('linux', 4096):
                return False, "Path is too long"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid path: {str(e)}"
    
    @classmethod
    def validate_template(cls, template: str, available_templates: list) -> Tuple[bool, Optional[str]]:
        """
        Validate template name
        """
        if template not in available_templates:
            return False, f"Unknown template '{template}'. Available: {', '.join(available_templates)}"
        return True, None
    
    @classmethod
    def check_disk_space(cls, path: Path, required_mb: int = 100) -> Tuple[bool, Optional[str]]:
        """
        Check if there's enough disk space
        """
        try:
            import shutil
            stat = shutil.disk_usage(path)
            free_mb = stat.free / (1024 * 1024)
            
            if free_mb < required_mb:
                return False, f"Insufficient disk space. Need {required_mb}MB, have {free_mb:.1f}MB"
            
            return True, None
        except Exception as e:
            return False, f"Cannot check disk space: {str(e)}"
    
    @classmethod
    def validate_git_available(cls) -> Tuple[bool, Optional[str]]:
        """
        Check if git is available
        """
        try:
            import subprocess
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=5)
            if result.returncode != 0:
                return False, "Git is not properly installed"
            return True, None
        except FileNotFoundError:
            return False, "Git is not installed"
        except Exception as e:
            return False, f"Cannot check git: {str(e)}"
    
    @classmethod
    def validate_network_path(cls, path: Path) -> Tuple[bool, Optional[str]]:
        """
        Check if path is on network storage and warn about potential issues
        """
        path_str = str(path)
        
        network_indicators = [
            '/mnt/nas', '/Volumes/', '\\\\', 'smb://', 
            'nfs://', 'afp://', '/media/', '/net/'
        ]
        
        warnings = []
        for indicator in network_indicators:
            if indicator in path_str:
                warnings.append(f"Network path detected. Performance may be affected.")
                
                # Check if network path is accessible
                try:
                    if not path.exists():
                        return False, "Network path is not accessible"
                except Exception:
                    return False, "Cannot access network path"
                
                break
        
        if warnings:
            return True, warnings[0]  # Return as warning, not error
        
        return True, None