# StudioFlow Quick Reference

## 🚀 Most Useful Commands

### Complete Workflows (Start Here!)
```bash
sf workflow episode EP001 /path/to/footage              # Complete episode setup
sf workflow import /media/sdcard EP001                  # Import with transcription
sf workflow publish video.mp4 --validate --upload       # Export and upload
```

### Quick Actions Menu
```bash
sf quick  # Interactive menu for everything
```

### Health & Status
```bash
sf dashboard status        # Check project health
sf dashboard quick         # Quick overview
sf project discover        # Find all projects
sf project open            # Interactive project picker
```

### Batch Operations
```bash
sf batch transcribe /path --parallel 4                  # Transcribe multiple files
sf batch trim-silence /path                             # Remove silence from multiple
sf batch thumbnails /path --template viral              # Generate thumbnails
```

### Auto-Editing
```bash
sf auto-edit episode EP001 /footage --transcript transcript.srt
sf auto-edit smart-bins EP001 /footage                  # Just organize
sf auto-edit chapters transcript.srt --format youtube   # Generate chapters
```

### Media Organization
```bash
sf media-org organize /path --transcribe                # Auto-tag and organize
sf media-org search /path "talking head"                # Search by content
```

### Export & Validation
```bash
sf export youtube video.mp4 --validate                  # Export with validation
sf export validate video.mp4                            # Just validate
```

---

## 📋 Common Workflows

### New Episode (5 minutes)
```bash
sf workflow episode EP001 /media/sdcard
sf dashboard status  # Check health
```

### Batch Process Footage
```bash
sf batch transcribe /mnt/ingest --parallel 4
sf batch trim-silence /mnt/ingest
```

### Quick Publishing
```bash
sf export youtube final.mp4 --validate
sf workflow publish final.mp4 --thumbnail
```

---

## 🎯 One-Command Magic

**Everything in one command:**
```bash
sf workflow episode EP001 /footage --transcript transcript.srt
```

**What it does:**
- Analyzes footage
- Creates smart bins
- Sets up Power Bins
- Generates chapters
- Creates timeline
- Validates health
- Ready for editing!

---

See `docs/COMPLETE_WORKFLOW_INTEGRATION.md` for full details.

