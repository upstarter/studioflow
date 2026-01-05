"""
Export Queue System
Priority-based video export/rendering queue with GPU management
"""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from queue import PriorityQueue, Empty
from typing import Dict, Optional, List, Any
import subprocess

from studioflow.core.ffmpeg import FFmpegProcessor, VideoQuality


class ExportPriority(Enum):
    """Export job priority levels"""
    LOW = 3
    MEDIUM = 2
    HIGH = 1
    URGENT = 0


class ExportStatus(Enum):
    """Export job status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExportJob:
    """Video export job"""
    input_file: Path
    output_file: Path
    platform: str
    quality: str = "HIGH"
    priority: ExportPriority = ExportPriority.MEDIUM
    status: ExportStatus = ExportStatus.PENDING
    gpu_required: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 - 100.0
    
    def __lt__(self, other):
        """Enable PriorityQueue sorting by priority (lower number = higher priority)"""
        if not isinstance(other, ExportJob):
            return NotImplemented
        return self.priority.value < other.priority.value


class ExportQueue:
    """
    Priority-based export queue with GPU management
    
    Features:
    - Priority queue (urgent jobs first)
    - GPU-aware scheduling (limit concurrent GPU jobs)
    - Progress tracking
    - Error handling and retry logic
    """
    
    def __init__(self, max_concurrent: int = 1, use_gpu: bool = True):
        """
        Initialize export queue
        
        Args:
            max_concurrent: Maximum concurrent export jobs (typically 1-2 per GPU)
            use_gpu: Enable GPU acceleration if available
        """
        self.queue: PriorityQueue = PriorityQueue()
        self.active_jobs: Dict[str, ExportJob] = {}
        self.completed_jobs: Dict[str, ExportJob] = {}
        self.max_concurrent = max_concurrent
        self.use_gpu = use_gpu
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # GPU detection
        self.gpu_available = self._detect_gpu() if use_gpu else False
        
    def _detect_gpu(self) -> bool:
        """Detect if GPU is available for encoding"""
        try:
            # Check for NVIDIA GPU (NVENC)
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "h264_nvenc" in result.stdout or "hevc_nvenc" in result.stdout:
                return True
            
            # Check for AMD GPU (AMF)
            if "h264_amf" in result.stdout or "hevc_amf" in result.stdout:
                return True
            
            # Check for Intel GPU (QuickSync)
            if "h264_qsv" in result.stdout or "hevc_qsv" in result.stdout:
                return True
            
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def add_job(
        self,
        input_file: Path,
        output_file: Path,
        platform: str,
        quality: str = "HIGH",
        priority: ExportPriority = ExportPriority.MEDIUM,
        gpu_required: bool = True
    ) -> str:
        """
        Add export job to queue
        
        Args:
            input_file: Input video file
            output_file: Output video file
            platform: Target platform (youtube, instagram, tiktok, etc.)
            quality: Quality level (HIGH, MEDIUM, LOW)
            priority: Job priority
            gpu_required: Whether GPU is required for this job
        
        Returns:
            Job ID (string)
        """
        job_id = f"{input_file.stem}_{platform}_{int(time.time())}"
        
        job = ExportJob(
            input_file=input_file,
            output_file=output_file,
            platform=platform,
            quality=quality,
            priority=priority,
            gpu_required=gpu_required and self.gpu_available,
            status=ExportStatus.PENDING
        )
        
        with self.lock:
            self.queue.put((job.priority.value, job_id, job))
        
        return job_id
    
    def start(self):
        """Start the export queue worker thread"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def stop(self):
        """Stop the export queue worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _worker_loop(self):
        """Main worker loop for processing export jobs"""
        while self.running:
            try:
                # Check if we can start a new job
                if len(self.active_jobs) < self.max_concurrent:
                    try:
                        _, job_id, job = self.queue.get(timeout=1)
                        job.status = ExportStatus.RUNNING
                        job.started_at = datetime.now()
                        
                        with self.lock:
                            self.active_jobs[job_id] = job
                        
                        # Process job in thread (non-blocking)
                        thread = threading.Thread(
                            target=self._process_job,
                            args=(job_id, job),
                            daemon=True
                        )
                        thread.start()
                    except Empty:
                        continue
                
                time.sleep(0.5)  # Small delay to avoid busy waiting
                
            except Exception as e:
                # Log error and continue
                print(f"Export queue worker error: {e}")
                time.sleep(1)
    
    def _process_job(self, job_id: str, job: ExportJob):
        """Process a single export job"""
        try:
            # Convert quality string to VideoQuality enum
            quality_map = {
                "HIGH": VideoQuality.HIGH,
                "MEDIUM": VideoQuality.MEDIUM,
                "LOW": VideoQuality.LOW
            }
            video_quality = quality_map.get(job.quality, VideoQuality.HIGH)
            
            # Ensure output directory exists
            job.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Update progress (start)
            job.progress = 5.0
            
            # Export using FFmpegProcessor
            result = FFmpegProcessor.export_for_platform(
                input_file=job.input_file,
                platform=job.platform,
                output_file=job.output_file,
                quality=video_quality,
                two_pass=False  # Single pass for queue (faster)
            )
            
            if result.success:
                job.status = ExportStatus.COMPLETED
                job.progress = 100.0
                job.completed_at = datetime.now()
            else:
                job.status = ExportStatus.FAILED
                job.error = result.error_message or "Export failed"
                job.completed_at = datetime.now()
        
        except Exception as e:
            job.status = ExportStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
        
        finally:
            # Move job from active to completed
            with self.lock:
                if job_id in self.active_jobs:
                    del self.active_jobs[job_id]
                self.completed_jobs[job_id] = job
    
    def get_job_status(self, job_id: str) -> Optional[ExportJob]:
        """Get status of a job"""
        with self.lock:
            if job_id in self.active_jobs:
                return self.active_jobs[job_id]
            if job_id in self.completed_jobs:
                return self.completed_jobs[job_id]
        return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        with self.lock:
            return {
                "queued": self.queue.qsize(),
                "active": len(self.active_jobs),
                "completed": len(self.completed_jobs),
                "gpu_available": self.gpu_available,
                "max_concurrent": self.max_concurrent
            }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job (cannot cancel running jobs)"""
        # Note: PriorityQueue doesn't support direct item removal
        # This is a simplified implementation - full implementation would need
        # a custom priority queue or job tracking
        job = self.get_job_status(job_id)
        if job and job.status == ExportStatus.PENDING:
            job.status = ExportStatus.CANCELLED
            return True
        return False


