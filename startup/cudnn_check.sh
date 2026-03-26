#!/usr/bin/env bash

# Get the OS and Architecture
OS=$(uname -s)
ARCH=$(uname -m)

if [[ "$OS" == "Linux" && "$ARCH" == "aarch64" ]]; then
    echo "Running on Linux aarch64 ARM."
    # for face-recognition
    export CUDNN_HOME=~/cudnn/cudnn-linux-aarch64-9.13.1.26_cuda13-archive
    export LD_LIBRARY_PATH=$CUDNN_HOME/lib:$LD_LIBRARY_PATH
    FOUND=$(ls "$CUDNN_HOME/lib/libcudnn.so" 2>/dev/null || true)
    if [[ -z "$FOUND" ]]; then
        echo "check cudnn version and fix this check"
        exit 1
    fi
    echo "cudnn library found OK"
else
    echo "Detected OS: $OS, Arch: $ARCH"
    echo "cudnn library needed if its linux only"
fi

