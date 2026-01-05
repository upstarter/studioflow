# StudioFlow Episode Naming Convention

## Core Principles
- **Sortable**: Episodes naturally order by date and number
- **Searchable**: Easy to find specific episodes or series
- **Automation-friendly**: Predictable patterns for scripts
- **Human-readable**: Clear at a glance what each episode is

## Recommended Formats

### 1. Series Episodes (Numbered)
**Format**: `YYYYMMDD_Series_Name_E##`

Examples:
- `20250920_StudioFlow_Tutorial_E01`
- `20250920_StudioFlow_Tutorial_E02`
- `20250921_Python_Course_E01`
- `20250922_Python_Course_E02`

Benefits:
- Episodes group together naturally
- Clear episode numbering
- Date shows production timeline
- E## format is universally understood

### 2. Season + Episode (TV Style)
**Format**: `YYYYMMDD_Series_S##E##`

Examples:
- `20250920_Tech_Reviews_S01E01`
- `20250920_Tech_Reviews_S01E02`
- `20251001_Tech_Reviews_S02E01`

Benefits:
- Professional broadcast standard
- Supports long-running series
- Clear season breaks
- Familiar to viewers

### 3. Standalone Videos (No Series)
**Format**: `YYYYMMDD_Descriptive_Title`

Examples:
- `20250920_iPhone_15_Review`
- `20250921_Build_Gaming_PC`
- `20250922_React_vs_Vue_Comparison`

Benefits:
- Each video is independent
- SEO-friendly titles
- No episode tracking needed
- Maximum flexibility

### 4. Daily/Weekly Shows
**Format**: `YYYYMMDD_Show_Name_MMDD` or `YYYYMMDD_Show_Name_Week##`

Examples:
- `20250920_Daily_News_0920`
- `20250920_Weekly_Roundup_Week38`
- `20250920_Morning_Show_Fri`

Benefits:
- Date-based episodes
- No manual numbering
- Automatic from date
- Clear schedule pattern

## Automation Patterns

### Episode Increment Function
```python
def get_next_episode_number(series_name: str) -> int:
    """Find highest episode number and increment"""
    import re
    from pathlib import Path

    projects_dir = Path("/mnt/studio/Projects")
    pattern = re.compile(rf"\d{{8}}_{series_name}_E(\d{{2}})")

    max_episode = 0
    for project in projects_dir.iterdir():
        match = pattern.match(project.name)
        if match:
            episode_num = int(match.group(1))
            max_episode = max(max_episode, episode_num)

    return max_episode + 1

# Usage
next_ep = get_next_episode_number("StudioFlow_Tutorial")
episode_name = f"StudioFlow_Tutorial_E{next_ep:02d}"
```

### Series Detection
```python
def detect_series(project_name: str) -> tuple:
    """Extract series and episode from name"""
    import re

    # Pattern: Series_E##
    pattern1 = re.compile(r"(\d{8})_(.+)_E(\d{2})$")
    # Pattern: Series_S##E##
    pattern2 = re.compile(r"(\d{8})_(.+)_S(\d{2})E(\d{2})$")

    if match := pattern1.match(project_name):
        return match.group(2), f"E{match.group(3)}"
    elif match := pattern2.match(project_name):
        return match.group(2), f"S{match.group(3)}E{match.group(4)}"
    else:
        return None, None
```

## Best Practices

### DO:
- ✅ Use consistent format within a series
- ✅ Zero-pad episode numbers (E01, not E1)
- ✅ Keep series names identical across episodes
- ✅ Use underscores as separators
- ✅ Include date for production tracking

### DON'T:
- ❌ Mix formats in same series
- ❌ Use spaces or special characters
- ❌ Change series name mid-production
- ❌ Skip episode numbers
- ❌ Use ambiguous abbreviations

## YouTube & Platform Considerations

### YouTube Title (Displayed)
The project name doesn't have to match YouTube title:
- **Project**: `20250920_React_Tutorial_E01`
- **YouTube**: "React Tutorial for Beginners - Part 1"

### Metadata Mapping
```yaml
# .sf/episode.yaml
project_id: 20250920_React_Tutorial_E01
youtube:
  title: "React Tutorial for Beginners - Part 1"
  playlist: "React Tutorial Series"
  episode: 1
instagram:
  title: "React Basics #1"
  series: "react_tutorial"
tiktok:
  title: "Learn React in 60 Seconds"
  part: 1
```

## Recommended Default: Series with Episodes

**Format**: `YYYYMMDD_Series_Name_E##`

This format is recommended because:
1. **Simple** - Just series name + episode number
2. **Scalable** - Supports 99 episodes (E01-E99)
3. **Clear** - Anyone understands E01 means Episode 1
4. **Sortable** - Groups series together, orders by date+episode
5. **Flexible** - Works for tutorials, vlogs, reviews, etc.

## Implementation in sf-project

```bash
# Create next episode automatically
sf-project create "StudioFlow Tutorial" --series --auto-increment
# Creates: 20250920_StudioFlow_Tutorial_E03 (if E02 exists)

# Create specific episode
sf-project create "StudioFlow Tutorial" --episode 5
# Creates: 20250920_StudioFlow_Tutorial_E05

# Create standalone
sf-project create "iPhone 15 Review"
# Creates: 20250920_iPhone_15_Review

# Create daily show
sf-project create "Daily News" --daily
# Creates: 20250920_Daily_News_0920
```

## Migration Examples

### From Old Format → New Format
```
Old: Tutorial_Part_1
New: 20250920_Tutorial_E01

Old: 2025-09-20-video
New: 20250920_Video_Title

Old: my video (final) v3
New: 20250920_My_Video_E01
```

## Automation Benefits

With consistent naming:
1. **Auto-thumbnail**: Use series template + episode number
2. **Auto-playlist**: Add to series playlist automatically
3. **Auto-metadata**: Inherit series tags and description
4. **Auto-render**: Use series-specific render settings
5. **Auto-backup**: Group series backups together

## Conclusion

Recommended format for most users:
- **Series**: `YYYYMMDD_Series_Name_E##`
- **Standalone**: `YYYYMMDD_Descriptive_Title`

This provides the best balance of:
- Human readability
- Automation capability
- Platform compatibility
- Future scalability