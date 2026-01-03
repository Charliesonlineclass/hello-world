"""
SCORPION Security System - Labienus Module
===========================================

Labienus is the TAIL of the SCORPION - the security and access control
system that protects all client data and monitors for threats.

Named after Titus Labienus, Julius Caesar's trusted lieutenant who
managed logistics and security for the Roman legions.

SCORPION Architecture Role:
    TAIL/Labienus responsibilities:
    - Access control and authentication
    - Audit logging of all actions
    - Anomaly detection
    - Client portal access management
    - Security alerting to HEAD

Access Levels:
    HEAD (100): Master Charlie - full access to everything
    CLAW (75): Senior operators - access to assigned clients
    LEG (50): Client users - access only to their own data
    PUBLIC (10): Website visitors - no authenticated access

Security Principles:
    1. All actions are logged
    2. Access is denied by default
    3. Clients are isolated from each other
    4. Sensitive actions trigger alerts
    5. HEAD has complete visibility

Usage:
    from tail.labienus import AccessControl, AuditLog, ClientPortal

    # Set up access control
    access = AccessControl()
    user = access.create_user("John", "john@client.com", AccessLevel.LEG, ["j3_structural"])

    # Log actions
    audit = AuditLog()
    audit.log_access(user, "view_leads", "leads", {"count": 10}, "192.168.1.1")

    # Create client portal
    portal = ClientPortal(user, j3_leg)
    dashboard = portal.get_dashboard_data()

Author: SCORPION System
Version: 1.0.0
"""

from .access_control import (
    AccessControl,
    AccessLevel,
    User,
    Permission,
    TokenData,
)

from .audit_log import (
    AuditLog,
    AuditEntry,
    AnomalyType,
    SecurityAlert,
)

from .client_portal import (
    ClientPortal,
    DashboardData,
    Notification,
    NotificationType,
)

__all__ = [
    # Access Control
    'AccessControl',
    'AccessLevel',
    'User',
    'Permission',
    'TokenData',
    # Audit Log
    'AuditLog',
    'AuditEntry',
    'AnomalyType',
    'SecurityAlert',
    # Client Portal
    'ClientPortal',
    'DashboardData',
    'Notification',
    'NotificationType',
]
