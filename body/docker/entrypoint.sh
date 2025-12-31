#!/bin/bash
# =============================================================================
# SCORPION BRAIN - Container Entrypoint
# =============================================================================
# Starts the SCORPION services based on environment configuration.
# =============================================================================

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   SCORPION BRAIN                              ║"
echo "║              Starting Services...                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Wait for dependencies
echo "[*] Checking dependencies..."

# Check ChromaDB
if [ -n "$CHROMA_HOST" ]; then
    echo "    Waiting for ChromaDB at $CHROMA_HOST:${CHROMA_PORT:-8000}..."
    timeout=60
    while ! nc -z "$CHROMA_HOST" "${CHROMA_PORT:-8000}" 2>/dev/null; do
        timeout=$((timeout - 1))
        if [ $timeout -le 0 ]; then
            echo "    WARNING: ChromaDB not available, continuing anyway..."
            break
        fi
        sleep 1
    done
    echo "    ChromaDB: OK"
fi

# Check Ollama
if [ -n "$OLLAMA_HOST" ]; then
    echo "    Checking Ollama..."
    if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        echo "    Ollama: OK"
    else
        echo "    WARNING: Ollama not available"
    fi
fi

# Create necessary directories
mkdir -p /app/logs /app/data /app/transcripts /app/quotes 2>/dev/null || true

# Start services based on MODE environment variable
MODE=${MODE:-api}

case "$MODE" in
    api)
        echo "[*] Starting MOUTH API on port ${MOUTH_PORT:-8080}..."
        exec python -m uvicorn mouth.api:app --host 0.0.0.0 --port "${MOUTH_PORT:-8080}"
        ;;
    bridge)
        echo "[*] Starting BRIDGE server on port ${BRIDGE_PORT:-9876}..."
        exec python -m bridge.phone_server
        ;;
    both)
        echo "[*] Starting MOUTH API and BRIDGE..."
        python -m uvicorn mouth.api:app --host 0.0.0.0 --port "${MOUTH_PORT:-8080}" &
        exec python -m bridge.phone_server
        ;;
    scheduler)
        echo "[*] Starting JARVIS Scheduler..."
        exec python -m integration.scheduler
        ;;
    health)
        echo "[*] Starting Health Monitor..."
        exec python -m monitoring.health_check --daemon
        ;;
    cli)
        echo "[*] Starting CLI..."
        exec python -m integration.cli "$@"
        ;;
    *)
        echo "[*] Running custom command: $@"
        exec "$@"
        ;;
esac
