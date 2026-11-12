#!/usr/bin/env bash
# Happy-path smoke test for the image-ingestion plugin.
# Requires the backend to be running (./run_backend_server). Uses MD5 and PDQ only,
# so no ONNX models or Ollama downloads are needed.

set -euo pipefail

API="${RESCUEBOX_API:-http://127.0.0.1:8000}/image_ingestion"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FOLDER="$ROOT/src-tauri/demo/image-ingestion/series_0013_Alexandria_Ocasio-Cortez_2019"
LABEL="smoke-test-$(date +%s)"
RENAMED="$LABEL-renamed"

call() {
    local task="$1" body="$2" expected="$3" response
    echo "+ curl -sS -X POST $API/$task -H 'Content-Type: application/json' -d '$body'"
    response=$(curl -sS -X POST "$API/$task" -H "Content-Type: application/json" -d "$body")
    echo "  $response"
    if [[ "$response" != *"$expected"* ]]; then
        echo "FAIL: expected '$expected'" >&2
        exit 1
    fi
}

ingest='{"inputs":{"input_dir":{"path":"'"$FOLDER"'"}},"parameters":{"label":"'"$LABEL"'","description":"smoke test","md5":"yes","pdq":"yes","semantic":"no","essay":"no"}}'
rename='{"inputs":{},"parameters":{"old_label":"'"$LABEL"'","new_label":"'"$RENAMED"'"}}'
delete='{"inputs":{},"parameters":{"label":"'"$RENAMED"'","retain_hashes":"no"}}'

call ingest_images "$ingest" "3 files"
call ingest_images "$ingest" "Label already in use"
call rename_archive "$rename" "Archive renamed"
call delete_archive "$delete" "Archive deleted"
call delete_archive "$delete" "Archive not found"

echo "PASS: ingest, duplicate label, rename, delete"
