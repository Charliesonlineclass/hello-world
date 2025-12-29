"""
SCORPION Bridge: Phone to Linux Connection
==========================================

Connect your Android phone (via Termux) to your Linux server.
Query AI babies from anywhere with a simple REST API.

Modules:
    - phone_server: FastAPI server running on Linux
    - termux_client: Simple client for Termux on Android

Usage (Server - Linux):
    from bridge import start_server
    start_server(port=9876)

Usage (Client - Termux):
    python termux_client.py ask marcus "What is Python?"
    python termux_client.py quick "Summarize this text"

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .phone_server import (
    app,
    start_server,
    ScorpionAPI
)

__version__ = "1.0.0"
__codename__ = "TESTUDO"
__all__ = [
    'app',
    'start_server',
    'ScorpionAPI'
]
