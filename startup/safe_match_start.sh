#!/usr/bin/env bash
#
# --- Safe Match intermediary (optional docker compose service) ---
# Run once after placing the UMass credentials file; Docker restarts the service
# after reboots. Re-run after upgrading RescueBox to rebuild it.
set -euo pipefail

DIR="${RESCUEBOX_SAFE_MATCH_DIR:-$HOME/.rescuebox/safe-match}"
MODE="${RESCUEBOX_SAFE_MATCH_MODE:-live}"
if [[ "$MODE" != "stub" && ! -f "$DIR/credentials.json" ]]; then
	echo "Safe Match not started: no credentials at $DIR/credentials.json" >&2
	echo "Place the file from UMass there (chmod 600), or set RESCUEBOX_SAFE_MATCH_MODE=stub." >&2
	exit 1
fi
mkdir -p -m 700 "$DIR"
RESCUEBOX_SAFE_MATCH_UID="$(id -u)"
RESCUEBOX_SAFE_MATCH_GID="$(id -g)"
export RESCUEBOX_SAFE_MATCH_DIR="$DIR" RESCUEBOX_SAFE_MATCH_MODE="$MODE"
export RESCUEBOX_SAFE_MATCH_UID RESCUEBOX_SAFE_MATCH_GID

cd "$(dirname "$0")"
docker compose --profile safe-match up -d --build safe-match
for _ in $(seq 1 15); do
	if STATUS=$(curl -fsS --max-time 2 http://127.0.0.1:8090/v1/status); then
		echo "Safe Match intermediary running: $STATUS"
		exit 0
	fi
	sleep 2
done
echo "Safe Match intermediary did not respond; see: docker logs rb-safe-match" >&2
exit 1
