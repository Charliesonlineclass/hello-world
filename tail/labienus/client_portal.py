"""
SCORPION Security System - Client Portal
==========================================

This module provides a secure portal interface for client users.
Each client can only access their own data through their leg.

SCORPION Architecture Role:
    Part of TAIL/Labienus - security boundary
    Enforces client isolation and access control

Features:
    - Dashboard data aggregation
    - Lead management interface
    - Report generation
    - Notifications
    - Secure data access

Security Guarantees:
    - Cannot access other clients' data
    - Cannot access HEAD-level analytics
    - Cannot see other LEG users
    - All actions logged to audit

Author: SCORPION System
Version: 1.0.0
"""

import json
from datetime import datetime, timedelta
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pathlib import Path
import uuid
import logging

if TYPE_CHECKING:
    from legs.base_leg import BaseClientLeg
    from tail.labienus.access_control import User

logger = logging.getLogger("scorpion.portal")


class NotificationType(Enum):
    """Types of notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ALERT = "alert"
    LEAD_NEW = "lead_new"
    LEAD_UPDATE = "lead_update"
    TASK_DUE = "task_due"
    REPORT_READY = "report_ready"
    SYSTEM = "system"


@dataclass
class Notification:
    """A notification for a client user."""
    id: str
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    created_at: datetime
    read: bool = False
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['notification_type'] = self.notification_type.value
        data['created_at'] = self.created_at.isoformat()
        data['read_at'] = self.read_at.isoformat() if self.read_at else None
        return data


@dataclass
class DashboardData:
    """Aggregated dashboard data for a client."""
    client_id: str
    client_name: str
    generated_at: datetime
    lead_stats: Dict[str, Any]
    recent_leads: List[Dict[str, Any]]
    activity_summary: Dict[str, Any]
    notifications: List[Dict[str, Any]]
    quick_actions: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data


class ClientPortal:
    """
    Secure client portal for SCORPION LEG users.

    Provides a controlled interface for clients to access their data.
    Enforces strict access control - clients can only see their own data.

    SCORPION Security:
    - Bound to a single user and leg at creation
    - Cannot access other clients' data
    - Cannot access HEAD-level analytics
    - Cannot see other LEG users
    - All actions are logged

    Usage:
        from tail.labienus import ClientPortal
        from legs import J3Leg

        # Create portal for a user
        portal = ClientPortal(user, j3_leg, access_control, audit_log)

        # Get dashboard
        dashboard = portal.get_dashboard_data()

        # Get leads
        leads = portal.get_leads({"status": "new"})

        # Update lead
        portal.update_lead_status(lead_id, "contacted")
    """

    def __init__(
        self,
        user: 'User',
        leg: 'BaseClientLeg',
        access_control: Optional[Any] = None,
        audit_log: Optional[Any] = None
    ):
        """
        Initialize client portal.

        Args:
            user: The authenticated user
            leg: The client's leg instance
            access_control: AccessControl instance for permission checks
            audit_log: AuditLog instance for logging
        """
        self.user = user
        self.leg = leg
        self.access_control = access_control
        self.audit_log = audit_log

        self._notifications: Dict[str, Notification] = {}

        # Verify user can access this leg
        if not self._can_access():
            raise PermissionError(
                f"User {user.id} cannot access client {leg.client_id}"
            )

        logger.info(f"ClientPortal created for user {user.id} accessing {leg.client_id}")

    def _can_access(self) -> bool:
        """Check if user can access this leg."""
        from tail.labienus.access_control import AccessLevel

        # HEAD can access everything
        if self.user.level == AccessLevel.HEAD:
            return True

        # Check if leg is in user's assigned clients
        return self.leg.client_id in self.user.assigned_clients

    def _log_action(self, action: str, details: Dict[str, Any]) -> None:
        """Log an action to the audit log."""
        if self.audit_log:
            self.audit_log.log_access(
                user_id=self.user.id,
                action=action,
                resource=f"portal:{self.leg.client_id}",
                details=details,
                client_id=self.leg.client_id
            )

    def _check_permission(self, resource: str, action: str) -> bool:
        """Check if user has permission for an action."""
        if self.access_control:
            return self.access_control.check_permission(self.user, resource, action)
        return True  # Default allow if no access control

    def get_dashboard_data(self) -> DashboardData:
        """
        Get aggregated dashboard data.

        Returns:
            DashboardData with stats, recent leads, and notifications
        """
        self._log_action("view_dashboard", {})

        # Get lead stats from leg
        stats = self.leg.get_stats()

        # Get recent leads
        leads = self.leg.get_leads()[:10]  # Last 10

        # Build activity summary
        activity_summary = {
            "leads_today": sum(
                1 for l in leads
                if l.created_at.date() == datetime.now().date()
            ),
            "ai_queries_today": stats.ai_queries if hasattr(stats, 'ai_queries') else 0,
            "conversion_rate": stats.conversion_rate if hasattr(stats, 'conversion_rate') else 0,
        }

        # Get unread notifications
        notifications = self.get_notifications()

        # Define quick actions based on industry
        quick_actions = self._get_quick_actions()

        dashboard = DashboardData(
            client_id=self.leg.client_id,
            client_name=self.leg.client_name,
            generated_at=datetime.now(),
            lead_stats={
                "total": stats.total_leads if hasattr(stats, 'total_leads') else len(leads),
                "new": stats.new_leads if hasattr(stats, 'new_leads') else 0,
                "converted": stats.converted_leads if hasattr(stats, 'converted_leads') else 0,
                "total_value": stats.total_value if hasattr(stats, 'total_value') else 0,
            },
            recent_leads=[l.to_dict() for l in leads[:5]],
            activity_summary=activity_summary,
            notifications=[n.to_dict() for n in notifications[:5]],
            quick_actions=quick_actions
        )

        return dashboard

    def _get_quick_actions(self) -> List[Dict[str, Any]]:
        """Get quick actions based on client industry."""
        from legs.base_leg import Industry

        actions = [
            {"id": "view_leads", "label": "View All Leads", "icon": "users"},
            {"id": "add_lead", "label": "Add New Lead", "icon": "plus"},
            {"id": "view_reports", "label": "View Reports", "icon": "chart"},
        ]

        industry_actions = {
            Industry.CONSTRUCTION: [
                {"id": "create_estimate", "label": "Create Estimate", "icon": "calculator"},
                {"id": "schedule_walkthrough", "label": "Schedule Walkthrough", "icon": "calendar"},
            ],
            Industry.CALL_CENTER: [
                {"id": "start_dialer", "label": "Start Dialer", "icon": "phone"},
                {"id": "view_scripts", "label": "Call Scripts", "icon": "file-text"},
            ],
            Industry.BANKING: [
                {"id": "new_application", "label": "New Application", "icon": "file-plus"},
                {"id": "risk_assessment", "label": "Risk Assessment", "icon": "shield"},
            ],
            Industry.REAL_ESTATE: [
                {"id": "search_properties", "label": "Search Properties", "icon": "home"},
                {"id": "schedule_showing", "label": "Schedule Showing", "icon": "calendar"},
            ],
        }

        if self.leg.industry in industry_actions:
            actions.extend(industry_actions[self.leg.industry])

        return actions

    def get_leads(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get leads with optional filtering.

        Args:
            filters: Optional filter criteria (status, date_range, etc.)

        Returns:
            List of lead dictionaries
        """
        if not self._check_permission("lead", "view"):
            raise PermissionError("No permission to view leads")

        status_filter = None
        if filters:
            status_filter = filters.get("status")

        leads = self.leg.get_leads(status_filter)

        # Apply additional filters
        if filters:
            if filters.get("search"):
                search = filters["search"].lower()
                leads = [
                    l for l in leads
                    if search in l.name.lower() or search in l.email.lower()
                ]

            if filters.get("date_from"):
                date_from = datetime.fromisoformat(filters["date_from"])
                leads = [l for l in leads if l.created_at >= date_from]

            if filters.get("date_to"):
                date_to = datetime.fromisoformat(filters["date_to"])
                leads = [l for l in leads if l.created_at <= date_to]

        self._log_action("view_leads", {
            "filters": filters,
            "count": len(leads)
        })

        return [l.to_dict() for l in leads]

    def get_lead_detail(self, lead_id: str) -> Dict[str, Any]:
        """
        Get full details for a lead.

        Args:
            lead_id: Lead ID

        Returns:
            Lead details dictionary

        Raises:
            PermissionError: If lead not found or not permitted
        """
        if not self._check_permission("lead", "view"):
            raise PermissionError("No permission to view leads")

        leads = self.leg.get_leads()
        lead = next((l for l in leads if l.id == lead_id), None)

        if not lead:
            raise PermissionError(f"Lead {lead_id} not found or access denied")

        self._log_action("view_lead_detail", {"lead_id": lead_id})

        return lead.to_dict()

    def update_lead_status(
        self,
        lead_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Update a lead's status.

        Args:
            lead_id: Lead ID
            status: New status

        Returns:
            Updated lead data
        """
        if not self._check_permission("lead", "update"):
            raise PermissionError("No permission to update leads")

        result = self.leg.update_lead(lead_id, status=status)

        if "error" in result:
            raise ValueError(result["error"])

        self._log_action("update_lead_status", {
            "lead_id": lead_id,
            "new_status": status
        })

        # Create notification for status change
        self._create_notification(
            notification_type=NotificationType.LEAD_UPDATE,
            title="Lead Status Updated",
            message=f"Lead status changed to {status}",
            data={"lead_id": lead_id, "status": status}
        )

        return result

    def request_quote(self, lead_id: str) -> Dict[str, Any]:
        """
        Request a quote generation for a lead.

        Args:
            lead_id: Lead ID

        Returns:
            Quote request result
        """
        if not self._check_permission("report", "generate"):
            raise PermissionError("No permission to generate quotes")

        # This would trigger the leg's quote generation
        result = self.leg.process_industry_request(
            "calculate_estimate" if hasattr(self.leg, "calculate_estimate") else "generate_report",
            {"lead_id": lead_id}
        )

        self._log_action("request_quote", {"lead_id": lead_id})

        return result

    def download_report(
        self,
        report_type: str,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Download a report. THIS ACTION IS LOGGED.

        Args:
            report_type: Type of report (leads, activity, performance)
            date_range: Optional date range

        Returns:
            Report data or download path
        """
        if not self._check_permission("report", "export"):
            raise PermissionError("No permission to export reports")

        # Get export format
        export_format = "csv"

        if report_type == "leads":
            result = self.leg.export_data(export_format)
        else:
            # Get stats as report
            stats = self.leg.get_stats(date_range)
            result = {
                "data": asdict(stats) if hasattr(stats, '__dataclass_fields__') else stats,
                "format": "json",
                "type": report_type
            }

        # Log as potential security concern
        if self.audit_log:
            self.audit_log.log_data_export(
                user_id=self.user.id,
                client_id=self.leg.client_id,
                export_format=export_format,
                row_count=result.get("count", 0)
            )

        self._log_action("download_report", {
            "report_type": report_type,
            "format": export_format,
            "_security_flag": "REPORT_DOWNLOAD"
        })

        return result

    def get_notifications(self) -> List[Notification]:
        """
        Get notifications for the current user.

        Returns:
            List of unread notifications
        """
        # Filter notifications for this user
        user_notifications = [
            n for n in self._notifications.values()
            if n.user_id == self.user.id
        ]

        # Sort by date, newest first
        user_notifications.sort(key=lambda n: n.created_at, reverse=True)

        return user_notifications

    def mark_notification_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID

        Returns:
            True if marked, False if not found
        """
        notification = self._notifications.get(notification_id)
        if not notification or notification.user_id != self.user.id:
            return False

        notification.read = True
        notification.read_at = datetime.now()

        self._log_action("read_notification", {"notification_id": notification_id})

        return True

    def _create_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Create a notification for the current user."""
        notification = Notification(
            id=f"notif_{uuid.uuid4().hex[:8]}",
            user_id=self.user.id,
            notification_type=notification_type,
            title=title,
            message=message,
            created_at=datetime.now(),
            data=data or {}
        )

        self._notifications[notification.id] = notification

        return notification

    def get_ai_assistant(self, prompt: str) -> Dict[str, Any]:
        """
        Query the AI assistant (baby) for this client.

        Args:
            prompt: Question or request

        Returns:
            AI response
        """
        if not self._check_permission("baby", "query"):
            raise PermissionError("No permission to query AI assistant")

        result = self.leg.query_baby(prompt)

        self._log_action("ai_query", {
            "prompt_length": len(prompt),
            "success": result.get("success", False)
        })

        return result

    def get_portal_info(self) -> Dict[str, Any]:
        """
        Get information about this portal session.

        Returns:
            Portal and user information
        """
        return {
            "user": {
                "id": self.user.id,
                "name": self.user.name,
                "level": self.user.level.name,
            },
            "client": {
                "id": self.leg.client_id,
                "name": self.leg.client_name,
                "industry": self.leg.industry.value,
            },
            "permissions": list(self.user.permissions),
            "available_actions": self.leg.get_industry_actions(),
            "baby_model": self.leg.baby_model,
        }

    def execute_industry_action(
        self,
        action: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an industry-specific action.

        Args:
            action: Action name
            data: Action parameters

        Returns:
            Action result
        """
        # Check if action is allowed
        available_actions = self.leg.get_industry_actions()
        if action not in available_actions:
            raise ValueError(f"Unknown action: {action}")

        # Execute through leg
        result = self.leg.process_industry_request(action, data)

        self._log_action(f"industry_action:{action}", {
            "data_keys": list(data.keys()),
            "success": "error" not in result
        })

        return result

    # Security restrictions - these methods explicitly deny access

    def access_other_client(self, client_id: str) -> None:
        """DENIED: Cannot access other clients."""
        raise PermissionError(
            "Access denied: Cannot access other clients' data. "
            "You are restricted to your assigned client only."
        )

    def view_head_analytics(self) -> None:
        """DENIED: Cannot view HEAD-level analytics."""
        raise PermissionError(
            "Access denied: HEAD-level analytics require elevated permissions."
        )

    def list_other_users(self) -> None:
        """DENIED: Cannot see other LEG users."""
        raise PermissionError(
            "Access denied: Cannot view other users at LEG access level."
        )

    def modify_system_settings(self) -> None:
        """DENIED: Cannot modify system settings."""
        raise PermissionError(
            "Access denied: System settings require HEAD access level."
        )
