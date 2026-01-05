#!/usr/bin/env python3
"""
Interactive FX30 clip renaming helper
Helps rename FX30 clips (C0001.MP4, etc.) to StudioFlow convention
"""

import os
from pathlib import Path
import re

def get_clip_type():
    """Get clip type from user"""
    print("\nClip Type:")
    print("1. Hook (HOOK)")
    print("2. Step/Topic (STEP##)")
    print("3. Screen Recording (SCREEN_STEP##)")
    print("4. B-Roll (BROLL_STEP##)")
    print("5. CTA/Outro (CTA/OUTRO)")
    print("6. Mistake (MISTAKE - will be excluded)")
    
    choice = input("Enter choice (1-6): ").strip()
    
    types = {
        "1": "HOOK",
        "2": "STEP",
        "3": "SCREEN",
        "4": "BROLL",
        "5": "CTA",
        "6": "MISTAKE"
    }
    
    return types.get(choice, "STEP")

def get_hook_flow():
    """Get hook flow type"""
    print("\nHook Flow Type:")
    print("1. COH - Contrarian (1.35x) ⭐ Best")
    print("2. CH - Curiosity (1.3x)")
    print("3. AH - Action (1.25x)")
    print("4. PSH - Problem-Solution (1.2x)")
    print("5. TPH - Time-Promise (1.15x)")
    print("6. QH - Question (1.15x)")
    print("7. SH - Statistic (1.2x)")
    
    choice = input("Enter choice (1-7): ").strip()
    
    flows = {
        "1": "COH",
        "2": "CH",
        "3": "AH",
        "4": "PSH",
        "5": "TPH",
        "6": "QH",
        "7": "SH"
    }
    
    return flows.get(choice, "CH")

def get_step_number():
    """Get step number"""
    step = input("Step number (01, 02, 03, etc.): ").strip()
    if not step.isdigit():
        step = step.zfill(2)
    return step.zfill(2)

def get_description():
    """Get description"""
    desc = input("Description (e.g., 'Introduction', 'Setup', 'Demo'): ").strip()
    return desc.replace(" ", "_")

def get_quality_marker():
    """Get quality marker"""
    print("\nQuality Marker:")
    print("1. None")
    print("2. BEST (best take)")
    print("3. SELECT (selected/approved)")
    print("4. HERO (hero shot)")
    print("5. TEST (test/backup - lower priority)")
    
    choice = input("Enter choice (1-5): ").strip()
    
    markers = {
        "1": "",
        "2": "_BEST",
        "3": "_SELECT",
        "4": "_HERO",
        "5": "_TEST"
    }
    
    return markers.get(choice, "")

def get_take_number():
    """Get take number for retakes"""
    take = input("Take number (leave empty if not a retake): ").strip()
    if take:
        return f" ({take})"
    return ""

def rename_clip(file_path: Path):
    """Rename a single clip"""
    print(f"\n{'='*60}")
    print(f"Renaming: {file_path.name}")
    print(f"{'='*60}")
    
    clip_type = get_clip_type()
    
    if clip_type == "HOOK":
        flow = get_hook_flow()
        desc = get_description()
        take = get_take_number()
        quality = get_quality_marker()
        new_name = f"CAM_HOOK_{flow}_{desc}{take}{quality}.mp4"
        
    elif clip_type == "SCREEN":
        step = get_step_number()
        desc = get_description()
        quality = get_quality_marker()
        new_name = f"SCREEN_STEP{step}_{desc}{quality}.mov"
        
    elif clip_type == "BROLL":
        step = get_step_number()
        desc = get_description()
        quality = get_quality_marker()
        new_name = f"BROLL_STEP{step}_{desc}{quality}.mp4"
        
    elif clip_type == "CTA":
        desc = get_description()
        new_name = f"CAM_CTA_{desc}.mp4"
        
    elif clip_type == "MISTAKE":
        desc = get_description()
        new_name = f"CAM_{desc}_MISTAKE.mp4"
        
    else:  # STEP
        step = get_step_number()
        desc = get_description()
        take = get_take_number()
        quality = get_quality_marker()
        new_name = f"CAM_STEP{step}_{desc}{take}{quality}.mp4"
    
    print(f"\nNew name: {new_name}")
    confirm = input("Confirm rename? (y/n): ").strip().lower()
    
    if confirm == 'y':
        new_path = file_path.parent / new_name
        if new_path.exists():
            print(f"⚠️  Warning: {new_name} already exists!")
            overwrite = input("Overwrite? (y/n): ").strip().lower()
            if overwrite != 'y':
                print("Skipped.")
                return False
        
        file_path.rename(new_path)
        print(f"✅ Renamed: {file_path.name} → {new_name}")
        return True
    else:
        print("Skipped.")
        return False

def main():
    """Main renaming workflow"""
    print("="*60)
    print("FX30 Clip Renaming Helper")
    print("="*60)
    
    # Get current directory
    cwd = Path.cwd()
    print(f"\nCurrent directory: {cwd}")
    
    # Find FX30 clips (C####.MP4 pattern)
    clips = sorted(cwd.glob("C*.MP4")) + sorted(cwd.glob("C*.mp4"))
    
    if not clips:
        print("\n❌ No FX30 clips found (C####.MP4 pattern)")
        print("Make sure you're in the footage directory with FX30 clips")
        return
    
    print(f"\nFound {len(clips)} FX30 clips:")
    for i, clip in enumerate(clips, 1):
        print(f"  {i}. {clip.name}")
    
    print("\n" + "="*60)
    print("Rename each clip (press Ctrl+C to exit)")
    print("="*60)
    
    renamed = 0
    for clip in clips:
        try:
            if rename_clip(clip):
                renamed += 1
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ Error renaming {clip.name}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Renamed {renamed} of {len(clips)} clips")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()


