"""
SCORPION Multi-Tenant System - Integration Module
==================================================

Integration helpers for connecting SCORPION with external systems.

Components:
    - wp_connector.py: WordPress integration
    - client_router.py: Central request routing

Author: SCORPION System
Version: 1.0.0
"""

from .wp_connector import WPConnector
from .client_router import ClientRouter, RouteResult

__all__ = [
    'WPConnector',
    'ClientRouter',
    'RouteResult',
]
