"""
Complete Workflow Engine
Auto-complete workflows that tie all features together
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .auto_editing import AutoEditingEngine, AutoEditConfig
from .batch_processor import BatchProcessor
from .project_health import ProjectHealthChecker
from .media import MediaScanner
from .transcription import TranscriptionService
from .resolve_api import ResolveDirectAPI
from .config import get_config


class WorkflowType(str, Enum):
    """Workflow types"""
    EPISODE = "episode"
    IMPORT = "import"
    PUBLISH = "publish"
    FULL = "full"


@dataclass
class WorkflowStep:
    """Single step in workflow"""
    name: str
    description: str
    function: Callable
    required: bool = True
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class WorkflowResult:
    """Complete workflow result"""
    workflow_type: WorkflowType
    success: bool
    steps: List[WorkflowStep] = field(default_factory=list)
    duration: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CompleteWorkflowEngine:
    """Orchestrates complete workflows"""
    
    def __init__(self):
        self.health_checker = ProjectHealthChecker()
        self.batch_processor = BatchProcessor()
        self.scanner = MediaScanner()
        self.transcription_service = TranscriptionService()
        self.resolve_api = ResolveDirectAPI()
    
    def execute_episode_workflow(
        self,
        project_name: str,
        footage_path: Path,
        transcript_path: Optional[Path] = None,
        library_path: Optional[Path] = None,
        **kwargs
    ) -> WorkflowResult:
        """
        Complete episode workflow:
        1. Import and organize media
        2. Transcribe (if needed)
        3. Create smart bins
        4. Generate chapters
        5. Create timeline
        6. Validate health
        """
        # Get library path from config if not provided
        if library_path is None:
            config = get_config()
            library_path = config.storage.library or config.storage.active or Path.home() / "Videos" / "StudioFlow" / "Library"
        
        start_time = datetime.now()
        steps = []
        
        try:
            # Step 1: Analyze and organize media
            step = WorkflowStep(
                name="Organize Media",
                description="Scanning and organizing footage",
                function=self._step_organize_media,
                status="running"
            )
            steps.append(step)
            step.result = self._step_organize_media(footage_path)
            step.status = "completed" if step.result.get("success") else "failed"
            
            # Step 2: Transcribe (if transcript not provided)
            if not transcript_path:
                step = WorkflowStep(
                    name="Transcribe",
                    description="Generating transcript from footage",
                    function=self._step_transcribe,
                    required=False,
                    status="running"
                )
                steps.append(step)
                step.result = self._step_transcribe(footage_path)
                step.status = "completed" if step.result.get("success") else "failed"
                if step.result.get("transcript_path"):
                    transcript_path = step.result["transcript_path"]
            
            # Step 3: Auto-edit setup
            step = WorkflowStep(
                name="Auto-Edit Setup",
                description="Creating smart bins, power bins, timeline",
                function=self._step_auto_edit,
                status="running"
            )
            steps.append(step)
            
            config = AutoEditConfig(
                project_name=project_name,
                footage_path=footage_path,
                transcript_path=transcript_path,
                library_path=library_path,
                **kwargs
            )
            engine = AutoEditingEngine(config)
            step.result = engine.process_episode()
            step.status = "completed" if step.result.get("success") else "failed"
            
            # Step 4: Health check
            step = WorkflowStep(
                name="Health Check",
                description="Validating project health",
                function=self._step_health_check,
                required=False,
                status="running"
            )
            steps.append(step)
            step.result = self.health_checker.check_health(project_name)
            step.status = "completed"
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Collect errors/warnings
            errors = [s.error for s in steps if s.status == "failed" and s.error]
            warnings = []
            if step.result and hasattr(step.result, 'warnings'):
                warnings = step.result.warnings
            
            return WorkflowResult(
                workflow_type=WorkflowType.EPISODE,
                success=all(s.status != "failed" for s in steps if s.required),
                steps=steps,
                duration=duration,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return WorkflowResult(
                workflow_type=WorkflowType.EPISODE,
                success=False,
                steps=steps,
                duration=(datetime.now() - start_time).total_seconds(),
                errors=[str(e)]
            )
    
    def execute_import_workflow(
        self,
        source_path: Path,
        project_name: str,
        organize: bool = True,
        transcribe: bool = False,
        create_proxies: bool = False
    ) -> WorkflowResult:
        """Import workflow with optional transcription and proxy creation"""
        start_time = datetime.now()
        steps = []
        
        # Step 1: Import media
        step = WorkflowStep(
            name="Import Media",
            description=f"Importing from {source_path}",
            function=lambda: {"success": True},
            status="running"
        )
        steps.append(step)
        # TODO: Implement actual import
        step.result = {"success": True, "files_imported": 0}
        step.status = "completed"
        
        # Step 2: Transcribe (if requested)
        if transcribe:
            step = WorkflowStep(
                name="Batch Transcribe",
                description="Transcribing all imported media",
                function=self._step_batch_transcribe,
                required=False,
                status="running"
            )
            steps.append(step)
            step.result = self._step_batch_transcribe(source_path)
            step.status = "completed" if step.result.get("success") else "failed"
        
        # Step 3: Create proxies (if requested)
        if create_proxies:
            step = WorkflowStep(
                name="Create Proxies",
                description="Generating proxy media",
                function=self._step_create_proxies,
                required=False,
                status="running"
            )
            steps.append(step)
            step.result = self._step_create_proxies(source_path)
            step.status = "completed" if step.result.get("success") else "failed"
        
        return WorkflowResult(
            workflow_type=WorkflowType.IMPORT,
            success=True,
            steps=steps,
            duration=(datetime.now() - start_time).total_seconds()
        )
    
    def execute_publish_workflow(
        self,
        video_path: Path,
        project_name: str,
        validate: bool = True,
        generate_thumbnail: bool = True,
        upload: bool = False
    ) -> WorkflowResult:
        """Complete publish workflow: validate, thumbnail, upload"""
        start_time = datetime.now()
        steps = []
        
        # Step 1: Validate export
        if validate:
            step = WorkflowStep(
                name="Validate Export",
                description="Checking YouTube compliance",
                function=self._step_validate_export,
                status="running"
            )
            steps.append(step)
            step.result = self._step_validate_export(video_path)
            step.status = "completed" if step.result.get("valid") else "failed"
            if not step.result.get("valid"):
                return WorkflowResult(
                    workflow_type=WorkflowType.PUBLISH,
                    success=False,
                    steps=steps,
                    errors=step.result.get("errors", [])
                )
        
        # Step 2: Generate thumbnail
        if generate_thumbnail:
            step = WorkflowStep(
                name="Generate Thumbnail",
                description="Creating YouTube thumbnail",
                function=self._step_generate_thumbnail,
                required=False,
                status="running"
            )
            steps.append(step)
            step.result = self._step_generate_thumbnail(video_path, project_name)
            step.status = "completed" if step.result.get("success") else "failed"
        
        # Step 3: Upload (if requested)
        if upload:
            step = WorkflowStep(
                name="Upload to YouTube",
                description="Uploading video",
                function=self._step_upload,
                required=False,
                status="running"
            )
            steps.append(step)
            step.result = self._step_upload(video_path, project_name)
            step.status = "completed" if step.result.get("success") else "failed"
        
        return WorkflowResult(
            workflow_type=WorkflowType.PUBLISH,
            success=True,
            steps=steps,
            duration=(datetime.now() - start_time).total_seconds()
        )
    
    # Step implementations
    def _step_organize_media(self, footage_path: Path) -> Dict:
        """Organize media step"""
        files = self.scanner.scan(footage_path)
        return {
            "success": True,
            "files_found": len(files),
            "total_size_gb": sum(f.size for f in files) / (1024**3) if files else 0
        }
    
    def _step_transcribe(self, footage_path: Path) -> Dict:
        """Transcribe step"""
        # Find video files
        videos = list(footage_path.glob("*.mp4")) + list(footage_path.glob("*.MP4"))
        
        if not videos:
            return {"success": False, "error": "No video files found"}
        
        # Transcribe first video (or all if batch)
        video = videos[0]
        result = self.transcription_service.transcribe(video)
        
        if result.get("success"):
            return {
                "success": True,
                "transcript_path": result["output_files"].get("json"),
                "text_length": len(result.get("text", ""))
            }
        
        return {"success": False, "error": result.get("error")}
    
    def _step_auto_edit(self, config: AutoEditConfig) -> Dict:
        """Auto-edit step"""
        engine = AutoEditingEngine(config)
        return engine.process_episode()
    
    def _step_health_check(self, project_name: str) -> Any:
        """Health check step"""
        return self.health_checker.check_health(project_name)
    
    def _step_batch_transcribe(self, source_path: Path) -> Dict:
        """Batch transcribe step"""
        videos = list(source_path.glob("**/*.mp4")) + list(source_path.glob("**/*.MP4"))
        
        if not videos:
            return {"success": False, "error": "No videos found"}
        
        results = []
        for video in videos[:5]:  # Limit to 5 for now
            result = self.transcription_service.transcribe(video)
            results.append(result.get("success", False))
        
        return {
            "success": all(results),
            "transcribed": sum(results),
            "total": len(videos)
        }
    
    def _step_create_proxies(self, source_path: Path) -> Dict:
        """Create proxies step"""
        # TODO: Implement proxy creation
        return {"success": True, "proxies_created": 0}
    
    def _step_validate_export(self, video_path: Path) -> Dict:
        """Validate export step"""
        from .export_validator import ExportValidator
        
        validator = ExportValidator()
        result = validator.validate_youtube(video_path)
        
        return {
            "valid": result.get("valid", False),
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", [])
        }
    
    def _step_generate_thumbnail(self, video_path: Path, project_name: str) -> Dict:
        """Generate thumbnail step"""
        # TODO: Implement thumbnail generation
        return {"success": True, "thumbnail_path": None}
    
    def _step_upload(self, video_path: Path, project_name: str) -> Dict:
        """Upload step"""
        from .youtube_api import YouTubeAPIService
        
        service = YouTubeAPIService()
        if not service.authenticate():
            return {"success": False, "error": "YouTube authentication failed"}
        
        # TODO: Implement actual upload
        return {"success": True, "video_id": None}


