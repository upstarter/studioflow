"""
StudioFlow Pattern Library - Comprehensive detection patterns for video production workflows
This module contains all naming patterns found in real-world video production environments.
"""

from typing import Dict, List, Set

class WorkflowPatterns:
    """Comprehensive pattern definitions for video production workflows"""
    
    # File extensions by category
    FILE_EXTENSIONS = {
        'project_files': {
            'davinci_resolve': ['.drp', '.dra', '.drb', '.drx', '.drt', '.drtimeline'],
            'premiere_pro': ['.prproj', '.prel', '.plproj', '.ppj'],
            'final_cut': ['.fcpxml', '.fcpbundle', '.fcpevent', '.fcpproject'],
            'avid': ['.avp', '.avb', '.ave', '.avs'],
            'after_effects': ['.aep', '.aepx', '.aet'],
            'nuke': ['.nk', '.nknc', '.nkple'],
            'fusion': ['.comp', '.setting', '.fu'],
        },
        'video_raw': {
            'red': ['.r3d', '.R3D'],
            'arri': ['.ari', '.arx', '.mxf'],
            'blackmagic': ['.braw', '.BRAW'],
            'sony': ['.sraw', '.x-ocn', '.mxf'],
            'canon': ['.crm', '.CRM', '.rmf', '.RMF'],
            'panasonic': ['.mxf', '.p2'],
        },
        'video_standard': [
            '.mov', '.mp4', '.avi', '.mkv', '.mxf', '.webm',
            '.MOV', '.MP4', '.AVI', '.MKV', '.MXF',
            '.m4v', '.mpg', '.mpeg', '.wmv', '.flv',
            '.f4v', '.vob', '.ogv', '.ogg', '.drc',
            '.gifv', '.mng', '.qt', '.yuv', '.rm',
            '.rmvb', '.asf', '.amv', '.m2v', '.svi',
            '.3gp', '.3g2', '.mpe', '.mpv', '.m2ts',
            '.mts', '.ts', '.divx', '.xvid', '.h264',
            '.h265', '.hevc', '.vp8', '.vp9', '.av1'
        ],
        'video_pro': [
            '.dpx', '.exr', '.cin', '.dnxhd', '.dnxhr',
            '.prores', '.cineform', '.dng', '.tiff', '.tif'
        ],
        'audio': [
            '.wav', '.aiff', '.aif', '.mp3', '.m4a',
            '.flac', '.ogg', '.wma', '.aac', '.ac3',
            '.dts', '.caf', '.bwf', '.amb', '.omf',
            '.aaf', '.mxf', '.stems'
        ],
        'image': [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.tiff', '.tif', '.psd', '.ai', '.svg',
            '.raw', '.cr2', '.nef', '.orf', '.sr2',
            '.dng', '.arw', '.rw2', '.raf', '.dcr'
        ],
        'subtitle': [
            '.srt', '.vtt', '.ass', '.ssa', '.sub',
            '.sbv', '.dfxp', '.ttml', '.itt', '.stl',
            '.scc', '.cap', '.smi', '.rt', '.txt'
        ],
        'lut': [
            '.cube', '.3dl', '.mga', '.m3d', '.csp',
            '.lut', '.itcp', '.look', '.cdl', '.cc',
            '.gcc', '.bdl', '.ctl', '.vf', '.vfz'
        ]
    }
    
    # Directory naming patterns (case-insensitive matching)
    DIRECTORY_PATTERNS = {
        'source_media': [
            # Common variations
            'footage', 'media', 'source', 'raw', 'original', 'originals',
            'dailies', 'rushes', 'selects', 'clips', 'video', 'videos',
            'assets', 'elements', 'material', 'materials', 'content',
            'capture', 'captured', 'import', 'imports', 'imported',
            'ingest', 'ingested', 'input', 'inputs', 'src', 'sources',
            
            # Camera/Card specific
            'card', 'cards', 'card_01', 'card_02', 'a_cam', 'b_cam',
            'a-cam', 'b-cam', 'cam_a', 'cam_b', 'camera', 'cameras',
            'cam1', 'cam2', 'cam_1', 'cam_2', 'multicam', 'multi-cam',
            'drone', 'aerial', 'gopro', 'action_cam', 'dslr', 'mirrorless',
            
            # Date-based
            'day1', 'day2', 'day_1', 'day_2', 'shoot_1', 'shoot_2',
            'd01', 'd02', 'monday', 'tuesday', 'wednesday', 'thursday',
            'friday', 'saturday', 'sunday', 'week1', 'week_1',
            
            # By type
            'interviews', 'interview', 'broll', 'b-roll', 'b_roll',
            'talking_heads', 'testimonials', 'vox_pops', 'voxpops',
            'standup', 'standups', 'establishing', 'exteriors',
            'interiors', 'aerials', 'timelapses', 'timelapse',
            'slowmo', 'slow_motion', 'highspeed', 'high_speed'
        ],
        
        'stock_library': [
            'stock', 'stocks', 'stock_footage', 'stockfootage',
            'library', 'libraries', 'archive', 'archives', 'vault',
            'collection', 'collections', 'bank', 'repository',
            'pool', 'shared', 'shared_assets', 'common', 'global',
            'company_assets', 'studio_assets', 'house_assets',
            'purchased', 'licensed', 'royalty_free', 'rf',
            'getty', 'shutterstock', 'pond5', 'artgrid', 'filmsupply',
            'storyblocks', 'videoblocks', 'audioblocks', 'envato'
        ],
        
        'audio': [
            'audio', 'sound', 'sounds', 'music', 'sfx', 'fx',
            'effects', 'sound_effects', 'soundfx', 'foley',
            'dialogue', 'dialog', 'vo', 'voiceover', 'voice_over',
            'narration', 'commentary', 'adr', 'mix', 'mixes',
            'stems', 'tracks', 'score', 'soundtrack', 'ambience',
            'atmosphere', 'atmos', 'roomtone', 'room_tone',
            'wildtrack', 'wild_track', 'sync', 'scratch'
        ],
        
        'graphics': [
            'graphics', 'gfx', 'motion', 'motion_graphics', 'mograph',
            'animation', 'animations', 'animated', '2d', '3d',
            'cg', 'cgi', 'vfx', 'visual_effects', 'fx', 'effects',
            'titles', 'title', 'lower_thirds', 'lowerthirds', 'l3',
            'supers', 'captions', 'text', 'overlays', 'bugs',
            'logo', 'logos', 'branding', 'brand', 'identity',
            'transitions', 'stingers', 'bumpers', 'packshot',
            'endframe', 'end_frame', 'endboard', 'end_board',
            'slate', 'slates', 'credits', 'roller', 'crawl'
        ],
        
        'color': [
            'color', 'colour', 'grade', 'grades', 'grading',
            'cc', 'color_correction', 'colorcorrection',
            'lut', 'luts', 'looks', 'cdl', 'dpx', 'baselight',
            'resolve', 'lustre', 'nucoda', 'mistika', 'scratch'
        ],
        
        'edit': [
            'edit', 'edits', 'editing', 'cut', 'cuts', 'timeline',
            'timelines', 'sequence', 'sequences', 'seq', 'assembly',
            'rough', 'rough_cut', 'roughcut', 'fine', 'fine_cut',
            'finecut', 'locked', 'lock', 'picture_lock', 'final',
            'master', 'conform', 'conformed', 'online', 'offline',
            'stringout', 'string_out', 'selects', 'select', 'pulls'
        ],
        
        'output': [
            'output', 'outputs', 'export', 'exports', 'render',
            'renders', 'rendering', 'transcode', 'transcodes',
            'encode', 'encodes', 'delivery', 'deliveries',
            'deliverable', 'deliverables', 'final', 'finals',
            'master', 'masters', 'release', 'publish', 'published',
            'distribution', 'dist', 'broadcast', 'air', 'tx',
            'web', 'online', 'social', 'youtube', 'vimeo',
            'instagram', 'facebook', 'tiktok', 'twitter'
        ],
        
        'project': [
            'project', 'projects', 'prj', 'work', 'working',
            'wip', 'current', 'active', 'in_progress', 'inprogress',
            'ongoing', 'development', 'dev', 'production', 'prod',
            'post', 'postproduction', 'post-production', 'finishing'
        ],
        
        'documents': [
            'documents', 'docs', 'documentation', 'paperwork',
            'scripts', 'script', 'screenplay', 'treatment',
            'storyboard', 'storyboards', 'boards', 'shotlist',
            'shot_list', 'breakdown', 'schedule', 'callsheet',
            'call_sheet', 'contracts', 'releases', 'agreements',
            'notes', 'feedback', 'review', 'reviews', 'comments',
            'reports', 'logs', 'continuity', 'lined_script'
        ],
        
        'temp': [
            'temp', 'tmp', 'temporary', 'cache', 'cached',
            'preview', 'previews', 'waveforms', 'peaks',
            'analysis', 'optimized', 'optimizedmedia',
            'proxies', 'proxy', 'transcoded', 'converted',
            'scratch', 'working', 'render_cache', 'rendercache'
        ],
        
        'backup': [
            'backup', 'backups', 'bak', 'bkp', 'archive',
            'archives', 'old', 'previous', 'legacy', 'historical',
            'snapshot', 'snapshots', 'safety', 'redundant',
            'mirror', 'copy', 'copies', 'duplicate', 'duplicates'
        ],
        
        'client': [
            'client', 'clients', 'customer', 'customers',
            'agency', 'agencies', 'brand', 'brands', 'sponsor',
            'advertiser', 'partner', 'vendor', 'supplier'
        ]
    }
    
    # Production-specific naming conventions
    PRODUCTION_PATTERNS = {
        'broadcast': [
            'act1', 'act2', 'act3', 'act_1', 'act_2',
            'segment', 'seg', 'block', 'part', 'chapter',
            'episode', 'ep', 'season', 's01e01', 'pilot',
            'teaser', 'cold_open', 'tag', 'commercial',
            'promo', 'trailer', 'sizzle', 'recap'
        ],
        'film': [
            'reel', 'reel1', 'reel_1', 'scene', 'sc',
            'shot', 'take', 'tk', 'pickup', 'pickups',
            'insert', 'inserts', 'cutaway', 'reaction',
            'establishing', 'wide', 'medium', 'closeup',
            'ecu', 'pov', 'ots', 'two-shot', 'single'
        ],
        'commercial': [
            'spot', 'tvc', 'commercial', 'ad', 'campaign',
            'version', 'v1', 'v2', 'alt', 'alternate',
            'director_cut', 'agency_cut', 'client_cut',
            '15s', '30s', '60s', 'cutdown', 'lift',
            'packshot', 'endframe', 'supers', 'legals'
        ],
        'corporate': [
            'presentation', 'pitch', 'demo', 'explainer',
            'testimonial', 'case_study', 'training',
            'webinar', 'conference', 'keynote', 'internal',
            'external', 'stakeholder', 'investor', 'hr'
        ],
        'social': [
            'story', 'stories', 'reel', 'reels', 'post',
            'vertical', 'horizontal', 'square', '9x16',
            '16x9', '1x1', '4x5', 'igtv', 'live', 'stream'
        ]
    }
    
    # Language variations
    LANGUAGE_VARIANTS = {
        'spanish': {
            'footage': ['metraje', 'material', 'grabacion'],
            'audio': ['sonido', 'musica', 'efectos'],
            'edit': ['edicion', 'montaje', 'corte'],
            'color': ['color', 'etalonaje', 'correccion'],
            'output': ['salida', 'exportar', 'entrega']
        },
        'french': {
            'footage': ['rushes', 'images', 'plans'],
            'audio': ['son', 'musique', 'effets'],
            'edit': ['montage', 'coupe', 'edition'],
            'color': ['etalonnage', 'colorimetrie'],
            'output': ['sortie', 'export', 'livraison']
        },
        'german': {
            'footage': ['material', 'aufnahmen', 'filmmaterial'],
            'audio': ['ton', 'musik', 'effekte'],
            'edit': ['schnitt', 'montage', 'bearbeitung'],
            'color': ['farbkorrektur', 'grading'],
            'output': ['ausgabe', 'export', 'lieferung']
        },
        'japanese': {
            'footage': ['素材', 'そざい', 'footage'],
            'audio': ['音声', 'おんせい', 'audio'],
            'edit': ['編集', 'へんしゅう', 'edit'],
            'color': ['カラー', 'カラコレ', 'color'],
            'output': ['出力', 'しゅつりょく', 'output']
        }
    }
    
    # Common production company/studio conventions
    STUDIO_PATTERNS = {
        'prefix_formats': [
            'YYYY_MM_DD_*',  # 2024_03_15_ProjectName
            'YYMMDD_*',      # 240315_ProjectName
            'CLIENT_*',      # NIKE_SpringCampaign
            'JOB####_*',     # JOB1234_ProjectName
            'PRJ_*',         # PRJ_SuperBowl
            'PROD_*'         # PROD_2024_Documentary
        ],
        'versioning': [
            '_v#', '_v##', '_v###',  # _v1, _v01, _v001
            '_r#', '_r##',            # _r1, _r01 (revision)
            '_FINAL', '_FINAL_FINAL', '_FINAL_FINAL_FINAL',
            '_LOCKED', '_APPROVED', '_MASTER',
            '_WIP', '_ROUGH', '_TEMP',
            '_ALT', '_OPTION', '_VARIANT',
            '_AMEND', '_REVISED', '_UPDATED'
        ]
    }
    
    @classmethod
    def get_all_video_extensions(cls) -> Set[str]:
        """Get all video file extensions"""
        extensions = set()
        for ext_list in cls.FILE_EXTENSIONS['video_raw'].values():
            extensions.update(ext_list)
        extensions.update(cls.FILE_EXTENSIONS['video_standard'])
        extensions.update(cls.FILE_EXTENSIONS['video_pro'])
        return extensions
    
    @classmethod
    def get_project_file_extensions(cls) -> Dict[str, List[str]]:
        """Get project file extensions by application"""
        return cls.FILE_EXTENSIONS['project_files']
    
    @classmethod
    def is_source_media_directory(cls, dir_name: str) -> bool:
        """Check if directory name suggests source media"""
        dir_lower = dir_name.lower()
        return any(pattern in dir_lower for pattern in cls.DIRECTORY_PATTERNS['source_media'])
    
    @classmethod
    def is_stock_directory(cls, dir_name: str) -> bool:
        """Check if directory name suggests stock footage"""
        dir_lower = dir_name.lower()
        return any(pattern in dir_lower for pattern in cls.DIRECTORY_PATTERNS['stock_library'])
    
    @classmethod
    def detect_workflow_type(cls, path) -> str:
        """Detect the workflow type based on file patterns"""
        from pathlib import Path
        path = Path(path)
        
        # Check for project files
        for app_name, extensions in cls.FILE_EXTENSIONS['project_files'].items():
            for ext in extensions:
                if list(path.rglob(f'*{ext}')):
                    return app_name
        
        # Check for camera formats
        for camera, extensions in cls.FILE_EXTENSIONS['video_raw'].items():
            for ext in extensions:
                if list(path.rglob(f'*{ext}')):
                    return f'{camera}_workflow'
        
        return 'generic_video'
    
    @classmethod
    def categorize_directory(cls, dir_name: str) -> List[str]:
        """Categorize a directory based on its name"""
        categories = []
        dir_lower = dir_name.lower()
        
        for category, patterns in cls.DIRECTORY_PATTERNS.items():
            if any(pattern in dir_lower for pattern in patterns):
                categories.append(category)
        
        return categories if categories else ['uncategorized']