#!/usr/bin/env python3
"""
SCORPION AI - Castle Startup Script
Start all services for Pandora's Castle
"""

import subprocess
import sys
import time
import os
from pathlib import Path
import signal
import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crm.database import init_database, seed_demo_data
from config.settings import API_PORT, WEBSITE_PORT, OLLAMA_HOST

# Banner
BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🦂  SCORPION AI - PANDORA'S CASTLE                         ║
║                                                               ║
║   AI-Powered Business Automation System                      ║
║   Rent-to-Own Technology Solutions                           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""

processes = []


def check_ollama():
    """Check if Ollama is running"""
    try:
        response = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            return True
    except Exception:
        pass
    print("⚠️  Ollama not detected - AI chat will use fallback responses")
    return False


def start_api_server():
    """Start the FastAPI server"""
    api_path = Path(__file__).parent.parent / "api" / "main.py"
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "api.main:app",
        "--host", "0.0.0.0",
        "--port", str(API_PORT),
        "--reload"
    ], cwd=str(Path(__file__).parent.parent))
    processes.append(process)
    print(f"🚀 API Server starting on http://localhost:{API_PORT}")
    return process


def start_website_server():
    """Start a simple HTTP server for the website"""
    website_path = Path(__file__).parent.parent / "website"
    process = subprocess.Popen([
        sys.executable, "-m", "http.server",
        str(WEBSITE_PORT),
        "--directory", str(website_path)
    ])
    processes.append(process)
    print(f"🌐 Website serving on http://localhost:{WEBSITE_PORT}")
    return process


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🌙 Shutting down castle...")
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            process.kill()
    sys.exit(0)


def main():
    print(BANNER)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize database
    print("\n📦 Initializing database...")
    init_database()

    # Seed demo data if empty
    print("🌱 Checking demo data...")
    seed_demo_data()

    # Check Ollama
    print("\n🤖 Checking AI services...")
    check_ollama()

    # Start servers
    print("\n🏰 Starting Castle services...")
    start_api_server()
    time.sleep(2)  # Wait for API to start
    start_website_server()

    print("\n" + "═" * 60)
    print("🏰 PANDORA'S CASTLE IS ONLINE!")
    print("═" * 60)
    print(f"""
📍 Access Points:
   Website:     http://localhost:{WEBSITE_PORT}
   API:         http://localhost:{API_PORT}
   API Docs:    http://localhost:{API_PORT}/docs
   Admin:       http://localhost:{WEBSITE_PORT}/dashboard/index.html
   Portal:      http://localhost:{WEBSITE_PORT}/portal/login.html

🔑 Demo Credentials:
   Admin:  admin@ometeolt.com / admin123
   Client: j3@structural.com / demo123

Press Ctrl+C to shutdown
""")

    # Keep running
    try:
        while True:
            time.sleep(1)
            # Check if processes are still running
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"⚠️  Process {i} exited with code {process.returncode}")
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
