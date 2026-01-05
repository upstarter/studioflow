#!/usr/bin/env python3
"""Fix the broken config.yaml file"""

from pathlib import Path
import yaml

# Create a proper config with string paths
config = {
    'user_name': 'eric',
    'notifications': True,
    'theme': 'auto',
    'storage': {
        'ingest': '/home/eric/Videos/StudioFlow/Ingest',
        'active': '/home/eric/Videos/StudioFlow/Projects',
        'render': '/home/eric/Videos/StudioFlow/Render',
        'archive': '/home/eric/Videos/StudioFlow/Archive',
        'library': None,
        'nas': None
    },
    'resolve': {
        'install_path': '/opt/resolve',
        'api_path': '/opt/resolve/Developer/Scripting',
        'enabled': True,
        'default_framerate': 29.97,
        'default_resolution': '3840x2160',
        'color_space': 'Rec.709'
    },
    'project': {
        'default_template': 'youtube',
        'folder_structure': [
            '01_MEDIA',
            '02_AUDIO',
            '03_GRAPHICS',
            '04_PROJECTS',
            '05_RENDERS',
            '.studioflow'
        ],
        'naming_pattern': '{date}_{name}_{type}',
        'auto_categorize': True
    },
    'media': {
        'extensions': ['.mp4', '.mov', '.avi', '.mkv', '.mxf'],
        'image_extensions': ['.jpg', '.png', '.tiff', '.bmp'],
        'audio_extensions': ['.wav', '.mp3', '.aac', '.m4a'],
        'test_clip_max': 3,
        'b_roll_min': 10,
        'b_roll_max': 30,
        'a_roll_min': 60,
        'verify_checksums': True,
        'skip_duplicates': True,
        'parallel_copy': True,
        'preserve_structure': False
    },
    'youtube': {
        'upload_defaults': {
            'privacy': 'private',
            'category': '28',
            'language': 'en',
            'embeddable': True,
            'publicStatsViewable': True
        },
        'thumbnail_template': None,
        'description_template': None,
        'tags_template': [],
        'optimal_length_minutes': 10,
        'schedule_time': '14:00',
        'schedule_days': ['tuesday', 'thursday']
    },
    'log_level': 'INFO',
    'telemetry': False,
    'auto_update': True,
    'plugins_enabled': []
}

# Save the fixed config
config_file = Path.home() / '.studioflow' / 'config.yaml'
config_file.parent.mkdir(exist_ok=True)

with open(config_file, 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

print(f"✅ Fixed config file: {config_file}")
print("\nConfig is now properly formatted with string paths instead of Path objects.")