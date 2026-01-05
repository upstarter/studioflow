#!/bin/bash
# Install shell completions for StudioFlow CLI

echo "Installing StudioFlow shell completions..."

# Detect shell
if [ -n "$BASH_VERSION" ]; then
    SHELL_TYPE="bash"
    COMPLETION_DIR="${HOME}/.local/share/bash-completion/completions"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_TYPE="zsh"
    COMPLETION_DIR="${HOME}/.zfunc"
elif [ -n "$FISH_VERSION" ]; then
    SHELL_TYPE="fish"
    COMPLETION_DIR="${HOME}/.config/fish/completions"
else
    echo "Unknown shell. Please install completions manually."
    exit 1
fi

echo "Detected shell: $SHELL_TYPE"

# Create completion directory if it doesn't exist
mkdir -p "$COMPLETION_DIR"

# Generate completions using Typer
echo "Generating completions..."
python3 -c "
from studioflow.cli.main import app
import typer

# Get completion for detected shell
shell = '$SHELL_TYPE'
completion = typer.get_completion(app, shell)

# Write to file
output_file = '$COMPLETION_DIR/sf'
if shell == 'fish':
    output_file += '.fish'

with open(output_file, 'w') as f:
    f.write(completion)

print(f'✓ Completions written to {output_file}')
"

# Add sourcing to shell RC file
case "$SHELL_TYPE" in
    bash)
        RC_FILE="$HOME/.bashrc"
        if ! grep -q "bash-completion/completions" "$RC_FILE"; then
            echo "" >> "$RC_FILE"
            echo "# StudioFlow completions" >> "$RC_FILE"
            echo "for comp in ~/.local/share/bash-completion/completions/*; do" >> "$RC_FILE"
            echo "    [ -r \"\$comp\" ] && source \"\$comp\"" >> "$RC_FILE"
            echo "done" >> "$RC_FILE"
            echo "✓ Added completion sourcing to $RC_FILE"
        fi
        ;;
    zsh)
        RC_FILE="$HOME/.zshrc"
        if ! grep -q "fpath.*zfunc" "$RC_FILE"; then
            echo "" >> "$RC_FILE"
            echo "# StudioFlow completions" >> "$RC_FILE"
            echo "fpath=(~/.zfunc \$fpath)" >> "$RC_FILE"
            echo "autoload -Uz compinit && compinit" >> "$RC_FILE"
            echo "✓ Added completion sourcing to $RC_FILE"
        fi
        ;;
    fish)
        echo "✓ Fish will automatically load completions from $COMPLETION_DIR"
        ;;
esac

echo ""
echo "Installation complete!"
echo ""
echo "To enable completions:"
echo "  1. Restart your shell, or"
echo "  2. Run: source $RC_FILE"
echo ""
echo "Then try: sf <TAB> to see available commands"
echo "         sf new <TAB> to see options"