#!/bin/bash
# StudioFlow Suite Full Installer
# Installs all SF tools for complete YouTube production workflow

echo "🎬 StudioFlow Suite - Complete Installation"
echo "==========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "❌ Please don't run as root"
   exit 1
fi

# Set paths
INSTALL_DIR="/mnt/projects/studioflow"
BIN_DIR="/usr/local/bin"

echo "📦 Installing StudioFlow tools..."
echo ""

# Core tools
CORE_TOOLS="sf-project sf-storage sf-capture"
# YouTube tools
YT_TOOLS="sf-youtube sf-audio sf-ai"
# Integration tools
INT_TOOLS="sf-obs sf-resolve"
# Wizard system
WIZARD_TOOLS="sf-wizard"

ALL_TOOLS="$CORE_TOOLS $YT_TOOLS $INT_TOOLS $WIZARD_TOOLS"

# Make all tools executable
for tool in $ALL_TOOLS; do
    if [ -f "$INSTALL_DIR/$tool" ]; then
        chmod +x "$INSTALL_DIR/$tool"
        sudo ln -sf "$INSTALL_DIR/$tool" "$BIN_DIR/$tool"
        echo "✓ Installed $tool"
    fi
done

# Update master 'sf' command
cat > /tmp/sf << 'EOF'
#!/bin/bash
# StudioFlow master command - Complete suite

if [ $# -eq 0 ]; then
    echo "StudioFlow Suite - Complete YouTube Production Toolkit"
    echo "======================================================"
    echo ""
    echo "Usage: sf <tool> [arguments]"
    echo ""
    echo "🎯 Core Tools:"
    echo "  project  - Project creation and management"
    echo "  storage  - Storage tier management"
    echo "  capture  - Screenshot and recording tools"
    echo ""
    echo "📺 YouTube Tools:"
    echo "  youtube  - SEO, thumbnails, descriptions"
    echo "  audio    - Transcription, denoising, music"
    echo "  ai       - Script writing, ideas, prompts"
    echo ""
    echo "🔧 Integration Tools:"
    echo "  obs      - OBS Studio setup and scenes"
    echo "  resolve  - DaVinci Resolve configuration"
    echo ""
    echo "Examples:"
    echo "  sf project create 'Tutorial Video'"
    echo "  sf youtube seo 'Best Linux Commands'"
    echo "  sf audio transcribe recording.mp4"
    echo "  sf ai script 'My Project'"
    echo "  sf obs setup 'My Project'"
    echo "  sf resolve color 'My Project'"
    exit 0
fi

TOOL=$1
shift

case $TOOL in
    # Core tools
    project|proj|p)
        sf-project "$@"
        ;;
    storage|store|s)
        sf-storage "$@"
        ;;
    capture|cap|c)
        sf-capture "$@"
        ;;
    # YouTube tools
    youtube|yt|y)
        sf-youtube "$@"
        ;;
    audio|aud|a)
        sf-audio "$@"
        ;;
    ai)
        sf-ai "$@"
        ;;
    # Integration tools
    obs|o)
        sf-obs "$@"
        ;;
    resolve|res|r)
        sf-resolve "$@"
        ;;
    # Wizard system
    wizard|wiz|w)
        sf-wizard "$@"
        ;;
    *)
        echo "Unknown tool: $TOOL"
        echo "Available: project, storage, capture, youtube, audio, ai, obs, resolve, wizard"
        exit 1
        ;;
esac
EOF

sudo mv /tmp/sf "$BIN_DIR/sf"
sudo chmod +x "$BIN_DIR/sf"

echo ""
echo "🎯 Creating helpful aliases..."

# Extended aliases
cat > /tmp/sf-aliases << 'EOF'

# StudioFlow Complete Aliases
# Core
alias sfnew='sf-project create'
alias sflist='sf-project list'
alias sfinfo='sf-project info'

# Storage
alias sfstat='sf-storage status'
alias sfarchive='sf-storage archive'
alias sfmove='sf-storage move'

# Capture
alias sfcap='sf-capture snap'
alias sfrec='sf-capture record'
alias sforg='sf-capture organize'

# YouTube
alias sfseo='sf-youtube seo'
alias sfdesc='sf-youtube description'
alias sfthumb='sf-youtube thumbnail'

# Audio
alias sftrans='sf-audio transcribe'
alias sfdenoise='sf-audio denoise'
alias sfmusic='sf-audio library'

# AI
alias sfscript='sf-ai script'
alias sfideas='sf-ai ideas'
alias sfprompt='sf-ai prompt'

# OBS
alias sfobs='sf-obs setup'
alias sfscenes='sf-obs scenes'

# Resolve
alias sfresolve='sf-resolve setup'
alias sfcolor='sf-resolve color'
alias sfrender='sf-resolve render'

# Quick workflows
sftutorial() {
    echo "🎬 Starting Tutorial Workflow"
    sf-project create "$1" --template tutorial
    sf-obs setup "$1"
    sf-resolve setup "$1"
    sf-ai script "$1" --style educational
}

sfcomparison() {
    echo "🔍 Starting Comparison Workflow"
    sf-project create "$1" --template comparison
    sf-youtube seo "$1"
    sf-ai prompt "$1" --type comparison
}

sfquick() {
    echo "⚡ Quick Video Setup"
    sf-project create "$1"
    sf-youtube description "$1"
    sf-obs setup "$1"
    sf-resolve setup "$1"
}
EOF

# Add to bashrc if not already there
if ! grep -q "# StudioFlow Complete Aliases" ~/.bashrc; then
    cat /tmp/sf-aliases >> ~/.bashrc
    echo "✓ Added aliases to ~/.bashrc"
fi

echo ""
echo "📦 Checking optional dependencies..."
echo ""

# Check for optional tools
check_tool() {
    if command -v $1 &> /dev/null; then
        echo "✓ $1 installed"
    else
        echo "⚠ $1 not found - $2"
    fi
}

check_tool "ffmpeg" "Required for audio/video processing"
check_tool "obs" "Required for recording"
check_tool "resolve" "DaVinci Resolve for editing"
check_tool "whisper" "Install with: pip install openai-whisper"
check_tool "convert" "ImageMagick for image processing"
check_tool "jq" "JSON processing for automation"

echo ""
echo "✨ Creating workspace directories..."

# Create essential directories
mkdir -p ~/.config/studioflow
mkdir -p ~/.cache/studioflow
mkdir -p ~/Captures

echo ""
echo "=================================="
echo "✅ StudioFlow Suite Installed!"
echo "=================================="
echo ""
echo "🎬 Complete YouTube Production Toolkit:"
echo ""
echo "📁 Project Management:"
echo "  sf project create 'Video Name'"
echo "  sf storage status"
echo ""
echo "📹 Recording:"
echo "  sf obs setup 'Project'"
echo "  sf capture snap"
echo ""
echo "✂️ Editing:"
echo "  sf resolve setup 'Project'"
echo "  sf audio transcribe video.mp4"
echo ""
echo "📊 YouTube Optimization:"
echo "  sf youtube seo 'Title'"
echo "  sf ai script 'Project'"
echo ""
echo "🚀 Quick Workflows:"
echo "  sftutorial 'Tutorial Name'   - Complete tutorial setup"
echo "  sfcomparison 'Compare X Y'   - Comparison video setup"
echo "  sfquick 'Video Name'         - Quick video setup"
echo ""
echo "Run 'source ~/.bashrc' to activate all aliases"
echo "Run 'sf' to see all available tools"