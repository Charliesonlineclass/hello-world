"""
SCORPION TAIL - Security & Access Control (LABIENUS)
======================================================

Security layer providing authentication, authorization, and access control.
Named after Titus Labienus, Caesar's trusted second-in-command.

Access Levels:
    - HEAD: Full system access (Commander)
    - CLAW: Business unit access (Managers)
    - LEG: Container-specific access (Workers)
    - PUBLIC: Read-only public content

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .labienus.access_control import (
    AccessControl,
    AccessLevel,
    User,
    authenticate,
    check_permission,
    create_user
)

__version__ = "1.0.0"
__codename__ = "TESTUDO"
