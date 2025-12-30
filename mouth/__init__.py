"""
SCORPION MOUTH - Dashboard API
===============================

FastAPI backend for the SCORPION dashboard.
Provides unified access to all system components.

Endpoints:
    - GET /status - System status
    - GET /babies - Available AI models
    - GET /stats - System statistics
    - POST /ask - Query AI babies
    - POST /quote - Generate construction quote
    - POST /log-call - Log NSIPA call

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .api import app, start_server

__version__ = "1.0.0"
__codename__ = "TESTUDO"
