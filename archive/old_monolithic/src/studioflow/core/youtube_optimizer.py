"""
YouTube Workflow Optimizer - Smart template configuration for creators
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from datetime import datetime

class YouTubeOptimizer:
    """Optimizes YouTube project structure based on creator needs"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.workflow_type = self.config.get('workflow', {}).get('type', 'standard')
    
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load user's YouTube configuration"""
        if not config_path:
            # Check default locations
            user_config = Path.home() / '.studioflow' / 'youtube-config.yml'
            if user_config.exists():
                config_path = user_config
        
        if config_path and config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        
        # Return sensible defaults
        return self._get_defaults()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Default YouTube creator configuration"""
        return {
            'workflow': {
                'type': 'standard',
                'complexity': 'standard'
            },
            'directories': {
                'core': [
                    'footage',
                    'audio', 
                    'graphics',
                    'exports'
                ]
            },
            'platforms': {
                'youtube': True,
                'shorts': True
            }
        }
    
    def build_structure(self, project_name: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Build optimized directory structure"""
        
        structure = {
            'directories': [],
            'files': []
        }
        
        # Start with core directories
        core_dirs = self.config.get('directories', {}).get('core', [])
        
        # Apply user's naming preferences
        naming = self.config.get('naming', {})
        for dir_name in core_dirs:
            # Apply custom names if defined
            if dir_name in naming:
                dir_name = naming[dir_name]
            structure['directories'].append(dir_name)
        
        # Add platform-specific exports
        platforms = self.config.get('platforms', {})
        exports = self.config.get('exports', {})
        
        if platforms.get('youtube'):
            structure['directories'].append(f"{naming.get('exports', 'exports')}/youtube")
            if exports.get('youtube', {}).get('resolution') == '3840x2160':
                structure['directories'].append(f"{naming.get('exports', 'exports')}/youtube/4k")
                structure['directories'].append(f"{naming.get('exports', 'exports')}/youtube/1080p")
        
        if platforms.get('shorts'):
            structure['directories'].append(f"{naming.get('exports', 'exports')}/shorts")
        
        if platforms.get('instagram'):
            structure['directories'].append(f"{naming.get('exports', 'exports')}/instagram")
        
        # Add optional features based on flags
        if options.get('add'):
            optional = self.config.get('directories', {}).get('optional', {})
            for feature in options['add']:
                if feature in optional:
                    for dir_path in optional[feature]:
                        structure['directories'].append(dir_path)
        
        # Add workflow-specific directories
        if self.workflow_type in ['tutorial', 'review']:
            structure['directories'].extend([
                f"{naming.get('footage', 'footage')}/screen-capture",
                f"{naming.get('graphics', 'graphics')}/annotations"
            ])
        elif self.workflow_type == 'vlog':
            structure['directories'].extend([
                f"{naming.get('footage', 'footage')}/b-roll",
                f"{naming.get('footage', 'footage')}/drone"
            ])
        
        # Add auto-generated files
        structure['files'] = self._generate_files(project_name)
        
        # Apply smart organization rules
        if self.config.get('organize', {}).get('rules'):
            structure['organize_rules'] = self.config['organize']['rules']
        
        return structure
    
    def _generate_files(self, project_name: str) -> List[Dict[str, str]]:
        """Generate workflow-specific files"""
        files = []
        
        # Add user's auto-files
        for file_spec in self.config.get('auto_files', []):
            content = file_spec['content'].replace('{project_name}', project_name)
            content = content.replace('{date}', datetime.now().strftime('%Y-%m-%d'))
            files.append({
                'path': file_spec['name'],
                'content': content
            })
        
        # Add workflow-specific files
        if self.workflow_type == 'tutorial':
            files.append({
                'path': 'tutorial-outline.md',
                'content': self._tutorial_template(project_name)
            })
        elif self.workflow_type == 'review':
            files.append({
                'path': 'review-checklist.md',
                'content': self._review_template(project_name)
            })
        
        # Add export settings file
        if self.config.get('exports'):
            files.append({
                'path': '.export-settings.yml',
                'content': yaml.dump(self.config['exports'], default_flow_style=False)
            })
        
        return files
    
    def _tutorial_template(self, project_name: str) -> str:
        """Tutorial-specific template"""
        return f"""# Tutorial: {project_name}

## Learning Objectives
1. 
2. 
3. 

## Prerequisites
- 

## Steps
1. Introduction (0:00-0:30)
   - Hook
   - What we'll learn
   
2. Setup (0:30-2:00)
   - Required tools
   - Initial configuration
   
3. Main Content
   - Step 1: 
   - Step 2: 
   - Step 3: 
   
4. Conclusion
   - Recap
   - Next steps
   - CTA

## Resources
- Code: github.com/...
- Written guide: blog.com/...
"""
    
    def _review_template(self, project_name: str) -> str:
        """Review-specific template"""
        return f"""# Review: {project_name}

## Product Details
- Name: 
- Price: 
- Category: 
- Purchase date: 
- Testing period: 

## Review Sections
- [ ] Unboxing
- [ ] First impressions
- [ ] Build quality
- [ ] Features walkthrough
- [ ] Performance tests
- [ ] Comparisons
- [ ] Pros & Cons
- [ ] Final verdict

## B-Roll Checklist
- [ ] Product shots (multiple angles)
- [ ] Close-ups of details
- [ ] Size comparisons
- [ ] In-use footage
- [ ] Packaging shots

## Talking Points
### Pros
1. 

### Cons
1. 

### Who it's for


### Alternatives


## Affiliate Links
- Amazon: 
- Direct: 
"""
    
    def optimize_for_platform(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific optimization settings"""
        
        platform_specs = {
            'youtube': {
                'resolution': '1920x1080',
                'fps': 30,
                'codec': 'h264',
                'bitrate': '12M',
                'audio': '-14 LUFS',
                'format': 'mp4'
            },
            'shorts': {
                'resolution': '1080x1920',
                'fps': 30,
                'codec': 'h264',
                'bitrate': '15M',
                'audio': '-14 LUFS',
                'format': 'mp4',
                'max_duration': 60
            },
            'instagram': {
                'resolution': '1080x1920',
                'fps': 30,
                'codec': 'h264',
                'bitrate': '20M',
                'audio': '-14 LUFS',
                'format': 'mp4',
                'max_duration': 90
            },
            'tiktok': {
                'resolution': '1080x1920',
                'fps': 30,
                'codec': 'h264',
                'bitrate': '15M',
                'audio': '-16 LUFS',
                'format': 'mp4',
                'max_duration': 180
            }
        }
        
        # Override with user preferences if they exist
        user_export = self.config.get('exports', {}).get(platform)
        if user_export:
            platform_specs[platform].update(user_export)
        
        return platform_specs.get(platform, platform_specs['youtube'])
    
    def suggest_improvements(self, project_path: Path) -> List[str]:
        """Analyze project and suggest workflow improvements"""
        suggestions = []
        
        # Check for common issues
        footage_dir = project_path / self.config.get('naming', {}).get('footage', 'footage')
        if footage_dir.exists():
            footage_files = list(footage_dir.glob('*'))
            
            # Check for organization
            if len(footage_files) > 10:
                has_subdirs = any(f.is_dir() for f in footage_files)
                if not has_subdirs:
                    suggestions.append(
                        "Consider organizing footage into subdirectories "
                        "(a-roll, b-roll, screen-capture) for easier navigation"
                    )
            
            # Check for common file patterns
            screen_files = [f for f in footage_files if 'screen' in f.name.lower()]
            if screen_files and not (footage_dir / 'screen-capture').exists():
                suggestions.append(
                    "Detected screen recordings. Consider moving to 'footage/screen-capture'"
                )
        
        # Check exports
        exports_dir = project_path / self.config.get('naming', {}).get('exports', 'exports')
        if exports_dir.exists():
            youtube_dir = exports_dir / 'youtube'
            if youtube_dir.exists():
                exports = list(youtube_dir.glob('*.mp4'))
                if len(exports) > 3:
                    suggestions.append(
                        "Multiple exports detected. Consider versioning (v1, v2, v3) "
                        "or dating exports for better tracking"
                    )
        
        # Check for thumbnail variations
        graphics_dir = project_path / self.config.get('naming', {}).get('graphics', 'graphics')
        if graphics_dir.exists():
            thumbnails = list(graphics_dir.glob('*thumb*'))
            if len(thumbnails) == 1:
                suggestions.append(
                    "Consider creating A/B test thumbnail variations "
                    "to optimize click-through rate"
                )
        
        return suggestions