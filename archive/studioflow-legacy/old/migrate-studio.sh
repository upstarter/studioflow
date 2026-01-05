#!/bin/bash
# StudioFlow /mnt/studio Migration Script
# Cleans up legacy directories and updates configurations

set -euo pipefail

echo "🚀 StudioFlow Studio Migration Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Safety check
if [[ $EUID -ne 0 ]]; then
   log_error "This script should be run with sudo for backup modifications"
   echo "Run: sudo $0"
   exit 1
fi

echo ""
log_info "Starting migration process..."

# 1. Set up archive Projects structure
echo ""
log_info "Setting up archive directory structure..."

# Keep archive/Projects for completed project storage
if [[ ! -d "/mnt/archive/Projects" ]]; then
    mkdir -p /mnt/archive/Projects/{2024,2025}
    chown -R eric:eric /mnt/archive/Projects
    log_info "✅ Created archive Projects structure"
else
    # Clean up Resolve's .gallery if it exists
    if [[ -d "/mnt/archive/Projects/.gallery" ]]; then
        log_warn "Removing Resolve's .gallery folder"
        rm -rf /mnt/archive/Projects/.gallery
    fi

    # Create year folders if missing
    for year in 2024 2025; do
        if [[ ! -d "/mnt/archive/Projects/$year" ]]; then
            mkdir -p "/mnt/archive/Projects/$year"
            chown eric:eric "/mnt/archive/Projects/$year"
            log_info "Created /mnt/archive/Projects/$year"
        fi
    done
fi

# 2. Update StudioFlow sfcore.py
echo ""
log_info "Updating StudioFlow core library..."

SFCORE="/mnt/projects/studioflow/sfcore.py"
if [[ -f "$SFCORE" ]]; then
    # Backup original
    cp "$SFCORE" "$SFCORE.pre-migration"

    # Update storage tiers
    sed -i "s|/mnt/resolve/Projects|/mnt/studio/Projects|g" "$SFCORE"
    sed -i "s|/mnt/archive/Projects|/mnt/studio/Projects|g" "$SFCORE"

    log_info "✅ Updated sfcore.py storage paths"
else
    log_warn "sfcore.py not found at expected location"
fi

# 3. Update any StudioFlow configs
echo ""
log_info "Checking StudioFlow configurations..."

# Fix old monolithic archive references
OLD_FILE="/mnt/projects/studioflow/archive/old_monolithic/src/studioflow/extensions/ai_creator.py"
if [[ -f "$OLD_FILE" ]]; then
    sed -i "s|/mnt/resolve/Projects|/mnt/studio/Projects|g" "$OLD_FILE"
    log_info "✅ Updated legacy ai_creator.py"
fi

# 4. Verify backup configuration
echo ""
log_info "Verifying backup configuration..."

BACKUP_SCRIPT="/usr/local/bin/restic-active-backup.sh"
if [[ -f "$BACKUP_SCRIPT" ]]; then
    if grep -q "/mnt/studio/Projects" "$BACKUP_SCRIPT"; then
        log_info "✅ Backup script already covers /mnt/studio/Projects"
    else
        log_warn "⚠️  Backup script may need update"
    fi

    # Show what's being backed up
    echo ""
    log_info "Currently backed up studio directories:"
    grep "/mnt/studio" "$BACKUP_SCRIPT" | grep -v "^#" | while read -r line; do
        echo "  • $line"
    done
fi

# 5. Create missing studio subdirectories
echo ""
log_info "Ensuring studio directory structure..."

STUDIO_DIRS=(
    "/mnt/studio/Templates"
    "/mnt/studio/Export"
    "/mnt/studio/Camera"
    "/mnt/studio/captures"
    "/mnt/studio/Studio/Active"
    "/mnt/studio/Studio/Templates"
    "/mnt/studio/Studio/Library"
    "/mnt/studio/Studio/Tools"
)

for dir in "${STUDIO_DIRS[@]}"; do
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        chown eric:eric "$dir"
        log_info "Created $dir"
    fi
done

# 6. Update CLAUDE.md with new structure
echo ""
log_info "Updating CLAUDE.md documentation..."

CLAUDE_MD="/mnt/projects/studioflow/CLAUDE.md"
if [[ -f "$CLAUDE_MD" ]]; then
    # Update storage tiers section
    sed -i 's|"active": Path("/mnt/resolve/Projects")|"active": Path("/mnt/studio/Projects")|g' "$CLAUDE_MD"
    log_info "✅ Updated CLAUDE.md storage tiers"
fi

# 7. Summary report
echo ""
echo "======================================"
log_info "Migration Summary"
echo "======================================"

# Check disk usage
echo ""
log_info "Current disk usage:"
df -h /mnt/studio /mnt/projects /mnt/archive 2>/dev/null | grep -v "Filesystem"

# Show backup status
echo ""
log_info "Backup timer status:"
systemctl list-timers restic-active.timer --no-pager | grep restic || true

# List studio structure
echo ""
log_info "Studio directory structure:"
tree -L 2 /mnt/studio 2>/dev/null || ls -la /mnt/studio/

echo ""
log_info "🎉 Migration complete!"
echo ""
echo "Next steps:"
echo "1. Verify your DaVinci Resolve projects still open correctly"
echo "2. Check that auto-import still works when inserting CF cards"
echo "3. Monitor next backup run: watch systemctl status restic-active"
echo ""
echo "Backup of sfcore.py saved to: $SFCORE.pre-migration"