#!/bin/bash

SERVICE="ollama"

if systemctl is-active --quiet $SERVICE; then
    echo "Stopping $SERVICE..."
    sudo systemctl stop $SERVICE
    
    # Wait up to 5 seconds for it to fully shut down
    for i in {1..5}; do
        if ! systemctl is-active --quiet $SERVICE; then
            echo "✅ $SERVICE is now offline."
            exit 0
        fi
        sleep 1
    done
    echo "⚠️ $SERVICE is taking a while to stop..."
else
    echo "ℹ️ $SERVICE was already stopped."
fi
