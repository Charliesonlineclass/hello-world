"""
IPC Solutions LEG
=================
Call center operations for Joe's IPC Solutions business.

Features:
- Lead capture and management
- Agent performance tracking
- Shift scheduling
- CLAW1 pipeline integration
"""

from .ipc_solutions import (
    IPCSolutionsLeg,
    lead_capture,
    agent_performance,
    shift_scheduler,
    Lead,
    Agent,
    Shift
)

__all__ = [
    'IPCSolutionsLeg',
    'lead_capture',
    'agent_performance',
    'shift_scheduler',
    'Lead',
    'Agent',
    'Shift',
]
