"""
SCORPION LEG Template Module
============================

Provides base classes and templates for client LEG containers.
"""

from .client_template import (
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
