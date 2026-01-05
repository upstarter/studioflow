"""
Template Engine - Processes user and built-in templates
"""

import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from .youtube_optimizer import YouTubeOptimizer

class TemplateEngine:
    """Process and apply templates with variable substitution"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.builtin_templates = self._load_builtin_templates()
        self.youtube_optimizer = None  # Lazy load when needed
    
    def _load_builtin_templates(self) -> Dict[str, Dict]:
        """Load built-in templates that ship with StudioFlow"""
        return {
            'minimal': {
                'name': 'Minimal',
                'description': 'Just the essentials',
                'directories': ['footage', 'exports'],
                'files': [
                    {'path': 'project.drp', 'content': ''}
                ]
            },
            
            'youtube': {
                'name': 'YouTube',
                'description': 'Optimized for YouTube creators',
                'directories': [
                    'footage',
                    'audio',
                    'graphics',
                    'exports/youtube',
                    'exports/shorts',
                    'exports/thumbnail'
                ],
                'files': [
                    {'path': 'project.drp', 'content': ''},
                    {'path': 'metadata.yml', 'content': self._youtube_metadata_template()},
                    {'path': 'description.md', 'content': self._youtube_description_template()}
                ]
            },
            
            'client': {
                'name': 'Client Project',
                'description': 'Professional client work',
                'directories': [
                    'footage/raw',
                    'footage/selects',
                    'audio',
                    'graphics',
                    'exports/drafts',
                    'exports/review',
                    'exports/final',
                    'feedback',
                    'documents'
                ],
                'files': [
                    {'path': 'project.drp', 'content': ''},
                    {'path': 'README.md', 'content': self._client_readme_template()},
                    {'path': 'feedback/notes.md', 'content': '# Client Feedback\n\n## Round 1\n- [ ] '}
                ]
            },
            
            'flexible': {
                'name': 'Flexible',
                'description': 'Adapts to your needs',
                'directories': ['footage', 'exports'],
                'files': [{'path': 'project.drp', 'content': ''}],
                'options': {
                    'audio': ['audio'],
                    'graphics': ['graphics'],
                    'vfx': ['vfx'],
                    'color': ['color/luts', 'color/grades'],
                    'cache': ['cache'],
                    'documents': ['documents/scripts', 'documents/notes']
                }
            }
        }
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get template by name - checks user templates first, then built-in"""
        
        # 1. Check user templates
        user_template = self.config.get_user_template(name)
        if user_template:
            return user_template
        
        # 2. Check built-in templates
        if name in self.builtin_templates:
            return self.builtin_templates[name]
        
        # 3. Check if it's a path to a template file
        if Path(name).exists():
            with open(name) as f:
                return yaml.safe_load(f)
        
        return None
    
    def apply_template(self, template: Dict[str, Any], project_name: str, 
                      base_path: Path, options: Dict[str, Any] = None) -> Path:
        """Apply a template to create project structure"""
        
        project_path = base_path / self._format_name(project_name)
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Get variable substitutions
        variables = self._get_variables(project_name, options)
        
        # Check if this is a YouTube template and user has custom config
        template_name = template.get('template_name', options.get('template_name', ''))
        if 'youtube' in template_name.lower():
            # Use YouTube optimizer for smart configuration
            if not self.youtube_optimizer:
                self.youtube_optimizer = YouTubeOptimizer()
            
            # Build optimized structure
            optimized = self.youtube_optimizer.build_structure(project_name, options or {})
            dirs = optimized['directories']
            files = optimized.get('files', template.get('files', []))
            
            # Apply user's custom directory names if configured
            dir_config = self.config.config.get('structure', {}).get('dirs', {})
            dirs = self._apply_custom_names(dirs, dir_config)
        else:
            # Standard template processing
            dirs = template.get('directories', [])
            files = template.get('files', [])
            
            # Apply user's custom directory names if configured
            dir_config = self.config.config.get('structure', {}).get('dirs', {})
            dirs = self._apply_custom_names(dirs, dir_config)
            
            # Add optional directories based on options
            if options and 'add' in options:
                for option in options['add']:
                    if option in template.get('options', {}):
                        for opt_dir in template['options'][option]:
                            dirs.append(opt_dir)
        
        # Create directories
        for dir_name in dirs:
            dir_path = project_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create files with variable substitution
        for file_spec in files:
            file_path = project_path / file_spec['path']
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = file_spec.get('content', '')
            # Substitute variables
            for key, value in variables.items():
                content = content.replace(f'{{{key}}}', str(value))
            
            file_path.write_text(content)
        
        return project_path
    
    def _format_name(self, name: str) -> str:
        """Format project name according to user preferences"""
        naming = self.config.config.get('naming', {})
        style = naming.get('style', 'kebab')
        
        # Clean the name
        name = name.strip()
        
        # Apply naming style
        if style == 'kebab':
            name = name.lower().replace(' ', '-').replace('_', '-')
        elif style == 'snake':
            name = name.lower().replace(' ', '_').replace('-', '_')
        elif style == 'PascalCase':
            name = ''.join(word.capitalize() for word in name.split())
        elif style == 'camelCase':
            words = name.split()
            name = words[0].lower() + ''.join(w.capitalize() for w in words[1:])
        
        # Add date if configured
        if naming.get('include_date', False):
            date_format = naming.get('date_format', '%Y-%m-%d')
            date_str = datetime.now().strftime(date_format)
            separator = naming.get('separator', '-')
            name = f"{date_str}{separator}{name}"
        
        return name
    
    def _apply_custom_names(self, dirs: List[str], custom_config: Dict[str, str]) -> List[str]:
        """Apply user's custom directory names"""
        result = []
        for dir_name in dirs:
            # Check if this is a base directory that user has renamed
            base_name = dir_name.split('/')[0]
            if base_name in custom_config:
                # Replace with user's preferred name
                dir_name = dir_name.replace(base_name, custom_config[base_name], 1)
            result.append(dir_name)
        return result
    
    def _get_variables(self, project_name: str, options: Dict[str, Any] = None) -> Dict[str, str]:
        """Get variables for template substitution"""
        return {
            'project_name': project_name,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'year': datetime.now().strftime('%Y'),
            'user': os.environ.get('USER', 'creator'),
            'platform': options.get('platform', 'generic') if options else 'generic',
            'client': options.get('client', 'Client') if options else 'Client'
        }
    
    def _youtube_metadata_template(self) -> str:
        return """# YouTube Metadata
project: {project_name}
created: {date}

video:
  title: ""
  description: |
    
  tags:
    - 
  
thumbnail:
  title: ""
  subtitle: ""
  
settings:
  visibility: unlisted  # public, unlisted, private
  category: Education
  language: en
  
analytics:
  target_audience: ""
  target_duration: "10-15 min"
  publish_time: "Tuesday 9am"
"""

    def _youtube_description_template(self) -> str:
        return """# {project_name}

## Description


## Timestamps
00:00 Introduction


## Links


## Tags
#
"""

    def _client_readme_template(self) -> str:
        return """# {project_name}

**Client:** {client}  
**Created:** {date}  
**Status:** In Progress

## Project Brief


## Deliverables
- [ ] 
- [ ] 

## Timeline
- First Draft: 
- Review: 
- Final Delivery: 

## Notes

"""