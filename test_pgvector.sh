
# pre req docker-compose.yml and  docker-compose.yml

#docker compose up -d

docker exec -it 7ba363812934 psql -U rbuser -d rescuebox -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extversion FROM pg_extension WHERE extname = 'vector';"

pgcli -h 127.0.0.1 -p 5433 -u rbuser -d rescuebox
