"""
Batch Processing System
Parallel processing for multiple files with progress tracking
"""

import concurrent.futures
from pathlib import Path
from typing import List, Callable, Dict, Any, Optional
from dataclasses import dataclass
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TaskID
from rich.console import Console

console = Console()


@dataclass
class BatchResult:
    """Result of batch operation"""
    file: Path
    success: bool
    output: Optional[Path] = None
    error: Optional[str] = None
    duration: float = 0.0


class BatchProcessor:
    """Handles batch processing with parallel execution"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results: List[BatchResult] = []
    
    def process(
        self,
        files: List[Path],
        operation: Callable,
        operation_name: str = "Processing",
        show_progress: bool = True,
        **operation_kwargs
    ) -> List[BatchResult]:
        """
        Process multiple files in parallel
        
        Args:
            files: List of files to process
            operation: Function to call for each file: operation(file, **kwargs) -> BatchResult
            operation_name: Display name for progress
            show_progress: Whether to show progress bar
            **operation_kwargs: Additional arguments to pass to operation
        """
        self.results = []
        
        if show_progress:
            with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeRemainingColumn(),
                console=console
            ) as progress:
                task = progress.add_task(f"{operation_name}...", total=len(files))
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {
                        executor.submit(operation, file, **operation_kwargs): file
                        for file in files
                    }
                    
                    for future in concurrent.futures.as_completed(futures):
                        file = futures[future]
                        try:
                            result = future.result()
                            self.results.append(result)
                            
                            if result.success:
                                progress.update(task, description=f"✓ {file.name}")
                            else:
                                progress.update(task, description=f"✗ {file.name}: {result.error}")
                        except Exception as e:
                            self.results.append(BatchResult(
                                file=file,
                                success=False,
                                error=str(e)
                            ))
                            progress.update(task, description=f"✗ {file.name}: {str(e)}")
                        
                        progress.advance(task)
        else:
            # No progress bar
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(operation, file, **operation_kwargs): file
                    for file in files
                }
                
                for future in concurrent.futures.as_completed(futures):
                    file = futures[future]
                    try:
                        result = future.result()
                        self.results.append(result)
                    except Exception as e:
                        self.results.append(BatchResult(
                            file=file,
                            success=False,
                            error=str(e)
                        ))
        
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of batch processing results"""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "results": self.results
        }


