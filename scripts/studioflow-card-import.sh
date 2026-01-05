#!/bin/bash
# StudioFlow SD Card Auto-Import
# Detects video project cards and runs full automation

set -euo pipefail

DEVICE="/dev/$1"
LOG_FILE="/var/log/studioflow-import.log"
STUDIOFLOW="/mnt/dev/studioflow/sf"
REGISTERED_CARDS="/etc/studioflow/registered-cards.conf"
INGEST_DIR="/mnt/nas/Scratch/Ingest"

# Only import footage from last N days (0 = all)
DAYS_AGO=${STUDIOFLOW_DAYS:-3}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

notify() {
    sudo -u eric DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
        notify-send -i camera-video "StudioFlow" "$1" 2>/dev/null || true
}

log "=== Card inserted: $DEVICE ==="

# Wait for device to settle and desktop to auto-mount
sleep 5

# Get device info
LABEL=$(lsblk -no LABEL "$DEVICE" 2>/dev/null || echo "")
UUID=$(lsblk -no UUID "$DEVICE" 2>/dev/null || echo "")
FSTYPE=$(lsblk -no FSTYPE "$DEVICE" 2>/dev/null || echo "")

log "Label: $LABEL, UUID: $UUID, FSType: $FSTYPE"

# Check if this is a registered video card
is_registered_card() {
    if [ -f "$REGISTERED_CARDS" ]; then
        grep -qE "^(UUID=$UUID|LABEL=$LABEL)$" "$REGISTERED_CARDS" 2>/dev/null
        return $?
    fi
    return 1
}

# Check if card has video content (Sony or generic camera)
is_video_card() {
    local mount="$1"

    # Sony FX30/FX3/FX6: M4ROOT/CLIP at root level
    if [ -d "$mount/M4ROOT/CLIP" ]; then
        log "Detected: Sony Cinema Line card (FX30/FX3/FX6)"
        return 0
    fi

    # Sony cameras: PRIVATE/M4ROOT/CLIP or PRIVATE/AVCHD
    if [ -d "$mount/PRIVATE/M4ROOT/CLIP" ] || [ -d "$mount/PRIVATE/AVCHD" ]; then
        log "Detected: Sony camera card"
        return 0
    fi

    # Sony XAVC: XROOT folder
    if [ -d "$mount/XROOT" ]; then
        log "Detected: Sony XAVC card"
        return 0
    fi

    # Generic: DCIM with video files
    if [ -d "$mount/DCIM" ]; then
        # Check for video files (mp4, mov, mxf, mts)
        if find "$mount/DCIM" -maxdepth 3 -type f \( -iname "*.mp4" -o -iname "*.mov" -o -iname "*.mxf" -o -iname "*.mts" \) -print -quit | grep -q .; then
            log "Detected: Camera card with video files"
            return 0
        fi
    fi

    return 1
}

# Get or create mount point - wait for desktop auto-mount first
MOUNT_POINT=""
for i in 1 2 3 4 5; do
    MOUNT_POINT=$(lsblk -no MOUNTPOINT "$DEVICE" 2>/dev/null | head -1)
    if [ -n "$MOUNT_POINT" ]; then
        break
    fi
    log "Waiting for auto-mount... attempt $i"
    sleep 2
done

if [ -z "$MOUNT_POINT" ]; then
    # Desktop didn't mount it, try mounting ourselves
    MOUNT_POINT="/tmp/studioflow_import_$$"
    mkdir -p "$MOUNT_POINT"

    if mount -t exfat "$DEVICE" "$MOUNT_POINT" 2>/dev/null || mount -t auto "$DEVICE" "$MOUNT_POINT" 2>/dev/null; then
        TEMP_MOUNT=true
        log "Mounted $DEVICE at $MOUNT_POINT"
    else
        log "ERROR: Failed to mount $DEVICE"
        rmdir "$MOUNT_POINT" 2>/dev/null || true
        exit 1
    fi
else
    TEMP_MOUNT=false
    log "Already mounted at $MOUNT_POINT"
fi

cleanup() {
    if [ "$TEMP_MOUNT" = true ]; then
        umount "$MOUNT_POINT" 2>/dev/null || true
        rmdir "$MOUNT_POINT" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Check if this is a video card we should process
if ! is_registered_card && ! is_video_card "$MOUNT_POINT"; then
    log "Not a video project card, skipping"
    exit 0
fi

# Found video card - start import
notify "Video card detected! Scanning for recent footage..."
log "Starting import from $MOUNT_POINT (last $DAYS_AGO days)"

# Create dated ingest folder
DATE_FOLDER=$(date +%Y-%m-%d)
DEST_DIR="$INGEST_DIR/$DATE_FOLDER"
sudo -u eric mkdir -p "$DEST_DIR"

# Find video files modified in last N days (by file mtime, not filename)
# Extensions: mp4, mov, mxf, mts (common camera formats)
if [ "$DAYS_AGO" -gt 0 ]; then
    FIND_ARGS="-mtime -$DAYS_AGO"
else
    FIND_ARGS=""
fi

# Count files to import
FILE_COUNT=$(find "$MOUNT_POINT" -type f \( -iname "*.mp4" -o -iname "*.mov" -o -iname "*.mxf" -o -iname "*.mts" \) $FIND_ARGS 2>/dev/null | wc -l)

if [ "$FILE_COUNT" -eq 0 ]; then
    log "No recent video files found (last $DAYS_AGO days)"
    notify "No recent footage found on card"
    exit 0
fi

log "Found $FILE_COUNT video files to import"
notify "Importing $FILE_COUNT files..."

# Copy files with progress, preserving timestamps
IMPORTED=0
SKIPPED=0

while IFS= read -r -d '' src_file; do
    filename=$(basename "$src_file")
    dest_file="$DEST_DIR/$filename"

    # Skip if already exists (duplicate check by name + size)
    if [ -f "$dest_file" ]; then
        src_size=$(stat -c%s "$src_file")
        dest_size=$(stat -c%s "$dest_file")
        if [ "$src_size" -eq "$dest_size" ]; then
            log "Skipping duplicate: $filename"
            ((SKIPPED++)) || true
            continue
        fi
    fi

    # Copy with rsync for reliability (--no-perms for NAS compatibility)
    if sudo -u eric rsync -a --no-perms --no-group --progress "$src_file" "$dest_file" 2>&1 | tail -1 >> "$LOG_FILE"; then
        ((IMPORTED++)) || true
        log "Imported: $filename"
    fi
done < <(find "$MOUNT_POINT" -type f \( -iname "*.mp4" -o -iname "*.mov" -o -iname "*.mxf" -o -iname "*.mts" \) $FIND_ARGS -print0 2>/dev/null)

log "Import complete: $IMPORTED imported, $SKIPPED skipped (duplicates)"
notify "Imported $IMPORTED files! Starting automation..."

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
