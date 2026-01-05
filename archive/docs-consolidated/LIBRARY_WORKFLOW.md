# Library Workflow Optimization Guide

## Overview

StudioFlow has been optimized for working with the `/mnt/library/` directory structure where Resolve projects are managed. This document explains the optimizations and how to use them.

## What Changed

### 1. Resolve API Updates

**File:** `studioflow/core/resolve_api.py`

- **FX30ProjectSettings** now defaults to library paths:
  - Cache: `/mnt/library/CACHE`
  - Proxies: `/mnt/library/PROXIES`
  - Working folder: `/mnt/library/PROJECTS`

- **ResolveDirectAPI.create_project()** automatically detects and uses `/mnt/library` if it exists
- Paths are auto-configured when creating projects

### 2. New Library Commands

**File:** `studioflow/cli/commands/library.py`

New command group: `sf library` with subcommands:

- `sf library status` - Show library workspace status and structure
- `sf library init` - Initialize library directory structure
- `sf library create` - Create new Resolve project in library
- `sf library projects` - List all projects in library
- `sf library optimize` - Cleanup and optimize library workspace

### 3. Storage System Updates

**File:** `studioflow/core/storage.py`

- Library tier description updated to reflect it's used for Resolve projects
- Better integration with `/mnt/library` structure

## Quick Start

### 1. Initialize Library Workspace

```bash
# Initialize /mnt/library with standard structure
sf library init

# This creates:
# /mnt/library/
#   ├── PROJECTS/
#   │   ├── DOCS/
#   │   ├── EPISODES/
#   │   └── FILMS/
#   ├── CACHE/
#   ├── PROXIES/
#   ├── EXPORTS/
#   │   ├── YOUTUBE/
#   │   ├── INSTAGRAM/
#   │   └── TIKTOK/
#   └── ASSETS/
#       ├── MUSIC/
#       ├── SFX/
#       ├── GRAPHICS/
#       └── LUTS/
```

### 2. Check Library Status

```bash
# View library structure and disk usage
sf library status

# Output shows:
# - Directory structure
# - File counts
# - Disk usage
# - Resolve connection status
```

### 3. Create Resolve Project

```bash
# Create episode project
sf library create "EP001_My_Episode" --type episode

# Create documentary project
sf library create "DOC001_Dad_Project" --type doc --media /path/to/footage

# Create film project
sf library create "FILM001_Short" --type film
```

This automatically:
- Creates project in appropriate library subdirectory
- Configures Resolve with library paths (cache, proxies)
- Sets up bin structure
- Creates timeline stack
- Imports media if provided

### 4. List Projects

```bash
# List all projects
sf library projects

# Filter by type
sf library projects --type episode
sf library projects --type doc
```

### 5. Work with Existing Projects

```bash
# Check what's in your library
sf library status

# Sync Resolve project (if already created)
sf resolve sync --project "EP001_My_Episode"
```

## Directory Structure

```
/mnt/library/
├── PROJECTS/           # Resolve project files
│   ├── DOCS/          # Documentary projects
│   ├── EPISODES/      # Episode projects
│   └── FILMS/         # Film projects
├── CACHE/             # Resolve cache files
├── PROXIES/           # Proxy media files
├── EXPORTS/           # Final exports
│   ├── YOUTUBE/
│   ├── INSTAGRAM/
│   └── TIKTOK/
└── ASSETS/            # Reusable assets
    ├── MUSIC/
    ├── SFX/
    ├── GRAPHICS/
    └── LUTS/
```

## Resolve Integration

When you create a project using `sf library create`, the Resolve project is automatically configured with:

- **Working Folder:** `/mnt/library/PROJECTS/{type}/{project_name}`
- **Cache Folder:** `/mnt/library/CACHE`
- **Proxy Media:** Uses proxies from `/mnt/library/PROXIES`

### Manual Resolve Setup

If you prefer to create Resolve projects manually:

```python
from studioflow.core.resolve_api import ResolveDirectAPI, FX30ProjectSettings
from pathlib import Path

api = ResolveDirectAPI()
settings = FX30ProjectSettings()  # Automatically uses /mnt/library paths

# Create project
api.create_project("My_Project", settings, library_path=Path("/mnt/library"))
```

## Configuration

The library path is automatically detected, but you can configure it:

```bash
# Set library path in config
sf config --set storage.library=/mnt/library

# Or edit config file directly
sf config --edit
```

## Workflow Examples

### Complete Episode Workflow

```bash
# 1. Initialize library (one-time)
sf library init

# 2. Import Sony camera footage
sf import-sony --output /mnt/library/PROJECTS/EPISODES/EP001_Raw/01_footage

# 3. Create Resolve project
sf library create "EP001_My_Episode" --type episode \
  --media /mnt/library/PROJECTS/EPISODES/EP001_Raw/01_footage

# 4. Work in Resolve (project is now open)

# 5. Export when ready
sf export-youtube /mnt/library/EXPORTS/YOUTUBE/final.mp4

# 6. Check all projects
sf library projects
```

### Documentary Project Workflow

```bash
# 1. Create project with media
sf library create "DOC001_Dad" --type doc \
  --media /mnt/ingest/Camera/Card_01

# Project automatically:
# - Created in /mnt/library/PROJECTS/DOCS/DOC001_Dad
# - Resolve project configured with library paths
# - Media imported and organized
# - Bins and timelines created

# 2. Edit in Resolve

# 3. Export
sf resolve export final.mp4 --platform youtube
```

## Benefits

1. **Organized Structure** - Clear separation of projects, cache, exports
2. **Path Optimization** - Resolve automatically uses library paths
3. **Easy Discovery** - `sf library projects` shows all your work
4. **Storage Management** - Cache and proxies organized separately
5. **Multi-Project** - Easy to manage multiple projects in one location

## Migration from Old Structure

If you have existing projects in different locations:

1. Move projects to `/mnt/library/PROJECTS/{type}/`
2. Run `sf library init` to create structure
3. Re-link projects in Resolve if needed

Or keep existing structure and just use library commands for new projects.

## Troubleshooting

### Library path not found

```bash
# Check if library exists
ls -la /mnt/library

# Initialize if missing
sf library init
```

### Resolve can't find projects

```bash
# Check Resolve connection
sf resolve status

# List projects to verify location
sf library projects

# Sync specific project
sf resolve sync --project "PROJECT_NAME"
```

### Cache/proxy issues

```bash
# Clean up old cache
sf library optimize --cleanup-cache

# Check disk usage
sf library status
```

## Advanced Usage

### Custom Library Location

```bash
# Use different library path
sf library init --path /mnt/my_custom_library

# Create project in custom location
sf library create "My_Project" --library /mnt/my_custom_library
```

### Integration with Existing Workflow

If you already use `/mnt/library`, the commands work with your existing structure:

```bash
# Just check status - works with existing structure
sf library status

# Create new projects in your existing structure
sf library create "New_Project" --type episode
```

The library commands are designed to work with both new and existing `/mnt/library` setups.



