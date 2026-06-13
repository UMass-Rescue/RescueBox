#!/bin/bash

# List of models required for v3
MODELS=(
    "gemma3:1b"
    "ibm/granite4.1:3b"
    "moondream:latest"
)

# sudo systemctl stop ollama
#   curl -fsSL https://ollama.com/install.sh | sh
#   ollama --version
#  ollama version is 0.20.2

echo "🔍 Validating Ollama Environment..."

# 1. Check if Ollama is running (API check)
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Error: Ollama server is not responding at localhost:11434."
    echo "   Ensure 'ollama serve' is running."
    exit 1
fi

# 2. Get a list of currently installed models
INSTALLED_MODELS=$(ollama list | tail -n +2 | awk '{print $1}')

# 3. Iterate and Pull missing models
for MODEL in "${MODELS[@]}"; do
    if echo "$INSTALLED_MODELS" | grep -q "^$MODEL$"; then
        echo "✅ $MODEL is already installed."
    else
        echo "📥 $MODEL not found. Starting pull..."
        if ollama pull "$MODEL"; then
            echo "✅ Successfully pulled $MODEL."
        else
            echo "❌ Failed to pull $MODEL. Check your internet connection or model name."
            exit 1
        fi
    fi
done

echo "🚀 All rescuebox models are ready."
