#!/usr/bin/bash
#
# --- PostgreSQL + pgvector (docker compose) ---
cd startup
if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker is required for the pgvector database." >&2
    exit 1
fi

echo "Starting pgvector database (docker compose)..."
docker compose up -d
CONTAINER=rb-postgres
# Match by name so other containers on the host are ignored
ID=`docker ps -q --filter "name=^${CONTAINER}$"`

if [[ "$ID" == "" ]];then
	echo "pgvector docker not running, fix and rerun"
	exit 1
else
	echo "pgvector docker running OK"
fi
# Wait for postgres to accept connections (up to ~60s)
for i in $(seq 1 30); do
	docker exec $CONTAINER pg_isready -U rbuser >/dev/null 2>&1 && break
	sleep 2
done
# Non-interactive: do not use -t (TTY), or docker exec can hang when no terminal
EXT=`docker exec -i $CONTAINER psql -U rbuser -d rescuebox -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extversion FROM pg_extension WHERE extname = 'vector';"`
if [[ "$EXT" == "" ]];then
	echo "pgvector extension not created, fix and rerun"
	exit 1
else
	echo "pgvector extension created OK"
fi
