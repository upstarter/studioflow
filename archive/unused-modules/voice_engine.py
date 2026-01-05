"""
Voice Command Engine for StudioFlow
Natural language control for video editing
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import re
import whisper
import torch
from rich.console import Console

console = Console()


@dataclass
class VoiceCommand:
    """Represents a parsed voice command"""
    raw_text: str
    intent: str
    entities: Dict[str, Any]
    confidence: float


class CommandGrammar:
    """Define and parse editing command patterns"""

    def __init__(self):
        self.patterns = {
            "speed_up": [
                r"make (?:it|this) (?P<factor>faster|slower|2x|3x)",
                r"speed up (?:by )?(?P<amount>\d+)(?:%| percent)?",
                r"(?P<factor>slow down|speed up) (?:this )?(?:section|clip)",
            ],
            "cut": [
                r"cut (?:from )?(?P<start>\d+:\d+) (?:to )?(?P<end>\d+:\d+)",
                r"remove (?:the )?(?P<what>silence|pauses|dead air)",
                r"trim (?P<amount>\d+) seconds? (?:from )?(?P<where>start|end|beginning|ending)",
            ],
            "transition": [
                r"add (?:a )?(?P<type>\w+) transition (?:here)?",
                r"transition to (?:the )?next (?:clip|scene) with (?P<type>\w+)",
            ],
            "color": [
                r"make (?:it )?(?P<adjustment>warmer|cooler|brighter|darker|more vibrant)",
                r"(?P<action>increase|decrease) (?:the )?(?P<param>contrast|saturation|brightness)",
            ],
            "audio": [
                r"(?P<action>add|remove) (?P<type>music|sound effects?|voice over)",
                r"(?P<action>increase|decrease|mute) (?:the )?(?P<target>volume|audio|sound)",
                r"duck (?:the )?audio (?:under )?(?:the )?(?P<target>dialogue|voice)",
            ],
            "navigate": [
                r"go to (?P<target>beginning|end|middle|\d+:\d+)",
                r"find (?:all )?(?P<what>cuts|transitions|clips with \w+)",
                r"show me (?P<what>the timeline|effects|color page|audio)",
            ],
            "mark": [
                r"mark (?:this )?(?:as )?(?P<type>in|out|important|b-roll|highlight)",
                r"(?:add|create) (?:a )?marker (?:here)?(?:called )?(?P<name>.*)?",
            ],
            "export": [
                r"export (?:for )?(?P<platform>youtube|instagram|tiktok)",
                r"render (?:in )?(?P<quality>4k|1080p|draft)",
                r"create (?:a )?(?P<type>thumbnail|preview)",
            ],
            "undo": [
                r"(?P<action>undo|redo)(?: that)?",
                r"go back (?P<steps>\d+) steps?",
            ]
        }

        self.compiled_patterns = {
            intent: [re.compile(pattern, re.IGNORECASE)
                    for pattern in patterns]
            for intent, patterns in self.patterns.items()
        }

    def parse(self, text: str) -> Optional[VoiceCommand]:
        """Parse natural language into structured command"""
        text = text.strip().lower()

        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.match(text)
                if match:
                    return VoiceCommand(
                        raw_text=text,
                        intent=intent,
                        entities=match.groupdict(),
                        confidence=0.9  # Simple confidence for now
                    )

        return None


class VoiceCommandEngine:
    """Main voice command processing engine"""

    def __init__(self, model_size: str = "base", device: str = "cuda"):
        """Initialize voice engine with Whisper model"""
        self.device = device if torch.cuda.is_available() else "cpu"
        console.print(f"[cyan]Loading Whisper model ({model_size}) on {self.device}...[/cyan]")
        self.whisper_model = whisper.load_model(model_size, device=self.device)
        self.grammar = CommandGrammar()
        self.command_handlers: Dict[str, Callable] = {}
        self.setup_handlers()
        console.print("[green]✓ Voice engine ready![/green]")

    def setup_handlers(self):
        """Register command handlers"""
        self.command_handlers = {
            "speed_up": self.handle_speed,
            "cut": self.handle_cut,
            "transition": self.handle_transition,
            "color": self.handle_color,
            "audio": self.handle_audio,
            "navigate": self.handle_navigate,
            "mark": self.handle_mark,
            "export": self.handle_export,
            "undo": self.handle_undo,
        }

    def listen(self, audio_path: Optional[Path] = None) -> str:
        """
        Listen for voice input via microphone or file
        Returns transcribed text
        """
        if audio_path:
            # Process audio file
            result = self.whisper_model.transcribe(
                str(audio_path),
                language="en",
                fp16=self.device == "cuda"
            )
            return result["text"]
        else:
            # TODO: Real-time microphone input
            # For now, return sample
            return "make it faster"

    def process_command(self, text: str) -> Dict[str, Any]:
        """Process natural language command"""
        # Parse command
        command = self.grammar.parse(text)

        if not command:
            return {
                "success": False,
                "message": f"Couldn't understand: '{text}'",
                "suggestion": "Try: 'make it faster' or 'cut from 0:10 to 0:20'"
            }

        # Execute handler
        handler = self.command_handlers.get(command.intent)
        if handler:
            return handler(command)

        return {
            "success": False,
            "message": f"No handler for intent: {command.intent}"
        }

    # Command Handlers
    def handle_speed(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle speed adjustment commands"""
        factor = command.entities.get("factor", "faster")

        speed_map = {
            "faster": 1.5,
            "slower": 0.5,
            "2x": 2.0,
            "3x": 3.0,
            "slow down": 0.75,
            "speed up": 1.25
        }

        multiplier = speed_map.get(factor, 1.5)

        return {
            "success": True,
            "action": "adjust_speed",
            "multiplier": multiplier,
            "message": f"Speed adjusted to {multiplier}x"
        }

    def handle_cut(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle cut/trim commands"""
        what = command.entities.get("what")

        if what in ["silence", "pauses", "dead air"]:
            return {
                "success": True,
                "action": "remove_silence",
                "threshold_db": -40,
                "min_silence_ms": 500,
                "message": f"Removing {what}"
            }

        start = command.entities.get("start")
        end = command.entities.get("end")

        if start and end:
            return {
                "success": True,
                "action": "cut_range",
                "start": start,
                "end": end,
                "message": f"Cutting from {start} to {end}"
            }

        return {
            "success": False,
            "message": "Specify what to cut"
        }

    def handle_transition(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle transition commands"""
        transition_type = command.entities.get("type", "dissolve")

        return {
            "success": True,
            "action": "add_transition",
            "type": transition_type,
            "duration": 0.5,  # Default 0.5 seconds
            "message": f"Adding {transition_type} transition"
        }

    def handle_color(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle color grading commands"""
        adjustment = command.entities.get("adjustment")
        action = command.entities.get("action")
        param = command.entities.get("param")

        if adjustment:
            adjustments_map = {
                "warmer": {"temperature": 500},
                "cooler": {"temperature": -500},
                "brighter": {"exposure": 0.5},
                "darker": {"exposure": -0.5},
                "more vibrant": {"saturation": 1.2}
            }

            settings = adjustments_map.get(adjustment, {})
            return {
                "success": True,
                "action": "color_adjust",
                "adjustments": settings,
                "message": f"Making image {adjustment}"
            }

        if action and param:
            value = 1.1 if action == "increase" else 0.9
            return {
                "success": True,
                "action": "color_adjust",
                "adjustments": {param: value},
                "message": f"{action.capitalize()} {param}"
            }

        return {
            "success": False,
            "message": "Specify color adjustment"
        }

    def handle_audio(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle audio commands"""
        action = command.entities.get("action")
        target = command.entities.get("target") or command.entities.get("type")

        return {
            "success": True,
            "action": f"audio_{action}",
            "target": target,
            "message": f"Audio: {action} {target}"
        }

    def handle_navigate(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle navigation commands"""
        target = command.entities.get("target")
        what = command.entities.get("what")

        if target:
            return {
                "success": True,
                "action": "navigate_to",
                "target": target,
                "message": f"Navigating to {target}"
            }

        if what:
            return {
                "success": True,
                "action": "find",
                "query": what,
                "message": f"Finding {what}"
            }

        return {
            "success": False,
            "message": "Specify navigation target"
        }

    def handle_mark(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle marker/marking commands"""
        mark_type = command.entities.get("type", "marker")
        name = command.entities.get("name", "")

        return {
            "success": True,
            "action": "add_marker",
            "type": mark_type,
            "name": name,
            "message": f"Added {mark_type} marker{' - ' + name if name else ''}"
        }

    def handle_export(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle export commands"""
        platform = command.entities.get("platform")
        quality = command.entities.get("quality")
        export_type = command.entities.get("type")

        if platform:
            presets = {
                "youtube": {"resolution": "3840x2160", "bitrate": "45M", "codec": "h265"},
                "instagram": {"resolution": "1080x1080", "bitrate": "8M", "codec": "h264"},
                "tiktok": {"resolution": "1080x1920", "bitrate": "12M", "codec": "h264"}
            }

            preset = presets.get(platform, presets["youtube"])
            return {
                "success": True,
                "action": "export",
                "preset": preset,
                "platform": platform,
                "message": f"Exporting for {platform}"
            }

        if quality:
            return {
                "success": True,
                "action": "render",
                "quality": quality,
                "message": f"Rendering in {quality}"
            }

        return {
            "success": True,
            "action": "export",
            "preset": "default",
            "message": "Starting export"
        }

    def handle_undo(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle undo/redo commands"""
        action = command.entities.get("action", "undo")
        steps = int(command.entities.get("steps", 1))

        return {
            "success": True,
            "action": action,
            "steps": steps,
            "message": f"{action.capitalize()} {steps} step(s)"
        }


# Example usage functions
def demo_voice_engine():
    """Demo the voice command engine"""
    engine = VoiceCommandEngine(model_size="tiny")  # Use tiny for testing

    test_commands = [
        "make it faster",
        "cut from 0:10 to 0:20",
        "add a dissolve transition",
        "make it warmer",
        "remove the silence",
        "go to the beginning",
        "export for youtube",
        "undo that",
        "mark this as important",
        "increase the contrast"
    ]

    console.print("\n[bold cyan]Voice Command Demo[/bold cyan]\n")

    for cmd in test_commands:
        console.print(f"[yellow]Voice:[/yellow] '{cmd}'")
        result = engine.process_command(cmd)

        if result["success"]:
            console.print(f"[green]✓ Action:[/green] {result.get('action', 'unknown')}")
            console.print(f"[green]  Result:[/green] {result['message']}")
            if "adjustments" in result:
                console.print(f"[green]  Settings:[/green] {result['adjustments']}")
        else:
            console.print(f"[red]✗ Failed:[/red] {result['message']}")
            if "suggestion" in result:
                console.print(f"[yellow]  Try:[/yellow] {result['suggestion']}")

        console.print()


if __name__ == "__main__":
    demo_voice_engine()