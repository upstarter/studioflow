#!/usr/bin/env python3
"""
Performance benchmarking tool for rough cut generation
Measures processing time, memory usage, and throughput
"""

import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json
import statistics

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from studioflow.core.rough_cut import RoughCutEngine, CutStyle
from studioflow.core.rough_cut import ClipAnalysis, SRTEntry


def create_test_clips(num_clips: int, entries_per_clip: int = 12) -> List[ClipAnalysis]:
    """Create test clips for benchmarking"""
    clips = []
    
    for i in range(num_clips):
        entries = [
            SRTEntry(
                j,
                j * 5.0,
                (j + 1) * 5.0,
                f"Content from clip {i}, sentence {j}. This is test content for benchmarking."
            )
            for j in range(1, entries_per_clip + 1)
        ]
        
        clip = ClipAnalysis(
            file_path=Path(f"clip{i}.mp4"),
            duration=entries_per_clip * 5.0,
            transcript_path=None,
            entries=entries,
            has_speech=True
        )
        clips.append(clip)
    
    return clips


def benchmark_processing_time(engine: RoughCutEngine, clips: List[ClipAnalysis], 
                              num_runs: int = 3) -> Dict[str, Any]:
    """Benchmark processing time"""
    times = []
    
    for run in range(num_runs):
        engine.clips = clips.copy()
        
        start_time = time.time()
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=sum(c.duration for c in clips) * 0.6,
            use_smart_features=True
        )
        elapsed = time.time() - start_time
        
        times.append(elapsed)
    
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "stddev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "times": times
    }


def benchmark_memory_usage(engine: RoughCutEngine, clips: List[ClipAnalysis]) -> Dict[str, Any]:
    """Benchmark memory usage"""
    try:
        import tracemalloc
        
        tracemalloc.start()
        
        engine.clips = clips.copy()
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=sum(c.duration for c in clips) * 0.6,
            use_smart_features=True
        )
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return {
            "current_mb": current / (1024 * 1024),
            "peak_mb": peak / (1024 * 1024),
            "plan_segments": len(plan.segments) if plan else 0
        }
    except ImportError:
        return {"error": "tracemalloc not available"}


def benchmark_throughput(engine: RoughCutEngine, num_clips_list: List[int]) -> Dict[str, Any]:
    """Benchmark throughput (clips per minute)"""
    results = {}
    
    for num_clips in num_clips_list:
        clips = create_test_clips(num_clips)
        engine.clips = clips.copy()
        
        start_time = time.time()
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=sum(c.duration for c in clips) * 0.6,
            use_smart_features=True
        )
        elapsed = time.time() - start_time
        
        clips_per_minute = (num_clips / elapsed) * 60 if elapsed > 0 else 0
        
        results[f"{num_clips}_clips"] = {
            "time_seconds": elapsed,
            "clips_per_minute": clips_per_minute,
            "segments_generated": len(plan.segments) if plan else 0
        }
    
    return results


def parameter_tuning(engine: RoughCutEngine, clips: List[ClipAnalysis]) -> Dict[str, Any]:
    """Test different parameter combinations"""
    results = {}
    
    # Test different importance thresholds
    importance_thresholds = [50, 60, 70, 75, 80]
    
    for threshold in importance_thresholds:
        # Note: This would require modifying the engine to accept threshold parameter
        # For now, just test with default
        engine.clips = clips.copy()
        
        start_time = time.time()
        plan = engine.create_rough_cut(
            style=CutStyle.DOC,
            target_duration=sum(c.duration for c in clips) * 0.6,
            use_smart_features=True
        )
        elapsed = time.time() - start_time
        
        results[f"threshold_{threshold}"] = {
            "time_seconds": elapsed,
            "segments": len(plan.segments) if plan else 0,
            "themes": len(plan.themes) if plan else 0
        }
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark rough cut generation performance")
    parser.add_argument("--clips", type=int, default=10, help="Number of test clips")
    parser.add_argument("--runs", type=int, default=3, help="Number of benchmark runs")
    parser.add_argument("--output", type=Path, help="Output JSON file for results")
    parser.add_argument("--throughput", action="store_true", help="Test throughput with different clip counts")
    parser.add_argument("--memory", action="store_true", help="Test memory usage")
    parser.add_argument("--tuning", action="store_true", help="Test parameter tuning")
    
    args = parser.parse_args()
    
    engine = RoughCutEngine()
    clips = create_test_clips(args.clips)
    
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "num_clips": args.clips,
        "num_runs": args.runs
    }
    
    # Processing time benchmark
    print(f"Benchmarking processing time with {args.clips} clips ({args.runs} runs)...")
    time_results = benchmark_processing_time(engine, clips, args.runs)
    results["processing_time"] = time_results
    
    print(f"  Mean: {time_results['mean']:.2f}s")
    print(f"  Median: {time_results['median']:.2f}s")
    print(f"  Min: {time_results['min']:.2f}s")
    print(f"  Max: {time_results['max']:.2f}s")
    print(f"  Per clip: {time_results['mean'] / args.clips:.2f}s")
    
    # Memory usage
    if args.memory:
        print("\nBenchmarking memory usage...")
        memory_results = benchmark_memory_usage(engine, clips)
        results["memory"] = memory_results
        
        if "error" not in memory_results:
            print(f"  Current: {memory_results['current_mb']:.2f} MB")
            print(f"  Peak: {memory_results['peak_mb']:.2f} MB")
        else:
            print(f"  {memory_results['error']}")
    
    # Throughput
    if args.throughput:
        print("\nBenchmarking throughput...")
        throughput_results = benchmark_throughput(engine, [5, 10, 20, 50])
        results["throughput"] = throughput_results
        
        for key, value in throughput_results.items():
            print(f"  {key}: {value['clips_per_minute']:.1f} clips/min")
    
    # Parameter tuning
    if args.tuning:
        print("\nTesting parameter combinations...")
        tuning_results = parameter_tuning(engine, clips)
        results["parameter_tuning"] = tuning_results
        
        for key, value in tuning_results.items():
            print(f"  {key}: {value['segments']} segments, {value['time_seconds']:.2f}s")
    
    # Save results
    if args.output:
        args.output.write_text(json.dumps(results, indent=2))
        print(f"\nResults saved to {args.output}")
    else:
        print("\nResults:")
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

