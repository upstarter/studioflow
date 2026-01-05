"""
Abstract template system for polymorphic content generation
Allows multiple implementations of templates to be registered and used dynamically
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, TypeVar, Generic
from dataclasses import dataclass, field
import json
import yaml


# Type variable for template implementations
T = TypeVar('T', bound='Template')


class Template(ABC):
    """Abstract base class for all templates"""

    def __init__(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.metadata = metadata or {}
        self._validate()

    @abstractmethod
    def _validate(self) -> None:
        """Validate template configuration"""
        pass

    @abstractmethod
    def apply(self, context: Dict[str, Any]) -> Any:
        """Apply template with given context"""
        pass

    @abstractmethod
    def preview(self) -> Dict[str, Any]:
        """Preview template without applying"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize template to dictionary"""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "metadata": self.metadata
        }


class ComposableTemplate(Template):
    """Template that can be composed from multiple sub-templates"""

    def __init__(self, name: str, components: List[Template], metadata: Optional[Dict[str, Any]] = None):
        self.components = components
        super().__init__(name, metadata)

    def _validate(self) -> None:
        """Validate all component templates"""
        for component in self.components:
            component._validate()

    def apply(self, context: Dict[str, Any]) -> List[Any]:
        """Apply all component templates in sequence"""
        results = []
        for component in self.components:
            result = component.apply(context)
            results.append(result)
            # Pass results forward in context
            context[f"{component.name}_result"] = result
        return results

    def preview(self) -> Dict[str, Any]:
        """Preview all components"""
        return {
            "type": "composite",
            "components": [c.preview() for c in self.components]
        }


class TemplateRegistry(Generic[T]):
    """Registry pattern for managing template implementations"""

    def __init__(self):
        self._templates: Dict[str, Type[T]] = {}
        self._instances: Dict[str, T] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, name: str, template_class: Type[T], category: Optional[str] = None) -> None:
        """Register a template class"""
        self._templates[name] = template_class
        if category:
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(name)

    def create(self, name: str, **kwargs) -> T:
        """Create instance of registered template"""
        if name not in self._templates:
            raise ValueError(f"Template '{name}' not registered")

        template_class = self._templates[name]
        instance = template_class(name=name, **kwargs)
        self._instances[name] = instance
        return instance

    def get(self, name: str) -> Optional[T]:
        """Get existing template instance"""
        return self._instances.get(name)

    def list_templates(self, category: Optional[str] = None) -> List[str]:
        """List all registered templates, optionally by category"""
        if category:
            return self._categories.get(category, [])
        return list(self._templates.keys())

    def list_categories(self) -> List[str]:
        """List all template categories"""
        return list(self._categories.keys())


# Specific Template Implementations

class VideoEffectTemplate(Template):
    """Template for video effects and overlays"""

    def __init__(self, name: str, effect_file: Path, parameters: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.effect_file = effect_file
        self.parameters = parameters or {}
        super().__init__(name, metadata)

    def _validate(self) -> None:
        """Validate effect file exists"""
        if not self.effect_file.exists():
            raise FileNotFoundError(f"Effect file not found: {self.effect_file}")

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply video effect with parameters"""
        return {
            "effect": str(self.effect_file),
            "parameters": {**self.parameters, **context.get("overrides", {})},
            "timeline_position": context.get("position", 0),
            "duration": context.get("duration", -1)
        }

    def preview(self) -> Dict[str, Any]:
        """Preview effect configuration"""
        return {
            "name": self.name,
            "type": "video_effect",
            "file": str(self.effect_file),
            "parameters": self.parameters,
            "metadata": self.metadata
        }


class ScriptPatternTemplate(Template):
    """Template for video script patterns and structures"""

    def __init__(self, name: str, structure: Dict[str, Any], hooks: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.structure = structure
        self.hooks = hooks or []
        super().__init__(name, metadata)

    def _validate(self) -> None:
        """Validate script structure has required sections"""
        required = ["intro", "body", "outro"]
        for section in required:
            if section not in self.structure:
                raise ValueError(f"Script structure missing required section: {section}")

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate script based on pattern"""
        topic = context.get("topic", "")
        style = context.get("style", "educational")

        script = {
            "title": self._generate_title(topic, style),
            "sections": []
        }

        for section_name, section_config in self.structure.items():
            section = {
                "name": section_name,
                "duration": section_config.get("duration", "auto"),
                "content": self._expand_template(section_config.get("template", ""), context),
                "techniques": section_config.get("techniques", []),
                "b_roll_suggestions": section_config.get("b_roll", [])
            }
            script["sections"].append(section)

        if self.hooks:
            script["hooks"] = [self._expand_template(hook, context) for hook in self.hooks]

        return script

    def preview(self) -> Dict[str, Any]:
        """Preview script structure"""
        return {
            "name": self.name,
            "type": "script_pattern",
            "structure": list(self.structure.keys()),
            "hooks_available": len(self.hooks) > 0,
            "metadata": self.metadata
        }

    def _generate_title(self, topic: str, style: str) -> str:
        """Generate title based on topic and style"""
        templates = {
            "educational": f"How to {topic} - Complete Guide",
            "entertainment": f"{topic} You Won't Believe!",
            "review": f"{topic} - Honest Review",
            "tutorial": f"Master {topic} in Minutes"
        }
        return templates.get(style, f"{topic} - Video")

    def _expand_template(self, template: str, context: Dict[str, Any]) -> str:
        """Expand template strings with context variables"""
        for key, value in context.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template


class EncodingProfileTemplate(Template):
    """Template for video encoding profiles"""

    def __init__(self, name: str, codec: str, settings: Dict[str, Any], two_pass: bool = False, metadata: Optional[Dict[str, Any]] = None):
        self.codec = codec
        self.settings = settings
        self.two_pass = two_pass
        super().__init__(name, metadata)

    def _validate(self) -> None:
        """Validate codec and required settings"""
        required_settings = ["bitrate", "preset", "pix_fmt"]
        for setting in required_settings:
            if setting not in self.settings and not self.settings.get("auto_" + setting):
                raise ValueError(f"Encoding profile missing required setting: {setting}")

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate encoding command based on profile"""
        input_file = context.get("input")
        output_file = context.get("output")

        # Build ffmpeg command components
        command_parts = {
            "input": f"-i {input_file}",
            "codec": f"-c:v {self.codec}",
            "settings": []
        }

        # Apply settings with context overrides
        final_settings = {**self.settings, **context.get("overrides", {})}

        for key, value in final_settings.items():
            if key == "bitrate":
                command_parts["settings"].append(f"-b:v {value}")
            elif key == "preset":
                command_parts["settings"].append(f"-preset {value}")
            elif key == "crf":
                command_parts["settings"].append(f"-crf {value}")
            elif key == "pix_fmt":
                command_parts["settings"].append(f"-pix_fmt {value}")
            elif not key.startswith("auto_"):
                command_parts["settings"].append(f"-{key} {value}")

        # Handle two-pass encoding
        if self.two_pass:
            pass1 = f"ffmpeg {command_parts['input']} {command_parts['codec']} {' '.join(command_parts['settings'])} -pass 1 -f null /dev/null"
            pass2 = f"ffmpeg {command_parts['input']} {command_parts['codec']} {' '.join(command_parts['settings'])} -pass 2 {output_file}"
            return {
                "commands": [pass1, pass2],
                "two_pass": True,
                "profile": self.name
            }
        else:
            command = f"ffmpeg {command_parts['input']} {command_parts['codec']} {' '.join(command_parts['settings'])} {output_file}"
            return {
                "command": command,
                "two_pass": False,
                "profile": self.name
            }

    def preview(self) -> Dict[str, Any]:
        """Preview encoding settings"""
        return {
            "name": self.name,
            "type": "encoding_profile",
            "codec": self.codec,
            "settings": self.settings,
            "two_pass": self.two_pass,
            "metadata": self.metadata
        }


class ProjectTemplate(Template):
    """Template for complete project setup"""

    def __init__(self, name: str, structure: Dict[str, Any], workflows: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.structure = structure
        self.workflows = workflows or []
        super().__init__(name, metadata)

    def _validate(self) -> None:
        """Validate project structure"""
        if "directories" not in self.structure:
            raise ValueError("Project template must define directories")

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create project structure"""
        project_name = context.get("name", "untitled")
        base_path = Path(context.get("path", ".")) / project_name

        created = {
            "directories": [],
            "files": [],
            "configs": {}
        }

        # Create directories
        for dir_name in self.structure.get("directories", []):
            dir_path = base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            created["directories"].append(str(dir_path))

        # Create config files
        for config_name, config_data in self.structure.get("configs", {}).items():
            config_path = base_path / config_name

            if config_name.endswith(".yaml") or config_name.endswith(".yml"):
                with open(config_path, 'w') as f:
                    yaml.dump(config_data, f)
            elif config_name.endswith(".json"):
                with open(config_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
            else:
                config_path.write_text(str(config_data))

            created["files"].append(str(config_path))
            created["configs"][config_name] = config_data

        # Set up workflows
        if self.workflows:
            created["workflows"] = self.workflows

        return created

    def preview(self) -> Dict[str, Any]:
        """Preview project structure"""
        return {
            "name": self.name,
            "type": "project_template",
            "directories": self.structure.get("directories", []),
            "configs": list(self.structure.get("configs", {}).keys()),
            "workflows": self.workflows,
            "metadata": self.metadata
        }


# Factory for creating templates from configuration
class TemplateFactory:
    """Factory for creating templates from configuration files or dictionaries"""

    @staticmethod
    def from_file(file_path: Path) -> Template:
        """Create template from configuration file"""
        with open(file_path) as f:
            if file_path.suffix in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            elif file_path.suffix == '.json':
                config = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

        return TemplateFactory.from_dict(config)

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> Template:
        """Create template from configuration dictionary"""
        template_type = config.get("type")
        name = config.get("name", "unnamed")

        if template_type == "video_effect":
            return VideoEffectTemplate(
                name=name,
                effect_file=Path(config["effect_file"]),
                parameters=config.get("parameters"),
                metadata=config.get("metadata")
            )
        elif template_type == "script_pattern":
            return ScriptPatternTemplate(
                name=name,
                structure=config["structure"],
                hooks=config.get("hooks"),
                metadata=config.get("metadata")
            )
        elif template_type == "encoding_profile":
            return EncodingProfileTemplate(
                name=name,
                codec=config["codec"],
                settings=config["settings"],
                two_pass=config.get("two_pass", False),
                metadata=config.get("metadata")
            )
        elif template_type == "project":
            return ProjectTemplate(
                name=name,
                structure=config["structure"],
                workflows=config.get("workflows"),
                metadata=config.get("metadata")
            )
        elif template_type == "composite":
            components = [TemplateFactory.from_dict(c) for c in config["components"]]
            return ComposableTemplate(
                name=name,
                components=components,
                metadata=config.get("metadata")
            )
        else:
            raise ValueError(f"Unknown template type: {template_type}")