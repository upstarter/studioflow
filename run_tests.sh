#!/bin/bash
# Comprehensive test runner for StudioFlow

set -e

echo "=========================================="
echo "StudioFlow Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test categories
PASSED=0
FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Running $test_name... "
    if eval "$test_command" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Output:"
        tail -20 /tmp/test_output.log
        ((FAILED++))
        return 1
    fi
}

# Core tests
echo "=== Core Functionality ==="
run_test "Configuration" "pytest tests/test_config.py -v"
run_test "CLI Commands" "pytest tests/test_cli.py -v"
run_test "Unified Import (Unit)" "pytest tests/test_unified_import_unit.py -v"
run_test "Unified Import (E2E)" "pytest tests/test_unified_import_e2e.py -v"

# Marker tests
echo ""
echo "=== Audio Markers ==="
run_test "Audio Markers Basic" "pytest tests/test_audio_markers.py -v"
run_test "Audio Markers Comprehensive" "pytest tests/test_audio_markers_comprehensive.py -v"
run_test "Audio Markers Integration" "pytest tests/test_audio_markers_integration.py -v"
run_test "Audio Markers Segments" "pytest tests/test_audio_markers_segments.py -v"
run_test "Audio Markers Permutations" "pytest tests/test_audio_markers_permutations.py -v"
run_test "Marker Commands" "pytest tests/test_marker_commands.py -v"
run_test "Marker E2E" "pytest tests/test_marker_e2e.py -v"
run_test "Marker Integration" "pytest tests/test_marker_integration.py -v"
run_test "Marker Property" "pytest tests/test_marker_property.py -v"
run_test "Transcription Markers" "pytest tests/test_transcription_markers.py -v"

# Workflow tests
echo ""
echo "=== Workflow ==="
run_test "Rough Cut Integration" "pytest tests/test_rough_cut_integration.py -v"
run_test "Smart Rough Cut" "pytest tests/test_smart_rough_cut.py -v"
run_test "E2E Workflow" "pytest tests/test_e2e_workflow.py -v"

# Utility tests
echo ""
echo "=== Utilities ==="
run_test "NLP Fallbacks" "pytest tests/test_nlp_fallbacks.py -v"

# Fixture pipeline test
echo ""
echo "=== Fixture Pipeline ==="
if [ -f "test_unified_pipeline_fixtures.py" ]; then
    run_test "Unified Pipeline Fixtures" "python test_unified_pipeline_fixtures.py"
else
    echo -e "${YELLOW}⚠ Skipping fixture pipeline test (file not found)${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}Failed: $FAILED${NC}"
    echo ""
    echo "All tests passed! ✅"
    exit 0
fi

