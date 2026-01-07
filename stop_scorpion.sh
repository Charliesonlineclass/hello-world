#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# SCORPION EMPIRE - Shutdown Script
# Gracefully stop all services
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              🦂 SCORPION EMPIRE - SHUTTING DOWN               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Use docker compose (v2) or docker-compose (v1)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "🛑 Stopping services..."
$COMPOSE_CMD down

echo ""
echo "✅ All SCORPION services stopped"
echo ""
echo "💾 Data volumes preserved. To remove all data:"
echo "   docker volume rm scorpion-ollama-data scorpion-chroma-data scorpion-n8n-data scorpion-grafana-data scorpion-redis-data"
echo ""
echo "🦂 SCORPION EMPIRE offline. See you next time!"
echo ""
