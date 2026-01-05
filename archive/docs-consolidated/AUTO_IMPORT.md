# StudioFlow Auto-Import System

Automatic SD card import with the 5 key features you requested.

## ✅ The 5 Features

1. **Detect camera type** - Identifies FX30, ZV-E10, A7IV by card structure
2. **Copy to ingest pool** - Verified copy to `/mnt/ingest/Camera/Pool`
3. **Organize into project** - Smart organization by date/camera
4. **Generate proxies** - DNxHD/ProRes proxies for smooth editing
5. **Create Resolve timeline** - Python script ready for Resolve

## 🚀 Installation

```bash
# Install the auto-import system
sudo /mnt/projects/studioflow/scripts/install-auto-import.sh
```

This will:
- Install udev rules for automatic SD card detection
- Set up logging
- Configure the import pipeline

## 📷 Usage

### Automatic (Recommended)
Just insert your camera's SD card! StudioFlow will:
1. Detect it automatically
2. Show desktop notification
3. Import all media
4. Generate proxies
5. Organize everything

### Manual
```bash
# Import from specific mount point
sf media auto-import /media/eric/SONY_SD

# Watch for changes
sf media auto-import /media/eric/SONY_SD --watch
```

## 📁 File Organization

```
/mnt/ingest/Camera/Pool/
├── 2024-09/
│   ├── 20240923_Shoot/
│   │   ├── FX30_20240923_143022_C0001.MP4
│   │   ├── FX30_20240923_143522_C0002.MP4
│   │   └── ...

/mnt/studio/Projects/20240923_Shoot/
├── 01_Media/
│   ├── Original/
│   │   └── FX30/
│   │       ├── FX30_20240923_143022_C0001.MP4
│   │       └── ...
│   └── Proxy/
│       ├── FX30_20240923_143022_C0001_proxy.mov
│       └── ...
├── 02_Project/
│   └── create_timeline.py  # Run in Resolve console
└── import_20240923_143022.json  # Import manifest
```

## 🔍 Monitoring

```bash
# Watch import progress
tail -f /var/log/studioflow-import.log

# Check if service is working
journalctl -f | grep studioflow

# Test udev rule
udevadm test /dev/sdb1
```

## 🎥 Supported Cameras

### Sony
- **FX30/FX3** - 4K XAVC-S, S-Cinetone
- **ZV-E10** - 1080p/4K, S-Cinetone
- **A7 IV** - 4K, S-Log3

### Coming Soon
- Canon R5/R6
- Panasonic GH6
- Blackmagic Pocket

## ⚙️ Configuration

Edit camera profiles in:
`/mnt/projects/studioflow/studioflow/core/auto_import.py`

```python
"FX30": CameraProfile(
    name="Sony FX30",
    card_patterns=["PRIVATE/M4ROOT", "XROOT"],
    file_patterns=["C*.MP4", "C*.MXF"],
    color_space="S-Cinetone",
    resolution="3840x2160",
    fps=29.97
)
```

## 🐛 Troubleshooting

### Card not detected
1. Check if mounted: `lsblk`
2. Check udev: `udevadm monitor` (then insert card)
3. Check logs: `tail /var/log/studioflow-import.log`

### Import fails
1. Check permissions: `ls -la /mnt/ingest/Camera/Pool`
2. Check space: `df -h /mnt/ingest`
3. Run manually: `sf media auto-import /media/eric/CARD_NAME`

### Proxies not generating
1. Check ffmpeg: `ffmpeg -version`
2. Check codec support: `ffmpeg -codecs | grep dnxhd`
3. Check disk space: `df -h /mnt/render`

## 📊 Import Statistics

After each import, check the manifest file:
```bash
cat /mnt/studio/Projects/*/import_*.json | jq .
```

Shows:
- Import timestamp
- Camera detected
- Files imported with checksums
- File sizes
- Any errors

## 🔄 Previous System Migration

If you had the old `cf-card-import` system:
1. Your existing imports in `/mnt/ingest` are preserved
2. The new system uses the same paths
3. Old udev rules are backed up to `.bak` files
4. You can switch back anytime by restoring the backup

## 🚦 Status

The auto-import system is now:
- ✅ Integrated into StudioFlow CLI
- ✅ Using the same paths as before
- ✅ Enhanced with proxies and Resolve integration
- ✅ Ready for your next shoot!

Just insert an SD card and watch the magic happen! 🎬