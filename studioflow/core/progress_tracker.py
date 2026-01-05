"""
Real-time Progress Tracking
Enhanced progress updates with ETA, speed, and detailed status
"""

import time
from typing import Optional, Callable, Any
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
    ProgressColumn
)
from rich.console import Console


class SpeedColumn(ProgressColumn):
    """Display processing speed"""
    
    def render(self, task):
        if task.completed and task.elapsed:
            speed = task.completed / task.elapsed
            return f"{speed:.1f}/s"
        return "-"


class DetailedProgress:
    """Enhanced progress tracking with detailed information"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            SpeedColumn(),
            console=self.console,
            expand=True
        )
    
    def __enter__(self):
        self.progress.__enter__()
        return self
    
    def __exit__(self, *args):
        self.progress.__exit__(*args)
    
    def add_task(self, description: str, total: Optional[float] = None) -> Any:
        """Add a new task"""
        return self.progress.add_task(description, total=total)
    
    def update(self, task_id, **kwargs):
        """Update task progress"""
        self.progress.update(task_id, **kwargs)


def track_operation(
    operation: Callable,
    description: str,
    total: Optional[float] = None,
    **operation_kwargs
) -> Any:
    """
    Track operation with progress bar
    
    Usage:
        result = track_operation(transcribe_file, "Transcribing", total=100, file=video)
    """
    with DetailedProgress() as progress:
        task = progress.add_task(description, total=total)
        
        # Wrap operation to update progress
        def tracked_operation(*args, **kwargs):
            try:
                result = operation(*args, **kwargs)
                progress.update(task, completed=total if total else 100)
                return result
            except Exception as e:
                progress.update(task, description=f"[red]Error: {e}[/red]")
                raise
        
        return tracked_operation(**operation_kwargs)


