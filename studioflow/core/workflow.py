"""
Workflow automation for StudioFlow
Automate repetitive tasks and complex pipelines
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import yaml
import json
import time
import threading
from datetime import datetime, timedelta
from queue import Queue


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TriggerType(Enum):
    """Workflow trigger types"""
    MANUAL = "manual"
    WATCH_FOLDER = "watch_folder"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    FILE_CREATED = "file_created"
    PROJECT_EVENT = "project_event"


@dataclass
class Task:
    """Individual workflow task"""
    id: str
    name: str
    type: str  # "import", "cut", "effect", "export", "upload", etc.
    params: Dict[str, Any]
    inputs: List[str] = field(default_factory=list)  # Input task IDs
    outputs: List[str] = field(default_factory=list)  # Output paths
    status: TaskStatus = TaskStatus.PENDING
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class Workflow:
    """Complete workflow definition"""
    id: str
    name: str
    description: str
    trigger: TriggerType
    trigger_config: Dict[str, Any]
    tasks: List[Task]
    variables: Dict[str, Any] = field(default_factory=dict)
    created: datetime = field(default_factory=datetime.now)


class WorkflowEngine:
    """Execute and manage workflows"""

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.running_workflows: Dict[str, threading.Thread] = {}
        self.task_queue: Queue = Queue()
        self.watchers: Dict[str, threading.Thread] = {}

        # Task executors
        self.executors = {
            "import": self._execute_import,
            "cut": self._execute_cut,
            "concat": self._execute_concat,
            "effect": self._execute_effect,
            "export": self._execute_export,
            "upload": self._execute_upload,
            "thumbnail": self._execute_thumbnail,
            "transcribe": self._execute_transcribe,
            "resolve": self._execute_resolve,
            "composite": self._execute_composite,
            "normalize": self._execute_normalize
        }

    def add_workflow(self, workflow: Workflow):
        """Add workflow to engine"""
        self.workflows[workflow.id] = workflow

        # Set up triggers
        if workflow.trigger == TriggerType.WATCH_FOLDER:
            self._setup_folder_watcher(workflow)
        elif workflow.trigger == TriggerType.SCHEDULE:
            self._setup_scheduler(workflow)

    def execute_workflow(self, workflow_id: str, context: Dict[str, Any] = None):
        """Execute a workflow"""

        if workflow_id not in self.workflows:
            return False

        workflow = self.workflows[workflow_id]

        # Create execution thread
        thread = threading.Thread(
            target=self._run_workflow,
            args=(workflow, context or {})
        )
        thread.start()
        self.running_workflows[workflow_id] = thread

        return True

    def _run_workflow(self, workflow: Workflow, context: Dict[str, Any]):
        """Run workflow tasks"""

        print(f"🚀 Starting workflow: {workflow.name}")

        # Merge context with workflow variables
        variables = {**workflow.variables, **context}

        # Execute tasks in order
        for task in workflow.tasks:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()

            try:
                # Check dependencies
                if not self._check_dependencies(task, workflow.tasks):
                    task.status = TaskStatus.SKIPPED
                    continue

                # Execute task
                if task.type in self.executors:
                    result = self.executors[task.type](task, variables)
                    if result:
                        task.outputs = result if isinstance(result, list) else [result]
                        task.status = TaskStatus.COMPLETED
                    else:
                        task.status = TaskStatus.FAILED
                        task.error = "Task execution failed"
                else:
                    task.status = TaskStatus.FAILED
                    task.error = f"Unknown task type: {task.type}"

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)

            finally:
                task.end_time = datetime.now()

            # Log task result
            duration = (task.end_time - task.start_time).total_seconds()
            status_emoji = "✅" if task.status == TaskStatus.COMPLETED else "❌"
            print(f"{status_emoji} {task.name}: {task.status.value} ({duration:.1f}s)")

            # Stop on failure if not configured to continue
            if task.status == TaskStatus.FAILED and not variables.get("continue_on_error"):
                break

        # Cleanup
        if workflow.id in self.running_workflows:
            del self.running_workflows[workflow.id]

        print(f"✨ Workflow complete: {workflow.name}")

    def _check_dependencies(self, task: Task, all_tasks: List[Task]) -> bool:
        """Check if task dependencies are met"""

        for input_id in task.inputs:
            input_task = next((t for t in all_tasks if t.id == input_id), None)
            if input_task and input_task.status != TaskStatus.COMPLETED:
                return False
        return True

    # Task executors
    def _execute_import(self, task: Task, variables: Dict) -> List[str]:
        """Import media files"""
        from .media import MediaImporter

        source = Path(self._resolve_variable(task.params["source"], variables))
        verify = task.params.get("verify", True)

        importer = MediaImporter(Path.cwd())
        imported = importer.import_media([source], verify=verify)

        return [str(f) for f in imported]

    def _execute_cut(self, task: Task, variables: Dict) -> str:
        """Cut video segment"""
        from .ffmpeg import FFmpegProcessor

        input_file = Path(self._resolve_variable(task.params["input"], variables))
        output_file = Path(self._resolve_variable(task.params["output"], variables))
        start = float(task.params["start"])
        duration = float(task.params["duration"])

        result = FFmpegProcessor.cut_video(input_file, output_file, start, duration)
        return str(output_file) if result.success else None

    def _execute_concat(self, task: Task, variables: Dict) -> str:
        """Concatenate videos"""
        from .ffmpeg import FFmpegProcessor

        inputs = [Path(self._resolve_variable(f, variables))
                 for f in task.params["inputs"]]
        output = Path(self._resolve_variable(task.params["output"], variables))

        result = FFmpegProcessor.concat_videos(inputs, output)
        return str(output) if result.success else None

    def _execute_effect(self, task: Task, variables: Dict) -> str:
        """Apply effect"""
        from .simple_effects import SimpleEffects

        input_file = Path(self._resolve_variable(task.params["input"], variables))
        effect = task.params["effect"]
        output_file = Path(self._resolve_variable(
            task.params.get("output", f"{input_file.stem}_{effect}{input_file.suffix}"),
            variables
        ))

        result = SimpleEffects.apply_effect(
            input_file, effect, output_file,
            task.params.get("params", {})
        )
        return str(output_file) if result.success else None

    def _execute_export(self, task: Task, variables: Dict) -> str:
        """Export for platform"""
        from .ffmpeg import FFmpegProcessor, VideoQuality

        input_file = Path(self._resolve_variable(task.params["input"], variables))
        platform = task.params["platform"]
        quality = VideoQuality[task.params.get("quality", "HIGH").upper()]
        output_file = Path(self._resolve_variable(
            task.params.get("output", f"{input_file.stem}_{platform}{input_file.suffix}"),
            variables
        ))

        result = FFmpegProcessor.export_for_platform(
            input_file, platform, output_file, quality
        )
        return str(output_file) if result.success else None

    def _execute_upload(self, task: Task, variables: Dict) -> str:
        """Upload to platform"""
        from .youtube_api import YouTubeAPIService

        video_file = Path(self._resolve_variable(task.params["video"], variables))
        platform = task.params.get("platform", "youtube")

        if platform == "youtube":
            service = YouTubeAPIService()
            result = service.upload_video(
                video_file,
                title=task.params.get("title", video_file.stem),
                description=task.params.get("description", ""),
                tags=task.params.get("tags", [])
            )
            return result.get("id") if result else None

        return None

    def _execute_thumbnail(self, task: Task, variables: Dict) -> str:
        """Generate thumbnail"""
        from .ffmpeg import FFmpegProcessor

        video_file = Path(self._resolve_variable(task.params["video"], variables))
        output_file = Path(self._resolve_variable(
            task.params.get("output", f"{video_file.stem}_thumb.jpg"),
            variables
        ))
        timestamp = task.params.get("timestamp")
        best_frame = task.params.get("best_frame", False)

        result = FFmpegProcessor.generate_thumbnail(
            video_file, output_file, timestamp, best_frame
        )
        return str(output_file) if result.success else None

    def _execute_transcribe(self, task: Task, variables: Dict) -> str:
        """Transcribe audio"""
        from .transcription import TranscriptionService

        audio_file = Path(self._resolve_variable(task.params["audio"], variables))
        model = task.params.get("model", "base")
        output_file = Path(self._resolve_variable(
            task.params.get("output", f"{audio_file.stem}.srt"),
            variables
        ))

        service = TranscriptionService()
        result = service.transcribe(audio_file, model=model)

        if result:
            output_file.write_text(result.get("srt", ""))
            return str(output_file)
        return None

    def _execute_resolve(self, task: Task, variables: Dict) -> str:
        """Create Resolve project"""
        from .resolve import ResolveIntegration, ResolveProject, TimelineClip

        clips = []
        for clip_data in task.params.get("clips", []):
            clips.append(TimelineClip(
                file_path=Path(self._resolve_variable(clip_data["path"], variables)),
                start_time=clip_data["start"],
                duration=clip_data["duration"]
            ))

        project = ResolveProject(
            name=task.params["name"],
            resolution=task.params.get("resolution", "1920x1080"),
            framerate=task.params.get("framerate", 30),
            clips=clips
        )

        output_file = Path(self._resolve_variable(
            task.params.get("output", f"{project.name}.fcpxml"),
            variables
        ))

        if ResolveIntegration.create_timeline_xml(project, output_file):
            return str(output_file)
        return None

    def _execute_composite(self, task: Task, variables: Dict) -> str:
        """Composite multiple videos"""
        from .node_graph import create_composite_pipeline

        background = Path(self._resolve_variable(task.params["background"], variables))
        foreground = Path(self._resolve_variable(task.params["foreground"], variables))
        output = Path(self._resolve_variable(task.params["output"], variables))
        blend_mode = task.params.get("blend_mode", "over")

        graph = create_composite_pipeline(background, foreground, output, blend_mode)
        results = graph.execute()

        return str(output) if results else None

    def _execute_normalize(self, task: Task, variables: Dict) -> str:
        """Normalize audio"""
        from .ffmpeg import FFmpegProcessor

        input_file = Path(self._resolve_variable(task.params["input"], variables))
        output_file = Path(self._resolve_variable(
            task.params.get("output", f"{input_file.stem}_normalized{input_file.suffix}"),
            variables
        ))
        target_lufs = task.params.get("lufs", -16.0)

        result = FFmpegProcessor.normalize_audio(input_file, output_file, target_lufs)
        return str(output_file) if result.success else None

    def _resolve_variable(self, value: str, variables: Dict) -> str:
        """Resolve variables in strings"""
        if isinstance(value, str) and "{" in value:
            return value.format(**variables)
        return value

    def _setup_folder_watcher(self, workflow: Workflow):
        """Set up folder watching trigger"""
        watch_path = Path(workflow.trigger_config["path"])
        pattern = workflow.trigger_config.get("pattern", "*")

        def watch():
            seen_files = set()
            while True:
                for file in watch_path.glob(pattern):
                    if file not in seen_files:
                        seen_files.add(file)
                        self.execute_workflow(workflow.id, {"input_file": str(file)})
                time.sleep(5)

        thread = threading.Thread(target=watch, daemon=True)
        thread.start()
        self.watchers[workflow.id] = thread

    def _setup_scheduler(self, workflow: Workflow):
        """Set up scheduled trigger"""
        # Simplified - would use proper scheduler like APScheduler
        pass

    @staticmethod
    def load_workflow(path: Path) -> Workflow:
        """Load workflow from YAML"""
        with open(path) as f:
            data = yaml.safe_load(f)

        tasks = []
        for task_data in data.get("tasks", []):
            tasks.append(Task(
                id=task_data["id"],
                name=task_data["name"],
                type=task_data["type"],
                params=task_data.get("params", {}),
                inputs=task_data.get("inputs", [])
            ))

        return Workflow(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            trigger=TriggerType[data.get("trigger", "MANUAL").upper()],
            trigger_config=data.get("trigger_config", {}),
            tasks=tasks,
            variables=data.get("variables", {})
        )

    def save_workflow(self, workflow: Workflow, path: Path):
        """Save workflow to YAML"""
        data = {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "trigger": workflow.trigger.value,
            "trigger_config": workflow.trigger_config,
            "variables": workflow.variables,
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "type": task.type,
                    "params": task.params,
                    "inputs": task.inputs
                }
                for task in workflow.tasks
            ]
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)


# Preset workflows
def create_youtube_workflow() -> Workflow:
    """Create standard YouTube production workflow"""

    return Workflow(
        id="youtube_production",
        name="YouTube Production Pipeline",
        description="Complete YouTube video production",
        trigger=TriggerType.WATCH_FOLDER,
        trigger_config={"path": "~/StudioFlow/Incoming", "pattern": "*.mp4"},
        tasks=[
            Task("import", "Import Media", "import",
                 {"source": "{input_file}", "verify": True}),
            Task("normalize", "Normalize Audio", "normalize",
                 {"input": "{input_file}", "lufs": -14}, inputs=["import"]),
            Task("thumbnail", "Generate Thumbnail", "thumbnail",
                 {"video": "{input_file}", "best_frame": True}, inputs=["import"]),
            Task("effects", "Apply Effects", "effect",
                 {"input": "{input_file}", "effect": "auto_enhance"}, inputs=["normalize"]),
            Task("export", "Export for YouTube", "export",
                 {"input": "{input_file}", "platform": "youtube", "quality": "HIGH"},
                 inputs=["effects"]),
            Task("upload", "Upload to YouTube", "upload",
                 {"video": "{input_file}", "platform": "youtube"},
                 inputs=["export"])
        ],
        variables={"continue_on_error": False}
    )


def create_dailies_workflow() -> Workflow:
    """Create dailies generation workflow"""

    return Workflow(
        id="generate_dailies",
        name="Generate Dailies",
        description="Create dailies with timecode burn-in",
        trigger=TriggerType.SCHEDULE,
        trigger_config={"time": "18:00", "days": "weekdays"},
        tasks=[
            Task("import", "Import Today's Media", "import",
                 {"source": "~/StudioFlow/RAW/{date}", "verify": True}),
            Task("resolve", "Generate Dailies", "resolve",
                 {"action": "dailies", "burn_in_tc": True}, inputs=["import"]),
            Task("upload", "Upload to Review", "upload",
                 {"platform": "frame.io"}, inputs=["resolve"])
        ],
        variables={"date": datetime.now().strftime("%Y%m%d")}
    )