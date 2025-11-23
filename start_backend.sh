#!/bin/bash
#
# J3 Interior Design - Backend Startup Script
# Run this script to start the lead qualification API
#

set -e

echo "========================================"
echo "J3 Interior Design - Backend Server"
echo "========================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

cd "$BACKEND_DIR"

# Create data directory for JSON persistence
mkdir -p data

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python 3.8+"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q flask flask-cors requests gunicorn

echo ""
echo "========================================"
echo "Starting API Server..."
echo "========================================"
echo "API URL: http://localhost:5000"
echo "Health: http://localhost:5000/api/health"
echo ""
echo "Test commands:"
echo "  curl http://localhost:5000/api/health"
echo "  curl -X POST http://localhost:5000/api/leads -H 'Content-Type: application/json' -d '{\"name\":\"Test\",\"email\":\"test@test.com\",\"phone\":\"713-555-1234\",\"zip\":\"77002\",\"project_type\":\"kitchen\",\"budget\":\"50k\"}'"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

# Run with gunicorn in production or flask in development
if [ "$1" == "prod" ]; then
    echo "Starting in PRODUCTION mode..."
    gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
else
    echo "Starting in DEVELOPMENT mode..."
    FLASK_DEBUG=true python3 api_server.py
fi
