"""
SCORPION_BRAIN Eagles Module
============================
High-level tools for file operations, code execution,
and system commands with safety features.

The Eagles are the "eyes in the sky" - providing
oversight and execution capabilities.
"""

from .eagle_toolbox import (
    EagleToolbox,
    create_file,
    execute_code,
    run_command,
    capture_screen,
    FileCreator,
    CodeSandbox,
    CommandRunner
)

__all__ = [
    'EagleToolbox',
    'create_file',
    'execute_code',
    'run_command',
    'capture_screen',
    'FileCreator',
    'CodeSandbox',
    'CommandRunner',
]
