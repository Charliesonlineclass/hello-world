"""
SCORPION Legs Module
====================

Client-specific implementations that extend the base leg functionality.
Each leg represents a unique client with their specific business logic,
integrations, and workflow requirements.

Available Legs:
- JoeLeg: IPC Solutions call center
- JonathanLeg: J3 Structural Solutions
- AntonioLeg: Banking services
- WillLeg: Real estate services
"""

from .clients import (
    JoeLeg,
    JonathanLeg,
    AntonioLeg,
    WillLeg,
    BaseClientLeg,
)

__all__ = [
    "JoeLeg",
    "JonathanLeg",
    "AntonioLeg",
    "WillLeg",
    "BaseClientLeg",
]

__version__ = "1.0.0"
