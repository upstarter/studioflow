# FX30 Naming Guide - Automated Clip Naming

**Efficient naming system for Sony FX30 footage with StudioFlow**

---

## The Problem

FX30 records files as: `C0001.MP4`, `C0002.MP4`, etc.

StudioFlow needs descriptive names like: `CAM_HOOK_COH_Contrarian_Take1.mp4`

**Solution:** Automated renaming script + naming template

---

## ⚠️ Important: Duplicate Handling

**Numbered takes like `(1)`, `(2)` are NOT duplicates!**

The system distinguishes between:
- ✅ **Numbered takes** `(1)`, `(2)`, `(3)` → **ALWAYS KEPT** (different recordings)
- ❌ **Normalized duplicates** `_normalized` → **REMOVED** (if original exists)

**Example:**
```
CAM_STEP01_Introduction.mp4          ✅ KEPT (original)
CAM_STEP01_Introduction (1).mp4       ✅ KEPT (retake 1 - different file!)
CAM_STEP01_Introduction (2).mp4       ✅ KEPT (retake 2 - different file!)
CAM_STEP01_Introduction_normalized.mp4  ❌ REMOVED (duplicate of original)
```

**All numbered takes are analyzed and available for selection. The system picks the best one based on quality scores.**

**See:** `DUPLICATE_HANDLING.md` for complete details

---

## Quick Start: Automated Renaming

### Option 1: Use the Renaming Script

```bash
# After importing footage from FX30
cd [PROJECT]/01_footage/A_ROLL/

# Run the renaming helper
python3 ~/studioflow/mydocs/rename_fx30_clips.py

# Follow the interactive prompts
```

### Option 2: Manual Renaming Template

Create a simple text file to track your recordings:

```
Recording Log:
=============
C0001.MP4 → CAM_HOOK_COH_Contrarian_Take1
C0002.MP4 → CAM_HOOK_CH_Curiosity_Take2
C0003.MP4 → CAM_HOOK_PSH_Problem_Take3
C0004.MP4 → CAM_STEP01_Introduction
C0005.MP4 → CAM_STEP01_Introduction (1)  # Retake
C0006.MP4 → CAM_STEP01_Introduction_BEST  # Best take
C0007.MP4 → CAM_STEP02_Setup
C0008.MP4 → SCREEN_STEP02_Configuration
C0009.MP4 → CAM_STEP03_Demo
C0010.MP4 → CAM_CTA_Subscribe
```

Then rename files:
```bash
mv C0001.MP4 CAM_HOOK_COH_Contrarian_Take1.mp4
mv C0002.MP4 CAM_HOOK_CH_Curiosity_Take2.mp4
# ... etc
```

---

## Naming Convention Cheat Sheet

### Hook Clips

```
CAM_HOOK_COH_Contrarian_Take1.mp4
CAM_HOOK_CH_Curiosity_Take2.mp4
CAM_HOOK_PSH_Problem_Take3.mp4
CAM_HOOK_TPH_TimePromise_Take4.mp4
CAM_HOOK_QH_Question_Take5.mp4
```

**Hook Flow Types:**
- `COH` = Contrarian Hook (1.35x multiplier) ⭐ Best
- `CH` = Curiosity Hook (1.3x)
- `AH` = Action Hook (1.25x)
- `PSH` = Problem-Solution Hook (1.2x)
- `TPH` = Time-Promise Hook (1.15x)
- `QH` = Question Hook (1.15x)
- `SH` = Statistic Hook (1.2x)

### Main Content Clips

```
# Talking Head
CAM_STEP01_Introduction.mp4
CAM_STEP02_Setup.mp4
CAM_STEP03_Demo.mp4
CAM_STEP04_Features.mp4
CAM_STEP05_Conclusion.mp4

# Screen Recordings (if tutorial)
SCREEN_STEP01_Installation.mov
SCREEN_STEP02_Configuration.mov
SCREEN_STEP03_Features.mov

# B-Roll
BROLL_STEP01_Product_Shot.mp4
BROLL_STEP02_Environment.mov
```

### Quality Markers

```
# Best Take
CAM_STEP01_Introduction_BEST.mp4

# Selected/Approved
CAM_STEP02_Setup_SELECT.mp4

# Hero Shot
CAM_STEP03_Demo_HERO.mp4

# Test/Backup (lower priority)
CAM_STEP04_Features_TEST.mp4
```

### Retakes & Mistakes

```
# Retake (keep all, system picks best)
CAM_STEP01_Introduction (1).mp4
CAM_STEP01_Introduction (2).mp4
CAM_STEP01_Introduction (3).mp4

# Mistake (auto-excluded)
CAM_STEP01_Introduction_MISTAKE.mp4
CAM_STEP02_Setup_DELETE.mp4
```

**Important:** Numbered takes like `(1)`, `(2)` are **NOT duplicates** - they're different takes! The system:
- ✅ **Keeps all numbered versions** - They represent different takes/attempts
- ✅ **Removes only `_normalized` duplicates** - If original exists, normalized version is excluded
- ✅ **Treats `(1)`, `(2)`, etc. as distinct files** - All will be analyzed and available for selection

### CTA/Outro

```
CAM_CTA_Subscribe.mp4
CAM_OUTRO_Summary.mp4
CAM_OUTRO_ThankYou.mp4
```

---

## Recording Workflow

### During Recording

**1. Record Hook Options First (3-5 takes)**
```
Take 1: Contrarian Hook
Take 2: Curiosity Hook
Take 3: Problem-Solution Hook
Take 4: Time-Promise Hook
Take 5: Question Hook
```

**2. Record Main Content**
- Record each step as separate clip
- If you mess up, keep recording (don't stop)
- Record retake immediately after
- Mark best take mentally or with camera marker

**3. Record CTA/Outro**
- Final clip of recording session

### After Recording (Before Import)

**Option A: Rename on Camera (if supported)**
- Some cameras allow renaming
- Check FX30 manual

**Option B: Use Recording Log**
- Write down what each clip is while recording
- Use log to rename after import

**Option C: Use Renaming Script**
- Import first
- Run automated renaming script
- Follow prompts

---

## Automated Renaming Script

Save this as `mydocs/rename_fx30_clips.py`:

```python
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
```

**Usage:**
```bash
# Make executable
chmod +x mydocs/rename_fx30_clips.py

# Navigate to footage directory
cd [PROJECT]/01_footage/A_ROLL/

# Run script
python3 ~/studioflow/mydocs/rename_fx30_clips.py
```

---

## Recording Template

Use this template while recording to track your clips:

```
Episode: _________________________
Date: _________________________

Recording Log:
=============

HOOKS:
------
C____ → CAM_HOOK_COH_Contrarian_Take1
C____ → CAM_HOOK_CH_Curiosity_Take2
C____ → CAM_HOOK_PSH_Problem_Take3

STEPS:
------
C____ → CAM_STEP01_Introduction
C____ → CAM_STEP01_Introduction (1)  # Retake
C____ → CAM_STEP01_Introduction_BEST  # Best
C____ → CAM_STEP02_Setup
C____ → SCREEN_STEP02_Configuration
C____ → CAM_STEP03_Demo
C____ → CAM_STEP04_Features
C____ → CAM_STEP05_Conclusion

CTA/OUTRO:
----------
C____ → CAM_CTA_Subscribe
C____ → CAM_OUTRO_Summary

MISTAKES (to exclude):
---------------------
C____ → CAM_STEP02_Setup_MISTAKE
```

---

## Quick Reference

### Essential Patterns

```
Hook:        CAM_HOOK_[FLOW]_Description[_Take#][_BEST].mp4
Step:        CAM_STEP##_Description[ (N)][_BEST].mp4
Screen:      SCREEN_STEP##_Description[_BEST].mov
B-Roll:      BROLL_STEP##_Description[_BEST].mp4
CTA:         CAM_CTA_Description.mp4
Outro:       CAM_OUTRO_Description.mp4
Mistake:     CAM_Description_MISTAKE.mp4
```

### Hook Flow Codes

- `COH` = Contrarian (1.35x) ⭐
- `CH` = Curiosity (1.3x)
- `AH` = Action (1.25x)
- `PSH` = Problem-Solution (1.2x)
- `TPH` = Time-Promise (1.15x)
- `QH` = Question (1.15x)
- `SH` = Statistic (1.2x)

### Quality Markers

- `_BEST` = Best take (highest priority)
- `_SELECT` = Selected/approved
- `_HERO` = Hero shot
- `_TEST` = Test/backup (lower priority)

### Retakes

- `(1)`, `(2)`, `(3)` = Different takes (all kept, system picks best)

---

## Tips

1. **Record hooks first** - Get them out of the way
2. **Record multiple hook options** - A/B testing is powerful
3. **Mark best takes immediately** - Add `_BEST` suffix
4. **Don't delete mistakes** - Mark as `_MISTAKE` (auto-excluded)
5. **Use step numbers** - Auto-generates chapters
6. **Keep recording log** - Makes renaming easier

---

**See Also:**
- `EPISODE_WORKFLOW.md` - Complete workflow checklist
- `../docs/FILENAME_CONVENTION.md` - Full naming convention guide
- `../docs/YOUTUBE_HOOK_FLOWS.md` - Hook flow details

