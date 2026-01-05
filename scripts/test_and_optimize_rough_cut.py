#!/usr/bin/env python3
"""
Iterative testing and optimization script for rough cut generation
Runs tests, measures performance, and suggests optimizations
"""

import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_tests() -> Dict[str, Any]:
    """Run all rough cut tests and collect results"""
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": {}
    }
    
    test_files = [
        "tests/test_smart_rough_cut.py",
        "tests/test_nlp_fallbacks.py",
        "tests/test_rough_cut_integration.py"
    ]
    
    for test_file in test_files:
        if not Path(test_file).exists():
            continue
        
        print(f"\n{'='*60}")
        print(f"Running {test_file}...")
        print('='*60)
        
        start_time = time.time()
        try:
            # Run pytest
            result = subprocess.run(
                ["python3", "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            elapsed = time.time() - start_time
            
            # Parse output
            output = result.stdout + result.stderr
            passed = output.count("PASSED")
            failed = output.count("FAILED")
            errors = output.count("ERROR")
            
            results["tests"][test_file] = {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "time_seconds": elapsed,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
            
            print(f"  Passed: {passed}, Failed: {failed}, Errors: {errors}")
            if failed > 0 or errors > 0:
                print(f"  Output:\n{output[-500:]}")  # Last 500 chars
            
        except subprocess.TimeoutExpired:
            results["tests"][test_file] = {
                "error": "Timeout after 300 seconds"
            }
        except Exception as e:
            results["tests"][test_file] = {
                "error": str(e)
            }
    
    return results


def benchmark_performance() -> Dict[str, Any]:
    """Benchmark rough cut performance"""
    print(f"\n{'='*60}")
    print("Benchmarking Performance...")
    print('='*60)
    
    try:
        result = subprocess.run(
            ["python3", "scripts/benchmark_rough_cut.py", "--clips", "10", "--runs", "3", "--memory"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(result.stdout)
            return {"success": True, "output": result.stdout}
        else:
            print(f"Benchmark failed: {result.stderr}")
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_code_quality() -> Dict[str, Any]:
    """Analyze code for potential improvements"""
    print(f"\n{'='*60}")
    print("Analyzing Code Quality...")
    print('='*60)
    
    issues = []
    suggestions = []
    
    # Check for common performance issues
    rough_cut_file = Path("studioflow/core/rough_cut.py")
    if rough_cut_file.exists():
        content = rough_cut_file.read_text()
        
        # Check for uncached NLP calls
        if "SentimentIntensityAnalyzer()" in content and content.count("SentimentIntensityAnalyzer()") > 1:
            issues.append("VADER analyzer created multiple times - should be cached")
        
        # Check for inefficient loops
        if "for quote in all_quotes:" in content and "for seg in self.interview_segments" in content:
            nested_count = content.count("for seg in self.interview_segments if quote in s.quotes")
            if nested_count > 0:
                suggestions.append("Consider pre-computing quote-segment mappings to avoid nested loops")
        
        # Check for missing caching
        if "_cached" not in content or content.count("_cached") < 3:
            suggestions.append("Consider adding more caching for frequently computed values")
    
    return {
        "issues": issues,
        "suggestions": suggestions
    }


def generate_optimization_report(test_results: Dict, benchmark_results: Dict, 
                                code_analysis: Dict) -> str:
    """Generate optimization report"""
    report = []
    report.append("=" * 60)
    report.append("ROUGH CUT OPTIMIZATION REPORT")
    report.append("=" * 60)
    report.append("")
    
    # Test Results
    report.append("TEST RESULTS")
    report.append("-" * 60)
    total_passed = sum(t.get("passed", 0) for t in test_results.get("tests", {}).values())
    total_failed = sum(t.get("failed", 0) for t in test_results.get("tests", {}).values())
    report.append(f"Total Passed: {total_passed}")
    report.append(f"Total Failed: {total_failed}")
    report.append("")
    
    for test_file, result in test_results.get("tests", {}).items():
        if result.get("success"):
            report.append(f"✓ {test_file}: {result.get('passed', 0)} passed")
        else:
            report.append(f"✗ {test_file}: {result.get('failed', 0)} failed")
    report.append("")
    
    # Performance
    report.append("PERFORMANCE")
    report.append("-" * 60)
    if benchmark_results.get("success"):
        report.append(benchmark_results.get("output", "Benchmark completed"))
    else:
        report.append("Benchmark not available")
    report.append("")
    
    # Code Quality
    report.append("CODE QUALITY ANALYSIS")
    report.append("-" * 60)
    if code_analysis.get("issues"):
        report.append("Issues Found:")
        for issue in code_analysis["issues"]:
            report.append(f"  - {issue}")
    else:
        report.append("No critical issues found")
    
    if code_analysis.get("suggestions"):
        report.append("\nSuggestions:")
        for suggestion in code_analysis["suggestions"]:
            report.append(f"  - {suggestion}")
    report.append("")
    
    # Recommendations
    report.append("RECOMMENDATIONS")
    report.append("-" * 60)
    
    if total_failed > 0:
        report.append("1. Fix failing tests before further optimization")
    
    if total_passed > 0 and total_failed == 0:
        report.append("1. All tests passing - ready for performance tuning")
        report.append("2. Consider adding more integration tests with real footage")
        report.append("3. Collect editor feedback to improve quote selection")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)


def main():
    print("Starting Iterative Testing and Optimization...")
    print("=" * 60)
    
    # Run tests
    test_results = run_tests()
    
    # Benchmark performance
    benchmark_results = benchmark_performance()
    
    # Analyze code
    code_analysis = analyze_code_quality()
    
    # Generate report
    report = generate_optimization_report(test_results, benchmark_results, code_analysis)
    print(report)
    
    # Save results
    results_file = Path("rough_cut_optimization_results.json")
    results = {
        "test_results": test_results,
        "benchmark_results": benchmark_results,
        "code_analysis": code_analysis
    }
    results_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {results_file}")
    
    # Return exit code based on test results
    total_failed = sum(t.get("failed", 0) for t in test_results.get("tests", {}).values())
    return 1 if total_failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

