"""
Interactive Setup Wizard for First-Time Users
Guides through initial configuration and project setup
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import subprocess
import shutil

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown
from rich import print as rprint

from studioflow.core.config import Config, ConfigManager
from studioflow.core.project import ProjectManager


console = Console()


class SetupWizard:
    """Interactive setup wizard for first-time users"""

    def __init__(self):
        self.console = console
        self.config = Config()
        self.config_manager = ConfigManager()
        self.answers: Dict[str, Any] = {}

    def run(self) -> bool:
        """Run the complete setup wizard"""
        self.console.clear()
        self._show_welcome()

        # Check if this is first run
        if self._is_first_run():
            self.console.print("\n[yellow]First time setup detected![/yellow]")
            self.console.print("Let's configure StudioFlow for your workflow.\n")
        else:
            if not Confirm.ask("Run setup wizard again?", default=False):
                return False

        try:
            # Step 1: Basic configuration
            self._configure_basics()

            # Step 2: Check dependencies
            self._check_dependencies()

            # Step 3: Configure paths
            self._configure_paths()

            # Step 4: Select workflow
            self._select_workflow()

            # Step 5: Configure integrations
            self._configure_integrations()

            # Step 6: Create first project
            if Confirm.ask("\nWould you like to create your first project?", default=True):
                self._create_first_project()

            # Step 7: Save configuration
            self._save_configuration()

            # Step 8: Show next steps
            self._show_next_steps()

            return True

        except KeyboardInterrupt:
            self.console.print("\n[red]Setup cancelled by user[/red]")
            return False
        except Exception as e:
            self.console.print(f"\n[red]Setup error: {e}[/red]")
            return False

    def _is_first_run(self) -> bool:
        """Check if this is the first time running StudioFlow"""
        config_file = Path.home() / ".config" / "studioflow" / "config.yaml"
        return not config_file.exists()

    def _show_welcome(self):
        """Show welcome message"""
        welcome = """
# Welcome to StudioFlow! 🎬

**StudioFlow** is your automated video production pipeline that integrates:
- 📹 **Media Management** - Organize footage efficiently
- 🎨 **DaVinci Resolve** - Professional editing integration
- 🎵 **Audio Processing** - Fairlight templates & LUFS targeting
- ✨ **Effects System** - Node-based Fusion effects
- 📺 **Publishing** - YouTube optimization & multi-platform export

This wizard will help you:
1. Configure your environment
2. Set up your first project
3. Learn essential commands
"""
        self.console.print(Panel(Markdown(welcome), title="StudioFlow Setup", border_style="cyan"))

    def _configure_basics(self):
        """Configure basic settings"""
        self.console.print("\n[bold cyan]📋 Basic Configuration[/bold cyan]\n")

        # User name
        self.answers["user_name"] = Prompt.ask(
            "What's your name?",
            default=os.environ.get("USER", "Creator")
        )

        # Primary use case
        self.console.print("\nWhat type of content do you primarily create?")
        content_types = [
            "1. YouTube videos",
            "2. Podcasts",
            "3. Online courses/tutorials",
            "4. Short-form content (TikTok/Reels)",
            "5. Professional/commercial video",
            "6. Live streaming"
        ]
        for ct in content_types:
            self.console.print(f"  {ct}")

        content_choice = IntPrompt.ask("Select [1-6]", default=1)
        content_map = {
            1: "youtube",
            2: "podcast",
            3: "tutorial",
            4: "short_form",
            5: "commercial",
            6: "streaming"
        }
        self.answers["content_type"] = content_map.get(content_choice, "youtube")

        # Experience level
        self.console.print("\nWhat's your experience level with video editing?")
        levels = ["1. Beginner", "2. Intermediate", "3. Advanced", "4. Professional"]
        for level in levels:
            self.console.print(f"  {level}")

        level_choice = IntPrompt.ask("Select [1-4]", default=2)
        self.answers["experience_level"] = level_choice

    def _check_dependencies(self):
        """Check and install dependencies"""
        self.console.print("\n[bold cyan]🔍 Checking Dependencies[/bold cyan]\n")

        dependencies = [
            ("ffmpeg", "ffmpeg -version", "Media processing"),
            ("python3", "python3 --version", "Python runtime"),
            ("git", "git --version", "Version control"),
        ]

        missing = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            for name, command, description in dependencies:
                task = progress.add_task(f"Checking {name}...", total=1)

                try:
                    result = subprocess.run(
                        command.split(),
                        capture_output=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        progress.update(task, completed=1)
                        self.console.print(f"  [green]✓[/green] {name}: {description}")
                    else:
                        missing.append(name)
                        self.console.print(f"  [yellow]⚠[/yellow] {name}: Not found")
                except:
                    missing.append(name)
                    self.console.print(f"  [yellow]⚠[/yellow] {name}: Not found")

        if missing:
            self.console.print(f"\n[yellow]Missing dependencies: {', '.join(missing)}[/yellow]")

            if "ffmpeg" in missing:
                self.console.print("\nTo install ffmpeg:")
                self.console.print("  • macOS: brew install ffmpeg")
                self.console.print("  • Ubuntu: sudo apt install ffmpeg")
                self.console.print("  • Windows: Download from ffmpeg.org")

            if not Confirm.ask("\nContinue anyway?", default=True):
                raise Exception("Missing required dependencies")

    def _configure_paths(self):
        """Configure storage paths"""
        self.console.print("\n[bold cyan]📁 Storage Configuration[/bold cyan]\n")

        # Default paths
        home = Path.home()
        default_project = home / "StudioFlow"
        default_media = home / "StudioFlow" / "Media"

        # Project directory
        self.console.print("Where would you like to store your projects?")
        project_path = Prompt.ask(
            "Project directory",
            default=str(default_project)
        )
        self.answers["project_path"] = Path(project_path)

        # Media directory
        self.console.print("\nWhere do you store your raw media files?")
        media_path = Prompt.ask(
            "Media directory",
            default=str(default_media)
        )
        self.answers["media_path"] = Path(media_path)

        # Create directories if they don't exist
        for path in [self.answers["project_path"], self.answers["media_path"]]:
            if not path.exists():
                if Confirm.ask(f"Create {path}?", default=True):
                    path.mkdir(parents=True, exist_ok=True)
                    self.console.print(f"  [green]✓[/green] Created: {path}")

    def _select_workflow(self):
        """Select preferred workflow"""
        self.console.print("\n[bold cyan]🎯 Workflow Selection[/bold cyan]\n")

        workflows = {
            "1": {
                "name": "Quick YouTube",
                "description": "Record → Edit → Upload to YouTube",
                "templates": ["youtube_creator"],
                "features": ["auto_thumbnail", "auto_chapters", "seo_optimization"]
            },
            "2": {
                "name": "Podcast Production",
                "description": "Record → Process Audio → Publish",
                "templates": ["podcast"],
                "features": ["auto_transcription", "lufs_targeting", "multi_platform"]
            },
            "3": {
                "name": "Tutorial Series",
                "description": "Screen Record → Edit → Course Platform",
                "templates": ["tutorial"],
                "features": ["screen_capture", "annotations", "chapter_marks"]
            },
            "4": {
                "name": "Professional",
                "description": "Full pipeline with color grading and mastering",
                "templates": ["youtube_creator", "podcast"],
                "features": ["color_grading", "audio_mastering", "multi_format"]
            }
        }

        self.console.print("Select your preferred workflow:\n")
        for key, workflow in workflows.items():
            self.console.print(f"  {key}. [bold]{workflow['name']}[/bold]")
            self.console.print(f"     {workflow['description']}")
            self.console.print(f"     Features: {', '.join(workflow['features'])}\n")

        choice = Prompt.ask("Select workflow [1-4]", default="1")
        self.answers["workflow"] = workflows.get(choice, workflows["1"])

    def _configure_integrations(self):
        """Configure external integrations"""
        self.console.print("\n[bold cyan]🔗 Integrations[/bold cyan]\n")

        # DaVinci Resolve
        if Confirm.ask("Do you use DaVinci Resolve?", default=True):
            resolve_path = None

            # Try to find Resolve automatically
            possible_paths = [
                Path("/opt/resolve"),
                Path("/Applications/DaVinci Resolve/DaVinci Resolve.app"),
                Path("C:/Program Files/Blackmagic Design/DaVinci Resolve"),
            ]

            for path in possible_paths:
                if path.exists():
                    resolve_path = path
                    self.console.print(f"  [green]✓[/green] Found Resolve at: {path}")
                    break

            if not resolve_path:
                custom_path = Prompt.ask("DaVinci Resolve installation path", default="")
                if custom_path:
                    resolve_path = Path(custom_path)

            self.answers["resolve_path"] = resolve_path

        # YouTube
        if self.answers["content_type"] in ["youtube", "tutorial"]:
            if Confirm.ask("\nConnect YouTube account?", default=False):
                self.console.print("  [dim]Note: You'll need to set up OAuth credentials[/dim]")
                self.console.print("  [dim]See: sf youtube auth --help[/dim]")
                self.answers["youtube_setup"] = True

    def _create_first_project(self):
        """Create the first project"""
        self.console.print("\n[bold cyan]🎬 Create Your First Project[/bold cyan]\n")

        # Get project name
        project_name = Prompt.ask(
            "Project name",
            default="My First Video"
        )

        # Sanitize name
        safe_name = "".join(c for c in project_name if c.isalnum() or c in " -_")
        safe_name = safe_name.replace(" ", "_")

        # Get template
        template = self.answers["workflow"]["templates"][0]

        # Create project
        try:
            manager = ProjectManager()
            project_path = self.answers["project_path"] / safe_name

            self.console.print(f"\nCreating project: {project_name}")

            with Progress(console=self.console) as progress:
                task = progress.add_task("Setting up project structure...", total=5)

                # Create directories
                progress.update(task, advance=1, description="Creating directories...")
                directories = [
                    "01_MEDIA/A-Roll",
                    "01_MEDIA/B-Roll",
                    "01_MEDIA/Audio",
                    "02_PROJECT/Resolve",
                    "02_PROJECT/Assets",
                    "03_EXPORTS/Drafts",
                    "03_EXPORTS/Final",
                    "04_DOCUMENTS/Scripts"
                ]

                for dir_path in directories:
                    (project_path / dir_path).mkdir(parents=True, exist_ok=True)

                # Create README
                progress.update(task, advance=1, description="Creating documentation...")
                readme = project_path / "README.md"
                readme.write_text(f"""# {project_name}

Created with StudioFlow

## Quick Start

1. **Import Media**: `sf media import /path/to/footage`
2. **Create Timeline**: `sf resolve create "{project_name}"`
3. **Edit in Resolve**: Open DaVinci Resolve
4. **Export**: `sf resolve export mp4 --preset youtube_4k`
5. **Publish**: `sf publish youtube --auto`

## Project Structure

- `01_MEDIA/` - Raw footage and audio
- `02_PROJECT/` - Project files and assets
- `03_EXPORTS/` - Rendered videos
- `04_DOCUMENTS/` - Scripts and notes
""")

                # Create project config
                progress.update(task, advance=1, description="Configuring project...")
                config_file = project_path / ".studioflow" / "project.yaml"
                config_file.parent.mkdir(exist_ok=True)

                import yaml
                project_config = {
                    "name": project_name,
                    "template": template,
                    "created": str(Path.cwd()),
                    "settings": {
                        "resolution": "1920x1080",
                        "framerate": 29.97,
                        "audio": {
                            "sample_rate": 48000,
                            "target_lufs": -14.0
                        }
                    }
                }
                config_file.write_text(yaml.dump(project_config))

                # Create sample script
                progress.update(task, advance=1, description="Adding sample content...")
                script_file = project_path / "04_DOCUMENTS" / "Scripts" / "script.md"
                script_file.write_text(f"""# {project_name} Script

## Introduction (0:00 - 0:15)
- Hook: Start with an attention-grabbing statement
- Preview what viewers will learn

## Main Content (0:15 - 4:30)
- Point 1: [Your first main point]
- Point 2: [Your second main point]
- Point 3: [Your third main point]

## Conclusion (4:30 - 5:00)
- Recap key points
- Call to action
- End screen elements
""")

                progress.update(task, advance=1, description="Complete!")

            self.answers["first_project"] = project_path
            self.console.print(f"\n[green]✓[/green] Project created at: {project_path}")

        except Exception as e:
            self.console.print(f"[red]Failed to create project: {e}[/red]")
            self.answers["first_project"] = None

    def _save_configuration(self):
        """Save configuration to file"""
        self.console.print("\n[bold cyan]💾 Saving Configuration[/bold cyan]\n")

        config_dir = Path.home() / ".config" / "studioflow"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"

        # Build configuration
        config = {
            "user": {
                "name": self.answers.get("user_name"),
                "content_type": self.answers.get("content_type"),
                "experience_level": self.answers.get("experience_level")
            },
            "paths": {
                "projects": str(self.answers.get("project_path")),
                "media": str(self.answers.get("media_path"))
            },
            "workflow": self.answers.get("workflow", {}).get("name"),
            "features": self.answers.get("workflow", {}).get("features", [])
        }

        if self.answers.get("resolve_path"):
            config["resolve"] = {
                "install_path": str(self.answers["resolve_path"])
            }

        # Save config
        import yaml
        config_file.write_text(yaml.dump(config, default_flow_style=False))

        self.console.print(f"[green]✓[/green] Configuration saved to: {config_file}")

    def _show_next_steps(self):
        """Show next steps and useful commands"""
        self.console.print("\n[bold cyan]🚀 Setup Complete![/bold cyan]\n")

        # Build personalized quick start based on workflow
        workflow_name = self.answers.get("workflow", {}).get("name", "Quick YouTube")

        quick_commands = {
            "Quick YouTube": [
                ("Record footage", "Use your camera/OBS/screen recorder"),
                ("Import media", "sf media import /path/to/footage"),
                ("Create timeline", "sf resolve create 'Episode 1'"),
                ("Apply effects", "sf effects apply glow video.mp4 output.mp4"),
                ("Generate thumbnail", "sf thumbnail generate --auto"),
                ("Publish to YouTube", "sf youtube upload final.mp4")
            ],
            "Podcast Production": [
                ("Record audio", "Use your DAW or sf capture audio"),
                ("Process audio", "sf effects apply podcast_mastering audio.wav final.wav"),
                ("Generate transcript", "sf ai transcribe audio.wav"),
                ("Create video version", "sf resolve create 'Podcast Ep1' --audio final.wav"),
                ("Publish", "sf publish multi-platform final.mp4")
            ],
            "Tutorial Series": [
                ("Record screen", "sf capture screen --audio"),
                ("Edit recording", "sf ai edit recording.mp4 --remove-silence"),
                ("Add annotations", "sf effects compose 'Tutorial' --template lower_third"),
                ("Export", "sf resolve export mp4 --preset tutorial"),
                ("Upload to platform", "sf publish course final.mp4")
            ],
            "Professional": [
                ("Import footage", "sf media import /path/to/footage --organize"),
                ("Create project", "sf project create 'Client Project'"),
                ("Sync multicam", "sf multicam sync --audio"),
                ("Color grade", "sf resolve create 'Master' --lut cinematic"),
                ("Master audio", "sf effects apply music_mastering audio.wav"),
                ("Export all formats", "sf resolve export --multi-format")
            ]
        }

        commands = quick_commands.get(workflow_name, quick_commands["Quick YouTube"])

        # Create next steps panel
        next_steps = Table(show_header=False, box=None, padding=(0, 2))
        next_steps.add_column("Step", style="cyan")
        next_steps.add_column("Command", style="green")

        for i, (desc, cmd) in enumerate(commands, 1):
            next_steps.add_row(f"{i}. {desc}", f"[bold]{cmd}[/bold]")

        panel_content = f"""
[bold]Your personalized workflow:[/bold] {workflow_name}

[yellow]Essential Commands:[/yellow]
"""

        self.console.print(Panel(panel_content, title="Next Steps", border_style="green"))
        self.console.print(next_steps)

        # Show first project info if created
        if self.answers.get("first_project"):
            self.console.print(f"\n[bold]Your first project:[/bold] {self.answers['first_project']}")
            self.console.print(f"[dim]cd {self.answers['first_project']}[/dim]")
            self.console.print(f"[dim]sf project status[/dim]")

        # Help resources
        self.console.print("\n[bold]Need help?[/bold]")
        self.console.print("  • Quick help: [cyan]sf --help[/cyan]")
        self.console.print("  • Command help: [cyan]sf [command] --help[/cyan]")
        self.console.print("  • Interactive guide: [cyan]sf quickstart[/cyan]")
        self.console.print("  • Documentation: [cyan]sf docs[/cyan]")

        self.console.print("\n[green]✨ You're all set! Happy creating![/green]")


def run_setup():
    """Run the setup wizard"""
    wizard = SetupWizard()
    return wizard.run()


if __name__ == "__main__":
    run_setup()