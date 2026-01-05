"""
Archive Utilities for StudioFlow
Best-practice project archiving with duplicate removal and cache cleanup
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

console = Console()


@dataclass
class ArchiveAnalysis:
    """Results of project archive analysis"""
    project_path: Path
    total_size: int = 0
    file_count: int = 0
    duplicate_sets: int = 0
    duplicate_waste: int = 0
    cache_size: int = 0
    removable_files: List[Path] = field(default_factory=list)
    duplicate_files: List[Tuple[Path, List[Path]]] = field(default_factory=list)
    cache_dirs: List[Path] = field(default_factory=list)

    @property
    def potential_savings(self) -> int:
        return self.duplicate_waste + self.cache_size

    @property
    def savings_percent(self) -> float:
        if self.total_size == 0:
            return 0
        return (self.potential_savings / self.total_size) * 100

    def human_size(self, size: int) -> str:
        """Convert bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


# Directories that can be safely removed (regeneratable)
REMOVABLE_DIRS = [
    "CacheClip",
    "OptimizedMedia",
    "ProxyMedia",
    "RenderCache",
    "ResolveCache",
    ".gallery",
    ".Trash-1000",
    "__MACOSX",
    ".cache",
]

# Files that can be safely removed
REMOVABLE_FILES = [
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "._.DS_Store",
]


def check_jdupes() -> bool:
    """Check if jdupes is installed"""
    try:
        subprocess.run(["jdupes", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def analyze_project(project_path: Path) -> ArchiveAnalysis:
    """
    Analyze a project for archiving

    Returns analysis with:
    - Total size and file count
    - Duplicate files and waste
    - Cache directories
    - Potential savings
    """
    analysis = ArchiveAnalysis(project_path=project_path)

    console.print(f"[cyan]Analyzing:[/cyan] {project_path}")

    # Step 1: Calculate total size and file count
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task("Counting files...", total=None)

        for file in project_path.rglob("*"):
            if file.is_file():
                try:
                    analysis.file_count += 1
                    analysis.total_size += file.stat().st_size
                except (OSError, PermissionError):
                    pass

    console.print(f"  Total: {analysis.human_size(analysis.total_size)} ({analysis.file_count} files)")

    # Step 2: Find cache directories
    console.print("  Scanning for cache directories...")
    for dir_name in REMOVABLE_DIRS:
        for found_dir in project_path.rglob(dir_name):
            if found_dir.is_dir():
                dir_size = sum(f.stat().st_size for f in found_dir.rglob("*") if f.is_file())
                analysis.cache_dirs.append(found_dir)
                analysis.cache_size += dir_size

    if analysis.cache_dirs:
        console.print(f"  [yellow]Cache found:[/yellow] {analysis.human_size(analysis.cache_size)} in {len(analysis.cache_dirs)} directories")

    # Step 3: Find removable files
    for file_name in REMOVABLE_FILES:
        for found_file in project_path.rglob(file_name):
            if found_file.is_file():
                analysis.removable_files.append(found_file)

    if analysis.removable_files:
        console.print(f"  [yellow]Junk files:[/yellow] {len(analysis.removable_files)} files")

    # Step 4: Find duplicates using jdupes
    if check_jdupes():
        console.print("  Scanning for duplicates...")
        try:
            result = subprocess.run(
                ["jdupes", "-r", "-S", str(project_path)],
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse jdupes output
            current_size = 0
            current_group = []

            for line in result.stdout.split('\n'):
                if 'bytes each' in line:
                    # New duplicate group
                    if current_group and len(current_group) > 1:
                        # Store previous group (keep first, rest are duplicates)
                        keep = Path(current_group[0])
                        dupes = [Path(f) for f in current_group[1:]]
                        analysis.duplicate_files.append((keep, dupes))
                        analysis.duplicate_waste += current_size * len(dupes)

                    # Parse size from line like "12345 bytes each:"
                    try:
                        current_size = int(line.split()[0])
                    except (ValueError, IndexError):
                        current_size = 0
                    current_group = []
                    analysis.duplicate_sets += 1
                elif line.strip() and not line.startswith(' '):
                    current_group.append(line.strip())

            # Don't forget last group
            if current_group and len(current_group) > 1:
                keep = Path(current_group[0])
                dupes = [Path(f) for f in current_group[1:]]
                analysis.duplicate_files.append((keep, dupes))
                analysis.duplicate_waste += current_size * len(dupes)

            if analysis.duplicate_sets > 0:
                console.print(f"  [yellow]Duplicates:[/yellow] {analysis.duplicate_sets} sets, {analysis.human_size(analysis.duplicate_waste)} wasted")

        except subprocess.TimeoutExpired:
            console.print("  [red]Duplicate scan timed out[/red]")
        except Exception as e:
            console.print(f"  [red]Duplicate scan failed:[/red] {e}")
    else:
        console.print("  [dim]Install jdupes for duplicate detection: sudo apt install jdupes[/dim]")

    return analysis


def display_analysis(analysis: ArchiveAnalysis):
    """Display analysis results in a nice table"""
    table = Table(title="Archive Analysis", show_header=True)
    table.add_column("Category", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("Details", style="dim")

    table.add_row(
        "Total Project",
        analysis.human_size(analysis.total_size),
        f"{analysis.file_count} files"
    )

    if analysis.cache_size > 0:
        table.add_row(
            "Cache (removable)",
            f"[red]-{analysis.human_size(analysis.cache_size)}[/red]",
            f"{len(analysis.cache_dirs)} directories"
        )

    if analysis.duplicate_waste > 0:
        table.add_row(
            "Duplicates (removable)",
            f"[red]-{analysis.human_size(analysis.duplicate_waste)}[/red]",
            f"{analysis.duplicate_sets} duplicate sets"
        )

    if analysis.removable_files:
        junk_size = sum(f.stat().st_size for f in analysis.removable_files if f.exists())
        table.add_row(
            "Junk files",
            f"[red]-{analysis.human_size(junk_size)}[/red]",
            f"{len(analysis.removable_files)} files"
        )

    table.add_row(
        "[bold]After cleanup[/bold]",
        f"[green]{analysis.human_size(analysis.total_size - analysis.potential_savings)}[/green]",
        f"[green]{analysis.savings_percent:.1f}% smaller[/green]"
    )

    console.print(table)


def cleanup_project(
    project_path: Path,
    remove_duplicates: bool = True,
    remove_cache: bool = True,
    remove_junk: bool = True,
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Clean up a project before archiving

    Args:
        project_path: Path to project
        remove_duplicates: Remove duplicate files (keep first occurrence)
        remove_cache: Remove cache/proxy/optimized directories
        remove_junk: Remove .DS_Store, Thumbs.db, etc.
        dry_run: If True, don't actually delete anything

    Returns:
        Dict with bytes_removed and files_removed counts
    """
    stats = {"bytes_removed": 0, "files_removed": 0, "dirs_removed": 0}
    action = "[dim]would remove[/dim]" if dry_run else "removed"

    # Step 1: Remove junk files
    if remove_junk:
        console.print("\n[bold]Removing junk files...[/bold]")
        for file_name in REMOVABLE_FILES:
            for found_file in project_path.rglob(file_name):
                if found_file.is_file():
                    try:
                        size = found_file.stat().st_size
                        if not dry_run:
                            found_file.unlink()
                        stats["bytes_removed"] += size
                        stats["files_removed"] += 1
                    except (OSError, PermissionError) as e:
                        console.print(f"  [red]Error:[/red] {found_file}: {e}")

        if stats["files_removed"] > 0:
            console.print(f"  {action} {stats['files_removed']} junk files")

    # Step 2: Remove cache directories
    if remove_cache:
        console.print("\n[bold]Removing cache directories...[/bold]")
        for dir_name in REMOVABLE_DIRS:
            for found_dir in list(project_path.rglob(dir_name)):
                if found_dir.is_dir() and found_dir.exists():
                    try:
                        dir_size = sum(f.stat().st_size for f in found_dir.rglob("*") if f.is_file())
                        dir_files = sum(1 for f in found_dir.rglob("*") if f.is_file())

                        if not dry_run:
                            shutil.rmtree(found_dir)

                        stats["bytes_removed"] += dir_size
                        stats["files_removed"] += dir_files
                        stats["dirs_removed"] += 1
                        console.print(f"  {action}: {found_dir.relative_to(project_path)}")
                    except (OSError, PermissionError) as e:
                        console.print(f"  [red]Error:[/red] {found_dir}: {e}")

        if stats["dirs_removed"] > 0:
            console.print(f"  {action} {stats['dirs_removed']} cache directories")

    # Step 3: Remove duplicates
    if remove_duplicates and check_jdupes():
        console.print("\n[bold]Removing duplicates...[/bold]")
        if dry_run:
            # Just show what would be removed
            result = subprocess.run(
                ["jdupes", "-r", "-S", str(project_path)],
                capture_output=True,
                text=True
            )
            dupe_count = result.stdout.count("bytes each")
            console.print(f"  {action} duplicates from {dupe_count} sets")
        else:
            # Actually remove duplicates (keep first occurrence)
            result = subprocess.run(
                ["jdupes", "-r", "-d", "-N", str(project_path)],
                capture_output=True,
                text=True
            )
            # Count removed files from output
            removed = result.stdout.count("Deleted")
            stats["files_removed"] += removed
            if removed > 0:
                console.print(f"  Removed {removed} duplicate files")

    return stats


def archive_project(
    project_path: Path,
    destination: Path,
    cleanup: bool = True,
    verify: bool = True,
    delete_source: bool = False
) -> bool:
    """
    Archive a project to destination

    Args:
        project_path: Source project path
        destination: Destination directory (project will be copied inside)
        cleanup: Run cleanup before archiving
        verify: Verify transfer with rsync checksum
        delete_source: Delete source after successful archive

    Returns:
        True if successful
    """
    project_name = project_path.name
    dest_path = destination / project_name

    console.print(Panel(f"Archiving: {project_name}", style="bold blue"))
    console.print(f"  From: {project_path}")
    console.print(f"  To:   {dest_path}")

    # Step 1: Cleanup if requested
    if cleanup:
        console.print("\n[bold cyan]Step 1: Cleanup[/bold cyan]")
        analysis = analyze_project(project_path)
        display_analysis(analysis)

        if analysis.potential_savings > 0:
            cleanup_project(project_path)
            # Recalculate size
            new_size = sum(f.stat().st_size for f in project_path.rglob("*") if f.is_file())
            console.print(f"\n[green]Cleaned size: {analysis.human_size(new_size)}[/green]")

    # Step 2: Transfer
    console.print("\n[bold cyan]Step 2: Transfer[/bold cyan]")

    # Create destination directory
    destination.mkdir(parents=True, exist_ok=True)

    # Use rsync for reliable transfer
    rsync_args = [
        "rsync", "-av", "--progress",
        "--no-group",  # Avoid NAS permission issues
        str(project_path) + "/",
        str(dest_path) + "/"
    ]

    if verify:
        rsync_args.insert(2, "--checksum")

    try:
        result = subprocess.run(rsync_args, check=True)
        console.print(f"\n[green]Transfer complete![/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]Transfer failed:[/red] {e}")
        return False

    # Step 3: Verify
    if verify:
        console.print("\n[bold cyan]Step 3: Verify[/bold cyan]")
        # Quick verification - compare file counts
        src_count = sum(1 for _ in project_path.rglob("*") if _.is_file())
        dst_count = sum(1 for _ in dest_path.rglob("*") if _.is_file())

        if src_count == dst_count:
            console.print(f"  [green]Verified: {src_count} files[/green]")
        else:
            console.print(f"  [red]Mismatch: source={src_count}, dest={dst_count}[/red]")
            return False

    # Step 4: Create archive manifest
    manifest = {
        "project_name": project_name,
        "archived_at": datetime.now().isoformat(),
        "source_path": str(project_path),
        "archive_path": str(dest_path),
        "file_count": sum(1 for _ in dest_path.rglob("*") if _.is_file()),
        "total_size": sum(f.stat().st_size for f in dest_path.rglob("*") if f.is_file())
    }

    manifest_path = dest_path / "ARCHIVE_MANIFEST.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    console.print(f"  Created manifest: {manifest_path.name}")

    # Step 5: Delete source if requested
    if delete_source:
        console.print("\n[bold cyan]Step 4: Cleanup source[/bold cyan]")
        try:
            shutil.rmtree(project_path)
            console.print(f"  [green]Deleted source: {project_path}[/green]")
        except Exception as e:
            console.print(f"  [red]Failed to delete source:[/red] {e}")

    console.print(Panel("[green]Archive complete![/green]", style="bold green"))
    return True


# Preset destinations
ARCHIVE_DESTINATIONS = {
    "deepfreeze": "/mnt/nas/DeepFreeze/VIDEO/COMPLETED_PROJECTS",
    "archive": "/mnt/nas/Archive/Projects",
    "archive_video": "/mnt/nas/ArchiveVideo/PROJECT_BACKUPS",
}


def get_destination_path(destination: str, project_type: str = "DOCS") -> Path:
    """
    Get full destination path based on preset or custom path

    Args:
        destination: Preset name (deepfreeze, archive) or custom path
        project_type: DOCS, EPISODES, FILMS

    Returns:
        Full destination path
    """
    if destination in ARCHIVE_DESTINATIONS:
        base = Path(ARCHIVE_DESTINATIONS[destination])
        return base / project_type
    else:
        return Path(destination)
