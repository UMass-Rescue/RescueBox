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
sleep 2
ID=`docker ps -a |  awk -F" " '{print $1}' | grep -v CONT`

if [[ "$ID" == "" ]];then
	echo "pgvector docker not running, fix and rerun"
	exit 1
else
	echo "pgvector docker running OK"
	sleep 5
fi
# Non-interactive: do not use -t (TTY), or docker exec can hang when no terminal
EXT=`docker exec -i $ID psql -U rbuser -d rescuebox -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extversion FROM pg_extension WHERE extname = 'vector';"`
if [[ "$EXT" == "" ]];then
	echo "pgvector extension not created, fix and rerun"
	exit 1
else
	echo "pgvector extension created OK"
fi
