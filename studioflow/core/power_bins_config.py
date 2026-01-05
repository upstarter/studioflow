"""
Power Bins Configuration
Optimal structure for stock footage library (configurable via config system)
"""

from pathlib import Path
from typing import Dict, List, Optional

from studioflow.core.config import get_config


class PowerBinsConfig:
    """Optimal Power Bins structure for stock footage library (optional feature)"""
    
    @classmethod
    def get_base_path(cls) -> Optional[Path]:
        """Get base media path from config (NAS or local library)
        
        Returns:
            Path if configured, None if Power Bins not available
        """
        config = get_config()
        
        # Try NAS first (if configured)
        if config.storage.nas:
            nas_media = config.storage.nas / "Media"
            if nas_media.exists():
                return nas_media
        
        # Fallback to local library/assets if available
        if config.storage.library:
            library_assets = config.storage.library / "Assets"
            if library_assets.exists():
                return library_assets
        
        # Last resort: try NAS path from config if available
        if config.storage.nas:
            nas_media = config.storage.nas / "Media"
            if nas_media.exists():
                return nas_media
        
        # Not configured/available
        return None
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if Power Bins is configured and available"""
        return cls.get_base_path() is not None
    
    @classmethod
    def get_structure(cls) -> Optional[Dict[str, Dict[str, Path]]]:
        """Get Power Bins structure (built dynamically from config)
        
        Returns:
            Structure dict if available, None if not configured
        """
        base = cls.get_base_path()
        if base is None:
            return None
        
        return {
            "MUSIC": {
                "INTRO": base / "Audio" / "Music" / "Intro",
                "BACKGROUND": base / "Audio" / "Music" / "Background",
                "OUTRO": base / "Audio" / "Music" / "Outro",
                "TRANSITION": base / "Audio" / "Music" / "Transition",
                "BUILDUP": base / "Audio" / "Music" / "Buildup",
                "AMBIENT": base / "Audio" / "Music" / "Ambient",
            },
            "SFX": {
                "SWISHES": base / "Audio" / "SFX" / "Swishes",
                "CLICKS": base / "Audio" / "SFX" / "Clicks",
                "IMPACTS": base / "Audio" / "SFX" / "Impacts",
                "AMBIENT": base / "Audio" / "SFX" / "Ambient",
                "UI_SOUNDS": base / "Audio" / "SFX" / "UI_Sounds",
                "WHOOSHES": base / "Audio" / "SFX" / "Whooshes",
                "STINGS": base / "Audio" / "SFX" / "Stings",
            },
            "GRAPHICS": {
                "LOWER_THIRDS": base / "Graphics" / "Lower_Thirds",
                "TITLES": base / "Graphics" / "Titles",
                "INTROS": base / "Graphics" / "Intros",
                "OUTROS": base / "Graphics" / "Outros",
                "OVERLAYS": base / "Graphics" / "Overlays",
                "SUBTITLES": base / "Graphics" / "Subtitles",
                "LOGO_ANIMATIONS": base / "Graphics" / "Logo_Animations",
                "BACKGROUNDS": base / "Graphics" / "Backgrounds",
                "BORDERS": base / "Graphics" / "Borders",
            },
            "STOCK_FOOTAGE": {
                "B_ROLL_TECH": base / "Video" / "Stock_Footage" / "B_Roll" / "Tech",
                "B_ROLL_NATURE": base / "Video" / "Stock_Footage" / "B_Roll" / "Nature",
                "B_ROLL_URBAN": base / "Video" / "Stock_Footage" / "B_Roll" / "Urban",
                "B_ROLL_ABSTRACT": base / "Video" / "Stock_Footage" / "B_Roll" / "Abstract",
                "TRANSITIONS": base / "Video" / "Transitions",
                "LOOPS": base / "Video" / "Stock_Footage" / "Loops",
            },
            "LUTS": {
                "CINEMATIC": base / "LUTs" / "Cinematic",
                "YOUTUBE": base / "LUTs" / "YouTube",
                "BRANDS": base / "LUTs" / "Brands",
                "S_LOG3": base / "LUTs" / "S_Log3",
                "REC_709": base / "LUTs" / "Rec_709",
            },
            "TEMPLATES": {
                "TITLES": base / "Templates" / "Titles",
                "TRANSITIONS": base / "Templates" / "Transitions",
                "LOWER_THIRDS": base / "Templates" / "Lower_Thirds",
            },
        }
    
    # Supported file extensions for each category
    FILE_EXTENSIONS = {
        "MUSIC": ["*.mp3", "*.wav", "*.aac", "*.m4a", "*.flac"],
        "SFX": ["*.mp3", "*.wav", "*.aac", "*.m4a"],
        "GRAPHICS": ["*.png", "*.jpg", "*.jpeg", "*.mov", "*.mp4", "*.tga", "*.exr"],
        "STOCK_FOOTAGE": ["*.mp4", "*.mov", "*.mxf", "*.avi"],
        "LUTS": ["*.cube", "*.3dl"],
        "TEMPLATES": ["*.drt", "*.mov", "*.mp4"],
    }
    
    @classmethod
    def get_extensions(cls, category: str) -> List[str]:
        """Get file extensions for category"""
        return cls.FILE_EXTENSIONS.get(category, ["*.mp4", "*.mov", "*.mp3", "*.wav", "*.png", "*.jpg"])
    
    @classmethod
    def validate_structure(cls) -> Dict[str, bool]:
        """Validate that Power Bins structure exists
        
        Returns:
            Dict with validation results, or {"available": False} if not configured
        """
        base = cls.get_base_path()
        if base is None:
            return {"available": False, "base_exists": False}
        
        results = {"available": True}
        
        if not base.exists():
            return {"available": True, "base_exists": False}
        
        results["base_exists"] = True
        
        # Check each category
        structure = cls.get_structure()
        if structure is None:
            return {"available": False, "base_exists": False}
            
        for category, subcategories in structure.items():
            category_exists = False
            for subcat_name, subcat_path in subcategories.items():
                if subcat_path.exists():
                    category_exists = True
                    results[f"{category}/{subcat_name}"] = True
                else:
                    results[f"{category}/{subcat_name}"] = False
            results[category] = category_exists
        
        return results


