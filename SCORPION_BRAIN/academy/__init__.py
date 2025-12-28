"""
SCORPION_BRAIN Academy Module
=============================
The unified classroom system where AI babies learn and collaborate.

Babies:
- MARCUS: Logic & Reasoning specialist
- VULCAN: Building & Pattern specialist
- HERMES: Communication specialist
- ATHENA: Strategy & Planning specialist
- PHOENIX: Learning & Adaptation specialist
"""

from .classroom import UnifiedClassroom, Baby, Pipeline, CollaborationSession
from .algorithm_map import AlgorithmMap, BABY_SPECIALTIES
from .ollama_bridge import OllamaBridge, ModelConfig

__all__ = [
    'UnifiedClassroom',
    'Baby',
    'Pipeline',
    'CollaborationSession',
    'AlgorithmMap',
    'BABY_SPECIALTIES',
    'OllamaBridge',
    'ModelConfig'
]

__version__ = "1.0.0"
