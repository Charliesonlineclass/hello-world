"""
SCORPION LEGS - Client Container Templates
==========================================

Templates and utilities for creating client-specific LEG containers.
Each LEG handles a specific client's integrations and automations.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .template.client_template import (
    ClientConfig,
    BaseClientLeg,
    ExampleClientLeg,
    LegFactory
)

__all__ = [
    "ClientConfig",
    "BaseClientLeg",
    "ExampleClientLeg",
    "LegFactory"
]
