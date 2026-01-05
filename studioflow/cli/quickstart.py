"""
Interactive Quick Start Guide
Provides step-by-step workflows for common tasks
"""

from typing import Optional, Dict, List, Any
from pathlib import Path
import time

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree
from rich import box


console = Console()


class QuickStartGuide:
    """Interactive quick start guide for common workflows"""

    def __init__(self):
        self.console = console
        self.workflows = {
            "youtube": YouTubeWorkflow(),
            "podcast": PodcastWorkflow(),
            "tutorial": TutorialWorkflow(),
            "short_form": ShortFormWorkflow(),
            "multicam": MulticamWorkflow()
        }

    def run(self, workflow: Optional[str] = None):
        """Run the quick start guide"""
        self.console.clear()

        if workflow and workflow in self.workflows:
            # Run specific workflow
            self.workflows[workflow].run()
        else:
            # Show workflow selection
            self._select_workflow()

    def _select_workflow(self):
        """Interactive workflow selection"""
        self.console.print(Panel(
            "[bold cyan]StudioFlow Quick Start Guide[/bold cyan]\n\n"
            "Select a workflow to get step-by-step guidance:",
            border_style="cyan"
        ))

        # Display workflows as a tree
        tree = Tree("📚 Available Workflows")

        workflow_info = {
            "youtube": ("🎬", "YouTube Video", "Complete YouTube production workflow"),
            "podcast": ("🎙️", "Podcast Episode", "Audio recording and publishing"),
            "tutorial": ("📖", "Tutorial/Course", "Screen recording and educational content"),
            "short_form": ("📱", "Short-Form Content", "TikTok, Reels, Shorts"),
            "multicam": ("📹", "Multi-Camera", "Sync and edit multiple angles")
        }

        for key, (icon, name, desc) in workflow_info.items():
            branch = tree.add(f"{icon} [bold]{name}[/bold]")
            branch.add(f"[dim]{desc}[/dim]")
            branch.add(f"[cyan]sf quickstart --workflow {key}[/cyan]")

        self.console.print(tree)

        # Get selection
        self.console.print("\n[bold]Select a workflow:[/bold]")
        choices = list(workflow_info.keys())
        for i, key in enumerate(choices, 1):
            icon, name, _ = workflow_info[key]
            self.console.print(f"  {i}. {icon} {name}")

        choice = Prompt.ask("\nEnter number [1-5]", default="1")

        try:
            selected = choices[int(choice) - 1]
            self.console.print(f"\n[green]Starting {workflow_info[selected][1]} workflow...[/green]\n")
            time.sleep(1)
            self.workflows[selected].run()
        except (ValueError, IndexError):
            self.console.print("[red]Invalid selection[/red]")


class BaseWorkflow:
    """Base class for workflow guides"""

    def __init__(self):
        self.console = console
        self.steps = []
        self.current_step = 0

    def run(self):
        """Run the workflow guide"""
        self._show_overview()
        self._execute_steps()
        self._show_completion()

    def _show_overview(self):
        """Show workflow overview"""
        pass

    def _execute_steps(self):
        """Execute workflow steps"""
        for i, step in enumerate(self.steps, 1):
            self._show_step(i, step)

            if step.get("interactive"):
                self._interactive_step(step)
            else:
                self._show_command(step)

            if i < len(self.steps):
                if not Confirm.ask("\n[cyan]Continue to next step?[/cyan]", default=True):
                    self.console.print("[yellow]Workflow paused. Resume with 'sf quickstart'[/yellow]")
                    break

    def _show_step(self, number: int, step: Dict[str, Any]):
        """Display a single step"""
        self.console.print(f"\n[bold cyan]Step {number}: {step['title']}[/bold cyan]")
        self.console.print(f"{step['description']}\n")

    def _show_command(self, step: Dict[str, Any]):
        """Show command for step"""
        if "command" in step:
            self.console.print(Panel(
                f"[bold green]{step['command']}[/bold green]",
                title="Run this command",
                border_style="green"
            ))

            if "explanation" in step:
                self.console.print(f"\n[dim]{step['explanation']}[/dim]")

    def _interactive_step(self, step: Dict[str, Any]):
        """Handle interactive step"""
        if step.get("type") == "checklist":
            self._show_checklist(step["items"])
        elif step.get("type") == "input":
            response = Prompt.ask(step["prompt"], default=step.get("default", ""))
            step["response"] = response

    def _show_checklist(self, items: List[str]):
        """Show interactive checklist"""
        self.console.print("[bold]Complete these tasks:[/bold]")
        completed = []

        for item in items:
            self.console.print(f"  ☐ {item}")

        self.console.print("\n[dim]Press Enter as you complete each task[/dim]")

        for i, item in enumerate(items):
            Prompt.ask(f"[dim]Task {i+1}/{len(items)}[/dim]", default="")
            completed.append(item)
            self._refresh_checklist(items, completed)

    def _refresh_checklist(self, items: List[str], completed: List[str]):
        """Refresh checklist display"""
        # In a real terminal app, we'd clear and redraw
        # For now, just show progress
        done = len(completed)
        total = len(items)
        self.console.print(f"[green]Progress: {done}/{total} complete[/green]")

    def _show_completion(self):
        """Show workflow completion"""
        self.console.print("\n" + "=" * 50)
        self.console.print(Panel(
            "[bold green]✨ Workflow Complete![/bold green]\n\n"
            "Your project is ready for the next stage.",
            border_style="green"
        ))


class YouTubeWorkflow(BaseWorkflow):
    """YouTube video production workflow"""

    def __init__(self):
        super().__init__()
        self.steps = [
            {
                "title": "Create Project",
                "description": "Set up a new YouTube video project with the optimal structure",
                "command": 'sf new "My YouTube Video" --template youtube',
                "explanation": "This creates folders for media, projects, exports, and documents"
            },
            {
                "title": "Prepare Your Content",
                "description": "Before recording, let's plan your video",
                "interactive": True,
                "type": "checklist",
                "items": [
                    "Write your script or outline",
                    "Set up your recording space",
                    "Check camera and microphone",
                    "Prepare any props or visuals"
                ]
            },
            {
                "title": "Import Media",
                "description": "Import your recorded footage into the project",
                "command": "sf media import /path/to/your/footage",
                "explanation": "Replace /path/to/your/footage with your SD card or folder path"
            },
            {
                "title": "Create Timeline",
                "description": "Set up your editing timeline in DaVinci Resolve",
                "command": 'sf resolve create "Main Edit" --profile youtube --effects',
                "explanation": "This creates a 4K timeline optimized for YouTube with default effects"
            },
            {
                "title": "Apply Audio Processing",
                "description": "Enhance your audio quality",
                "command": "sf effects apply podcast_mastering audio.wav final_audio.wav",
                "explanation": "Applies professional audio mastering targeting -14 LUFS for YouTube"
            },
            {
                "title": "Generate Thumbnail",
                "description": "Create an eye-catching thumbnail",
                "command": 'sf thumbnail generate --text "YOUR TITLE HERE" --style youtube',
                "explanation": "Generates multiple thumbnail options using templates"
            },
            {
                "title": "Export Video",
                "description": "Render your video with optimal settings",
                "command": "sf resolve export mp4 --preset youtube_4k --output final.mp4",
                "explanation": "Exports with YouTube's recommended settings"
            },
            {
                "title": "Add Metadata",
                "description": "Prepare your video information",
                "interactive": True,
                "type": "input",
                "prompt": "Video title",
                "default": "My Amazing Video"
            },
            {
                "title": "Upload to YouTube",
                "description": "Publish your video",
                "command": "sf youtube upload final.mp4 --title \"Your Title\" --description \"Your Description\"",
                "explanation": "Uploads with optimized settings and metadata"
            },
            {
                "title": "Post-Upload Tasks",
                "description": "Final steps after uploading",
                "interactive": True,
                "type": "checklist",
                "items": [
                    "Add end screen elements",
                    "Create custom thumbnail if needed",
                    "Share on social media",
                    "Respond to early comments"
                ]
            }
        ]

    def _show_overview(self):
        """Show YouTube workflow overview"""
        overview = """
# YouTube Video Production Workflow

This guide will walk you through creating a YouTube video from start to finish:

1. **Project Setup** - Organize your files properly
2. **Content Preparation** - Plan your video
3. **Media Import** - Bring in your footage
4. **Timeline Creation** - Set up editing environment
5. **Audio Processing** - Enhance sound quality
6. **Thumbnail Creation** - Design eye-catching thumbnail
7. **Video Export** - Render with optimal settings
8. **Metadata** - Add title and description
9. **Upload** - Publish to YouTube
10. **Post-Upload** - Final touches

**Estimated time:** 30-60 minutes (excluding recording/editing)
"""
        self.console.print(Panel(Markdown(overview), title="YouTube Workflow", border_style="cyan"))

        if not Confirm.ask("\n[cyan]Ready to begin?[/cyan]", default=True):
            return


class PodcastWorkflow(BaseWorkflow):
    """Podcast production workflow"""

    def __init__(self):
        super().__init__()
        self.steps = [
            {
                "title": "Create Podcast Project",
                "description": "Set up a podcast episode project",
                "command": 'sf new "Podcast Episode 1" --template podcast',
                "explanation": "Creates folders optimized for audio production"
            },
            {
                "title": "Recording Setup",
                "description": "Prepare your recording environment",
                "interactive": True,
                "type": "checklist",
                "items": [
                    "Set up microphone(s)",
                    "Check audio levels",
                    "Minimize background noise",
                    "Prepare show notes"
                ]
            },
            {
                "title": "Import Audio",
                "description": "Import your recorded audio",
                "command": "sf media import recordings/ --organize",
                "explanation": "Automatically organizes multiple audio tracks"
            },
            {
                "title": "Apply Audio Processing",
                "description": "Master your podcast audio",
                "command": "sf effects apply podcast_mastering raw_podcast.wav --preset spotify",
                "explanation": "Applies EQ, compression, and LUFS targeting"
            },
            {
                "title": "Generate Transcript",
                "description": "Create transcript for accessibility",
                "command": "sf ai transcribe final_audio.wav --format srt",
                "explanation": "Uses Whisper AI for accurate transcription"
            },
            {
                "title": "Create Video Version",
                "description": "Generate video podcast with waveform",
                "command": 'sf resolve create "Video Podcast" --audio final_audio.wav',
                "explanation": "Creates video version for YouTube"
            },
            {
                "title": "Export Formats",
                "description": "Export for different platforms",
                "command": "sf publish multi-platform --audio --video",
                "explanation": "Creates versions for Spotify, Apple, YouTube"
            },
            {
                "title": "Publish",
                "description": "Distribute to podcast platforms",
                "interactive": True,
                "type": "checklist",
                "items": [
                    "Upload to podcast host",
                    "Submit to Spotify",
                    "Submit to Apple Podcasts",
                    "Post video to YouTube",
                    "Share on social media"
                ]
            }
        ]

    def _show_overview(self):
        """Show podcast workflow overview"""
        overview = """
# Podcast Production Workflow

Complete podcast production from recording to distribution:

1. **Project Setup** - Organize podcast files
2. **Recording** - Capture high-quality audio
3. **Import** - Bring in audio files
4. **Audio Mastering** - Professional processing
5. **Transcription** - Generate captions
6. **Video Version** - Create for YouTube
7. **Multi-Platform Export** - Different formats
8. **Distribution** - Publish everywhere

**Estimated time:** 20-30 minutes (excluding recording)
"""
        self.console.print(Panel(Markdown(overview), title="Podcast Workflow", border_style="cyan"))


class TutorialWorkflow(BaseWorkflow):
    """Tutorial and course creation workflow"""

    def __init__(self):
        super().__init__()
        self.steps = [
            {
                "title": "Create Tutorial Project",
                "description": "Set up a tutorial project structure",
                "command": 'sf new "Python Tutorial" --template tutorial',
                "explanation": "Creates structure for educational content"
            },
            {
                "title": "Screen Recording Setup",
                "description": "Configure screen recording",
                "command": "sf capture screen --audio --resolution 1080p",
                "explanation": "Sets up OBS or native screen recording"
            },
            {
                "title": "Record Content",
                "description": "Capture your tutorial",
                "interactive": True,
                "type": "checklist",
                "items": [
                    "Open necessary applications",
                    "Hide sensitive information",
                    "Start screen recording",
                    "Record your tutorial",
                    "Stop recording"
                ]
            },
            {
                "title": "Import Recording",
                "description": "Import screen recording",
                "command": "sf media import screen_recording.mp4",
                "explanation": "Imports and organizes recording"
            },
            {
                "title": "Edit Recording",
                "description": "Clean up the recording",
                "command": "sf ai edit recording.mp4 --remove-silence --remove-umms",
                "explanation": "AI-powered editing to remove pauses and filler words"
            },
            {
                "title": "Add Annotations",
                "description": "Enhance with graphics",
                "command": "sf effects compose 'Tutorial' --template lower_third",
                "explanation": "Adds titles, arrows, and highlights"
            },
            {
                "title": "Generate Chapters",
                "description": "Create chapter markers",
                "command": "sf ai analyze video.mp4 --generate-chapters",
                "explanation": "Automatically detects topic changes"
            },
            {
                "title": "Export for Platform",
                "description": "Render for your course platform",
                "command": "sf resolve export mp4 --preset tutorial --chapters",
                "explanation": "Exports with embedded chapter markers"
            }
        ]

    def _show_overview(self):
        """Show tutorial workflow overview"""
        overview = """
# Tutorial Creation Workflow

Create professional tutorials and course content:

1. **Project Setup** - Tutorial structure
2. **Screen Setup** - Configure recording
3. **Recording** - Capture content
4. **Import** - Organize footage
5. **AI Editing** - Remove silence/mistakes
6. **Annotations** - Add visual aids
7. **Chapters** - Create navigation
8. **Export** - Platform-optimized output

**Estimated time:** 15-20 minutes (excluding recording)
"""
        self.console.print(Panel(Markdown(overview), title="Tutorial Workflow", border_style="cyan"))


class ShortFormWorkflow(BaseWorkflow):
    """Short-form content workflow (TikTok, Reels, Shorts)"""

    def __init__(self):
        super().__init__()
        self.steps = [
            {
                "title": "Create Short-Form Project",
                "description": "Set up project for vertical video",
                "command": 'sf new "Viral Short" --template shorts',
                "explanation": "Creates 9:16 vertical project"
            },
            {
                "title": "Import Clips",
                "description": "Import your video clips",
                "command": "sf media import clips/ --organize",
                "explanation": "Organizes clips for quick editing"
            },
            {
                "title": "Create Vertical Timeline",
                "description": "Set up 9:16 timeline",
                "command": 'sf resolve create "Short" --profile vertical',
                "explanation": "Creates timeline for mobile viewing"
            },
            {
                "title": "Apply Trending Effects",
                "description": "Add popular effects",
                "command": "sf effects apply trending_pack video.mp4",
                "explanation": "Applies current trending effects and transitions"
            },
            {
                "title": "Add Captions",
                "description": "Generate and style captions",
                "command": "sf ai caption video.mp4 --style bold --position center",
                "explanation": "Creates eye-catching animated captions"
            },
            {
                "title": "Add Music",
                "description": "Add trending audio",
                "interactive": True,
                "type": "input",
                "prompt": "Music track name or path",
                "default": "trending_audio.mp3"
            },
            {
                "title": "Export for Platforms",
                "description": "Export for each platform",
                "command": "sf publish all --format vertical",
                "explanation": "Creates versions for TikTok, Reels, and Shorts"
            },
            {
                "title": "Schedule Posts",
                "description": "Plan your posting",
                "interactive": True,
                "type": "checklist",
                "items": [
                    "Upload to TikTok",
                    "Post to Instagram Reels",
                    "Upload YouTube Shorts",
                    "Cross-post to Twitter"
                ]
            }
        ]

    def _show_overview(self):
        """Show short-form workflow overview"""
        overview = """
# Short-Form Content Workflow

Create viral content for TikTok, Reels, and Shorts:

1. **Project Setup** - Vertical video project
2. **Import Clips** - Organize footage
3. **Vertical Timeline** - 9:16 format
4. **Trending Effects** - Popular styles
5. **Captions** - Auto-generated text
6. **Music** - Add trending audio
7. **Multi-Export** - Platform versions
8. **Distribution** - Post everywhere

**Estimated time:** 10-15 minutes
"""
        self.console.print(Panel(Markdown(overview), title="Short-Form Workflow", border_style="cyan"))


class MulticamWorkflow(BaseWorkflow):
    """Multi-camera production workflow"""

    def __init__(self):
        super().__init__()
        self.steps = [
            {
                "title": "Create Multicam Project",
                "description": "Set up multi-angle project",
                "command": 'sf new "Multicam Event" --template multicam',
                "explanation": "Creates structure for multiple camera angles"
            },
            {
                "title": "Import All Angles",
                "description": "Import footage from all cameras",
                "command": "sf media import --multicam cam1/ cam2/ cam3/",
                "explanation": "Imports and labels each camera angle"
            },
            {
                "title": "Sync Cameras",
                "description": "Synchronize all angles",
                "command": "sf multicam sync --method audio --auto",
                "explanation": "Uses audio waveforms to sync cameras"
            },
            {
                "title": "Create Multicam Sequence",
                "description": "Build multicam timeline",
                "command": "sf multicam create-sequence --layout quad",
                "explanation": "Creates sequence with all angles visible"
            },
            {
                "title": "Color Match",
                "description": "Match color between cameras",
                "command": "sf resolve color-match --reference cam1",
                "explanation": "Automatically matches color across angles"
            },
            {
                "title": "Switch Angles",
                "description": "Edit between angles",
                "interactive": True,
                "type": "checklist",
                "items": [
                    "Review all angles",
                    "Mark switch points",
                    "Create angle cuts",
                    "Add transitions"
                ]
            },
            {
                "title": "Export Master",
                "description": "Render final video",
                "command": "sf resolve export mp4 --preset master",
                "explanation": "Exports high-quality master file"
            }
        ]

    def _show_overview(self):
        """Show multicam workflow overview"""
        overview = """
# Multi-Camera Production Workflow

Professional multi-angle video production:

1. **Project Setup** - Multicam structure
2. **Import Angles** - All camera footage
3. **Sync Cameras** - Audio-based sync
4. **Multicam Sequence** - Combined timeline
5. **Color Matching** - Consistent look
6. **Angle Editing** - Switch between views
7. **Master Export** - Final render

**Estimated time:** 20-30 minutes
"""
        self.console.print(Panel(Markdown(overview), title="Multicam Workflow", border_style="cyan"))


def run_quickstart(workflow: Optional[str] = None):
    """Run the quick start guide"""
    guide = QuickStartGuide()
    guide.run(workflow)


if __name__ == "__main__":
    run_quickstart()