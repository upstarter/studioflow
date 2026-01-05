"""
Background Services for StudioFlow
Auto-transcription and auto-rough-cut generation with parallel processing
"""

import time
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

from studioflow.core.transcription import TranscriptionService
from studioflow.core.rough_cut import RoughCutEngine, CutStyle
from studioflow.core.audio_markers import AudioMarkerDetector
from studioflow.core.rough_cut_markers import detect_markers_in_clips


class JobStatus(str, Enum):
    """Job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TranscriptionJob:
    """Transcription job"""
    video_file: Path
    project_path: Path
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    transcript_path: Optional[Path] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['video_file'] = str(self.video_file)
        result['project_path'] = str(self.project_path)
        if self.transcript_path:
            result['transcript_path'] = str(self.transcript_path)
        result['status'] = self.status.value
        if self.started_at:
            result['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            result['completed_at'] = self.completed_at.isoformat()
        return result


@dataclass
class RoughCutJob:
    """Rough cut generation job"""
    footage_dir: Path
    project_path: Path
    style: str = "doc"
    use_audio_markers: bool = True
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    edl_path: Optional[Path] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['footage_dir'] = str(self.footage_dir)
        result['project_path'] = str(self.project_path)
        if self.edl_path:
            result['edl_path'] = str(self.edl_path)
        result['status'] = self.status.value
        if self.started_at:
            result['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            result['completed_at'] = self.completed_at.isoformat()
        return result


class BackgroundServices:
    """Background services for auto-transcription and rough-cut generation"""
    
    def __init__(self, max_workers: int = 4):
        """
        Args:
            max_workers: Maximum number of parallel transcription jobs
        """
        self.max_workers = max_workers
        self.running = False
        
        # Queues
        self.transcription_queue: Queue = Queue()
        self.rough_cut_queue: Queue = Queue()
        
        # Job tracking
        self.transcription_jobs: Dict[str, TranscriptionJob] = {}
        self.rough_cut_jobs: Dict[str, RoughCutJob] = {}
        
        # Watched directories (project_path -> footage_dir)
        self.watched_projects: Dict[Path, Path] = {}
        
        # Threads
        self.watcher_thread: Optional[threading.Thread] = None
        self.transcription_executor: Optional[ThreadPoolExecutor] = None
        self.rough_cut_thread: Optional[threading.Thread] = None
        
        # Services
        self.transcription_service = TranscriptionService()
        self.rough_cut_engine = RoughCutEngine()
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def watch_project(self, project_path: Path, footage_dir: Optional[Path] = None):
        """
        Start watching a project for new video files
        
        Args:
            project_path: Project root directory
            footage_dir: Footage directory (defaults to project_path/01_footage)
        """
        project_path = Path(project_path)
        if footage_dir is None:
            footage_dir = project_path / "01_footage"
        else:
            footage_dir = Path(footage_dir)
        
        with self.lock:
            self.watched_projects[project_path] = footage_dir
        
        # Scan existing files and queue missing transcripts
        self._scan_and_queue_transcriptions(footage_dir, project_path)
    
    def stop_watching(self, project_path: Path):
        """Stop watching a project"""
        with self.lock:
            self.watched_projects.pop(Path(project_path), None)
    
    def start(self):
        """Start background services"""
        if self.running:
            return
        
        self.running = True
        
        # Start transcription executor
        self.transcription_executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Start transcription worker threads
        for i in range(self.max_workers):
            thread = threading.Thread(
                target=self._transcription_worker,
                name=f"TranscriptionWorker-{i}",
                daemon=True
            )
            thread.start()
        
        # Start rough cut worker thread
        self.rough_cut_thread = threading.Thread(
            target=self._rough_cut_worker,
            name="RoughCutWorker",
            daemon=True
        )
        self.rough_cut_thread.start()
        
        # Start directory watcher thread
        self.watcher_thread = threading.Thread(
            target=self._directory_watcher,
            name="DirectoryWatcher",
            daemon=True
        )
        self.watcher_thread.start()
    
    def stop(self):
        """Stop background services"""
        self.running = False
        
        # Wait for queues to empty (with timeout)
        timeout = 30  # seconds
        start = time.time()
        
        while not self.transcription_queue.empty() and (time.time() - start) < timeout:
            time.sleep(0.5)
        
        if self.transcription_executor:
            self.transcription_executor.shutdown(wait=True, timeout=10)
    
    def _directory_watcher(self):
        """Watch directories for new video files"""
        last_scan: Dict[Path, Set[Path]] = {}
        
        while self.running:
            try:
                with self.lock:
                    projects = dict(self.watched_projects)
                
                for project_path, footage_dir in projects.items():
                    if not footage_dir.exists():
                        continue
                    
                    # Get all video files
                    video_files = set()
                    for ext in ['.mov', '.mp4', '.MOV', '.MP4', '.mxf', '.MXF']:
                        video_files.update(footage_dir.rglob(f"*{ext}"))
                    
                    # Check for new files or missing transcripts
                    last_files = last_scan.get(footage_dir, set())
                    new_files = video_files - last_files
                    
                    # Queue transcriptions for new files or files without transcripts
                    for video_file in video_files:
                        if self._needs_transcription(video_file):
                            job_key = str(video_file)
                            if job_key not in self.transcription_jobs:
                                job = TranscriptionJob(
                                    video_file=video_file,
                                    project_path=project_path
                                )
                                self.transcription_jobs[job_key] = job
                                self.transcription_queue.put(job)
                    
                    last_scan[footage_dir] = video_files
                
                # Sleep before next scan
                time.sleep(10)  # Scan every 10 seconds
                
            except Exception as e:
                # Log error but continue watching
                print(f"Error in directory watcher: {e}")
                time.sleep(5)
    
    def _needs_transcription(self, video_file: Path) -> bool:
        """Check if a video file needs transcription"""
        # Check if transcript already exists
        srt_path = video_file.with_suffix('.srt')
        if srt_path.exists():
            return False
        
        # Check if JSON transcript exists (for markers)
        json_path = video_file.parent / f"{video_file.stem}_transcript.json"
        if json_path.exists():
            return False
        
        return True
    
    def _transcription_worker(self):
        """Worker thread for transcription jobs"""
        while self.running:
            try:
                # Get job from queue (with timeout for clean shutdown)
                try:
                    job = self.transcription_queue.get(timeout=1)
                except Empty:
                    continue
                
                job_key = str(job.video_file)
                
                # Update job status
                with self.lock:
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.now()
                
                try:
                    # Transcribe with JSON output (for audio markers)
                    result = self.transcription_service.transcribe(
                        audio_path=job.video_file,
                        model="base",  # Use base model for speed
                        language="auto",
                        output_formats=["srt", "json"]
                    )
                    
                    if result.get("success"):
                        # Find generated transcript files
                        srt_path = job.video_file.with_suffix('.srt')
                        json_path = job.video_file.parent / f"{job.video_file.stem}_transcript.json"
                        
                        # Try alternative JSON path
                        if not json_path.exists():
                            json_path = job.video_file.parent / f"{job.video_file.stem}.json"
                        
                        with self.lock:
                            job.status = JobStatus.COMPLETED
                            job.completed_at = datetime.now()
                            job.transcript_path = srt_path if srt_path.exists() else None
                        
                        # Check if we should trigger rough cut generation
                        self._check_rough_cut_trigger(job.project_path, Path(job.video_file).parent)
                        
                    else:
                        with self.lock:
                            job.status = JobStatus.FAILED
                            job.completed_at = datetime.now()
                            job.error = result.get("error", "Transcription failed")
                
                except Exception as e:
                    with self.lock:
                        job.status = JobStatus.FAILED
                        job.completed_at = datetime.now()
                        job.error = str(e)
                
                finally:
                    self.transcription_queue.task_done()
            
            except Exception as e:
                print(f"Error in transcription worker: {e}")
                time.sleep(1)
    
    def _check_rough_cut_trigger(self, project_path: Path, footage_dir: Path):
        """Check if we should trigger rough cut generation"""
        # Check if all videos in directory have transcripts
        video_files = []
        for ext in ['.mov', '.mp4', '.MOV', '.MP4']:
            video_files.extend(footage_dir.rglob(f"*{ext}"))
        
        # Check if all have transcripts
        all_transcribed = True
        has_markers = False
        
        for video_file in video_files:
            srt_path = video_file.with_suffix('.srt')
            json_path = video_file.parent / f"{video_file.stem}_transcript.json"
            
            if not json_path.exists():
                json_path = video_file.parent / f"{video_file.stem}.json"
            
            if not srt_path.exists():
                all_transcribed = False
                break
            
            # Check for audio markers if JSON exists
            if json_path.exists() and not has_markers:
                try:
                    with open(json_path, 'r') as f:
                        transcript_data = json.load(f)
                    
                    # Quick check for markers
                    detector = AudioMarkerDetector()
                    markers = detector.detect_markers(transcript_data)
                    if markers:
                        has_markers = True
                except:
                    pass
        
        # Queue rough cut job if all transcribed
        if all_transcribed:
            job_key = str(footage_dir)
            if job_key not in self.rough_cut_jobs:
                job = RoughCutJob(
                    footage_dir=footage_dir,
                    project_path=project_path,
                    style="doc",  # Default, can be configured
                    use_audio_markers=has_markers
                )
                self.rough_cut_jobs[job_key] = job
                self.rough_cut_queue.put(job)
    
    def _rough_cut_worker(self):
        """Worker thread for rough cut generation"""
        while self.running:
            try:
                # Get job from queue
                try:
                    job = self.rough_cut_queue.get(timeout=1)
                except Empty:
                    continue
                
                job_key = str(job.footage_dir)
                
                # Update job status
                with self.lock:
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.now()
                
                try:
                    # Map style string to CutStyle enum
                    style_map = {
                        "doc": CutStyle.DOC,
                        "documentary": CutStyle.DOC,
                        "episode": CutStyle.EPISODE,
                        "interview": CutStyle.INTERVIEW,
                        "tutorial": CutStyle.EPISODE,
                    }
                    cut_style = style_map.get(job.style, CutStyle.DOC)
                    
                    # Generate rough cut
                    # Analyze clips first (transcripts already exist, skip auto-transcribe)
                    clips = self.rough_cut_engine.analyze_clips(
                        footage_dir=job.footage_dir,
                        auto_transcribe=False  # Transcripts already exist
                    )
                    
                    if not clips:
                        raise ValueError("No clips found in footage directory")
                    
                    # Create rough cut plan
                    # Note: create_rough_cut expects clips to be set on self.clips
                    # Set clips on engine instance first (analyze_clips already did this, but ensure it's set)
                    self.rough_cut_engine.clips = clips
                    use_smart = (cut_style == CutStyle.DOC)
                    plan = self.rough_cut_engine.create_rough_cut(
                        cut_style,
                        target_duration=None,  # Use default for style
                        use_smart_features=use_smart,
                        use_audio_markers=job.use_audio_markers
                    )
                    
                    # Export EDL
                    output_dir = job.project_path / "03_exports" / "rough_cuts"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    edl_path = output_dir / f"rough_cut_auto_{job.style}.edl"
                    # export_edl is an instance method
                    self.rough_cut_engine.export_edl(plan, edl_path)
                    
                    with self.lock:
                        job.status = JobStatus.COMPLETED
                        job.completed_at = datetime.now()
                        job.edl_path = edl_path
                
                except Exception as e:
                    with self.lock:
                        job.status = JobStatus.FAILED
                        job.completed_at = datetime.now()
                        job.error = str(e)
                
                finally:
                    self.rough_cut_queue.task_done()
            
            except Exception as e:
                print(f"Error in rough cut worker: {e}")
                time.sleep(1)
    
    def _scan_and_queue_transcriptions(self, footage_dir: Path, project_path: Path):
        """Scan directory and queue transcriptions for files without transcripts"""
        if not footage_dir.exists():
            return
        
        video_files = []
        for ext in ['.mov', '.mp4', '.MOV', '.MP4', '.mxf', '.MXF']:
            video_files.extend(footage_dir.rglob(f"*{ext}"))
        
        for video_file in video_files:
            if self._needs_transcription(video_file):
                job_key = str(video_file)
                if job_key not in self.transcription_jobs:
                    job = TranscriptionJob(
                        video_file=video_file,
                        project_path=project_path
                    )
                    self.transcription_jobs[job_key] = job
                    self.transcription_queue.put(job)
    
    def get_status(self) -> Dict:
        """Get status of all jobs"""
        with self.lock:
            transcription_status = {
                "pending": sum(1 for j in self.transcription_jobs.values() if j.status == JobStatus.PENDING),
                "running": sum(1 for j in self.transcription_jobs.values() if j.status == JobStatus.RUNNING),
                "completed": sum(1 for j in self.transcription_jobs.values() if j.status == JobStatus.COMPLETED),
                "failed": sum(1 for j in self.transcription_jobs.values() if j.status == JobStatus.FAILED),
            }
            
            rough_cut_status = {
                "pending": sum(1 for j in self.rough_cut_jobs.values() if j.status == JobStatus.PENDING),
                "running": sum(1 for j in self.rough_cut_jobs.values() if j.status == JobStatus.RUNNING),
                "completed": sum(1 for j in self.rough_cut_jobs.values() if j.status == JobStatus.COMPLETED),
                "failed": sum(1 for j in self.rough_cut_jobs.values() if j.status == JobStatus.FAILED),
            }
        
        return {
            "running": self.running,
            "watched_projects": len(self.watched_projects),
            "transcription": transcription_status,
            "rough_cut": rough_cut_status,
            "queue_sizes": {
                "transcription": self.transcription_queue.qsize(),
                "rough_cut": self.rough_cut_queue.qsize()
            }
        }
    
    def get_job_details(self) -> Dict:
        """Get detailed job information"""
        with self.lock:
            transcription_jobs = [job.to_dict() for job in self.transcription_jobs.values()]
            rough_cut_jobs = [job.to_dict() for job in self.rough_cut_jobs.values()]
        
        return {
            "transcription_jobs": transcription_jobs,
            "rough_cut_jobs": rough_cut_jobs
        }

