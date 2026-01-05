"""
Smart Project Context
Auto-detects project structure and suggests appropriate files for commands
"""

from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ProjectContext:
    """Current project context"""
    project_path: Optional[Path] = None
    project_name: Optional[str] = None
    project_type: Optional[str] = None  # EPISODES, DOCS, FILMS

    # Detected content locations
    unsorted_footage: Optional[Path] = None
    a_roll: Optional[Path] = None
    b_roll: Optional[Path] = None
    audio: Optional[Path] = None
    exports: Optional[Path] = None

    # Workflow state
    has_footage: bool = False
    has_normalized: bool = False
    has_transcripts: bool = False
    has_exports: bool = False


class ProjectContextManager:
    """Detects and manages project context for smart command defaults"""

    # Known project root patterns
    PROJECT_ROOTS = [
        "/mnt/studio/PROJECTS",
        Path.home() / "Videos" / "StudioFlow" / "Projects",
        Path.home() / "StudioFlow",
    ]

    # Standard folder structure
    FOLDER_STRUCTURE = {
        "footage": "01_footage",
        "audio": "02_audio",
        "graphics": "03_graphics",
        "projects": "04_projects",
        "exports": "05_exports",
        "archive": "06_archive",
    }

    FOOTAGE_SUBFOLDERS = ["00_UNSORTED", "A_ROLL", "B_ROLL", "INTERVIEWS", "ARCHIVAL"]

    @classmethod
    def detect_context(cls, from_path: Optional[Path] = None) -> ProjectContext:
        """Detect project context from current directory or given path"""
        ctx = ProjectContext()

        search_path = Path(from_path) if from_path else Path.cwd()

        # Walk up to find project root
        project_path = cls._find_project_root(search_path)

        if not project_path:
            return ctx

        ctx.project_path = project_path
        ctx.project_name = project_path.name

        # Detect project type from parent folder
        parent_name = project_path.parent.name
        if parent_name in ["EPISODES", "DOCS", "FILMS"]:
            ctx.project_type = parent_name

        # Find content folders
        footage_dir = project_path / cls.FOLDER_STRUCTURE["footage"]
        if footage_dir.exists():
            ctx.unsorted_footage = footage_dir / "00_UNSORTED"
            ctx.a_roll = footage_dir / "A_ROLL"
            ctx.b_roll = footage_dir / "B_ROLL"

        ctx.audio = project_path / cls.FOLDER_STRUCTURE["audio"]
        ctx.exports = project_path / cls.FOLDER_STRUCTURE["exports"]

        # Check workflow state
        ctx.has_footage = cls._has_media_files(ctx.unsorted_footage) or cls._has_media_files(ctx.a_roll)
        ctx.has_normalized = cls._has_files_matching(ctx.a_roll, "*_normalized.*")
        ctx.has_transcripts = cls._has_files_matching(project_path, "*.srt") or cls._has_files_matching(project_path, "*.vtt")
        ctx.has_exports = cls._has_media_files(ctx.exports)

        return ctx

    @classmethod
    def _find_project_root(cls, start_path: Path) -> Optional[Path]:
        """Walk up directory tree to find project root"""
        current = start_path.resolve()

        # Check if we're already in a project
        while current != current.parent:
            # Project has characteristic folders
            if (current / "01_footage").exists() or (current / "04_projects").exists():
                return current

            # Check if parent is a known project root
            for root in cls.PROJECT_ROOTS:
                root = Path(root)
                if root.exists() and current.parent.parent == root:
                    return current

            current = current.parent

        return None

    @classmethod
    def _has_media_files(cls, path: Optional[Path]) -> bool:
        """Check if path contains media files"""
        if not path or not path.exists():
            return False

        media_exts = {'.mov', '.mp4', '.mxf', '.avi', '.mkv', '.wav', '.mp3'}
        for f in path.iterdir():
            if f.suffix.lower() in media_exts:
                return True
        return False

    @classmethod
    def _has_files_matching(cls, path: Optional[Path], pattern: str) -> bool:
        """Check if path contains files matching pattern"""
        if not path or not path.exists():
            return False
        return len(list(path.rglob(pattern))) > 0

    @classmethod
    def get_files_for_command(cls, command: str, ctx: Optional[ProjectContext] = None) -> Tuple[List[Path], str]:
        """
        Get appropriate files for a command based on context.
        Returns (files, description)
        """
        if ctx is None:
            ctx = cls.detect_context()

        if not ctx.project_path:
            return [], "No project detected"

        media_exts = ['*.mov', '*.mp4', '*.mxf', '*.avi']

        if command == "transcribe":
            # Prefer normalized A_ROLL, fall back to unsorted
            if ctx.a_roll and ctx.a_roll.exists():
                files = []
                for ext in media_exts:
                    files.extend(ctx.a_roll.glob(ext))
                if files:
                    return sorted(files), f"A_ROLL footage ({len(files)} files)"

            if ctx.unsorted_footage and ctx.unsorted_footage.exists():
                files = []
                for ext in media_exts:
                    files.extend(ctx.unsorted_footage.glob(ext))
                if files:
                    return sorted(files), f"Unsorted footage ({len(files)} files)"

        elif command == "fix-lufs":
            # Find files that haven't been normalized yet
            if ctx.unsorted_footage and ctx.unsorted_footage.exists():
                files = []
                for ext in media_exts:
                    for f in ctx.unsorted_footage.glob(ext):
                        if "_normalized" not in f.name:
                            files.append(f)
                if files:
                    return sorted(files), f"Footage needing normalization ({len(files)} files)"

        elif command == "check-lufs":
            # Check any video/audio files
            for folder in [ctx.a_roll, ctx.unsorted_footage]:
                if folder and folder.exists():
                    files = []
                    for ext in media_exts:
                        files.extend(folder.glob(ext))
                    if files:
                        folder_name = folder.name
                        return sorted(files), f"{folder_name} footage ({len(files)} files)"

        elif command == "analyze":
            # Prefer A_ROLL for analysis
            for folder in [ctx.a_roll, ctx.unsorted_footage]:
                if folder and folder.exists() and cls._has_media_files(folder):
                    return [folder], f"{folder.name} folder"

        elif command == "sanitize-names":
            # Check folders with files that need sanitizing
            import re
            for folder in [ctx.unsorted_footage, ctx.a_roll]:
                if folder and folder.exists():
                    needs_sanitize = []
                    for f in folder.iterdir():
                        if f.is_file() and re.search(r'[\s\(\)\[\]]', f.name):
                            needs_sanitize.append(f)
                    if needs_sanitize:
                        return [folder], f"{folder.name} ({len(needs_sanitize)} files need renaming)"

        elif command == "magic":
            # Use best available footage folder
            for folder in [ctx.a_roll, ctx.unsorted_footage]:
                if folder and folder.exists() and cls._has_media_files(folder):
                    return [folder], f"{folder.name} footage"

        elif command in ["rough-cut", "rough_cut"]:
            # Use A_ROLL if has transcripts, otherwise unsorted
            for folder in [ctx.a_roll, ctx.unsorted_footage]:
                if folder and folder.exists() and cls._has_media_files(folder):
                    # Check for transcripts
                    has_srt = len(list(folder.glob("*.srt"))) > 0
                    if has_srt:
                        return [folder], f"{folder.name} with transcripts"
                    return [folder], f"{folder.name} footage"

        return [], "No matching files found"

    @classmethod
    def suggest_next_step(cls, ctx: Optional[ProjectContext] = None) -> str:
        """Suggest the next workflow step based on current state"""
        if ctx is None:
            ctx = cls.detect_context()

        if not ctx.project_path:
            return "No project detected. Create one with: sf doc <number> <title>"

        if not ctx.has_footage:
            return "Import footage: sf import-media /path/to/source"

        if ctx.unsorted_footage and cls._has_media_files(ctx.unsorted_footage):
            if not ctx.has_normalized:
                return "Normalize audio: sf fix-lufs (auto-detects footage)"

        if not ctx.has_transcripts and ctx.has_footage:
            return "Transcribe footage: sf transcribe (auto-detects footage)"

        if ctx.has_footage and ctx.has_transcripts:
            return "Create rough cut: sf magic or open in Resolve"

        return "Project ready for editing"


def get_context() -> ProjectContext:
    """Get current project context"""
    return ProjectContextManager.detect_context()


def get_files_for(command: str) -> Tuple[List[Path], str]:
    """Get files appropriate for a command"""
    return ProjectContextManager.get_files_for_command(command)
