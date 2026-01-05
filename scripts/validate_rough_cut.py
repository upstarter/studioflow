#!/usr/bin/env python3
"""
Validation tool for rough cut accuracy
Compares generated rough cuts against ground truth manual edits
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from studioflow.core.rough_cut import RoughCutEngine, CutStyle, Segment


def parse_edl(edl_path: Path) -> List[Dict[str, Any]]:
    """Parse EDL file into segments"""
    segments = []
    
    if not edl_path.exists():
        return segments
    
    content = edl_path.read_text()
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # EDL format: "001  clipname  V  C  src_in  src_out  rec_in  rec_out"
        if line and not line.startswith('*') and not line.startswith('TITLE'):
            parts = line.split()
            if len(parts) >= 8:
                try:
                    src_in = _parse_timecode(parts[4])
                    src_out = _parse_timecode(parts[5])
                    
                    segments.append({
                        "source": parts[1],
                        "src_in": src_in,
                        "src_out": src_out,
                        "duration": src_out - src_in
                    })
                except (ValueError, IndexError):
                    pass
        
        i += 1
    
    return segments


def _parse_timecode(tc: str) -> float:
    """Parse timecode HH:MM:SS:FF to seconds"""
    parts = tc.split(':')
    if len(parts) == 4:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        frames = int(parts[3])
        fps = 30.0  # Default
        return hours * 3600 + minutes * 60 + seconds + frames / fps
    return 0.0


def compare_segments(generated: List[Segment], ground_truth: List[Dict[str, Any]], 
                    tolerance: float = 1.0) -> Dict[str, Any]:
    """Compare generated segments against ground truth"""
    matches = 0
    overlaps = 0
    misses = 0
    false_positives = 0
    
    # Convert generated segments to comparable format
    gen_segments = [
        {
            "source": str(seg.source_file),
            "src_in": seg.start_time,
            "src_out": seg.end_time,
            "duration": seg.end_time - seg.start_time
        }
        for seg in generated
    ]
    
    # Check each ground truth segment
    for gt_seg in ground_truth:
        matched = False
        
        for gen_seg in gen_segments:
            # Check if segments overlap (within tolerance)
            overlap_start = max(gt_seg["src_in"], gen_seg["src_in"])
            overlap_end = min(gt_seg["src_out"], gen_seg["src_out"])
            overlap_duration = max(0, overlap_end - overlap_start)
            
            if overlap_duration > tolerance:
                if abs(gt_seg["src_in"] - gen_seg["src_in"]) < tolerance and \
                   abs(gt_seg["src_out"] - gen_seg["src_out"]) < tolerance:
                    matches += 1
                    matched = True
                else:
                    overlaps += 1
                    matched = True
                break
        
        if not matched:
            misses += 1
    
    # Count false positives (generated segments not in ground truth)
    for gen_seg in gen_segments:
        matched = False
        for gt_seg in ground_truth:
            overlap_start = max(gt_seg["src_in"], gen_seg["src_in"])
            overlap_end = min(gt_seg["src_out"], gen_seg["src_out"])
            if max(0, overlap_end - overlap_start) > tolerance:
                matched = True
                break
        
        if not matched:
            false_positives += 1
    
    total_gt = len(ground_truth)
    total_gen = len(generated)
    
    precision = matches / total_gen if total_gen > 0 else 0.0
    recall = matches / total_gt if total_gt > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "matches": matches,
        "overlaps": overlaps,
        "misses": misses,
        "false_positives": false_positives,
        "total_ground_truth": total_gt,
        "total_generated": total_gen,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score
    }


def validate_narrative_structure(plan, expected_sections: List[str]) -> Dict[str, Any]:
    """Validate narrative arc structure"""
    arc = plan.narrative_arc
    
    results = {
        "expected_sections": expected_sections,
        "found_sections": list(arc.keys()),
        "section_counts": {},
        "section_durations": {}
    }
    
    for section in expected_sections:
        if section in arc:
            segs = arc[section]
            results["section_counts"][section] = len(segs)
            results["section_durations"][section] = sum(
                s.end_time - s.start_time for s in segs
            )
        else:
            results["section_counts"][section] = 0
            results["section_durations"][section] = 0.0
    
    return results


def generate_accuracy_report(generated_edl: Path, ground_truth_edl: Path,
                            generated_plan, output_path: Path):
    """Generate comprehensive accuracy report"""
    
    # Parse EDLs
    gen_segments = parse_edl(generated_edl)
    gt_segments = parse_edl(ground_truth_edl)
    
    # Compare segments
    comparison = compare_segments(
        generated_plan.segments if generated_plan else [],
        gt_segments
    )
    
    # Validate structure
    expected_sections = ['hook', 'setup', 'act_1', 'act_2', 'act_3', 'conclusion']
    structure_validation = validate_narrative_structure(
        generated_plan,
        expected_sections
    ) if generated_plan else {}
    
    # Generate report
    report = {
        "timestamp": Path(generated_edl).stat().st_mtime if generated_edl.exists() else None,
        "segment_comparison": comparison,
        "narrative_structure": structure_validation,
        "summary": {
            "precision": comparison["precision"],
            "recall": comparison["recall"],
            "f1_score": comparison["f1_score"],
            "segment_match_rate": comparison["matches"] / comparison["total_ground_truth"] if comparison["total_ground_truth"] > 0 else 0.0
        }
    }
    
    # Save report
    output_path.write_text(json.dumps(report, indent=2))
    
    # Print summary
    print("Accuracy Report")
    print("=" * 50)
    print(f"Precision: {comparison['precision']:.2%}")
    print(f"Recall: {comparison['recall']:.2%}")
    print(f"F1 Score: {comparison['f1_score']:.2%}")
    print(f"\nMatches: {comparison['matches']}/{comparison['total_ground_truth']}")
    print(f"Overlaps: {comparison['overlaps']}")
    print(f"Misses: {comparison['misses']}")
    print(f"False Positives: {comparison['false_positives']}")
    
    if structure_validation:
        print("\nNarrative Structure:")
        for section, count in structure_validation.get("section_counts", {}).items():
            duration = structure_validation.get("section_durations", {}).get(section, 0.0)
            print(f"  {section}: {count} segments ({duration:.1f}s)")
    
    print(f"\nFull report saved to {output_path}")
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Validate rough cut accuracy against ground truth")
    parser.add_argument("generated_edl", type=Path, help="Generated rough cut EDL")
    parser.add_argument("ground_truth_edl", type=Path, help="Ground truth manual edit EDL")
    parser.add_argument("--output", type=Path, help="Output JSON report file")
    parser.add_argument("--tolerance", type=float, default=1.0, 
                       help="Time tolerance in seconds for matching segments")
    
    args = parser.parse_args()
    
    if not args.generated_edl.exists():
        print(f"Error: Generated EDL not found: {args.generated_edl}")
        return 1
    
    if not args.ground_truth_edl.exists():
        print(f"Error: Ground truth EDL not found: {args.ground_truth_edl}")
        return 1
    
    # For now, we need the plan object - in real usage, this would be saved/loaded
    # For validation script, we'll parse from EDL
    output_path = args.output or args.generated_edl.parent / "validation_report.json"
    
    # Generate report (without plan object for now)
    gen_segments = parse_edl(args.generated_edl)
    gt_segments = parse_edl(args.ground_truth_edl)
    
    # Convert to Segment objects for comparison
    from studioflow.core.rough_cut import Segment
    gen_segment_objects = [
        Segment(
            source_file=Path(seg["source"]),
            start_time=seg["src_in"],
            end_time=seg["src_out"],
            text="",
            score=0.0
        )
        for seg in gen_segments
    ]
    
    comparison = compare_segments(gen_segment_objects, gt_segments, args.tolerance)
    
    report = {
        "timestamp": args.generated_edl.stat().st_mtime,
        "segment_comparison": comparison,
        "summary": {
            "precision": comparison["precision"],
            "recall": comparison["recall"],
            "f1_score": comparison["f1_score"],
        }
    }
    
    output_path.write_text(json.dumps(report, indent=2))
    
    print("Accuracy Report")
    print("=" * 50)
    print(f"Precision: {comparison['precision']:.2%}")
    print(f"Recall: {comparison['recall']:.2%}")
    print(f"F1 Score: {comparison['f1_score']:.2%}")
    print(f"\nMatches: {comparison['matches']}/{comparison['total_ground_truth']}")
    print(f"Overlaps: {comparison['overlaps']}")
    print(f"Misses: {comparison['misses']}")
    print(f"False Positives: {comparison['false_positives']}")
    print(f"\nFull report saved to {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

