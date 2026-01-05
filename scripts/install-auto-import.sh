#!/bin/bash
# Install StudioFlow auto-import for camera SD cards

set -e

echo "📷 StudioFlow Auto-Import Installer"
echo "===================================="
echo

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "✓ Running as root"
else
    echo "This script needs root privileges to install udev rules"
    echo "Please run: sudo $0"
    exit 1
fi

# Backup existing rules if they exist
if [ -f /etc/udev/rules.d/99-cf-card-import.rules ]; then
    echo "Backing up existing CF card import rules..."
    cp /etc/udev/rules.d/99-cf-card-import.rules /etc/udev/rules.d/99-cf-card-import.rules.bak
fi

# Install new udev rule
echo "Installing StudioFlow udev rule..."
cp /mnt/projects/studioflow/scripts/99-studioflow-import.rules /etc/udev/rules.d/

# Reload udev rules
echo "Reloading udev rules..."
udevadm control --reload-rules
udevadm trigger

# Create log file with proper permissions
echo "Setting up logging..."
touch /var/log/studioflow-import.log
chmod 666 /var/log/studioflow-import.log

# Test if StudioFlow is accessible
if [ -x /mnt/projects/studioflow/sf ]; then
    echo "✓ StudioFlow CLI is accessible"
else
    echo "⚠ Warning: StudioFlow CLI not found or not executable"
    echo "  Please ensure /mnt/projects/studioflow/sf exists and is executable"
fi

echo
echo "✅ Auto-import installation complete!"
echo
echo "How it works:"
echo "1. Insert a camera SD card"
echo "2. StudioFlow will automatically:"
echo "   - Detect camera type (FX30, ZV-E10, etc)"
echo "   - Copy files to /mnt/ingest/Camera/Pool"
echo "   - Organize into current project"
echo "   - Generate proxies"
echo "   - Create Resolve timeline"
echo
echo "Monitor imports with:"
echo "  tail -f /var/log/studioflow-import.log"
echo
echo "Test manually with:"
echo "  sf media auto-import /media/$USER/YOUR_SD_CARD"