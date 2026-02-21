FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY watcher.py .
COPY ws_server.py .

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    psycopg2-binary \
    requests \
    watchdog \
    meilisearch

# Expose websocket API port
EXPOSE 9000

# Run both services
CMD sh -c "python watcher.py & uvicorn ws_server:app --host 0.0.0.0 --port 9000"
