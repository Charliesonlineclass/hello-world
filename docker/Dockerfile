# SCORPION AI - Pandora's Castle Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose ports
EXPOSE 8080 9999

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV API_PORT=9999
ENV WEBSITE_PORT=8080
ENV OLLAMA_HOST=http://ollama:11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9999/health || exit 1

# Run startup script
CMD ["python", "scripts/start_castle.py"]
