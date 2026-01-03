"""
SCORPION Multi-Tenant System - Tail Module
==========================================

The TAIL (Labienus) is SCORPION's security and access control system.

Components:
    - labienus/access_control.py: Authentication and authorization
    - labienus/audit_log.py: Activity logging and anomaly detection
    - labienus/client_portal.py: Secure client portal interface

Author: SCORPION System
Version: 1.0.0
"""

from .labienus import (
    AccessControl,
    AccessLevel,
    User,
    Permission,
    TokenData,
    AuditLog,
    AuditEntry,
    AnomalyType,
    SecurityAlert,
    ClientPortal,
    DashboardData,
    Notification,
    NotificationType,
)

__all__ = [
    'AccessControl',
    'AccessLevel',
    'User',
    'Permission',
    'TokenData',
    'AuditLog',
    'AuditEntry',
    'AnomalyType',
    'SecurityAlert',
    'ClientPortal',
    'DashboardData',
    'Notification',
    'NotificationType',
]
