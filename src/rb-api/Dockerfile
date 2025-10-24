# NB(Jagath): This dockerfile was hacked together to get the api running in a container.
# It can be improved with a multi-stage build process.

# Use the official lightweight Python 3.11 image
FROM python:3.11-slim

# Set environment variables for optimal Python performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.5.1 

# Create a working directory in the container
WORKDIR /rescuebox

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy all project files
COPY src /rescuebox/src/
COPY rescuebox /rescuebox/rescuebox
COPY pyproject.toml poetry.lock /rescuebox/
COPY key.pem /rescuebox/ca-certificates/
COPY cert.pem /rescuebox/ca-certificates/

# Update SSL certificates in the container
RUN update-ca-certificates

# Install dependencies without creating a virtual environment
WORKDIR /rescuebox/src/rb-api
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

# Expose the app’s port
EXPOSE 8000

# Run Uvicorn directly
CMD ["uvicorn", "rb.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--ssl-keyfile", "/rescuebox/ca-certificates/key.pem", "--ssl-certfile", "/rescuebox/ca-certificates/cert.pem"]
