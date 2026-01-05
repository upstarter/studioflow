"""
Optimization utilities for rough cut generation
Parameter tuning, performance profiling, and model training
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from studioflow.core.rough_cut import RoughCutEngine, CutStyle, RoughCutPlan


@dataclass
class OptimizationResult:
    """Result of an optimization run"""
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    plan: Optional[RoughCutPlan] = None


class RoughCutOptimizer:
    """Optimize rough cut generation parameters"""
    
    def __init__(self, engine: RoughCutEngine):
        self.engine = engine
    
    def tune_importance_threshold(self, clips, target_duration: float,
                                  thresholds: List[float] = [50, 60, 70, 75, 80]) -> List[OptimizationResult]:
        """Test different importance thresholds"""
        results = []
        
        for threshold in thresholds:
            # Note: Would need to modify engine to accept threshold parameter
            # For now, this is a placeholder for the optimization framework
            self.engine.clips = clips.copy()
            
            start_time = time.time()
            plan = self.engine.create_rough_cut(
                style=CutStyle.DOC,
                target_duration=target_duration,
                use_smart_features=True
            )
            elapsed = time.time() - start_time
            
            results.append(OptimizationResult(
                parameters={"importance_threshold": threshold},
                metrics={
                    "processing_time": elapsed,
                    "num_segments": len(plan.segments),
                    "num_themes": len(plan.themes),
                    "total_duration": plan.total_duration
                },
                plan=plan
            ))
        
        return results
    
    def tune_gap_threshold(self, clips, target_duration: float,
                          gaps: List[float] = [1.0, 1.5, 2.0, 2.5, 3.0]) -> List[OptimizationResult]:
        """Test different gap thresholds for merging"""
        results = []
        
        for gap in gaps:
            self.engine.clips = clips.copy()
            
            start_time = time.time()
            plan = self.engine.create_rough_cut(
                style=CutStyle.DOC,
                target_duration=target_duration,
                use_smart_features=True
            )
            elapsed = time.time() - start_time
            
            # Count merged segments (would need to track this)
            results.append(OptimizationResult(
                parameters={"gap_threshold": gap},
                metrics={
                    "processing_time": elapsed,
                    "num_segments": len(plan.segments),
                    "total_duration": plan.total_duration
                },
                plan=plan
            ))
        
        return results
    
    def profile_performance(self, clips, target_duration: float) -> Dict[str, float]:
        """Profile performance of different stages"""
        profile = {}
        
        # Stage 1: Clip analysis
        self.engine.clips = clips.copy()
        start = time.time()
        # Analysis happens in analyze_clips, which is already done
        profile["clip_analysis"] = 0.0  # Would need to instrument
        
        # Stage 2: NLP analysis
        start = time.time()
        plan = self.engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=target_duration,
            use_smart_features=True
        )
        profile["total_generation"] = time.time() - start
        
        return profile
    
    def find_optimal_parameters(self, clips, target_duration: float,
                               ground_truth: Optional[RoughCutPlan] = None) -> Dict[str, Any]:
        """Find optimal parameters using grid search"""
        best_params = {}
        best_score = 0.0
        
        # Test importance thresholds
        importance_results = self.tune_importance_threshold(clips, target_duration)
        
        # Score each configuration
        for result in importance_results:
            # Score based on metrics (would need ground truth for accuracy)
            score = self._score_configuration(result, ground_truth)
            
            if score > best_score:
                best_score = score
                best_params = result.parameters
        
        return {
            "optimal_parameters": best_params,
            "best_score": best_score,
            "tested_configurations": len(importance_results)
        }
    
    def _score_configuration(self, result: OptimizationResult,
                            ground_truth: Optional[RoughCutPlan]) -> float:
        """Score a configuration (higher is better)"""
        score = 0.0
        
        # Prefer faster processing
        score += 1.0 / (result.metrics["processing_time"] + 0.1)
        
        # Prefer reasonable number of segments (not too few, not too many)
        num_segments = result.metrics["num_segments"]
        if 10 <= num_segments <= 50:
            score += 1.0
        elif 5 <= num_segments <= 100:
            score += 0.5
        
        # If ground truth available, compare accuracy
        if ground_truth and result.plan:
            # Simple overlap metric
            overlap = self._calculate_overlap(result.plan, ground_truth)
            score += overlap * 10.0
        
        return score
    
    def _calculate_overlap(self, plan1: RoughCutPlan, plan2: RoughCutPlan) -> float:
        """Calculate overlap between two plans"""
        # Simple implementation: count matching segments
        matches = 0
        total = max(len(plan1.segments), len(plan2.segments))
        
        if total == 0:
            return 0.0
        
        # Check for overlapping segments (within 1s tolerance)
        for seg1 in plan1.segments:
            for seg2 in plan2.segments:
                if seg1.source_file == seg2.source_file:
                    overlap_start = max(seg1.start_time, seg2.start_time)
                    overlap_end = min(seg1.end_time, seg2.end_time)
                    if overlap_end - overlap_start > 1.0:  # At least 1s overlap
                        matches += 1
                        break
        
        return matches / total if total > 0 else 0.0

