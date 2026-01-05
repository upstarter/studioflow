"""
Auto-import service for camera SD cards
Detects camera type, imports media, organizes, creates proxies, and sets up Resolve
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


@dataclass
class CameraProfile:
    """Camera detection and settings"""
    name: str
    card_patterns: List[str]  # Paths to check on SD card
    file_patterns: List[str]  # File naming patterns
    color_space: str
    resolution: str
    fps: float
    proxy_codec: str = "DNxHD"
    proxy_resolution: str = "1920x1080"


class AutoImportService:
    """Handles automatic media import from camera cards"""

    def __init__(self):
        self.cameras = {
            "FX30": CameraProfile(
                name="Sony FX30",
                card_patterns=["PRIVATE/M4ROOT", "XROOT"],
                file_patterns=["C*.MP4", "C*.MXF"],
                color_space="S-Cinetone",
                resolution="3840x2160",
                fps=29.97,
                proxy_codec="DNxHD",
                proxy_resolution="1920x1080"
            ),
            "ZV-E10": CameraProfile(
                name="Sony ZV-E10",
                card_patterns=["DCIM/*MSDCF", "DCIM/100MSDCF"],
                file_patterns=["DSC*.MP4", "DSC*.JPG"],
                color_space="S-Cinetone",
                resolution="1920x1080",
                fps=29.97,
                proxy_codec="ProRes",
                proxy_resolution="1280x720"
            ),
            "A7IV": CameraProfile(
                name="Sony A7 IV",
                card_patterns=["DCIM/*MSDCF", "PRIVATE/M4ROOT"],
                file_patterns=["C*.MP4", "DSC*.ARW"],
                color_space="S-Log3",
                resolution="3840x2160",
                fps=29.97
            )
        }

        # Paths - use config system
        from .config import get_config
        config = get_config()
        self.ingest_pool = config.storage.ingest / "Camera" / "Pool"
        self.projects_dir = config.storage.active
        self.archive_dir = config.storage.archive
        # Don't create proxy_dir at init - use project-specific directories instead
        # self.proxy_dir = config.storage.render / "Proxies"

        # Ensure directories exist
        self.ingest_pool.mkdir(parents=True, exist_ok=True)
        # Don't create proxy_dir at init - may not have permissions
        # self.proxy_dir.mkdir(parents=True, exist_ok=True)

    def detect_camera(self, mount_point: Path) -> Optional[Tuple[str, CameraProfile]]:
        """
        Detect camera type from SD card structure
        Returns camera ID and profile
        """
        console.print(f"[cyan]Detecting camera from {mount_point}...[/cyan]")

        for camera_id, profile in self.cameras.items():
            for pattern in profile.card_patterns:
                # Handle wildcards in pattern
                if "*" in pattern:
                    base = pattern.split("*")[0]
                    check_path = mount_point / base
                    if check_path.exists():
                        # Check if any subdirectory matches
                        for item in check_path.iterdir():
                            if item.is_dir() and pattern.split("*")[1] in item.name:
                                console.print(f"[green]✓ Detected {profile.name}[/green]")
                                return camera_id, profile
                else:
                    check_path = mount_point / pattern
                    if check_path.exists():
                        console.print(f"[green]✓ Detected {profile.name}[/green]")
                        return camera_id, profile

        console.print("[yellow]⚠ Unknown camera type[/yellow]")
        return None, None

    def find_media_files(self, mount_point: Path, profile: CameraProfile) -> List[Path]:
        """Find all media files on the card matching camera patterns"""
        media_files = []

        for pattern in profile.file_patterns:
            # Search in common locations
            search_paths = [
                mount_point,
                mount_point / "DCIM",
                mount_point / "PRIVATE" / "M4ROOT" / "CLIP",
                mount_point / "XROOT" / "Clip"
            ]

            for search_path in search_paths:
                if search_path.exists():
                    media_files.extend(search_path.glob(f"**/{pattern}"))

        return sorted(media_files)

    def get_active_project(self) -> Path:
        """Get or create today's active project"""
        today = datetime.now().strftime("%Y%m%d")

        # Check for existing project today
        for project in self.projects_dir.glob(f"{today}_*"):
            if project.is_dir():
                console.print(f"[cyan]Using existing project: {project.name}[/cyan]")
                return project

        # Create new project
        project_name = f"{today}_Shoot"
        project_path = self.projects_dir / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        # Create standard directories
        (project_path / "01_MEDIA" / "Original").mkdir(parents=True, exist_ok=True)
        (project_path / "01_MEDIA" / "Proxy").mkdir(parents=True, exist_ok=True)
        (project_path / "02_Project").mkdir(parents=True, exist_ok=True)
        (project_path / "03_Render").mkdir(parents=True, exist_ok=True)

        console.print(f"[green]Created new project: {project_name}[/green]")
        return project_path

    def calculate_checksum(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate MD5 checksum for deduplication"""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()

    def copy_with_verification(self, source: Path, dest: Path) -> bool:
        """Copy file with checksum verification"""
        # Copy file
        shutil.copy2(source, dest)

        # Verify
        source_sum = self.calculate_checksum(source)
        dest_sum = self.calculate_checksum(dest)

        if source_sum == dest_sum:
            return True
        else:
            console.print(f"[red]✗ Checksum mismatch for {source.name}[/red]")
            dest.unlink()  # Remove corrupted copy
            return False

    def import_media(self, mount_point: Path, camera_id: str, profile: CameraProfile) -> Dict:
        """
        Main import function - the 5 features:
        1. Detect camera type ✓ (done before this)
        2. Copy to ingest pool
        3. Organize into project
        4. Generate proxies
        5. Create Resolve timeline
        """
        results = {
            "camera": profile.name,
            "files_imported": 0,
            "proxies_created": 0,
            "errors": []
        }

        # Get media files
        media_files = self.find_media_files(mount_point, profile)
        if not media_files:
            console.print("[yellow]No media files found on card[/yellow]")
            return results

        console.print(f"[cyan]Found {len(media_files)} media files[/cyan]")

        # Get active project
        project = self.get_active_project()
        media_dir = project / "01_MEDIA" / "Original" / camera_id
        proxy_dir = project / "01_MEDIA" / "Proxy"
        media_dir.mkdir(parents=True, exist_ok=True)
        proxy_dir.mkdir(parents=True, exist_ok=True)

        # Import manifest
        manifest = {
            "import_date": datetime.now().isoformat(),
            "camera": profile.name,
            "files": []
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:

            # Task 1: Import files
            import_task = progress.add_task(
                f"[cyan]Importing from {profile.name}...[/cyan]",
                total=len(media_files)
            )

            imported_videos = []

            for media_file in media_files:
                # Generate organized name
                timestamp = datetime.fromtimestamp(media_file.stat().st_mtime)
                organized_name = f"{camera_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{media_file.name}"

                # Check if already imported (deduplication)
                dest_path = media_dir / organized_name
                ingest_path = self.ingest_pool / organized_name

                if dest_path.exists():
                    console.print(f"[yellow]⊘ Skipping {media_file.name} (already imported)[/yellow]")
                else:
                    # Copy to ingest pool first
                    if not ingest_path.exists():
                        if self.copy_with_verification(media_file, ingest_path):
                            console.print(f"[green]✓ Imported to pool: {organized_name}[/green]")

                    # Then link to project
                    if ingest_path.exists():
                        shutil.copy2(ingest_path, dest_path)
                        results["files_imported"] += 1

                        # Track video files for proxy generation
                        if media_file.suffix.lower() in ['.mp4', '.mov', '.mxf']:
                            imported_videos.append(dest_path)

                        manifest["files"].append({
                            "original": str(media_file),
                            "imported": str(dest_path),
                            "checksum": self.calculate_checksum(dest_path),
                            "size": dest_path.stat().st_size
                        })

                progress.update(import_task, advance=1)

            # Task 2: Generate proxies (parallel)
            if imported_videos:
                proxy_task = progress.add_task(
                    "[cyan]Generating proxies...[/cyan]",
                    total=len(imported_videos)
                )

                # Filter out videos that already have proxies
                videos_to_process = [
                    video for video in imported_videos
                    if not (proxy_dir / f"{video.stem}_proxy.mov").exists()
                ]

                if videos_to_process:
                    # Generate proxies in parallel
                    max_workers = min(4, len(videos_to_process))  # Limit concurrent FFmpeg processes
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {
                            executor.submit(
                                self.generate_proxy,
                                video,
                                proxy_dir / f"{video.stem}_proxy.mov",
                                profile
                            ): video
                            for video in videos_to_process
                        }
                        
                        for future in concurrent.futures.as_completed(futures):
                            video = futures[future]
                            try:
                                if future.result():
                                    console.print(f"[green]✓ Proxy: {video.stem}_proxy.mov[/green]")
                                    results["proxies_created"] += 1
                                else:
                                    results["errors"].append(f"Failed to create proxy for {video.name}")
                            except Exception as e:
                                results["errors"].append(f"Error creating proxy for {video.name}: {e}")
                            
                            progress.update(proxy_task, advance=1)
                else:
                    # All proxies already exist
                    progress.update(proxy_task, completed=len(imported_videos))

        # Save manifest
        manifest_path = project / "01_MEDIA" / f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        # Task 3: Create Resolve timeline
        if imported_videos:
            self.create_resolve_timeline(project, imported_videos, profile)

        return results

    def generate_proxy(self, source: Path, dest: Path, profile: CameraProfile) -> bool:
        """Generate proxy file using ffmpeg"""
        try:
            cmd = [
                "ffmpeg", "-i", str(source),
                "-c:v", "dnxhd" if profile.proxy_codec == "DNxHD" else "prores",
                "-profile:v", "dnxhd_sq" if profile.proxy_codec == "DNxHD" else "0",
                "-s", profile.proxy_resolution,
                "-c:a", "pcm_s16le",
                "-ar", "48000",
                "-y", str(dest)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0

        except Exception as e:
            console.print(f"[red]Proxy generation error: {e}[/red]")
            return False

    def create_resolve_timeline(self, project: Path, videos: List[Path], profile: CameraProfile) -> bool:
        """Create DaVinci Resolve timeline with imported clips"""
        timeline_name = f"{project.name}_{profile.name.replace(' ', '_')}"

        # Create Resolve Python script
        resolve_script = f"""
import DaVinciResolveScript as dvr
resolve = dvr.scriptapp("Resolve")
pm = resolve.GetProjectManager()

# Create or open project
project = pm.CreateProject("{project.name}")
if not project:
    project = pm.LoadProject("{project.name}")

if project:
    mp = project.GetMediaPool()

    # Import media
    clips = mp.ImportMedia({[str(v) for v in videos]})

    # Create timeline
    timeline = mp.CreateTimelineFromClips("{timeline_name}", clips)

    # Set timeline settings
    timeline.SetSetting("timelineFrameRate", "{profile.fps}")
    timeline.SetSetting("timelineResolutionWidth", "{profile.resolution.split('x')[0]}")
    timeline.SetSetting("timelineResolutionHeight", "{profile.resolution.split('x')[1]}")

    print(f"Created timeline: {timeline_name}")
"""

        # Save and attempt to run
        script_path = project / "02_Project" / "create_timeline.py"
        script_path.parent.mkdir(parents=True, exist_ok=True)

        with open(script_path, 'w') as f:
            f.write(resolve_script)

        console.print(f"[cyan]Resolve timeline script saved to: {script_path}[/cyan]")
        console.print("[yellow]Run this script in Resolve's console to create the timeline[/yellow]")

        return True

    def process_device(self, device_path: str):
        """Main entry point called by systemd service"""
        mount_point = Path(device_path)

        if not mount_point.exists():
            console.print(f"[red]Mount point does not exist: {device_path}[/red]")
            return 1

        console.print(f"\n[bold cyan]🎬 StudioFlow Auto-Import[/bold cyan]")
        console.print(f"[cyan]Processing: {device_path}[/cyan]\n")

        # Detect camera
        camera_id, profile = self.detect_camera(mount_point)

        if not profile:
            console.print("[yellow]Cannot determine camera type, skipping import[/yellow]")
            return 1

        # Run import
        results = self.import_media(mount_point, camera_id, profile)

        # Summary
        console.print("\n[bold green]Import Complete![/bold green]")
        console.print(f"  Camera: {results['camera']}")
        console.print(f"  Files Imported: {results['files_imported']}")
        console.print(f"  Proxies Created: {results['proxies_created']}")

        if results['errors']:
            console.print(f"  [red]Errors: {len(results['errors'])}[/red]")
            for error in results['errors']:
                console.print(f"    - {error}")

        # Notification
        try:
            subprocess.run([
                "notify-send",
                "StudioFlow Import Complete",
                f"Imported {results['files_imported']} files from {results['camera']}"
            ])
        except:
            pass  # Ignore if notify-send not available

        return 0


def main():
    """CLI entry point for manual or automated import"""
    if len(sys.argv) < 2:
        console.print("[red]Usage: sf-auto-import <mount_point>[/red]")
        console.print("Example: sf-auto-import /path/to/sd-card")
        return 1

    service = AutoImportService()
    return service.process_device(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())