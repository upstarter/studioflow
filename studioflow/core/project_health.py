"""
Project Health Dashboard
Analyzes project status, identifies issues, suggests next steps
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .project import ProjectManager
from .media import MediaScanner
from .resolve_api import ResolveDirectAPI
from .transcription import TranscriptionService


class HealthStatus(str, Enum):
    """Health status levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    details: Optional[str] = None
    action: Optional[str] = None
    priority: int = 0  # Higher = more important


@dataclass
class ProjectHealth:
    """Complete project health assessment"""
    project_name: str
    project_path: Path
    overall_status: HealthStatus
    checks: List[HealthCheck] = field(default_factory=list)
    media_stats: Dict[str, Any] = field(default_factory=dict)
    resolve_status: Dict[str, Any] = field(default_factory=dict)
    next_steps: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ProjectHealthChecker:
    """Analyzes project health and provides recommendations"""
    
    def __init__(self):
        self.project_manager = ProjectManager()
        self.scanner = MediaScanner()
        self.resolve_api = ResolveDirectAPI()
        self.transcription_service = TranscriptionService()
    
    def check_health(self, project_name: Optional[str] = None) -> ProjectHealth:
        """Perform complete health check on project"""
        from .state import StateManager
        
        state = StateManager()
        project_name = project_name or state.current_project
        
        if not project_name:
            return ProjectHealth(
                project_name="None",
                project_path=Path("/"),
                overall_status=HealthStatus.UNKNOWN,
                errors=["No project selected"]
            )
        
        project = self.project_manager.get_project(project_name)
        if not project:
            return ProjectHealth(
                project_name=project_name,
                project_path=Path("/"),
                overall_status=HealthStatus.ERROR,
                errors=[f"Project '{project_name}' not found"]
            )
        
        health = ProjectHealth(
            project_name=project_name,
            project_path=project.path,
            overall_status=HealthStatus.UNKNOWN
        )
        
        # Run checks
        self._check_media(health, project)
        self._check_resolve(health, project)
        self._check_transcripts(health, project)
        self._check_organization(health, project)
        self._check_exports(health, project)
        self._check_storage(health, project)
        
        # Determine overall status
        health.overall_status = self._determine_overall_status(health)
        
        # Generate next steps
        health.next_steps = self._generate_next_steps(health)
        
        return health
    
    def _check_media(self, health: ProjectHealth, project):
        """Check media files"""
        media_dir = project.path / "01_MEDIA"
        
        if not media_dir.exists():
            health.checks.append(HealthCheck(
                name="Media Directory",
                status=HealthStatus.ERROR,
                message="Media directory not found",
                action="Import media: sf import /path/to/footage",
                priority=10
            ))
            health.errors.append("No media directory found")
            return
        
        # Scan media
        files = self.scanner.scan(media_dir)
        
        if not files:
            health.checks.append(HealthCheck(
                name="Media Files",
                status=HealthStatus.WARNING,
                message="No media files found",
                action="Import media: sf import /path/to/footage",
                priority=8
            ))
            health.warnings.append("No media files in project")
        else:
            total_size = sum(f.size for f in files)
            health.checks.append(HealthCheck(
                name="Media Files",
                status=HealthStatus.GOOD,
                message=f"{len(files)} files, {total_size / (1024**3):.2f} GB",
                priority=1
            ))
        
        health.media_stats = {
            "file_count": len(files),
            "total_size_gb": sum(f.size for f in files) / (1024**3) if files else 0,
            "by_type": {}
        }
        
        # Check for corrupted files
        corrupted = []
        for f in files[:10]:  # Sample check
            if not f.path.exists():
                corrupted.append(f.path.name)
        
        if corrupted:
            health.checks.append(HealthCheck(
                name="File Integrity",
                status=HealthStatus.WARNING,
                message=f"{len(corrupted)} files may be missing",
                details=", ".join(corrupted[:3]),
                priority=7
            ))
    
    def _check_resolve(self, health: ProjectHealth, project):
        """Check Resolve integration"""
        if not self.resolve_api.is_connected():
            health.checks.append(HealthCheck(
                name="Resolve Connection",
                status=HealthStatus.WARNING,
                message="Resolve not connected",
                action="Start Resolve and run: sf resolve sync",
                priority=5
            ))
            health.warnings.append("Resolve not connected")
            return
        
        # Check if project exists in Resolve
        pm = self.resolve_api.resolve.GetProjectManager()
        project_list = pm.GetProjectListInCurrentFolder()
        
        if project.name not in project_list:
            health.checks.append(HealthCheck(
                name="Resolve Project",
                status=HealthStatus.WARNING,
                message="Project not found in Resolve",
                action="Run: sf resolve sync",
                priority=6
            ))
            health.warnings.append("Resolve project not synced")
        else:
            health.checks.append(HealthCheck(
                name="Resolve Project",
                status=HealthStatus.GOOD,
                message="Project synced with Resolve",
                priority=2
            ))
        
        health.resolve_status = {
            "connected": True,
            "project_exists": project.name in project_list if project_list else False
        }
    
    def _check_transcripts(self, health: ProjectHealth, project):
        """Check transcript availability"""
        transcript_dir = project.path / "02_TRANSCRIPTS"
        
        if not transcript_dir.exists():
            health.checks.append(HealthCheck(
                name="Transcripts",
                status=HealthStatus.WARNING,
                message="No transcripts directory",
                action="Transcribe: sf media transcribe video.mp4",
                priority=4
            ))
            return
        
        transcripts = list(transcript_dir.glob("*.srt")) + list(transcript_dir.glob("*.json"))
        
        if not transcripts:
            health.checks.append(HealthCheck(
                name="Transcripts",
                status=HealthStatus.WARNING,
                message="No transcripts found",
                action="Transcribe: sf media transcribe video.mp4",
                priority=4
            ))
            health.warnings.append("No transcripts available")
        else:
            health.checks.append(HealthCheck(
                name="Transcripts",
                status=HealthStatus.GOOD,
                message=f"{len(transcripts)} transcript(s) available",
                priority=2
            ))
    
    def _check_organization(self, health: ProjectHealth, project):
        """Check project organization"""
        expected_dirs = [
            "01_MEDIA",
            "02_TRANSCRIPTS",
            "03_RESOLVE",
            "04_EXPORTS",
        ]
        
        missing = []
        for dir_name in expected_dirs:
            if not (project.path / dir_name).exists():
                missing.append(dir_name)
        
        if missing:
            health.checks.append(HealthCheck(
                name="Organization",
                status=HealthStatus.WARNING,
                message=f"Missing directories: {', '.join(missing)}",
                action="Run: sf auto-edit episode {project.name}",
                priority=3
            ))
        else:
            health.checks.append(HealthCheck(
                name="Organization",
                status=HealthStatus.GOOD,
                message="Project structure complete",
                priority=1
            ))
    
    def _check_exports(self, health: ProjectHealth, project):
        """Check for exports"""
        export_dir = project.path / "04_EXPORTS"
        
        if export_dir.exists():
            exports = list(export_dir.glob("*.mp4")) + list(export_dir.glob("*.mov"))
            
            if exports:
                latest = max(exports, key=lambda p: p.stat().st_mtime)
                age_days = (datetime.now().timestamp() - latest.stat().st_mtime) / 86400
                
                health.checks.append(HealthCheck(
                    name="Exports",
                    status=HealthStatus.GOOD,
                    message=f"{len(exports)} export(s), latest: {age_days:.0f} days ago",
                    priority=1
                ))
            else:
                health.checks.append(HealthCheck(
                    name="Exports",
                    status=HealthStatus.WARNING,
                    message="No exports found",
                    action="Export: sf export youtube video.mp4",
                    priority=3
                ))
    
    def _check_storage(self, health: ProjectHealth, project):
        """Check storage usage"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(project.path)
            free_gb = free / (1024**3)
            
            if free_gb < 10:
                health.checks.append(HealthCheck(
                    name="Storage",
                    status=HealthStatus.ERROR,
                    message=f"Low disk space: {free_gb:.1f} GB free",
                    action="Free up space or archive old projects",
                    priority=9
                ))
                health.errors.append(f"Low disk space: {free_gb:.1f} GB")
            elif free_gb < 50:
                health.checks.append(HealthCheck(
                    name="Storage",
                    status=HealthStatus.WARNING,
                    message=f"Limited disk space: {free_gb:.1f} GB free",
                    action="Consider archiving old projects",
                    priority=5
                ))
            else:
                health.checks.append(HealthCheck(
                    name="Storage",
                    status=HealthStatus.GOOD,
                    message=f"{free_gb:.1f} GB free",
                    priority=1
                ))
        except:
            pass
    
    def _determine_overall_status(self, health: ProjectHealth) -> HealthStatus:
        """Determine overall health status"""
        if health.errors:
            return HealthStatus.ERROR
        elif health.warnings:
            return HealthStatus.WARNING
        elif all(c.status in [HealthStatus.GOOD, HealthStatus.EXCELLENT] for c in health.checks):
            return HealthStatus.GOOD
        else:
            return HealthStatus.WARNING
    
    def _generate_next_steps(self, health: ProjectHealth) -> List[str]:
        """Generate recommended next steps"""
        steps = []
        
        # Sort checks by priority
        checks = sorted(health.checks, key=lambda c: c.priority, reverse=True)
        
        # Get top 3 actionable items
        for check in checks[:3]:
            if check.action and check.status != HealthStatus.GOOD:
                steps.append(check.action)
        
        # Default steps if project is healthy
        if not steps and health.overall_status == HealthStatus.GOOD:
            steps = [
                "Continue editing in Resolve",
                "Export when ready: sf export youtube video.mp4",
                "Generate thumbnails: sf thumbnail generate"
            ]
        
        return steps


