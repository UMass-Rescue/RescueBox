# Optional Docker deployment of the Safe Match intermediary; see README.md.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    RESCUEBOX_SAFE_MATCH_HOST=0.0.0.0 \
    RESCUEBOX_SAFE_MATCH_DATA_DIR=/data

WORKDIR /app

# pip does not read poetry.lock: keep these in step with it.
RUN pip install --no-cache-dir \
    fastapi==0.115.14 starlette==0.46.2 pydantic==2.12.5 httpx==0.28.1 uvicorn==0.32.1

COPY pyproject.toml ./
COPY safe_match_intermediary ./safe_match_intermediary
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8090
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD \
    python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/v1/status', timeout=4)"
CMD ["python", "-m", "safe_match_intermediary"]
