#!/bin/bash
#
# StudioFlow Installer
# Automated installation script for StudioFlow video production suite
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking system dependencies..."

    # Check for required commands
    local missing_deps=()

    for cmd in python3 ffprobe rsync udevadm; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install them with:"
        log_info "  Ubuntu/Debian: sudo apt install python3 ffmpeg rsync udev"
        log_info "  RHEL/CentOS: sudo yum install python3 ffmpeg rsync systemd"
        exit 1
    fi

    # Check for Python YAML module
    if ! python3 -c "import yaml" 2>/dev/null; then
        log_warning "PyYAML not found, installing..."
        pip3 install --user PyYAML || {
            log_error "Failed to install PyYAML"
            log_info "Please run: pip3 install --user PyYAML"
            exit 1
        }
    fi

    log_success "All dependencies satisfied"
}

create_directories() {
    log_info "Creating directory structure..."

    # Create user directories
    mkdir -p "$HOME/.studioflow"
    mkdir -p "$HOME/.config/studioflow"
    mkdir -p "$HOME/bin"

    # Create default project directories (user can customize in config)
    mkdir -p "$HOME/Videos/StudioFlow/Projects"
    mkdir -p "$HOME/Videos/StudioFlow/Ingest"
    mkdir -p "$HOME/Videos/StudioFlow/Archive"

    log_success "Directory structure created"
}

install_studioflow() {
    log_info "Installing StudioFlow components..."

    # Get the directory where this script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

    # Target installation directory
    INSTALL_DIR="/opt/studioflow"
    USER_INSTALL_DIR="$HOME/.local/share/studioflow"

    # Determine install location based on permissions
    if [ "$EUID" -eq 0 ]; then
        # Running as root, install system-wide
        TARGET_DIR="$INSTALL_DIR"
        BIN_DIR="/usr/local/bin"
        mkdir -p "$TARGET_DIR"
    else
        # User installation
        TARGET_DIR="$USER_INSTALL_DIR"
        BIN_DIR="$HOME/bin"
        mkdir -p "$TARGET_DIR"
    fi

    log_info "Installing to: $TARGET_DIR"

    # Copy StudioFlow files
    cp "$SCRIPT_DIR"/*.py "$TARGET_DIR/"
    cp "$SCRIPT_DIR"/sf* "$TARGET_DIR/"

    # Copy configuration
    mkdir -p "$TARGET_DIR/config"
    if [ -f "$HOME/.studioflow/config.yaml" ]; then
        # Use existing user config as default
        cp "$HOME/.studioflow/config.yaml" "$TARGET_DIR/config/default.yaml"
    else
        # Create default config
        cat > "$TARGET_DIR/config/default.yaml" << 'EOF'
# StudioFlow Default Configuration
user:
  name: ${USER}
  notification: true

paths:
  studio_projects: ${HOME}/Videos/StudioFlow/Projects
  ingest: ${HOME}/Videos/StudioFlow/Ingest
  archive: ${HOME}/Videos/StudioFlow/Archive
  library: ${HOME}/Videos/StudioFlow/Library
  render: ${HOME}/Videos/StudioFlow/Render

project:
  resolution: "3840x2160"
  framerate: 29.97
  template: "YouTube 4K30 Optimized"
  color_space: "Rec.709"
  audio_target_lufs: -14.0
  folder_structure:
    - "01_MEDIA"
    - "02_PROJECTS"
    - "03_RENDERS"
    - "04_ASSETS"
    - ".studioflow"

categorization:
  test_clip_max: 3
  b_roll_min: 10
  b_roll_max: 30
  a_roll_min: 60

resolve:
  install_path: /opt/resolve
  api_path: /opt/resolve/Developer/Scripting
  enabled: true

import:
  file_extensions: [".MP4", ".MOV", ".AVI", ".MXF", ".XML", ".JPG", ".THM"]
  verify_checksums: true
  skip_duplicates: true
  auto_organize: true
  pool_dir: ${HOME}/Videos/StudioFlow/Ingest/Pool
  notification_enabled: true

logging:
  level: INFO
  file: ${HOME}/.studioflow/studioflow.log
  max_size_mb: 100
EOF
    fi

    # Make scripts executable
    chmod +x "$TARGET_DIR"/sf*

    # Create main sf command symlink
    if [ ! -f "$BIN_DIR/sf" ]; then
        ln -s "$TARGET_DIR/sf" "$BIN_DIR/sf"
        log_success "Created sf command in $BIN_DIR"
    fi

    # Add bin directory to PATH if not already there
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$HOME/.bashrc"
        log_info "Added $BIN_DIR to PATH in ~/.bashrc"
        log_warning "Please run 'source ~/.bashrc' or restart your shell"
    fi

    log_success "StudioFlow installed to $TARGET_DIR"
    return 0  # Set TARGET_DIR for later use
}

setup_configuration() {
    log_info "Setting up configuration..."

    # Copy user config if it doesn't exist
    if [ ! -f "$HOME/.studioflow/config.yaml" ]; then
        if [ -f "$TARGET_DIR/config/default.yaml" ]; then
            cp "$TARGET_DIR/config/default.yaml" "$HOME/.studioflow/config.yaml"
        else
            log_warning "Default config not found, user will need to create config manually"
        fi
        log_success "Created user configuration"
    else
        log_info "User configuration already exists"
    fi
}

setup_udev_rules() {
    log_info "Setting up SD card auto-import..."

    # Only setup udev rules if running as root
    if [ "$EUID" -eq 0 ]; then
        cat > /etc/udev/rules.d/99-studioflow-sdcard.rules << EOF
# StudioFlow SD Card Auto-Import Rules
# Automatically mount and import when SD cards are inserted

ACTION=="add", KERNEL=="sd[a-z][0-9]", SUBSYSTEM=="block", ENV{ID_FS_TYPE}=="vfat", RUN+="/bin/systemd-run --uid=${SUDO_USER:-1000} --gid=${SUDO_GID:-1000} ${HOME}/bin/cf-card-mount-helper %k"
EOF

        # Create mount helper script
        cat > "$HOME/bin/cf-card-mount-helper" << 'EOF'
#!/bin/bash
# StudioFlow SD Card Mount Helper
# Called by udev rules when SD card is inserted

DEVICE="/dev/$1"
MOUNT_POINT="/media/$USER/$(blkid -o value -s UUID $DEVICE)"

# Create mount point
mkdir -p "$MOUNT_POINT"

# Mount the device
mount "$DEVICE" "$MOUNT_POINT"

# Run import after short delay
sleep 2
"$HOME/bin/cf-card-import" "$DEVICE" "$MOUNT_POINT"
EOF

        chmod +x "$HOME/bin/cf-card-mount-helper"

        # Reload udev rules
        udevadm control --reload-rules
        udevadm trigger

        log_success "SD card auto-import configured"
    else
        log_warning "Not running as root, skipping udev rules setup"
        log_info "To enable SD card auto-import, run: sudo ./install-studioflow.sh"
    fi
}

install_cf_card_import() {
    log_info "Installing CF card import script..."

    # Copy the updated cf-card-import script
    if [ -f "$HOME/bin/cf-card-import" ]; then
        log_info "CF card import script already exists, backing up..."
        cp "$HOME/bin/cf-card-import" "$HOME/bin/cf-card-import.backup.$(date +%s)"
    fi

    # Create updated cf-card-import script
    cat > "$HOME/bin/cf-card-import" << 'EOF'
#!/bin/bash
# StudioFlow CF Card Import Script
# Imports media from SD cards and triggers StudioFlow processing

DEVICE="$1"
MOUNT_POINT="$2"
NOTIFY_USER="${USER:-$LOGNAME}"

# Find StudioFlow installation
STUDIOFLOW_DIRS=(
    "$HOME/.local/share/studioflow"
    "/opt/studioflow"
    "/usr/local/share/studioflow"
)

STUDIOFLOW_DIR=""
for dir in "${STUDIOFLOW_DIRS[@]}"; do
    if [ -f "$dir/sf-orchestrator" ]; then
        STUDIOFLOW_DIR="$dir"
        break
    fi
done

if [ -z "$STUDIOFLOW_DIR" ]; then
    echo "Error: StudioFlow installation not found"
    exit 1
fi

# Get current project
CURRENT_PROJECT=$(python3 -c "
import sys
sys.path.insert(0, '$STUDIOFLOW_DIR')
try:
    from sfcore import get_current_project
    project = get_current_project()
    print(project) if project else print('')
except:
    print('')
")

if [ -z "$CURRENT_PROJECT" ]; then
    echo "No current StudioFlow project set"
    echo "Run: sf new 'Project Name' first"
    exit 1
fi

# Create import directory
IMPORT_DIR="$CURRENT_PROJECT/01_MEDIA/$(date +%Y%m%d_%H%M%S)_import"
mkdir -p "$IMPORT_DIR"

# Copy files
echo "Importing media from $MOUNT_POINT to $IMPORT_DIR..."
rsync -av --ignore-existing "$MOUNT_POINT/" "$IMPORT_DIR/"

# Run StudioFlow orchestrator
"$STUDIOFLOW_DIR/sf-orchestrator" "$IMPORT_DIR"

# Notify user
if command -v notify-send &> /dev/null; then
    notify-send "StudioFlow" "Media import completed for $(basename "$CURRENT_PROJECT")"
fi

echo "Import completed successfully"
EOF

    chmod +x "$HOME/bin/cf-card-import"
    log_success "CF card import script installed"
}

verify_installation() {
    log_info "Verifying installation..."

    # Check if sf command is available
    if command -v sf &> /dev/null; then
        log_success "sf command is available"

        # Test basic functionality
        if sf help &> /dev/null; then
            log_success "StudioFlow is working correctly"
        else
            log_warning "sf command found but may have issues"
        fi
    else
        log_error "sf command not found in PATH"
        log_info "You may need to restart your shell or run 'source ~/.bashrc'"
    fi

    # Check configuration
    if [ -f "$HOME/.studioflow/config.yaml" ]; then
        log_success "Configuration file exists"
    else
        log_warning "Configuration file not found"
    fi
}

print_next_steps() {
    echo
    echo "==============================================="
    echo "🎉 StudioFlow Installation Complete!"
    echo "==============================================="
    echo
    echo "Next steps:"
    echo "1. Restart your shell or run: source ~/.bashrc"
    echo "2. Create your first project: sf new 'My First Project'"
    echo "3. Insert an SD card to test auto-import"
    echo "4. Open DaVinci Resolve and run: sf resolve"
    echo
    echo "Commands:"
    echo "  sf help           - Show help"
    echo "  sf new <name>     - Create new project"
    echo "  sf status         - Show project status"
    echo "  sf resolve        - Generate Resolve project"
    echo "  sf list           - List all projects"
    echo
    echo "Configuration: ~/.studioflow/config.yaml"
    echo "Logs: ~/.studioflow/studioflow.log"
    echo
    echo "For documentation, visit the StudioFlow project page."
    echo "==============================================="
}

main() {
    echo "==============================================="
    echo "🎬 StudioFlow Installer"
    echo "==============================================="
    echo

    check_dependencies
    create_directories
    install_studioflow
    setup_configuration
    install_cf_card_import
    setup_udev_rules
    verify_installation
    print_next_steps
}

# Run installer
main "$@"