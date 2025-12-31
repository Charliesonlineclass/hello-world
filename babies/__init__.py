"""
SCORPION Babies Module
======================

AI Baby orchestration, management, and routing.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .council import BabyCouncil
from .classroom import Classroom
from .prompts import SYSTEM_PROMPTS, get_prompt

__all__ = [
    "BabyCouncil",
    "Classroom",
    "SYSTEM_PROMPTS",
    "get_prompt"
]
