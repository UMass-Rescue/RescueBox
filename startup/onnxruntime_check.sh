#!/usr/bin/env bash
# Verify onnxruntime exposes the expected execution provider for this OS.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

if ! command -v poetry >/dev/null 2>&1; then
    echo "Error: poetry is required." >&2
fi

OUT=$(poetry run python -c "import onnxruntime as ort; print(ort.get_available_providers())")

OS=$(uname -s)
echo "onnxruntime providers: $OUT"

case "$OS" in
    Linux)
        # on linux  check if $OUT contains  CUDAExecutionProvider
        if [[ "$OUT" != *CUDAExecutionProvider* ]]; then
            echo "Error: expected CUDAExecutionProvider in onnxruntime providers on Linux." >&2
            echo "Install a CUDA-enabled onnxruntime wheel if you need GPU (see docs/DGX_SPARK.md)." >&2
            exit 1
        fi
        echo "OK: CUDAExecutionProvider is available."
        ;;
    Darwin)
        # on macos check if $OUT contains CoreMLExecutionProvider
        if [[ "$OUT" != *CoreMLExecutionProvider* ]]; then
            echo "Error: expected CoreMLExecutionProvider in onnxruntime providers on macOS." >&2
            exit 1
        fi
        echo "OK: CoreMLExecutionProvider is available."
        ;;
    *)
        echo "Skipping provider check (unsupported OS for this script: $OS)."
        ;;
esac
