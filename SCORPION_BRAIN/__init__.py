"""
SCORPION_BRAIN
==============
Unified AI Classroom System

A modular AI framework with 5 specialized "babies" that collaborate
using 13 core algorithms across reasoning, building, and communication.

Modules:
- academy: Unified classroom with babies, pipelines, collaboration
- algorithms: 13 algorithms (reasoning, building, communication, universal)
- senses: Input/output capabilities (visual, audio, speech, sensor, action)
- tools: Data harvesting and ingestion (GitHub, PyPI, ChromaDB)

Quick Start:
    from SCORPION_BRAIN.academy import UnifiedClassroom, create_classroom

    # Create the classroom
    classroom = create_classroom()

    # Quick task to any baby
    result = await classroom.quick_task("Analyze this code for patterns")

    # Start collaboration between babies
    session = classroom.start_collaboration(["MARCUS", "VULCAN"], mode="ROUND_ROBIN")
    result = await session.collaborate("Build a solution for X")

Babies:
- MARCUS: Logic & Reasoning (chain_of_thought, tree_of_thoughts, bayesian)
- VULCAN: Building & Patterns (cosine_similarity, graph_search, pattern_match)
- HERMES: Communication (tf_idf, sentiment, template_fill)
- ATHENA: Strategy & Planning
- PHOENIX: Learning & Adaptation

Author: The Scorpion King 🦂
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "The Scorpion King"
__codename__ = "SCORPION_BRAIN"

# Import main components for easy access
try:
    from .academy import UnifiedClassroom, create_classroom, Baby, Pipeline
    from .academy import AlgorithmMap, BABY_SPECIALTIES
    from .academy import OllamaBridge, get_ollama_bridge
except ImportError:
    # Allow partial imports during development
    pass

# Quick access to algorithm engines
try:
    from .algorithms import ReasoningEngine, BuildingEngine, CommunicationEngine, UniversalEngine
except ImportError:
    pass

# Quick access to senses
try:
    from .senses import VisualInput, AudioInput, SpeechOutput, SensorInput, ActionOutput
except ImportError:
    pass

# Quick access to tools
try:
    from .tools import GitHubHarvester, PyPIHarvester, IntelIngester
except ImportError:
    pass

__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__codename__',
    # Academy
    'UnifiedClassroom',
    'create_classroom',
    'Baby',
    'Pipeline',
    'AlgorithmMap',
    'BABY_SPECIALTIES',
    'OllamaBridge',
    'get_ollama_bridge',
    # Algorithms
    'ReasoningEngine',
    'BuildingEngine',
    'CommunicationEngine',
    'UniversalEngine',
    # Senses
    'VisualInput',
    'AudioInput',
    'SpeechOutput',
    'SensorInput',
    'ActionOutput',
    # Tools
    'GitHubHarvester',
    'PyPIHarvester',
    'IntelIngester',
]


def print_status():
    """Print SCORPION_BRAIN status banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                    🦂 SCORPION_BRAIN 🦂                    ║
    ║                  Unified AI Classroom v1.0                 ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  BABIES:                                                   ║
    ║    • MARCUS  - Logic & Reasoning     [chain_of_thought]   ║
    ║    • VULCAN  - Building & Patterns   [pattern_match]      ║
    ║    • HERMES  - Communication         [sentiment]          ║
    ║    • ATHENA  - Strategy & Planning   [tree_of_thoughts]   ║
    ║    • PHOENIX - Learning & Adaptation [exploration]        ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  ALGORITHMS: 13 core algorithms across 4 categories       ║
    ║  SENSES: Visual, Audio, Speech, Sensor, Action            ║
    ║  TOOLS: GitHub Harvester, PyPI Harvester, Intel Ingester  ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


if __name__ == "__main__":
    print_status()
