"""
SCORPION Core Module
====================

Central configuration and constants for the SCORPION automation platform.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .config import (
    ScorpionConfig,
    get_config,
    reload_config
)

from .constants import (
    PORTS,
    BABIES,
    ACCESS_LEVELS,
    FILE_PATHS,
    PIPELINE_STAGES,
    SERVICE_NAMES
)

__all__ = [
    # Config
    "ScorpionConfig",
    "get_config",
    "reload_config",
    # Constants
    "PORTS",
    "BABIES",
    "ACCESS_LEVELS",
    "FILE_PATHS",
    "PIPELINE_STAGES",
    "SERVICE_NAMES"
]

__version__ = "1.0.0"
__codename__ = "TESTUDO"
