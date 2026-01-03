"""
SCORPION Security System - Audit Log
=====================================

This module provides comprehensive audit logging for the SCORPION system.
Every action is logged for security review and compliance.

SCORPION Architecture Role:
    Part of TAIL/Labienus - the security backbone
    Records all system activity for audit and anomaly detection

Features:
    - Complete activity logging
    - AI query tracking
    - Data export monitoring
    - Anomaly detection
    - Security alerting to HEAD
    - Compliance reporting

Author: SCORPION System
Version: 1.0.0
"""

import json
from datetime import datetime, timedelta
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from collections import defaultdict
import logging

logger = logging.getLogger("scorpion.audit")


class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    EXCESSIVE_REQUESTS = "excessive_requests"
    UNUSUAL_HOURS = "unusual_hours"
    MASS_EXPORT = "mass_export"
    FAILED_LOGINS = "failed_logins"
    RAPID_QUERIES = "rapid_queries"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"


class AlertSeverity(Enum):
    """Severity levels for security alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """A single audit log entry."""
    id: str
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str]
    client_id: Optional[str] = None
    success: bool = True
    duration_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEntry':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class SecurityAlert:
    """A security alert for HEAD notification."""
    id: str
    timestamp: datetime
    anomaly_type: AnomalyType
    severity: AlertSeverity
    user_id: str
    details: Dict[str, Any]
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolution: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['anomaly_type'] = self.anomaly_type.value
        data['severity'] = self.severity.value
        data['acknowledged_at'] = self.acknowledged_at.isoformat() if self.acknowledged_at else None
        return data


class AuditLog:
    """
    SCORPION Audit Log System.

    Provides comprehensive logging and anomaly detection for security.
    All actions in the system are recorded for audit purposes.

    Features:
    - Action logging with full context
    - AI query tracking and cost monitoring
    - Data export monitoring (flight risk detection)
    - Anomaly detection algorithms
    - Security alerting to HEAD
    - Weekly security reports

    Usage:
        audit = AuditLog()

        # Log an access
        audit.log_access(user, "view", "leads", {"count": 10}, "192.168.1.1")

        # Log AI query
        audit.log_baby_query(user, "phi3:mini", "prompt...", 500)

        # Check for anomalies
        anomaly = audit.detect_anomaly(user_id)
    """

    # Thresholds for anomaly detection
    THRESHOLDS = {
        "requests_per_day": 1000,
        "requests_per_hour": 200,
        "queries_per_hour": 100,
        "export_rows_alert": 500,
        "failed_logins_max": 5,
        "unusual_hour_start": 2,  # 2 AM
        "unusual_hour_end": 5,    # 5 AM
    }

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the audit log system.

        Args:
            data_dir: Directory for storing audit logs
        """
        self.data_dir = Path(data_dir) if data_dir else Path("./data/audit")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._entries: List[AuditEntry] = []
        self._alerts: List[SecurityAlert] = []
        self._user_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "requests_today": 0,
            "requests_this_hour": 0,
            "queries_this_hour": 0,
            "failed_logins": 0,
            "last_request": None,
            "export_rows_today": 0,
        })

        self._alert_callbacks: List[Callable[[SecurityAlert], None]] = []
        self._entry_counter = 0

        # Load recent data
        self._load_recent_data()

        logger.info("AuditLog initialized")

    def _load_recent_data(self) -> None:
        """Load recent audit entries from disk."""
        today = datetime.now().date()
        log_file = self.data_dir / f"audit_{today.isoformat()}.json"

        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    data = json.load(f)
                    self._entries = [AuditEntry.from_dict(e) for e in data.get("entries", [])]
                    self._entry_counter = len(self._entries)
            except Exception as e:
                logger.error(f"Error loading audit log: {e}")

        alerts_file = self.data_dir / "alerts.json"
        if alerts_file.exists():
            try:
                with open(alerts_file, 'r') as f:
                    data = json.load(f)
                    for alert_data in data.get("alerts", []):
                        alert_data['anomaly_type'] = AnomalyType(alert_data['anomaly_type'])
                        alert_data['severity'] = AlertSeverity(alert_data['severity'])
                        alert_data['timestamp'] = datetime.fromisoformat(alert_data['timestamp'])
                        if alert_data.get('acknowledged_at'):
                            alert_data['acknowledged_at'] = datetime.fromisoformat(alert_data['acknowledged_at'])
                        self._alerts.append(SecurityAlert(**alert_data))
            except Exception as e:
                logger.error(f"Error loading alerts: {e}")

    def _save_entries(self) -> None:
        """Save today's audit entries to disk."""
        today = datetime.now().date()
        log_file = self.data_dir / f"audit_{today.isoformat()}.json"

        try:
            # Only keep today's entries in memory
            today_entries = [e for e in self._entries if e.timestamp.date() == today]
            data = {"entries": [e.to_dict() for e in today_entries[-10000:]]}  # Last 10k
            with open(log_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving audit log: {e}")

    def _save_alerts(self) -> None:
        """Save alerts to disk."""
        alerts_file = self.data_dir / "alerts.json"
        try:
            data = {"alerts": [a.to_dict() for a in self._alerts[-1000:]]}  # Last 1000
            with open(alerts_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving alerts: {e}")

    def log_access(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        client_id: Optional[str] = None,
        success: bool = True,
        duration_ms: Optional[int] = None
    ) -> AuditEntry:
        """
        Log an access or action.

        Args:
            user_id: ID of user performing action
            action: Type of action (view, create, update, delete, etc.)
            resource: Resource being accessed
            details: Additional details about the action
            ip_address: Client IP address
            client_id: Associated client ID
            success: Whether action succeeded
            duration_ms: Duration of action in milliseconds

        Returns:
            Created AuditEntry
        """
        self._entry_counter += 1
        entry = AuditEntry(
            id=f"audit_{self._entry_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            client_id=client_id,
            success=success,
            duration_ms=duration_ms
        )

        self._entries.append(entry)
        self._update_user_stats(user_id, action, details)

        # Check for anomalies after each action
        self._check_anomalies(user_id, action, details)

        # Save periodically (every 100 entries)
        if len(self._entries) % 100 == 0:
            self._save_entries()

        return entry

    def log_baby_query(
        self,
        user_id: str,
        baby_name: str,
        prompt: str,
        response_length: int,
        duration_ms: Optional[int] = None,
        client_id: Optional[str] = None
    ) -> AuditEntry:
        """
        Log an AI baby query.

        Args:
            user_id: User making the query
            baby_name: Name of the Ollama model
            prompt: The prompt sent (truncated for privacy)
            response_length: Length of AI response
            duration_ms: Query duration
            client_id: Associated client

        Returns:
            Created AuditEntry
        """
        # Truncate prompt for logging (privacy)
        truncated_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt

        details = {
            "baby_name": baby_name,
            "prompt_preview": truncated_prompt,
            "prompt_length": len(prompt),
            "response_length": response_length,
        }

        # Update query stats
        stats = self._user_stats[user_id]
        stats["queries_this_hour"] = stats.get("queries_this_hour", 0) + 1

        return self.log_access(
            user_id=user_id,
            action="baby_query",
            resource=f"baby:{baby_name}",
            details=details,
            client_id=client_id,
            duration_ms=duration_ms
        )

    def log_data_export(
        self,
        user_id: str,
        client_id: str,
        export_format: str,
        row_count: int,
        ip_address: Optional[str] = None
    ) -> AuditEntry:
        """
        Log a data export. ALERTS if large export.

        Args:
            user_id: User performing export
            client_id: Client whose data is exported
            export_format: Format (csv, json, pdf)
            row_count: Number of rows exported
            ip_address: Client IP

        Returns:
            Created AuditEntry
        """
        details = {
            "format": export_format,
            "row_count": row_count,
            "_security_flag": "DATA_EXPORT"
        }

        # Update export stats
        stats = self._user_stats[user_id]
        stats["export_rows_today"] = stats.get("export_rows_today", 0) + row_count

        entry = self.log_access(
            user_id=user_id,
            action="data_export",
            resource=f"client:{client_id}",
            details=details,
            ip_address=ip_address,
            client_id=client_id
        )

        # Alert on large exports
        if row_count >= self.THRESHOLDS["export_rows_alert"]:
            self._create_alert(
                anomaly_type=AnomalyType.MASS_EXPORT,
                severity=AlertSeverity.HIGH,
                user_id=user_id,
                details={
                    "row_count": row_count,
                    "client_id": client_id,
                    "format": export_format,
                    "ip_address": ip_address
                }
            )

        return entry

    def _update_user_stats(
        self,
        user_id: str,
        action: str,
        details: Dict[str, Any]
    ) -> None:
        """Update user statistics for anomaly detection."""
        now = datetime.now()
        stats = self._user_stats[user_id]

        # Reset hourly stats if needed
        last_request = stats.get("last_request")
        if last_request:
            if isinstance(last_request, str):
                last_request = datetime.fromisoformat(last_request)
            if (now - last_request) > timedelta(hours=1):
                stats["requests_this_hour"] = 0
                stats["queries_this_hour"] = 0

        # Reset daily stats if needed
        if last_request:
            if last_request.date() != now.date():
                stats["requests_today"] = 0
                stats["failed_logins"] = 0
                stats["export_rows_today"] = 0

        stats["requests_today"] = stats.get("requests_today", 0) + 1
        stats["requests_this_hour"] = stats.get("requests_this_hour", 0) + 1
        stats["last_request"] = now.isoformat()

        if action == "auth_failed":
            stats["failed_logins"] = stats.get("failed_logins", 0) + 1

    def _check_anomalies(
        self,
        user_id: str,
        action: str,
        details: Dict[str, Any]
    ) -> None:
        """Check for anomalous behavior patterns."""
        now = datetime.now()
        stats = self._user_stats[user_id]

        # Check excessive requests
        if stats.get("requests_this_hour", 0) > self.THRESHOLDS["requests_per_hour"]:
            self._create_alert(
                anomaly_type=AnomalyType.EXCESSIVE_REQUESTS,
                severity=AlertSeverity.MEDIUM,
                user_id=user_id,
                details={"requests_this_hour": stats["requests_this_hour"]}
            )

        # Check unusual hours
        hour = now.hour
        if self.THRESHOLDS["unusual_hour_start"] <= hour < self.THRESHOLDS["unusual_hour_end"]:
            # Only alert once per session during unusual hours
            if not stats.get("unusual_hour_alerted"):
                self._create_alert(
                    anomaly_type=AnomalyType.UNUSUAL_HOURS,
                    severity=AlertSeverity.LOW,
                    user_id=user_id,
                    details={"hour": hour, "action": action}
                )
                stats["unusual_hour_alerted"] = True

        # Check failed logins
        if stats.get("failed_logins", 0) >= self.THRESHOLDS["failed_logins_max"]:
            self._create_alert(
                anomaly_type=AnomalyType.FAILED_LOGINS,
                severity=AlertSeverity.HIGH,
                user_id=user_id,
                details={"failed_attempts": stats["failed_logins"]}
            )

        # Check rapid AI queries
        if stats.get("queries_this_hour", 0) > self.THRESHOLDS["queries_per_hour"]:
            self._create_alert(
                anomaly_type=AnomalyType.RAPID_QUERIES,
                severity=AlertSeverity.MEDIUM,
                user_id=user_id,
                details={"queries_this_hour": stats["queries_this_hour"]}
            )

    def detect_anomaly(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Perform full anomaly detection for a user.

        Args:
            user_id: User ID to check

        Returns:
            Dict with anomaly details if found, None otherwise
        """
        stats = self._user_stats.get(user_id, {})
        anomalies = []

        # Check all thresholds
        if stats.get("requests_today", 0) > self.THRESHOLDS["requests_per_day"]:
            anomalies.append({
                "type": AnomalyType.EXCESSIVE_REQUESTS.value,
                "metric": "requests_today",
                "value": stats["requests_today"],
                "threshold": self.THRESHOLDS["requests_per_day"]
            })

        if stats.get("failed_logins", 0) > self.THRESHOLDS["failed_logins_max"]:
            anomalies.append({
                "type": AnomalyType.FAILED_LOGINS.value,
                "metric": "failed_logins",
                "value": stats["failed_logins"],
                "threshold": self.THRESHOLDS["failed_logins_max"]
            })

        if stats.get("export_rows_today", 0) > self.THRESHOLDS["export_rows_alert"] * 3:
            anomalies.append({
                "type": AnomalyType.DATA_EXFILTRATION.value,
                "metric": "export_rows_today",
                "value": stats["export_rows_today"],
                "threshold": self.THRESHOLDS["export_rows_alert"] * 3
            })

        if anomalies:
            return {
                "user_id": user_id,
                "anomalies": anomalies,
                "detected_at": datetime.now().isoformat()
            }

        return None

    def _create_alert(
        self,
        anomaly_type: AnomalyType,
        severity: AlertSeverity,
        user_id: str,
        details: Dict[str, Any]
    ) -> SecurityAlert:
        """Create and store a security alert."""
        alert = SecurityAlert(
            id=f"alert_{len(self._alerts)}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now(),
            anomaly_type=anomaly_type,
            severity=severity,
            user_id=user_id,
            details=details
        )

        self._alerts.append(alert)
        self._save_alerts()

        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

        logger.warning(f"SECURITY ALERT: {anomaly_type.value} for user {user_id} - {severity.value}")

        return alert

    def alert_head(
        self,
        anomaly_type: AnomalyType,
        user_id: str,
        details: Dict[str, Any]
    ) -> SecurityAlert:
        """
        Send an alert to HEAD (Master Charlie).

        Args:
            anomaly_type: Type of anomaly detected
            user_id: User involved
            details: Alert details

        Returns:
            Created SecurityAlert
        """
        return self._create_alert(
            anomaly_type=anomaly_type,
            severity=AlertSeverity.CRITICAL,
            user_id=user_id,
            details=details
        )

    def get_trail(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditEntry]:
        """
        Get audit trail for a user.

        Args:
            user_id: User ID to get trail for
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of AuditEntry objects
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        entries = [
            e for e in self._entries
            if e.user_id == user_id and start_date <= e.timestamp <= end_date
        ]

        return sorted(entries, key=lambda e: e.timestamp, reverse=True)

    def get_client_activity(
        self,
        client_id: str,
        days: int = 30
    ) -> List[AuditEntry]:
        """
        Get all activity for a client.

        Args:
            client_id: Client ID
            days: Number of days to look back

        Returns:
            List of AuditEntry objects
        """
        cutoff = datetime.now() - timedelta(days=days)
        entries = [
            e for e in self._entries
            if e.client_id == client_id and e.timestamp >= cutoff
        ]

        return sorted(entries, key=lambda e: e.timestamp, reverse=True)

    def get_unacknowledged_alerts(self) -> List[SecurityAlert]:
        """Get all unacknowledged security alerts."""
        return [a for a in self._alerts if not a.acknowledged]

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        resolution: Optional[str] = None
    ) -> bool:
        """
        Acknowledge a security alert.

        Args:
            alert_id: Alert ID to acknowledge
            acknowledged_by: User ID acknowledging
            resolution: Optional resolution notes

        Returns:
            True if acknowledged, False if not found
        """
        alert = next((a for a in self._alerts if a.id == alert_id), None)
        if not alert:
            return False

        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()
        alert.resolution = resolution

        self._save_alerts()
        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")

        return True

    def generate_security_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate a weekly security report.

        Args:
            days: Number of days to include

        Returns:
            Security report data
        """
        cutoff = datetime.now() - timedelta(days=days)

        # Filter entries for period
        period_entries = [e for e in self._entries if e.timestamp >= cutoff]
        period_alerts = [a for a in self._alerts if a.timestamp >= cutoff]

        # Calculate metrics
        unique_users = len(set(e.user_id for e in period_entries))
        total_actions = len(period_entries)

        # Action breakdown
        action_counts: Dict[str, int] = defaultdict(int)
        for entry in period_entries:
            action_counts[entry.action] += 1

        # Alert breakdown
        alert_counts: Dict[str, int] = defaultdict(int)
        for alert in period_alerts:
            alert_counts[alert.anomaly_type.value] += 1

        # Failed actions
        failed_actions = len([e for e in period_entries if not e.success])

        # Export activity
        exports = [e for e in period_entries if e.action == "data_export"]
        total_exported_rows = sum(e.details.get("row_count", 0) for e in exports)

        report = {
            "report_period": {
                "start": cutoff.isoformat(),
                "end": datetime.now().isoformat(),
                "days": days
            },
            "summary": {
                "unique_users": unique_users,
                "total_actions": total_actions,
                "failed_actions": failed_actions,
                "failure_rate": (failed_actions / total_actions * 100) if total_actions > 0 else 0,
            },
            "actions": dict(action_counts),
            "alerts": {
                "total": len(period_alerts),
                "unacknowledged": len([a for a in period_alerts if not a.acknowledged]),
                "by_type": dict(alert_counts),
                "critical": len([a for a in period_alerts if a.severity == AlertSeverity.CRITICAL])
            },
            "data_security": {
                "exports": len(exports),
                "total_rows_exported": total_exported_rows,
                "export_alerts": len([a for a in period_alerts if a.anomaly_type == AnomalyType.MASS_EXPORT])
            },
            "recommendations": self._generate_recommendations(period_entries, period_alerts)
        }

        return report

    def _generate_recommendations(
        self,
        entries: List[AuditEntry],
        alerts: List[SecurityAlert]
    ) -> List[str]:
        """Generate security recommendations based on data."""
        recommendations = []

        unack_alerts = [a for a in alerts if not a.acknowledged]
        if unack_alerts:
            recommendations.append(f"Review and acknowledge {len(unack_alerts)} pending security alerts")

        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        if critical_alerts:
            recommendations.append(f"Investigate {len(critical_alerts)} critical security alerts immediately")

        exports = [e for e in entries if e.action == "data_export"]
        if len(exports) > 10:
            recommendations.append("High export activity detected - review data access policies")

        failed = [e for e in entries if not e.success]
        if len(failed) > len(entries) * 0.1:
            recommendations.append("High failure rate - review system health and user training")

        if not recommendations:
            recommendations.append("No immediate security concerns detected")

        return recommendations

    def register_alert_callback(
        self,
        callback: Callable[[SecurityAlert], None]
    ) -> None:
        """Register a callback for new alerts."""
        self._alert_callbacks.append(callback)
