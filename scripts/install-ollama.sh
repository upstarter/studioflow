#!/bin/bash
# Install and configure Ollama with optimal models for StudioFlow

set -e

echo "🤖 StudioFlow Ollama Setup"
echo "=========================="
echo

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✓ Ollama already installed"
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve > /dev/null 2>&1 &
sleep 3

# Function to install model with progress
install_model() {
    local model=$1
    local description=$2

    echo
    echo "📦 Installing $model"
    echo "   Purpose: $description"

    if ollama list | grep -q "$model"; then
        echo "   ✓ Already installed"
    else
        echo "   Downloading (this may take a few minutes)..."
        ollama pull $model
        echo "   ✓ Installed successfully"
    fi
}

echo
echo "Installing optimal models for content creation..."
echo "================================================="

# Install models in order of importance
install_model "llama3.1:13b" "Primary model for titles/hooks (best quality)"
install_model "mistral:7b" "Fast model for drafts/brainstorming (6x faster)"
install_model "phi3:mini" "Ultra-fast for simple tasks (instant)"

# Optional: Install technical model if needed
echo
read -p "Install Qwen2.5 for technical content? (14GB) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    install_model "qwen2.5:14b" "Technical content and tutorials"
fi

# Create systemd service for auto-start
echo
echo "Setting up Ollama to start automatically..."

sudo tee /etc/systemd/system/ollama.service > /dev/null << 'EOF'
[Unit]
Description=Ollama LLM Service
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/ollama serve
Restart=on-failure
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_MODELS=/home/$USER/.ollama/models"

[Install]
WantedBy=multi-user.target
EOF

# Replace $USER with actual username
sudo sed -i "s/\$USER/$USER/g" /etc/systemd/system/ollama.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl restart ollama

echo "✓ Ollama service configured"

# Test installation
echo
echo "Testing Ollama installation..."
echo "==============================="

# Test generation
TEST_RESPONSE=$(ollama run mistral:7b "Generate a YouTube title about Python. Reply with just the title, nothing else." --verbose=false 2>/dev/null | head -1)

if [ -n "$TEST_RESPONSE" ]; then
    echo "✓ Test successful!"
    echo "  Generated: $TEST_RESPONSE"
else
    echo "⚠ Test generation failed. Please check installation."
fi

# Display status
echo
echo "📊 Installation Summary"
echo "======================="
ollama list

echo
echo "✅ Ollama setup complete!"
echo
echo "You can now use:"
echo "  sf youtube titles --local     # Use Ollama (free)"
echo "  sf youtube titles --quality   # Use Claude (better)"
echo "  sf youtube titles --hybrid    # Smart routing (optimal)"
echo
echo "Monitor token usage:"
echo "  sf llm stats"
echo
echo "The system will automatically use Ollama for drafts and Claude only when needed!"