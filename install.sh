#!/bin/bash
"""
StudioFlow Suite Installer
Install all SF tools following Unix philosophy
"""

echo "🎬 StudioFlow Suite Installer"
echo "============================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "❌ Please don't run as root"
   exit 1
fi

# Set paths
INSTALL_DIR="/mnt/projects/studioflow"
BIN_DIR="/usr/local/bin"

# Make tools executable
echo "📦 Making tools executable..."
chmod +x "$INSTALL_DIR/sf-project"
chmod +x "$INSTALL_DIR/sf-storage"
chmod +x "$INSTALL_DIR/sf-capture"

# Create symlinks
echo "🔗 Creating symlinks..."
sudo ln -sf "$INSTALL_DIR/sf-project" "$BIN_DIR/sf-project"
sudo ln -sf "$INSTALL_DIR/sf-storage" "$BIN_DIR/sf-storage"
sudo ln -sf "$INSTALL_DIR/sf-capture" "$BIN_DIR/sf-capture"

# Create master 'sf' command
echo "✨ Creating master 'sf' command..."
cat > /tmp/sf << 'EOF'
#!/bin/bash
# StudioFlow master command
# Dispatches to individual sf-* tools

if [ $# -eq 0 ]; then
    echo "StudioFlow Suite - Video Production Tools"
    echo "=========================================="
    echo ""
    echo "Usage: sf <tool> [arguments]"
    echo ""
    echo "Tools:"
    echo "  project  - Project creation and management"
    echo "  storage  - Storage tier management"
    echo "  capture  - Screenshot and recording tools"
    echo ""
    echo "Examples:"
    echo "  sf project create 'My Video'"
    echo "  sf storage status"
    echo "  sf capture snap"
    echo ""
    echo "Or use tools directly:"
    echo "  sf-project create 'My Video'"
    echo "  sf-storage move 'Old Project' archive"
    echo "  sf-capture snap 'screenshot'"
    exit 0
fi

TOOL=$1
shift

case $TOOL in
    project|proj|p)
        sf-project "$@"
        ;;
    storage|store|s)
        sf-storage "$@"
        ;;
    capture|cap|c)
        sf-capture "$@"
        ;;
    *)
        echo "Unknown tool: $TOOL"
        echo "Available: project, storage, capture"
        exit 1
        ;;
esac
EOF

sudo mv /tmp/sf "$BIN_DIR/sf"
sudo chmod +x "$BIN_DIR/sf"

# Create config directory
echo "📁 Creating config directory..."
mkdir -p ~/.config/studioflow

# Create default config
if [ ! -f ~/.config/studioflow/config.yml ]; then
    echo "📝 Creating default configuration..."
    cat > ~/.config/studioflow/config.yml << 'EOF'
# StudioFlow Configuration
storage:
  ingest: /mnt/ingest
  active: /mnt/studio/Projects
  render: /mnt/render
  library: /mnt/library
  archive: /mnt/archive

defaults:
  template: youtube
  git: true

capture:
  screenshot_tool: gnome-screenshot  # or scrot
  recording_tool: ffmpeg
  default_browser: chrome
EOF
fi

# Create bash completions
echo "🔧 Setting up bash completions..."
cat > /tmp/sf-completion.bash << 'EOF'
# StudioFlow bash completions

_sf_project() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local commands="create list info remove"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
    fi
}

_sf_storage() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local commands="status move archive optimize link"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
    fi
}

_sf_capture() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local commands="snap record organize list crop"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
    fi
}

_sf() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local tools="project storage capture"

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=($(compgen -W "$tools" -- "$cur"))
    else
        case ${COMP_WORDS[1]} in
            project|proj|p)
                _sf_project
                ;;
            storage|store|s)
                _sf_storage
                ;;
            capture|cap|c)
                _sf_capture
                ;;
        esac
    fi
}

complete -F _sf sf
complete -F _sf_project sf-project
complete -F _sf_storage sf-storage
complete -F _sf_capture sf-capture
EOF

sudo mv /tmp/sf-completion.bash /etc/bash_completion.d/sf

# Add aliases to bashrc
echo "🎯 Adding convenient aliases..."
if ! grep -q "# StudioFlow aliases" ~/.bashrc; then
    cat >> ~/.bashrc << 'EOF'

# StudioFlow aliases
alias sfp='sf-project'
alias sfs='sf-storage'
alias sfc='sf-capture'
alias sfnew='sf-project create'
alias sflist='sf-project list'
alias sfcap='sf-capture snap'
alias sforg='sf-capture organize'
alias sfstat='sf-storage status'

# Quick capture to current project
cap() {
    sf-capture snap "$1" --project "$(sf-project list -j | jq -r '.projects[0].name')"
}
EOF
fi

echo ""
echo "✅ StudioFlow Suite Installed!"
echo ""
echo "🎬 Quick Start:"
echo "  sf project create 'My First Video'"
echo "  sf capture snap"
echo "  sf storage status"
echo ""
echo "📚 Tools installed:"
echo "  • sf-project - Project management"
echo "  • sf-storage - Storage tier management"
echo "  • sf-capture - Capture tools"
echo ""
echo "⚡ Aliases available (after sourcing .bashrc):"
echo "  • sfnew - Create new project"
echo "  • sfcap - Quick screenshot"
echo "  • sfstat - Storage status"
echo ""
echo "Run 'source ~/.bashrc' to activate aliases"