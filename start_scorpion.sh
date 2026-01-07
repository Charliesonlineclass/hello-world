#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# SCORPION EMPIRE - Startup Script
# One-click deployment with health checks
# ═══════════════════════════════════════════════════════════════════════

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              🦂 SCORPION EMPIRE - INITIALIZING                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────────────────────────
# PREFLIGHT CHECKS
# ─────────────────────────────────────────────────────────────────────

echo "🔍 Running preflight checks..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✅ Docker installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not installed."
    exit 1
fi
echo "✅ Docker Compose installed"

# Check Docker daemon
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon not running. Please start Docker."
    exit 1
fi
echo "✅ Docker daemon running"

# Check for NVIDIA GPU (optional)
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected"
    GPU_AVAILABLE=true
else
    echo "⚠️  No NVIDIA GPU detected (Ollama will use CPU)"
    GPU_AVAILABLE=false
fi

echo ""

# ─────────────────────────────────────────────────────────────────────
# START SERVICES
# ─────────────────────────────────────────────────────────────────────

echo "🚀 Starting SCORPION EMPIRE services..."
echo ""

# Use docker compose (v2) or docker-compose (v1)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Start services
$COMPOSE_CMD up -d

echo ""
echo "⏳ Waiting for services to initialize..."
echo ""

# ─────────────────────────────────────────────────────────────────────
# HEALTH CHECKS
# ─────────────────────────────────────────────────────────────────────

check_service() {
    local name=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "✅ $name"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "❌ $name (timeout after ${max_attempts} attempts)"
    return 1
}

echo "🔍 Checking service health..."
echo ""

check_service "Ollama (LLM)"      "http://localhost:11434/api/tags"
check_service "ChromaDB (Vector)" "http://localhost:8000/api/v1/heartbeat"
check_service "Empire API"        "http://localhost:8800/health-check"
check_service "n8n (Workflows)"   "http://localhost:5678"
check_service "Grafana (Monitor)" "http://localhost:3001/api/health"
check_service "Redis (Cache)"     "http://localhost:6379" || echo "   (Redis uses TCP, may show as failed)"

echo ""

# ─────────────────────────────────────────────────────────────────────
# DISPLAY INFO
# ─────────────────────────────────────────────────────────────────────

# Get local IP
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           🦂 SCORPION EMPIRE - ALL SYSTEMS ONLINE             ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║  🌐 SERVICES:                                                 ║"
echo "║  ├── Command Center:  http://$IP:8800                    ║"
echo "║  ├── Ollama API:      http://$IP:11434                   ║"
echo "║  ├── ChromaDB:        http://$IP:8000                    ║"
echo "║  ├── n8n Workflows:   http://$IP:5678                    ║"
echo "║  ├── Grafana:         http://$IP:3001                    ║"
echo "║  └── Redis:           http://$IP:6379                    ║"
echo "║                                                               ║"
echo "║  🔐 DEFAULT CREDENTIALS:                                      ║"
echo "║  ├── n8n:     admin / scorpion123                             ║"
echo "║  └── Grafana: admin / scorpion123                             ║"
echo "║                                                               ║"
echo "║  📋 COMMANDS:                                                 ║"
echo "║  ├── Stop:    ./stop_scorpion.sh                              ║"
echo "║  ├── Logs:    docker-compose logs -f                          ║"
echo "║  └── Status:  docker-compose ps                               ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🦂 SCORPION EMPIRE is ready. Go build something great!"
echo ""
