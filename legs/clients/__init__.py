"""
SCORPION Client Legs
====================

Individual client implementations with custom business logic.
Each leg inherits from BaseClientLeg and implements client-specific
methods for lead processing, reporting, and integrations.
"""

from .base_leg import BaseClientLeg
from .joe_leg import JoeLeg
from .jonathan_leg import JonathanLeg
from .antonio_leg import AntonioLeg
from .will_leg import WillLeg

__all__ = [
    "BaseClientLeg",
    "JoeLeg",
    "JonathanLeg",
    "AntonioLeg",
    "WillLeg",
]
