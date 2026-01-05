#!/usr/bin/env python3
"""
DaVinci Resolve PowerGrade Templates for StudioFlow
Creates reusable node tree templates for quick color grading
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import yaml

class ResolvePowerGradeManager:
    """Manages DaVinci Resolve PowerGrade templates for StudioFlow projects"""
    
    def __init__(self):
        self.library_path = Path("/mnt/library/PowerGrades")
        self.templates_path = self.library_path / "Templates"
        self.user_grades_path = self.library_path / "UserGrades"
        self._ensure_structure()
    
    def _ensure_structure(self):
        """Create PowerGrade library structure"""
        categories = [
            "Film_Looks",
            "Creative_Grades", 
            "Technical_Fixes",
            "YouTube_Optimized",
            "Cinematic",
            "Music_Video",
            "Documentary",
            "Quick_Fixes"
        ]
        
        for category in categories:
            (self.templates_path / category).mkdir(parents=True, exist_ok=True)
            (self.user_grades_path / category).mkdir(parents=True, exist_ok=True)
    
    def create_node_template(self, name: str, category: str, nodes: List[Dict]) -> Dict:
        """Create a reusable node tree template"""
        template = {
            "name": name,
            "category": category,
            "version": "1.0",
            "resolve_version": "18.6+",
            "nodes": nodes,
            "metadata": {
                "description": "",
                "tags": [],
                "author": "StudioFlow",
                "luts_required": [],
                "recommended_footage": ""
            }
        }
        
        template_file = self.templates_path / category / f"{name}.json"
        template_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(template_file, 'w') as f:
            json.dump(template, f, indent=2)
        
        return template
    
    def get_standard_templates(self) -> Dict[str, List[Dict]]:
        """Get standard PowerGrade templates"""
        return {
            "YouTube_Hero": [
                {
                    "type": "Serial",
                    "name": "Denoise",
                    "settings": {
                        "temporal_nr": 1,
                        "spatial_nr": 0,
                        "mode": "better"
                    }
                },
                {
                    "type": "Serial", 
                    "name": "Primary_Correction",
                    "settings": {
                        "lift": [0, 0, 0, 0],
                        "gamma": [0, 0, 0, 0],
                        "gain": [1, 1, 1, 1],
                        "contrast": 1.0,
                        "saturation": 1.15
                    }
                },
                {
                    "type": "Serial",
                    "name": "Skin_Tone_Isolation",
                    "qualifier": {
                        "hue_center": 25,
                        "hue_width": 15,
                        "saturation_low": 0.2,
                        "saturation_high": 0.8
                    },
                    "settings": {
                        "gamma": [0, 0.02, 0.01, 0],
                        "saturation": 0.95
                    }
                },
                {
                    "type": "Parallel",
                    "name": "Glow",
                    "settings": {
                        "composite_mode": "add",
                        "opacity": 0.15,
                        "blur": 50
                    }
                },
                {
                    "type": "Serial",
                    "name": "LUT_Application",
                    "lut": "/mnt/library/LUTs/Creative/VisionColor OSIRIS - Rec709 LUTs/Vision 4 - Rec709.cube",
                    "mix": 0.6
                },
                {
                    "type": "Serial",
                    "name": "Output_Sharpening",
                    "settings": {
                        "radius": 0.5,
                        "amount": 0.2
                    }
                }
            ],
            
            "Cinematic_Film": [
                {
                    "type": "Serial",
                    "name": "Film_Grain_Remove",
                    "settings": {
                        "temporal_nr": 2,
                        "spatial_nr": 1
                    }
                },
                {
                    "type": "Serial",
                    "name": "Log_to_Rec709",
                    "color_space_transform": {
                        "input": "S-Log3/S-Gamut3.Cine",
                        "output": "Rec.709 Gamma 2.4"
                    }
                },
                {
                    "type": "Layer",
                    "name": "Power_Windows",
                    "windows": [
                        {
                            "type": "linear",
                            "name": "sky",
                            "position": "top",
                            "gamma": [0, -0.1, -0.05, 0]
                        },
                        {
                            "type": "radial",
                            "name": "vignette",
                            "gamma": [0, 0, 0, -0.15]
                        }
                    ]
                },
                {
                    "type": "Serial",
                    "name": "Film_Emulation",
                    "lut": "/mnt/library/LUTs/Creative/VisionColor OSIRIS - LOG LUTs/M31 - LOG.cube",
                    "mix": 0.7
                },
                {
                    "type": "Serial",
                    "name": "Halation",
                    "settings": {
                        "blur": 100,
                        "gain": [1.05, 1.02, 1.0, 1.0],
                        "mix": 0.1
                    }
                },
                {
                    "type": "Serial",
                    "name": "Film_Grain",
                    "grain": {
                        "size": 0.3,
                        "strength": 0.15,
                        "type": "35mm"
                    }
                }
            ],
            
            "Music_Video_Vibrant": [
                {
                    "type": "Serial",
                    "name": "Base_Grade",
                    "settings": {
                        "contrast": 1.2,
                        "saturation": 1.3,
                        "gamma": [0, 0, 0, -0.05]
                    }
                },
                {
                    "type": "Parallel",
                    "name": "Color_Contrast",
                    "settings": {
                        "low_gain": [0.9, 0.95, 1.1, 1.0],
                        "high_gain": [1.1, 1.05, 0.9, 1.0],
                        "mix": 0.5
                    }
                },
                {
                    "type": "Serial",
                    "name": "Selective_Color",
                    "hsl_curves": {
                        "hue_vs_sat": [[0, 1.2], [60, 1.4], [180, 1.3], [300, 1.5]],
                        "sat_vs_sat": [[0, 0], [0.5, 0.6], [1, 1.2]]
                    }
                },
                {
                    "type": "Serial",
                    "name": "Creative_LUT",
                    "lut": "/mnt/library/LUTs/Creative/VisionColor OSIRIS - Rec709 LUTs/JUGO - Rec709.cube",
                    "mix": 0.8
                },
                {
                    "type": "Serial",
                    "name": "Glow_Highlights",
                    "settings": {
                        "key_input": "highlights",
                        "blur": 75,
                        "gain": 1.2,
                        "mix": 0.25
                    }
                }
            ],
            
            "Quick_Fix_Exposure": [
                {
                    "type": "Serial",
                    "name": "Auto_Balance",
                    "auto_color": True
                },
                {
                    "type": "Serial",
                    "name": "Exposure_Correction",
                    "settings": {
                        "offset": 0,
                        "highlight_recovery": True,
                        "shadow_detail": True
                    }
                },
                {
                    "type": "Serial",
                    "name": "Quick_Contrast",
                    "curves": {
                        "luma": [[0, 0.05], [0.25, 0.23], [0.75, 0.77], [1, 0.95]]
                    }
                }
            ],
            
            "Documentary_Natural": [
                {
                    "type": "Serial",
                    "name": "Natural_Balance",
                    "settings": {
                        "temperature": 0,
                        "tint": 0,
                        "saturation": 1.05
                    }
                },
                {
                    "type": "Serial",
                    "name": "Soft_Contrast",
                    "curves": {
                        "luma": [[0, 0.1], [0.5, 0.5], [1, 0.9]]
                    }
                },
                {
                    "type": "Serial",
                    "name": "Skin_Protection",
                    "qualifier": {
                        "hue_center": 25,
                        "hue_width": 20
                    },
                    "settings": {
                        "saturation": 0.9,
                        "gamma": [0, 0.01, 0, 0]
                    }
                },
                {
                    "type": "Serial",
                    "name": "Subtle_LUT",
                    "lut": "/mnt/library/LUTs/Creative/VisionColor OSIRIS - Rec709 LUTs/Vision 6 - Rec709.cube",
                    "mix": 0.3
                }
            ]
        }
    
    def create_all_standard_templates(self):
        """Create all standard PowerGrade templates"""
        templates = self.get_standard_templates()
        created = []
        
        for name, nodes in templates.items():
            if "YouTube" in name:
                category = "YouTube_Optimized"
            elif "Cinematic" in name:
                category = "Cinematic"
            elif "Music" in name:
                category = "Music_Video"
            elif "Documentary" in name:
                category = "Documentary"
            elif "Quick" in name:
                category = "Quick_Fixes"
            else:
                category = "Creative_Grades"
            
            template = self.create_node_template(name, category, nodes)
            created.append(template)
        
        return created
    
    def generate_resolve_script(self, template_name: str, project_path: Path) -> str:
        """Generate Python script for DaVinci Resolve to load PowerGrade"""
        script = f'''#!/usr/bin/env python3
"""
DaVinci Resolve PowerGrade Loader
Template: {template_name}
Generated by StudioFlow
"""

import DaVinciResolveScript as dvr
import json

def load_powergrade():
    resolve = dvr.scriptapp("Resolve")
    if not resolve:
        print("Please run from within DaVinci Resolve")
        return
    
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        print("No project loaded")
        return
    
    # Load template
    template_path = "{self.templates_path}/{template_name}.json"
    with open(template_path, 'r') as f:
        template = json.load(f)
    
    print(f"Loading PowerGrade: {{template['name']}}")
    print(f"Nodes: {{len(template['nodes'])}}")
    print("")
    print("To apply:")
    print("1. Select your clips in Color page")
    print("2. Middle-click this grade in Gallery")
    print("3. Adjust mix/opacity as needed")
    
    # Note: Actual node creation would require Resolve's node API
    # This script provides the template structure for manual creation
    
    return template

if __name__ == "__main__":
    load_powergrade()
'''
        return script


class PowerGradeLibrary:
    """PowerGrade library with categories and quick access"""
    
    def __init__(self):
        self.manager = ResolvePowerGradeManager()
        self.config_path = Path("/mnt/projects/studioflow/config/powergrades.yml")
        self._load_config()
    
    def _load_config(self):
        """Load PowerGrade configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._default_config()
            self._save_config()
    
    def _default_config(self) -> Dict:
        """Default PowerGrade configuration"""
        return {
            "library_path": "/mnt/library/PowerGrades",
            "resolve_path": "/opt/resolve/",
            "categories": {
                "YouTube_Optimized": {
                    "description": "Optimized for YouTube compression",
                    "tags": ["youtube", "web", "streaming"]
                },
                "Cinematic": {
                    "description": "Film-like looks and color grading",
                    "tags": ["film", "cinema", "movie"]
                },
                "Music_Video": {
                    "description": "Vibrant and stylized looks",
                    "tags": ["music", "vibrant", "stylized"]
                },
                "Documentary": {
                    "description": "Natural and authentic looks",
                    "tags": ["documentary", "natural", "authentic"]
                },
                "Quick_Fixes": {
                    "description": "Fast corrections and fixes",
                    "tags": ["fix", "correction", "quick"]
                }
            },
            "shortcuts": {
                "hero": "YouTube_Hero",
                "film": "Cinematic_Film",
                "music": "Music_Video_Vibrant",
                "fix": "Quick_Fix_Exposure",
                "doc": "Documentary_Natural"
            }
        }
    
    def _save_config(self):
        """Save configuration"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def quick_apply(self, shortcut: str) -> Optional[Dict]:
        """Quick apply a PowerGrade by shortcut"""
        if shortcut in self.config["shortcuts"]:
            template_name = self.config["shortcuts"][shortcut]
            templates = self.manager.get_standard_templates()
            if template_name in templates:
                return {
                    "name": template_name,
                    "nodes": templates[template_name],
                    "shortcut": shortcut
                }
        return None
    
    def list_available(self) -> Dict[str, List[str]]:
        """List all available PowerGrades by category"""
        available = {}
        for category_dir in self.manager.templates_path.iterdir():
            if category_dir.is_dir():
                templates = [f.stem for f in category_dir.glob("*.json")]
                if templates:
                    available[category_dir.name] = templates
        return available


def setup_powergrades():
    """Setup PowerGrades for StudioFlow"""
    print("🎨 Setting up DaVinci Resolve PowerGrades...")
    
    manager = ResolvePowerGradeManager()
    created = manager.create_all_standard_templates()
    
    print(f"✅ Created {len(created)} PowerGrade templates")
    print(f"📁 Location: /mnt/library/PowerGrades/")
    print("")
    print("Quick commands:")
    print("  hero - YouTube optimized look")
    print("  film - Cinematic film look")
    print("  music - Vibrant music video")
    print("  fix - Quick exposure fix")
    print("  doc - Documentary natural")
    print("")
    print("Import in Resolve:")
    print("  1. Open Color page")
    print("  2. Gallery → PowerGrades")
    print("  3. Import from /mnt/library/PowerGrades/Templates/")
    
    return created


if __name__ == "__main__":
    setup_powergrades()