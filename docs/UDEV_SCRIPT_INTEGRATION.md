# Udev Script Integration with Unified Import

## Summary

**Yes, the udev script was modified** to automatically run the unified import pipeline after copying files to the ingest pool.

## What Changed

### Before (Original Script)
- Copied files to ingest pool: `/mnt/nas/Scratch/Ingest/{date}/`
- Maybe tried to run `sf background start` (if it existed)
- **No project creation**
- **No full pipeline automation**

### After (Modified Script - Lines 181-208)
- Copies files to ingest pool: `/mnt/nas/Scratch/Ingest/{date}/` (backup)
- **Automatically runs:** `sf import unified "$DEST_DIR" --from-ingest`
- Extracts codeword from SD card label
- Passes codeword to unified import
- **Full pipeline runs automatically**

## Current Integration

### Flow When SD Card Inserted:

```
1. Udev Rule Detects Insertion
   ↓
2. studioflow-card-import.sh Runs
   ↓
3. Script Copies to Ingest Pool
   /mnt/nas/Scratch/Ingest/{date}/
   ↓
4. Script Extracts Codeword from SD Card Label
   (e.g., "COMPLIANT_APE" → "compliant_ape")
   ↓
5. Script Runs: sf import unified "$DEST_DIR" --from-ingest --codeword "$CODENAME"
   ↓
6. Unified Pipeline Executes:
   - Creates project: codeword-YYYYMMDD_Import
   - Imports from ingest pool (no duplicate copy)
   - Normalizes audio
   - Generates proxies
   - Transcribes
   - Detects markers
   - Generates rough cut
   - Sets up Resolve
   ↓
7. Project Ready in /mnt/library/PROJECTS/
   ↓
8. Desktop Notification: "Complete import pipeline finished!"
```

## Code Changes

### Lines 181-208 in `studioflow-card-import.sh`:

```bash
# Run StudioFlow unified import pipeline
# Use ingest pool as source (already copied) to avoid duplicate copy
if [ -x "$STUDIOFLOW" ] && [ "$IMPORTED" -gt 0 ]; then
    # Extract codeword from SD card label if available
    CODENAME=""
    if [ -n "$LABEL" ]; then
        # Sanitize label for use as codeword
        CODENAME=$(echo "$LABEL" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -cd '[:alnum:]_')
    fi
    
    # Run unified import pipeline using ingest pool (already copied)
    # This avoids duplicate copy from mount point
    if [ -n "$CODENAME" ]; then
        log "Running unified import with codeword: $CODENAME (from ingest pool)"
        if sudo -u eric "$STUDIOFLOW" import unified "$DEST_DIR" --codeword "$CODENAME" --from-ingest 2>&1 | tee -a "$LOG_FILE"; then
            notify "Complete import pipeline finished!"
        else
            notify "Import pipeline completed with warnings"
        fi
    else
        log "Running unified import (auto-detect codeword, from ingest pool)"
        if sudo -u eric "$STUDIOFLOW" import unified "$DEST_DIR" --from-ingest 2>&1 | tee -a "$LOG_FILE"; then
            notify "Complete import pipeline finished!"
        else
            notify "Import pipeline completed with warnings"
        fi
    fi
    log "=== Unified import complete ==="
else
    log "=== Import complete (no automation) ==="
fi
```

## Benefits

### ✅ **Automatic**
- No manual commands needed
- Insert card → everything happens

### ✅ **Efficient**
- Only 2 copies: backup + project
- Uses `--from-ingest` to avoid duplicate copy

### ✅ **Complete**
- Full pipeline runs automatically
- Project ready for editing

### ✅ **Smart**
- Extracts codeword from SD card label
- Creates project with proper naming

## Verification

To verify the integration is working:

```bash
# Check if udev rule is installed
ls -la /etc/udev/rules.d/99-studioflow-import.rules

# Check script has unified import call
grep "import unified" /mnt/dev/studioflow/scripts/studioflow-card-import.sh

# Monitor logs when inserting card
tail -f /var/log/studioflow-import.log
```

## Conclusion

**Yes, the udev script was modified** to automatically run the unified import pipeline. The integration is complete and ready to use!

When you insert an SD card:
1. Files copied to ingest pool (backup)
2. Unified pipeline runs automatically
3. Project created and fully processed
4. Ready for editing

No manual steps required! 🎬

