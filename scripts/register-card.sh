#!/bin/bash
# Register an SD card for StudioFlow auto-import
# Usage: sudo ./register-card.sh /dev/sdX1

REGISTERED_CARDS="/etc/studioflow/registered-cards.conf"

if [ -z "$1" ]; then
    echo "Usage: $0 /dev/sdX1"
    echo ""
    echo "Currently mounted cards:"
    lsblk -o NAME,LABEL,UUID,FSTYPE,SIZE,MOUNTPOINT | grep -E "sd[a-z][0-9]|mmcblk|nvme.*p"
    exit 1
fi

DEVICE="$1"

if [ ! -b "$DEVICE" ]; then
    echo "Error: $DEVICE is not a block device"
    exit 1
fi

UUID=$(lsblk -no UUID "$DEVICE" 2>/dev/null)
LABEL=$(lsblk -no LABEL "$DEVICE" 2>/dev/null)

if [ -z "$UUID" ] && [ -z "$LABEL" ]; then
    echo "Error: Could not get UUID or LABEL for $DEVICE"
    exit 1
fi

sudo mkdir -p /etc/studioflow

echo "Registering card:"
echo "  Device: $DEVICE"
echo "  UUID:   $UUID"
echo "  Label:  $LABEL"

if [ -n "$UUID" ]; then
    echo "UUID=$UUID" | sudo tee -a "$REGISTERED_CARDS" > /dev/null
    echo "Added UUID=$UUID"
fi

if [ -n "$LABEL" ]; then
    echo "LABEL=$LABEL" | sudo tee -a "$REGISTERED_CARDS" > /dev/null
    echo "Added LABEL=$LABEL"
fi

echo ""
echo "Card registered! It will now auto-import even without video files detected."
echo "Registered cards:"
cat "$REGISTERED_CARDS"
