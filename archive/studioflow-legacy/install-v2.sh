#!/bin/bash
# StudioFlow 2.0 Installation Script

set -e  # Exit on error

echo "═══════════════════════════════════════════════"
echo "    StudioFlow 2.0 - Installation Script"
echo "═══════════════════════════════════════════════"
echo

# Check Python version
echo "Checking Python version..."
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo "❌ Error: Python 3.10+ required"
    echo "   Current: $(python3 --version 2>&1)"
    exit 1
fi
echo "✅ Python $(python3 --version 2>&1 | cut -d' ' -f2) detected"
echo

# Check if pip is installed
echo "Checking pip..."
if ! python3 -m pip --version > /dev/null 2>&1; then
    echo "❌ Error: pip not installed"
    echo "   Install with: sudo apt install python3-pip"
    exit 1
fi
echo "✅ pip is installed"
echo

# Ask about installation type
echo "Installation options:"
echo "  1. User install (recommended)"
echo "  2. Development install (for contributors)"
echo "  3. System-wide install (requires sudo)"
echo
read -p "Select option [1-3]: " install_type

case $install_type in
    2)
        echo
        echo "Installing in development mode..."
        pip install --user -e .
        ;;
    3)
        echo
        echo "Installing system-wide (requires sudo)..."
        sudo pip install .
        ;;
    *)
        echo
        echo "Installing for current user..."
        pip install --user .
        ;;
esac

echo
echo "Installing dependencies..."
pip install --user -r requirements.txt

echo
echo "═══════════════════════════════════════════════"
echo "           Installation Complete!"
echo "═══════════════════════════════════════════════"
echo

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠️  Warning: ~/.local/bin is not in your PATH"
    echo
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
    echo
    echo "Then reload with: source ~/.bashrc"
    echo
fi

# Test installation
echo "Testing installation..."
if command -v sf > /dev/null 2>&1; then
    echo "✅ StudioFlow CLI is ready!"
    echo
    sf --version
else
    echo "⚠️  'sf' command not found in PATH"
    echo "   Try: python3 -m studioflow.cli.main --help"
fi

echo
echo "Next steps:"
echo "  1. Run setup wizard: sf config --wizard"
echo "  2. Create first project: sf new 'My First Video'"
echo "  3. Check help: sf --help"
echo
echo "For migration from old version: python3 migrate.py"
echo