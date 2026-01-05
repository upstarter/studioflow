#!/usr/bin/env python3
"""
Helper script to create the Ultimate Fixture Footage
Follows the specification in tests/docs/ULTIMATE_FIXTURE_FOOTAGE.md
"""

import sys
from pathlib import Path

def print_script():
    """Print the recommended script for recording"""
    script = """
# Ultimate Fixture Footage Recording Script
# Duration: ~90 seconds (allows for pauses and content)

"This is our test footage for comprehensive audio marker testing.

[Slate] Scene one intro [Done]
This is the introduction content for scene one. We need at least five seconds of content here.

[Slate] Mark [Done]
This is a marked section of content. This should be a simple standalone marker.

[Slate] Apply best [Done]
[Slate] Scene two main [Done]
This is the main content for scene two. This tests scene numbering and retroactive scoring.

[Slate] Step one setup [Done]
This is the setup step content. This tests step numbering within scenes.

[Slate] Step two execute [Done]
This is the execute step content. This tests multiple steps in sequence.

[Slate] Effect zoom [Done]
This content uses the zoom effect. This tests standalone effect markers.

[Slate] Apply conclusion [Done]
These are the final words. This tests retroactive apply commands. The segment will end naturally at the end of the video."

# Recording Tips:
# 1. Speak clearly and pause briefly after each "slate" and "done"
# 2. Provide at least 5 seconds of content between markers
# 3. Use the exact marker commands as specified
# 4. Record in a quiet environment for best transcription
# 5. Use a camera that records good audio (FX30 or ZV-E10 recommended)
"""
    print(script)

def print_validation_checklist():
    """Print validation checklist"""
    checklist = """
# Validation Checklist After Recording

## 1. File Check
- [ ] File is named: TEST-FIXTURE-comprehensive-markers.MP4
- [ ] File is 30-90 seconds long
- [ ] File size is reasonable (< 500MB for test footage)

## 2. Content Check
- [ ] All marker commands are spoken clearly
- [ ] "slate" and "done" are clearly audible
- [ ] At least 5 seconds of content between each marker
- [ ] All retroactive actions use "apply" (not "ending")

## 3. Test the Fixture
Run the test suite to verify:
  python3 test_unified_pipeline_fixtures.py

Expected results:
- [ ] 6 segments created (not 7 - ending doesn't create segment)
- [ ] Segment 002 is scored "best" (retroactive)
- [ ] Segment 006 is marked "conclusion" (retroactive)
- [ ] No segment created after "ending" marker
- [ ] All markers detected correctly
"""
    print(checklist)

def print_quick_reference():
    """Print quick reference of marker commands"""
    reference = """
# Quick Reference: Marker Commands for Ultimate Fixture

## START Markers (Create Segments)
- slate scene one intro done
- slate scene two main done
- slate step one setup done
- slate step two execute done

## STANDALONE Markers (Create Segments)
- slate mark done
- slate effect zoom done

## RETROACTIVE Markers (Don't Create Segments)
- slate apply best done
- slate apply conclusion done

Note: "ending" is DEPRECATED - use "apply" for all retroactive actions

## Expected Segments (6 total)
1. Segment 001: scene 1, intro (starts at 0:05, ends at 0:15 when next marker starts)
2. Segment 002: mark (starts at 0:15, ends at 0:30 when next marker starts), scored "best"
3. Segment 003: scene 2, main (starts at 0:30, ends at 0:40 when next marker starts)
4. Segment 004: step 1, setup (starts at 0:40, ends at 0:50 when next marker starts)
5. Segment 005: step 2, execute (starts at 0:50, ends at 1:00 when next marker starts)
6. Segment 006: effect zoom (starts at 1:00, ends at end of video), marked "conclusion"

Note: Segments end automatically at the next marker's "slate" timestamp. No explicit end markers needed!
"""
    print(reference)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        # Handle common typos/autocorrect issues
        if command == "script" or command == "scripts":
            print_script()
        elif command == "checklist":
            print_validation_checklist()
        elif command == "reference":
            print_quick_reference()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python3 scripts/create_ultimate_fixture.py [script|checklist|reference]")
            print("\nNote: 'scripts' is accepted as an alias for 'script'")
    else:
        print("=" * 70)
        print("Ultimate Fixture Footage Creation Helper")
        print("=" * 70)
        print("\nCommands:")
        print("  script     - Print the recording script")
        print("  checklist  - Print validation checklist")
        print("  reference  - Print quick reference of marker commands")
        print("\nFull specification: tests/docs/ULTIMATE_FIXTURE_FOOTAGE.md")
        print("\nQuick start:")
        print("  python3 scripts/create_ultimate_fixture.py script > recording_script.txt")
        print("  python3 scripts/create_ultimate_fixture.py checklist > validation.txt")

if __name__ == "__main__":
    main()

