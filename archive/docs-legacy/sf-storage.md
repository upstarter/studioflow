# sf-storage - Storage Tier Management

## Overview
`sf-storage` manages video projects across different storage tiers, optimizing for speed, cost, and accessibility. It implements a hierarchical storage system aligned with video production workflows.

## Installation
```bash
sf-storage  # Direct command
sf storage  # Via master command
sfstat      # Alias for status (after sourcing .bashrc)
```

## Storage Tiers

### 1. Ingest (/mnt/ingest)
- **Purpose**: Initial footage import from cameras/cards
- **Speed**: Fastest SSD
- **Duration**: Temporary (24-48 hours)
- **Use Case**: SD card dumps, initial organization

### 2. Active (/mnt/studio/Projects)
- **Purpose**: Current editing projects
- **Speed**: Fast SSD/NVMe
- **Duration**: Project duration
- **Use Case**: DaVinci Resolve active projects

### 3. Render (/mnt/render)
- **Purpose**: Export and rendering workspace
- **Speed**: Fast write speeds
- **Duration**: Until delivery
- **Use Case**: Final exports, drafts, versions

### 4. Library (/mnt/library)
- **Purpose**: Completed projects, reusable assets
- **Speed**: Balanced performance
- **Duration**: 6-12 months
- **Use Case**: Reference materials, templates

### 5. Archive (/mnt/archive)
- **Purpose**: Long-term storage
- **Speed**: Slower, cost-optimized
- **Duration**: Indefinite
- **Use Case**: Completed projects, backups

### 6. NAS (/mnt/nas)
- **Purpose**: Network attached storage
- **Speed**: Network-dependent
- **Duration**: Permanent
- **Use Case**: Shared assets, backups, LUTs

## Commands

### status
Show storage usage across all tiers.

```bash
sf-storage status
sf-storage status --json  # Machine-readable output
```

**Output:**
- Tier name and path
- Used/available space
- Percentage full
- File count
- Color-coded warnings (>80% = yellow, >90% = red)

### move
Move project between storage tiers.

```bash
sf-storage move "My Project" archive
sf-storage move "Tutorial" active --force
```

**Options:**
- `--force` - Skip confirmation prompt
- Validates destination has space
- Updates project metadata
- Preserves directory structure

### archive
Move project to archive tier (shortcut).

```bash
sf-storage archive "Old Project"
sf-storage archive "2024 Projects" --pattern "2024*"
```

### optimize
Suggest storage optimizations.

```bash
sf-storage optimize
sf-storage optimize --execute  # Apply suggestions
```

**Analyzes:**
- Projects not modified in 30+ days
- Large files in fast tiers
- Duplicate content
- Tier usage patterns

**Suggests:**
- Projects to archive
- Files to compress
- Tiers to rebalance

## Automation Features

### Auto-Archive Rules
```json
{
  "rules": [
    {"tier": "active", "age_days": 30, "action": "suggest_archive"},
    {"tier": "render", "age_days": 7, "action": "auto_compress"},
    {"tier": "ingest", "age_days": 2, "action": "alert"}
  ]
}
```

### Space Monitoring
- Automatic alerts when tier >80% full
- Daily optimization suggestions
- Project size tracking

## Integration Examples

### With sf-project
```bash
# Create project in active tier
sf-project create "New Video" && sf-storage status

# Archive completed project
sf-storage archive "$(sf-project list | head -1)"
```

### With sf-resolve
```bash
# Move to render tier for export
sf-storage move "My Project" render
sf-resolve render "My Project"

# Archive after delivery
sf-storage archive "My Project"
```

### In Scripts
```bash
#!/bin/bash
# Auto-archive old projects
sf-storage status --json | jq '.tiers.active.projects[] | 
select(.age_days > 30) | .name' | while read proj; do
  sf-storage archive "$proj"
done
```

## Performance Optimization

### Tier Recommendations
- **Ingest**: NVMe SSD (500GB min)
- **Active**: SSD (2TB recommended)
- **Render**: Fast HDD or SSD (1TB)
- **Library**: HDD RAID (4TB+)
- **Archive**: HDD or cloud (unlimited)

### Best Practices
1. **Keep active tier <70% full** for optimal performance
2. **Archive weekly** to maintain organization
3. **Use render tier** for exports, not active
4. **Compress before archiving** (50-70% savings)
5. **Maintain 20% free space** on each tier

## Configuration

Edit `~/.config/studioflow/storage.yml`:
```yaml
tiers:
  ingest:
    path: /mnt/ingest
    warn_percent: 80
    auto_clean: true
  active:
    path: /mnt/studio/Projects
    warn_percent: 70
  custom:
    path: /mnt/my-storage
    warn_percent: 90

auto_archive:
  enabled: true
  age_days: 30
  compress: true
```

## Troubleshooting

**"No space left on tier":**
- Run `sf-storage optimize` for suggestions
- Move projects to slower tiers
- Compress or delete render files

**"Permission denied":**
- Check mount permissions
- Ensure user owns tier directories
- Run with appropriate permissions

**"Project not found":**
- Use `sf-project list` to see available projects
- Check if project was already archived
- Search with `find /mnt -name "*ProjectName*"`

## JSON Events

For automation integration:
```json
{
  "event": "project_moved",
  "timestamp": "2025-01-14T10:30:00Z",
  "project": "My_Project",
  "from_tier": "active",
  "to_tier": "archive",
  "size_mb": 15000
}
```

## Related Tools

- `sf-project` - Create and manage projects
- `sf-capture` - Import footage to ingest tier
- `sf-resolve` - Work with active tier projects
- `sf-archive` - Advanced archive management