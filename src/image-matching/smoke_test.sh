#!/usr/bin/env bash
# Happy-path smoke test for the image-matching plugin.
# Requires the backend to be running (./run_backend_server). Uses MD5 and PDQ only,
# so no ONNX models or Ollama downloads are needed.
# ESSAY=1 also ingests with essays (downloads the Ollama model on first use) and
# prints them from the rb-postgres database.

set -euo pipefail

API="${RESCUEBOX_API:-http://127.0.0.1:8000}/image_matching"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FOLDER="$ROOT/src-tauri/demo/image-matching/series_0013_Alexandria_Ocasio-Cortez_2019"
LABEL="smoke-test-$(date +%s)"
RENAMED="$LABEL-renamed"
ESSAY_LABEL="$LABEL-essay"

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

check_essays() {
    local sql="SELECT f.essay FROM files f JOIN archive_files af ON af.file_sha256 = f.sha256 JOIN archives a ON a.id = af.archive_id WHERE a.label = '$1' AND f.essay <> '';"
    local essays
    echo "+ docker exec -i rb-postgres psql -U rbuser -d rescuebox -At -c \"$sql\""
    essays=$(docker exec -i rb-postgres psql -U rbuser -d rescuebox -At -c "$sql")
    echo "$essays"
    if [[ $(grep -c . <<< "$essays") -ne 3 ]]; then
        echo "FAIL: expected 3 essays" >&2
        exit 1
    fi
}

ingest='{"inputs":{"input_dir":{"path":"'"$FOLDER"'"}},"parameters":{"label":"'"$LABEL"'","description":"smoke test","md5":"yes","pdq":"yes","semantic":"no","essay":"no","max_essay_words":60}}'
rename='{"inputs":{},"parameters":{"old_label":"'"$LABEL"'","new_label":"'"$RENAMED"'"}}'
rename_blank='{"inputs":{},"parameters":{"old_label":"'"$LABEL"'","new_label":""}}'
delete='{"inputs":{},"parameters":{"label":"'"$RENAMED"'","retain_hashes":"no"}}'

call ingest_images "$ingest" "3 files"
call archive_labels '{}' "\"$LABEL\""
call ingest_images "$ingest" "Label already in use"
call rename_archive "$rename_blank" "Label required"
call rename_archive "$rename" "Archive renamed"
call delete_archive "$delete" "Archive deleted"
call delete_archive "$delete" "Archive not found"

echo "PASS: ingest, archive labels, duplicate label, rename, delete"

if [[ "${ESSAY:-0}" == "1" ]]; then
    essay_ingest='{"inputs":{"input_dir":{"path":"'"$FOLDER"'"}},"parameters":{"label":"'"$ESSAY_LABEL"'","description":"essay smoke test","md5":"no","pdq":"no","semantic":"no","essay":"yes","max_essay_words":60}}'
    essay_delete='{"inputs":{},"parameters":{"label":"'"$ESSAY_LABEL"'","retain_hashes":"no"}}'
    call ingest_images "$essay_ingest" "3 files"
    check_essays "$ESSAY_LABEL"
    call delete_archive "$essay_delete" "Archive deleted"
    echo "PASS: essays"
fi
