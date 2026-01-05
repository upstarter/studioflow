"""
Metrics tracking for rough cut generation
Tracks accuracy, performance, and editor feedback
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json


@dataclass
class RoughCutMetrics:
    """Metrics for a single rough cut generation"""
    timestamp: str
    num_clips: int
    num_segments: int
    processing_time_seconds: float
    memory_usage_mb: Optional[float] = None
    
    # Accuracy metrics
    quote_selection_accuracy: Optional[float] = None  # 0-1
    edit_point_precision: Optional[float] = None  # 0-1
    narrative_structure_score: Optional[float] = None  # 0-1
    
    # Editor feedback
    editor_rating: Optional[float] = None  # 1-5
    segments_kept: Optional[int] = None
    segments_removed: Optional[int] = None
    time_saved_minutes: Optional[float] = None
    
    # Performance
    nlp_analysis_time: Optional[float] = None
    segment_selection_time: Optional[float] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collect and store rough cut metrics"""
    
    def __init__(self, metrics_file: Optional[Path] = None):
        self.metrics_file = metrics_file or Path.home() / ".studioflow" / "rough_cut_metrics.json"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics: List[RoughCutMetrics] = []
        self._load_metrics()
    
    def _load_metrics(self):
        """Load existing metrics from file"""
        if self.metrics_file.exists():
            try:
                data = json.loads(self.metrics_file.read_text())
                self.metrics = [
                    RoughCutMetrics(**m) for m in data.get("metrics", [])
                ]
            except Exception:
                self.metrics = []
        else:
            self.metrics = []
    
    def _save_metrics(self):
        """Save metrics to file"""
        data = {
            "last_updated": datetime.now().isoformat(),
            "metrics": [asdict(m) for m in self.metrics]
        }
        self.metrics_file.write_text(json.dumps(data, indent=2))
    
    def record_generation(self, metrics: RoughCutMetrics):
        """Record a rough cut generation"""
        self.metrics.append(metrics)
        self._save_metrics()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregated statistics"""
        if not self.metrics:
            return {"error": "No metrics recorded"}
        
        stats = {
            "total_generations": len(self.metrics),
            "avg_processing_time": sum(m.processing_time_seconds for m in self.metrics) / len(self.metrics),
            "avg_clips_per_generation": sum(m.num_clips for m in self.metrics) / len(self.metrics),
            "avg_segments_per_generation": sum(m.num_segments for m in self.metrics) / len(self.metrics),
        }
        
        # Editor ratings (if available)
        ratings = [m.editor_rating for m in self.metrics if m.editor_rating is not None]
        if ratings:
            stats["avg_editor_rating"] = sum(ratings) / len(ratings)
            stats["editor_ratings_count"] = len(ratings)
        
        # Accuracy metrics (if available)
        accuracies = [m.quote_selection_accuracy for m in self.metrics if m.quote_selection_accuracy is not None]
        if accuracies:
            stats["avg_quote_accuracy"] = sum(accuracies) / len(accuracies)
        
        return stats
    
    def export_report(self, output_path: Path):
        """Export metrics as a report"""
        stats = self.get_statistics()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": stats,
            "recent_metrics": [asdict(m) for m in self.metrics[-10:]]  # Last 10
        }
        
        output_path.write_text(json.dumps(report, indent=2))

