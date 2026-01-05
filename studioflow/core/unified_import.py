"""
Unified Import Pipeline
Complete end-to-end automation from SD card to ready-to-edit project
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import json
import logging
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from .config import get_config
from .state import StateManager
from .project import Project, ProjectManager, ProjectResult
from .auto_import import AutoImportService, CameraProfile
from .ffmpeg import FFmpegProcessor
from .transcription import TranscriptionService
from .audio_markers import AudioMarkerDetector, extract_segments_from_markers
from .rough_cut import RoughCutEngine, CutStyle
from .resolve_api import ResolveDirectAPI, FX30ProjectSettings
from .gpu_utils import get_gpu_detector

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Result of unified import pipeline"""
    success: bool
    project_path: Optional[Path] = None
    files_imported: int = 0
    files_normalized: int = 0
    proxies_created: int = 0
    transcripts_generated: int = 0
    markers_detected: int = 0
    segments_extracted: int = 0
    rough_cut_created: bool = False
    resolve_project_created: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class UnifiedImportPipeline:
    """Complete import pipeline from SD card to ready-to-edit project"""
    
    def __init__(self):
        self.config = get_config()
        self.state = StateManager()
        self.project_manager = ProjectManager()
        self.auto_import = AutoImportService()
        self.transcription_service = TranscriptionService()
        self.marker_detector = AudioMarkerDetector()
        self.rough_cut_engine = RoughCutEngine()
        
    def determine_project(self, mount_point: Path, codeword: Optional[str] = None) -> Tuple[Project, str]:
        """
        Determine target project using priority:
        1. Codeword provided (explicit)
        2. SD card label (if matches codeword pattern)
        3. Active project (StateManager)
        4. Auto-create with codeword or default
        
        Returns: (Project object, project_name)
        """
        today = datetime.now().strftime("%Y%m%d")
        
        # Try to get codeword from various sources
        if not codeword:
            # 1. Try SD card label
            codeword = self._read_sd_card_label(mount_point)
            
            # 2. Try active project (extract codeword from name)
            if not codeword and self.state.current_project:
                codeword = self._extract_codeword(self.state.current_project)
        
        # Default codeword if none found
        if not codeword:
            codeword = "import"  # Simple default
        
        # Generate project name: codeword-YYYYMMDD_Import
        project_name = f"{codeword}-{today}_Import"
        
        # Check if project exists
        existing_project = self.project_manager.get_project(project_name)
        if existing_project:
            console.print(f"[cyan]Using existing project: {project_name}[/cyan]")
            return existing_project, project_name
        
        # Create new project
        console.print(f"[green]Creating project: {project_name}[/green]")
        result = self.project_manager.create_project(
            project_name,
            template="youtube",
            platform="youtube"
        )
        
        if not result.success:
            raise RuntimeError(f"Failed to create project: {result.error}")
        
        # Set as active project
        self.state.current_project = project_name
        
        project = Project(project_name, result.project_path)
        return project, project_name
    
    def _read_sd_card_label(self, mount_point: Path) -> Optional[str]:
        """Read project codeword from SD card label"""
        try:
            # Try to read label from mount point parent
            # SD cards often have labels like "COMPLIANT_APE" or "EP001"
            import subprocess
            result = subprocess.run(
                ["lsblk", "-no", "LABEL", mount_point],
                capture_output=True,
                text=True,
                timeout=2
            )
            label = result.stdout.strip()
            
            if label and len(label) > 0:
                # Sanitize label for use as codeword
                codeword = label.lower().replace(" ", "_").replace("-", "_")
                # Remove invalid characters
                codeword = "".join(c for c in codeword if c.isalnum() or c == "_")
                if codeword:
                    console.print(f"[dim]Detected codeword from SD card label: {codeword}[/dim]")
                    return codeword
        except Exception as e:
            logger.debug(f"Could not read SD card label: {e}")
        
        return None
    
    def _extract_codeword(self, project_name: str) -> Optional[str]:
        """Extract codeword from project name (e.g., 'compliant_ape-20260104_Import' -> 'compliant_ape')"""
        if "-" in project_name:
            codeword = project_name.split("-")[0]
            return codeword
        return None
    
    def _import_from_ingest_pool(self, ingest_dir: Path, project_path: Path, camera_id: str) -> int:
        """Import files from ingest pool directly to project (skip duplicate copy)"""
        import shutil
        
        media_dir = project_path / "01_Media" / "Original" / camera_id
        media_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all video files in ingest pool
        video_files = []
        for ext in ['.mp4', '.mov', '.mxf', '.mts']:
            video_files.extend(ingest_dir.glob(f"*{ext}"))
            video_files.extend(ingest_dir.glob(f"*{ext.upper()}"))
        
        imported_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Copying from ingest pool...", total=len(video_files))
            
            for video_file in video_files:
                dest_file = media_dir / video_file.name
                
                # Skip if already exists
                if dest_file.exists():
                    progress.update(task, advance=1)
                    continue
                
                # Copy to project
                try:
                    shutil.copy2(video_file, dest_file)
                    imported_count += 1
                    console.print(f"  [green]✓[/green] {video_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to copy {video_file.name}: {e}")
                    console.print(f"  [yellow]⚠[/yellow] {video_file.name} (failed)")
                
                progress.update(task, advance=1)
        
        return imported_count
    
    def process_sd_card(
        self,
        source_path: Path,
        codeword: Optional[str] = None,
        from_ingest: bool = False,
        normalize_audio: bool = True,
        transcribe: bool = True,
        detect_markers: bool = True,
        generate_rough_cut: bool = False,  # On-demand by default
        setup_resolve: bool = False  # On-demand by default
    ) -> ImportResult:
        """
        Complete pipeline: SD card or ingest pool → Ready-to-edit project
        
        Processing Phases:
        - Phase 1 (Immediate): Import, Normalize, Proxies
        - Phase 2 (Background): Transcription, Marker Detection
        - Phase 3 (On-Demand): Rough Cut, Resolve Setup
        
        Args:
            source_path: Mount point of SD card OR ingest pool directory
            codeword: Project codeword (e.g., 'compliant_ape'). If None, auto-detect.
            from_ingest: If True, source_path is ingest pool (already copied). If False, source_path is SD card mount.
            normalize_audio: Normalize audio to -14 LUFS (Phase 1)
            transcribe: Generate transcripts (Phase 2)
            detect_markers: Detect audio markers (Phase 2)
            generate_rough_cut: Generate rough cut (Phase 3 - on-demand)
            setup_resolve: Setup Resolve project (Phase 3 - on-demand)
        """
        result = ImportResult(success=False)
        import_result = None
        
        try:
            # ============================================================
            # PHASE 1: IMMEDIATE PROCESSING (Import, Normalize, Proxies)
            # ============================================================
            console.print(f"\n[bold cyan]PHASE 1: Immediate Processing[/bold cyan]")
            
            # Step 1: Detect camera (only if from SD card, not ingest pool)
            if from_ingest:
                # For ingest pool, try to detect from file structure or use default
                camera_id = "FX30"  # Default, or detect from files
                profile = self.auto_import.cameras.get(camera_id, list(self.auto_import.cameras.values())[0])
                console.print(f"[cyan]Using camera profile: {profile.name}[/cyan]")
            else:
                try:
                    camera_id, profile = self.auto_import.detect_camera(source_path)
                    if not camera_id:
                        result.errors.append("Could not detect camera type")
                        logger.error("Camera detection failed")
                        return result
                    console.print(f"[green]✓ Detected camera: {profile.name}[/green]")
                except Exception as e:
                    result.errors.append(f"Camera detection failed: {e}")
                    logger.exception("Camera detection error")
                    return result
            
            # Step 2: Determine project
            try:
                project, project_name = self.determine_project(source_path, codeword)
                result.project_path = project.path
                console.print(f"[green]✓ Project: {project_name}[/green]")
            except Exception as e:
                result.errors.append(f"Project determination failed: {e}")
                logger.exception("Project determination error")
                return result
            
            # Step 3: Import media
            console.print(f"\n[bold]Step 1.1: Importing media...[/bold]")
            
            try:
                if from_ingest:
                    # Files already in ingest pool - copy directly to project
                    result.files_imported = self._import_from_ingest_pool(source_path, project.path, camera_id)
                else:
                    # Import from SD card (will copy to ingest pool, then project)
                    # Temporarily set projects_dir to use our project
                    original_projects_dir = self.auto_import.projects_dir
                    self.auto_import.projects_dir = project.path.parent
                    
                    # Override get_active_project to return our project
                    original_get_active = self.auto_import.get_active_project
                    self.auto_import.get_active_project = lambda: project.path
                    
                    try:
                        import_result = self.auto_import.import_media(source_path, camera_id, profile)
                        result.files_imported = import_result.get("files_imported", 0)
                    finally:
                        # Restore original methods
                        self.auto_import.projects_dir = original_projects_dir
                        self.auto_import.get_active_project = original_get_active
                
                if result.files_imported == 0:
                    result.warnings.append("No files imported")
                    logger.warning("No files imported from source")
                    # Continue - might be intentional
            except Exception as e:
                result.errors.append(f"Media import failed: {e}")
                logger.exception("Media import error")
                return result  # Critical error - cannot continue
            
            media_dir = project.path / "01_Media" / "Original" / camera_id
            imported_files = (
                list(media_dir.glob("*.mp4")) + 
                list(media_dir.glob("*.MP4")) + 
                list(media_dir.glob("*.mov")) + 
                list(media_dir.glob("*.MOV"))
            )
            
            if not imported_files:
                result.warnings.append("No video files found after import")
                logger.warning("No video files found")
                # Continue - might be intentional
            
            # Step 4: Normalize audio (Phase 1 - Immediate)
            if normalize_audio and imported_files:
                console.print(f"\n[bold]Step 1.2: Normalizing audio...[/bold]")
                try:
                    normalized_count = self._normalize_media(imported_files, project.path)
                    result.files_normalized = normalized_count
                except Exception as e:
                    result.warnings.append(f"Audio normalization failed: {e}")
                    logger.warning(f"Audio normalization error: {e}")
                    # Non-critical - continue
            
            # Step 5: Generate proxies (Phase 1 - Immediate)
            console.print(f"\n[bold]Step 1.3: Generating proxies...[/bold]")
            try:
                if from_ingest:
                    # Generate proxies after import (import_result doesn't exist)
                    proxy_count = self._generate_proxies(imported_files, project.path, profile)
                else:
                    # Proxies already generated by AutoImportService
                    proxy_count = import_result.get("proxies_created", 0) if import_result else 0
                    if proxy_count == 0:
                        # Fallback: generate proxies if not already done
                        proxy_count = self._generate_proxies(imported_files, project.path, profile)
                result.proxies_created = proxy_count
            except Exception as e:
                result.warnings.append(f"Proxy generation failed: {e}")
                logger.warning(f"Proxy generation error: {e}")
                # Non-critical - continue
            
            # ============================================================
            # PHASE 2: BACKGROUND PROCESSING (Transcription, Markers)
            # ============================================================
            if transcribe or detect_markers:
                console.print(f"\n[bold cyan]PHASE 2: Background Processing[/bold cyan]")
            
            # Step 6: Transcribe (Phase 2 - Background)
            if transcribe and imported_files:
                console.print(f"\n[bold]Step 2.1: Transcribing...[/bold]")
                try:
                    transcript_count = self._transcribe_media(imported_files, project.path)
                    result.transcripts_generated = transcript_count
                except Exception as e:
                    result.warnings.append(f"Transcription failed: {e}")
                    logger.warning(f"Transcription error: {e}")
                    # Non-critical - continue (markers won't work without transcripts)
            
            # Step 7: Detect markers (Phase 2 - Background)
            if detect_markers and transcribe and imported_files:
                console.print(f"\n[bold]Step 2.2: Detecting audio markers...[/bold]")
                try:
                    markers_count, segments_count = self._detect_markers(imported_files, project.path)
                    result.markers_detected = markers_count
                    result.segments_extracted = segments_count
                except Exception as e:
                    result.warnings.append(f"Marker detection failed: {e}")
                    logger.warning(f"Marker detection error: {e}")
                    # Non-critical - continue
            
            # ============================================================
            # PHASE 3: ON-DEMAND PROCESSING (Rough Cut, Resolve Setup)
            # ============================================================
            if generate_rough_cut or setup_resolve:
                console.print(f"\n[bold cyan]PHASE 3: On-Demand Processing[/bold cyan]")
            
            # Step 8: Generate rough cut (Phase 3 - On-Demand)
            if generate_rough_cut:
                console.print(f"\n[bold]Step 3.1: Generating rough cut...[/bold]")
                try:
                    if result.segments_extracted > 0:
                        rough_cut_created = self._generate_rough_cut(project.path)
                        result.rough_cut_created = rough_cut_created
                    else:
                        result.warnings.append("No segments extracted - skipping rough cut")
                        logger.info("Skipping rough cut - no segments available")
                except Exception as e:
                    result.warnings.append(f"Rough cut generation failed: {e}")
                    logger.warning(f"Rough cut generation error: {e}")
                    # Non-critical - continue
            
            # Step 9: Setup Resolve (Phase 3 - On-Demand)
            if setup_resolve:
                console.print(f"\n[bold]Step 3.2: Setting up Resolve project...[/bold]")
                try:
                    resolve_created = self._setup_resolve_project(project, project_name)
                    result.resolve_project_created = resolve_created
                except Exception as e:
                    result.warnings.append(f"Resolve setup failed: {e}")
                    logger.warning(f"Resolve setup error: {e}")
                    # Non-critical - continue
            
            # ============================================================
            # SUCCESS
            # ============================================================
            result.success = True
            console.print(f"\n[bold green]✅ Import complete![/bold green]")
            console.print(f"Project: {project_name}")
            console.print(f"Location: {project.path}")
            
            # Log summary
            if result.warnings:
                console.print(f"\n[yellow]⚠ Warnings: {len(result.warnings)}[/yellow]")
                for warning in result.warnings:
                    logger.warning(f"Import warning: {warning}")
            
        except Exception as e:
            # Critical error - log and notify
            result.errors.append(str(e))
            logger.exception("Import pipeline failed with critical error")
            console.print(f"[red]✗ Import failed: {e}[/red]")
            result.success = False
        
        return result
    
    def _normalize_media(self, media_files: List[Path], project_path: Path) -> int:
        """Normalize audio for all media files (parallel processing)"""
        normalized_dir = project_path / "01_Media" / "Normalized"
        normalized_dir.mkdir(parents=True, exist_ok=True)
        
        # Filter out already normalized files
        files_to_process = []
        for media_file in media_files:
            output_file = normalized_dir / f"{media_file.stem}_normalized{media_file.suffix}"
            if not output_file.exists():
                files_to_process.append((media_file, output_file))
        
        if not files_to_process:
            return len(media_files)  # All already normalized
        
        normalized_count = len(media_files) - len(files_to_process)  # Already done
        
        # Process in parallel (limit to 4 concurrent FFmpeg processes to avoid overwhelming system)
        max_workers = min(4, len(files_to_process))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Normalizing audio...", total=len(media_files))
            
            def normalize_single(args):
                media_file, output_file = args
                result = FFmpegProcessor.normalize_audio(media_file, output_file, target_lufs=-14.0)
                return (media_file.name, result.success)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(normalize_single, args): args for args in files_to_process}
                
                for future in as_completed(futures):
                    file_name, success = future.result()
                    if success:
                        normalized_count += 1
                        console.print(f"  [green]✓[/green] {file_name}")
                    else:
                        console.print(f"  [yellow]⚠[/yellow] {file_name} (skipped)")
                    progress.update(task, advance=1)
        
        return normalized_count
    
    def _transcribe_media(self, media_files: List[Path], project_path: Path) -> int:
        """Transcribe all media files (parallel processing, GPU-aware)"""
        transcript_dir = project_path / "02_Transcription"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        
        # Filter out already transcribed files
        files_to_process = []
        for media_file in media_files:
            json_path = transcript_dir / f"{media_file.stem}_transcript.json"
            srt_path = transcript_dir / f"{media_file.stem}.srt"
            if not (json_path.exists() and srt_path.exists()):
                files_to_process.append(media_file)
        
        if not files_to_process:
            return len(media_files)  # All already transcribed
        
        transcript_count = len(media_files) - len(files_to_process)  # Already done
        
        # GPU-aware parallel processing: limit concurrent GPU jobs to 1-2
        gpu = get_gpu_detector()
        if gpu.cuda_available:
            max_workers = 1  # Whisper on GPU: one at a time to avoid VRAM issues
        else:
            max_workers = min(2, len(files_to_process))  # CPU: can run 2 in parallel
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Transcribing...", total=len(media_files))
            
            def transcribe_single(media_file):
                # Transcribe with JSON output (for markers)
                result = self.transcription_service.transcribe(
                    media_file,
                    model="base",
                    output_formats=["srt", "json"]
                )
                
                if result and result.get("success"):
                    # Move transcript files to transcript_dir
                    import shutil
                    for ext in ["_transcript.json", ".srt"]:
                        source_file = media_file.parent / f"{media_file.stem}{ext}"
                        if source_file.exists():
                            dest_file = transcript_dir / source_file.name
                            if not dest_file.exists():
                                shutil.move(str(source_file), str(dest_file))
                    return (media_file.name, True)
                else:
                    return (media_file.name, False)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(transcribe_single, media_file): media_file for media_file in files_to_process}
                
                for future in as_completed(futures):
                    file_name, success = future.result()
                    if success:
                        transcript_count += 1
                        console.print(f"  [green]✓[/green] {file_name}")
                    else:
                        console.print(f"  [yellow]⚠[/yellow] {file_name} (failed)")
                    progress.update(task, advance=1)
        
        return transcript_count
    
    def _detect_markers(self, media_files: List[Path], project_path: Path) -> Tuple[int, int]:
        """Detect audio markers and extract segments"""
        transcript_dir = project_path / "02_Transcription"
        segments_dir = project_path / "03_Segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        
        total_markers = 0
        total_segments = 0
        
        for media_file in media_files:
            json_path = transcript_dir / f"{media_file.stem}_transcript.json"
            
            if not json_path.exists():
                continue
            
            try:
                # Load transcript
                with open(json_path) as f:
                    transcript = json.load(f)
                
                # Detect markers
                markers = self.marker_detector.detect_markers(transcript, media_file)
                
                if markers:
                    total_markers += len(markers)
                    
                    # Extract segments
                    segments = extract_segments_from_markers(
                        markers,
                        transcript,
                        clip_duration=None  # Will be calculated from media
                    )
                    
                    total_segments += len(segments)
                    
                    # Save segments info
                    segments_file = segments_dir / f"{media_file.stem}_segments.json"
                    segments_data = {
                        "source_file": str(media_file),
                        "markers": len(markers),
                        "segments": len(segments),
                        "segments": [
                            {
                                "start": seg["start"],
                                "end": seg["end"],
                                "marker_info": seg["marker_info"]
                            }
                            for seg in segments
                        ]
                    }
                    
                    with open(segments_file, "w") as f:
                        json.dump(segments_data, f, indent=2)
                    
                    # Actually cut video segments into separate files
                    clips_created = self._create_segment_clips(media_file, segments, segments_dir)
                    
                    console.print(f"  [green]✓[/green] {media_file.name}: {len(markers)} markers, {len(segments)} segments, {clips_created} clips")
            
            except Exception as e:
                logger.warning(f"Failed to detect markers for {media_file.name}: {e}")
                console.print(f"  [yellow]⚠[/yellow] {media_file.name} (marker detection failed)")
        
        return total_markers, total_segments
    
    def _create_segment_clips(self, media_file: Path, segments: List[Dict], segments_dir: Path) -> int:
        """Create actual video clip files from segments"""
        clips_created = 0
        
        for i, seg in enumerate(segments, 1):
            # Generate segment filename
            clip_stem = media_file.stem
            seg_num = i
            
            # Use order/step if available for naming
            if seg["marker_info"].get("order") is not None:
                seg_name = f"{clip_stem}_seg{seg_num:03d}_order{seg['marker_info']['order']}"
            elif seg["marker_info"].get("step") is not None:
                seg_name = f"{clip_stem}_seg{seg_num:03d}_step{seg['marker_info']['step']}"
            else:
                seg_name = f"{clip_stem}_seg{seg_num:03d}"
            
            output_segment = segments_dir / f"{seg_name}.mov"
            
            # Skip if already exists
            if output_segment.exists():
                clips_created += 1
                continue
            
            # Cut video segment (use GPU-accelerated encoding for precise cuts)
            duration = seg["end"] - seg["start"]
            result = FFmpegProcessor.cut_video(
                input_file=media_file,
                output_file=output_segment,
                start_time=seg["start"],
                duration=duration,
                reencode=True  # Re-encode for precise cuts (uses GPU if available)
            )
            
            if result.success:
                clips_created += 1
        
        return clips_created
    
    def _generate_proxies(self, media_files: List[Path], project_path: Path, profile: CameraProfile) -> int:
        """Generate proxies for media files"""
        proxy_dir = project_path / "01_Media" / "Proxy"
        proxy_dir.mkdir(parents=True, exist_ok=True)
        
        proxy_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Generating proxies...", total=len(media_files))
            
            for media_file in media_files:
                proxy_file = proxy_dir / f"{media_file.stem}_proxy.mov"
                
                if proxy_file.exists():
                    progress.update(task, advance=1)
                    proxy_count += 1
                    continue
                
                # Generate proxy using AutoImportService method
                try:
                    if self.auto_import.generate_proxy(media_file, proxy_file, profile):
                        proxy_count += 1
                        console.print(f"  [green]✓[/green] {media_file.name}")
                    else:
                        console.print(f"  [yellow]⚠[/yellow] {media_file.name} (failed)")
                except Exception as e:
                    logger.warning(f"Failed to generate proxy for {media_file.name}: {e}")
                    console.print(f"  [yellow]⚠[/yellow] {media_file.name} (error)")
                
                progress.update(task, advance=1)
        
        return proxy_count
    
    def _generate_rough_cut(self, project_path: Path) -> bool:
        """Generate rough cut from segments"""
        try:
            media_dir = project_path / "01_Media" / "Original"
            
            # Analyze clips
            clips = self.rough_cut_engine.analyze_clips(media_dir)
            
            if not clips:
                return False
            
            # Detect markers in clips
            from .rough_cut_markers import detect_markers_in_clips
            clips_with_markers = detect_markers_in_clips(clips)
            
            # Create rough cut with audio markers
            plan = self.rough_cut_engine.create_rough_cut(
                CutStyle.EPISODE,
                use_audio_markers=True
            )
            
            # Export EDL
            edl_path = project_path / "04_Timelines" / "rough_cut.edl"
            edl_path.parent.mkdir(parents=True, exist_ok=True)
            self.rough_cut_engine.export_edl(plan, edl_path)
            
            console.print(f"  [green]✓[/green] Rough cut: {edl_path}")
            return True
        
        except Exception as e:
            logger.warning(f"Failed to generate rough cut: {e}")
            return False
    
    def _setup_resolve_project(self, project: Project, project_name: str) -> bool:
        """
        Setup Resolve project with bins and media
        
        Auto-creates:
        - Project with FX30 settings
        - Standard bin structure
        - Does NOT auto-open (manual)
        """
        try:
            api = ResolveDirectAPI()
            
            if not api.is_connected():
                console.print("  [yellow]⚠[/yellow] Resolve not running (skipping)")
                logger.info("Resolve not running - skipping project setup")
                return False
            
            # Create project
            settings = FX30ProjectSettings()
            
            # Set library path (use /mnt/library/PROJECTS/ if exists, fallback to config)
            library_path = self.config.storage.library
            if library_path and library_path.exists():
                # If library_path is /mnt/library/PROJECTS, use it directly
                if library_path.name == "PROJECTS":
                    settings.working_folder = str(library_path)
                    settings.cache_path = str(library_path.parent / "CACHE")
                    settings.proxy_path = str(library_path.parent / "PROXIES")
                else:
                    # If library_path is /mnt/library, append PROJECTS
                    settings.working_folder = str(library_path / "PROJECTS")
                    settings.cache_path = str(library_path / "CACHE")
                    settings.proxy_path = str(library_path / "PROXIES")
            else:
                # Fallback to project's base directory
                settings.working_folder = str(project.path.parent)
                settings.cache_path = str(project.path / "Cache")
                settings.proxy_path = str(project.path / "01_Media" / "Proxy")
            
            # Create project (does not auto-open)
            success = api.create_project(project_name, settings, library_path)
            
            if not success:
                console.print(f"  [yellow]⚠[/yellow] Failed to create Resolve project")
                logger.warning("Failed to create Resolve project")
                return False
            
            # Auto-create bin structure
            try:
                bins = api.create_bin_structure()
                console.print(f"  [green]✓[/green] Created {len(bins)} bins")
                logger.info(f"Created {len(bins)} bins in Resolve project")
            except Exception as e:
                console.print(f"  [yellow]⚠[/yellow] Bin creation failed: {e}")
                logger.warning(f"Bin creation error: {e}")
                # Non-critical - continue
            
            # Import media (optional - can be done manually)
            try:
                media_dir = project.path / "01_Media" / "Original"
                if media_dir.exists():
                    # Find all video files
                    video_files = []
                    for ext in ['.mp4', '.mov', '.mxf', '.mts']:
                        video_files.extend(media_dir.rglob(f"*{ext}"))
                        video_files.extend(media_dir.rglob(f"*{ext.upper()}"))
                    
                    if video_files:
                        # Import to appropriate bins based on camera
                        for video_file in video_files[:10]:  # Limit to first 10 for now
                            camera_id = video_file.parent.name  # e.g., "FX30", "ZV-E10"
                            target_bin = f"01_MEDIA/A_ROLL" if camera_id in ["FX30", "ZV-E10"] else "01_MEDIA/B_ROLL"
                            api.import_media([video_file], target_bin)
                        console.print(f"  [green]✓[/green] Imported {min(len(video_files), 10)} clips")
            except Exception as e:
                console.print(f"  [yellow]⚠[/yellow] Media import failed: {e}")
                logger.warning(f"Media import error: {e}")
                # Non-critical - continue
            
            console.print(f"  [green]✓[/green] Resolve project created: {project_name}")
            console.print(f"  [dim]Note: Project will not auto-open (manual)[/dim]")
            logger.info(f"Resolve project setup complete: {project_name}")
            return True
        
        except Exception as e:
            logger.warning(f"Failed to setup Resolve project: {e}")
            console.print(f"  [yellow]⚠[/yellow] Resolve setup failed: {e}")
            return False

