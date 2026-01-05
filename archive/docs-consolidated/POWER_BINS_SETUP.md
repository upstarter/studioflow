# Power Bins Setup Guide

## Overview

Power Bins are now optimized for your stock footage library at `/mnt/nas/Media`. This structure is designed for maximum workflow efficiency when creating YouTube episodes.

---

## 📁 Recommended Directory Structure

The app expects this structure on your NAS:

```
/mnt/nas/Media/
├── Audio/
│   ├── Music/
│   │   ├── Intro/
│   │   ├── Background/
│   │   ├── Outro/
│   │   ├── Transition/
│   │   ├── Buildup/
│   │   └── Ambient/
│   └── SFX/
│       ├── Swishes/
│       ├── Clicks/
│       ├── Impacts/
│       ├── Ambient/
│       ├── UI_Sounds/
│       ├── Whooshes/
│       └── Stings/
├── Graphics/
│   ├── Lower_Thirds/
│   ├── Titles/
│   ├── Intros/
│   ├── Outros/
│   ├── Overlays/
│   ├── Subtitles/
│   ├── Logo_Animations/
│   ├── Backgrounds/
│   └── Borders/
├── Video/
│   ├── Stock_Footage/
│   │   ├── B_Roll/
│   │   │   ├── Tech/
│   │   │   ├── Nature/
│   │   │   ├── Urban/
│   │   │   └── Abstract/
│   │   └── Loops/
│   └── Transitions/
├── LUTs/
│   ├── Cinematic/
│   ├── YouTube/
│   ├── Brands/
│   ├── S_Log3/
│   └── Rec_709/
└── Templates/
    ├── Titles/
    ├── Transitions/
    └── Lower_Thirds/
```

---

## 🚀 Quick Setup

### 1. Validate Your Structure

```bash
sf power-bins validate
```

This checks which directories exist and which are missing.

### 2. Create Missing Directories (Optional)

```bash
sf power-bins create-structure
```

This creates all recommended directories on your NAS.

### 3. Sync to Resolve

```bash
sf power-bins sync
```

This imports all media from `/mnt/nas/Media` into Resolve's Power Bins.

---

## 🎯 Usage

### During Episode Workflow

Power Bins are automatically set up when you run:

```bash
sf workflow episode EP001 /path/to/footage
```

Or explicitly:

```bash
sf auto-edit episode EP001 /path/to/footage --transcript transcript.srt
```

### Manual Sync

To sync Power Bins in any project:

```bash
sf power-bins sync
```

Or using the auto-edit command:

```bash
sf auto-edit power-bins --sync
```

---

## 📋 Power Bins in Resolve

### Make Power Bins Persistent

After syncing, **drag `_POWER_BINS` to Power Bins** in Resolve:

1. Find `_POWER_BINS` folder in Media Pool
2. Drag it to the Power Bins section (left sidebar)
3. It will now appear in **all projects** automatically

### Accessing Power Bins

- Power Bins appear in every Resolve project
- Assets are organized by category
- No need to re-import for each project
- Updates sync when you run `sf power-bins sync`

---

## 🎬 Workflow Benefits

### Before (Without Power Bins)
- Import music/SFX/graphics for each project
- Manually organize assets
- Copy files between projects
- **Time: 10-15 minutes per project**

### After (With Power Bins)
- Auto-sync from NAS
- Organized by category
- Available in all projects
- **Time: 0 minutes (automatic)**

---

## 🔍 File Extensions Supported

### Audio (Music & SFX)
- `.mp3`, `.wav`, `.aac`, `.m4a`, `.flac`

### Graphics
- `.png`, `.jpg`, `.jpeg`
- `.mov`, `.mp4` (animated graphics)
- `.tga`, `.exr` (high-quality)

### Stock Footage
- `.mp4`, `.mov`, `.mxf`, `.avi`

### LUTs
- `.cube`, `.3dl`

### Templates
- `.drt` (Resolve templates)
- `.mov`, `.mp4` (video templates)

---

## ⚙️ Configuration

The Power Bins structure is defined in `studioflow/core/power_bins_config.py`.

To customize:

1. Edit `POWER_BIN_STRUCTURE` in the config file
2. Add/remove categories as needed
3. Update file extensions if needed

---

## 🐛 Troubleshooting

### "Base path does not exist"

Ensure your NAS is mounted:

```bash
# Check if mounted
ls /mnt/nas/Media

# If not mounted, mount it (example)
sudo mount -t nfs nas-server:/media /mnt/nas
```

### "No assets found"

1. Check that directories exist: `sf power-bins validate`
2. Verify files are in correct format (supported extensions)
3. Check file permissions (readable)

### "Power Bins not showing in Resolve"

1. Run sync: `sf power-bins sync`
2. Make sure Resolve is running
3. Check Media Pool for `_POWER_BINS` folder
4. Drag to Power Bins section manually

---

## 📊 Structure Rationale

### Why This Structure?

1. **Category-Based** - Easy to find assets by type
2. **Workflow-Optimized** - Organized for YouTube editing
3. **Scalable** - Easy to add more categories
4. **Standard Extensions** - Supports common file formats

### Categories Explained

- **MUSIC**: Organized by usage (intro, background, outro)
- **SFX**: Common sound effects for YouTube videos
- **GRAPHICS**: Reusable visual elements
- **STOCK_FOOTAGE**: B-roll organized by theme
- **LUTS**: Color grading presets
- **TEMPLATES**: Resolve project templates

---

## 🎯 Best Practices

1. **Organize Before Adding** - Structure your NAS library first
2. **Naming Convention** - Use clear, descriptive filenames
3. **Regular Syncs** - Sync after adding new assets
4. **Keep Organized** - Maintain folder structure
5. **Version Control** - Avoid duplicates

---

## 🔄 Updating Assets

When you add new assets to `/mnt/nas/Media`:

1. Add files to appropriate directories
2. Run: `sf power-bins sync`
3. New assets appear in Power Bins automatically

---

## 💡 Tips

- **Keep stock footage organized** - Use subcategories (Tech, Nature, etc.)
- **Name files descriptively** - "epic_transition_01.mp4" not "vid1.mp4"
- **Regular cleanup** - Remove unused assets periodically
- **Backup NAS** - Your Power Bins library is valuable!

---

## 📚 Related Commands

```bash
sf power-bins validate         # Check structure
sf power-bins create-structure # Create directories
sf power-bins sync             # Sync with Resolve
sf power-bins show-structure   # Display recommended structure
sf auto-edit power-bins --sync # Alternative sync command
```

---

## Summary

Power Bins now use `/mnt/nas/Media` with an optimized structure for YouTube workflow:

✅ **Comprehensive** - Covers all asset types  
✅ **Organized** - Category-based structure  
✅ **Automatic** - Syncs during episode workflow  
✅ **Persistent** - Available in all projects  
✅ **Scalable** - Easy to extend  

**Result:** Zero-time asset management, maximum workflow efficiency.

