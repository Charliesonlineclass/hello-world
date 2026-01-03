"""
SCORPION Multi-Tenant System - Client Router
=============================================

Central routing system for all client requests.
Routes requests to appropriate legs with access control.

SCORPION Architecture Role:
    Core routing layer
    Connects all components (LEGS, TAIL, BABIES)

Features:
    - Request routing to correct leg
    - Access validation
    - Aggregate statistics (HEAD only)
    - Broadcast messaging (HEAD only)
    - Leg lifecycle management

Author: SCORPION System
Version: 1.0.0
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Type
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger("scorpion.router")


@dataclass
class RouteResult:
    """Result of a routed request."""
    success: bool
    client_id: str
    action: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ClientRouter:
    """
    Central Router for SCORPION Client Requests.

    Routes all client requests to the appropriate leg after
    validating access permissions. Provides HEAD-level
    aggregate functions.

    SCORPION Architecture:
    - Central hub connecting all components
    - Enforces access control via Labienus
    - Routes to LEGS for processing
    - Logs all activity for audit

    Access Levels:
    - HEAD: Can access all legs, aggregate stats, broadcast
    - CLAW: Can access assigned clients only
    - LEG: Can access only their single client

    Usage:
        from tail.labienus import AccessControl, AuditLog
        from integration import ClientRouter

        access = AccessControl()
        audit = AuditLog()
        router = ClientRouter(access, audit)

        # Route a request
        result = router.route_request(user, "j3_structural", "get_leads", {})

        # Get aggregate stats (HEAD only)
        stats = router.aggregate_stats(head_user)
    """

    def __init__(
        self,
        access_control: Optional[Any] = None,
        audit_log: Optional[Any] = None,
        legs: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the client router.

        Args:
            access_control: AccessControl instance for permission checks
            audit_log: AuditLog instance for logging
            legs: Optional pre-initialized leg instances
        """
        self.access_control = access_control
        self.audit_log = audit_log

        # Leg instances cache
        self._legs: Dict[str, Any] = legs or {}

        # Leg class registry
        self._leg_classes: Dict[str, Type] = {}

        # Initialize leg registry
        self._register_leg_classes()

        logger.info("ClientRouter initialized")

    def _register_leg_classes(self) -> None:
        """Register available leg classes."""
        try:
            from legs import JoeLeg, AntonioLeg, J3Leg, WillLeg

            self._leg_classes = {
                "joe_ipc": JoeLeg,
                "antonio_banking": AntonioLeg,
                "j3_structural": J3Leg,
                "will_realestate": WillLeg,
            }
            logger.info(f"Registered {len(self._leg_classes)} leg classes")
        except ImportError as e:
            logger.warning(f"Could not import leg classes: {e}")

    def get_leg(self, client_id: str) -> Optional[Any]:
        """
        Get or create a leg instance for a client.

        Args:
            client_id: Client identifier

        Returns:
            Leg instance or None if not found
        """
        # Return cached instance if available
        if client_id in self._legs:
            return self._legs[client_id]

        # Try to create new instance
        leg_class = self._leg_classes.get(client_id)
        if not leg_class:
            logger.warning(f"No leg class registered for client {client_id}")
            return None

        try:
            # Create with default token (would be from config in production)
            leg = leg_class(access_token=f"default_token_{client_id}")
            self._legs[client_id] = leg
            logger.info(f"Created leg instance for {client_id}")
            return leg
        except Exception as e:
            logger.error(f"Error creating leg for {client_id}: {e}")
            return None

    def route_request(
        self,
        user: Any,
        client_id: str,
        action: str,
        data: Dict[str, Any]
    ) -> RouteResult:
        """
        Route a request to the appropriate leg.

        Validates access, routes to leg, and logs the action.

        Args:
            user: Authenticated user making request
            client_id: Target client ID
            action: Action to perform
            data: Action parameters

        Returns:
            RouteResult with success status and data
        """
        import time
        start_time = time.time()

        # Validate access
        if not self.validate_access(user, client_id, action):
            self._log_action(
                user_id=user.id if user else "unknown",
                client_id=client_id,
                action=action,
                success=False,
                details={"error": "access_denied"}
            )
            return RouteResult(
                success=False,
                client_id=client_id,
                action=action,
                error="Access denied"
            )

        # Get leg
        leg = self.get_leg(client_id)
        if not leg:
            return RouteResult(
                success=False,
                client_id=client_id,
                action=action,
                error=f"Client {client_id} not found"
            )

        # Route to leg
        try:
            # Determine request type
            from legs.base_leg import RequestType

            # Check if it's a standard request type
            standard_actions = {
                "query": RequestType.QUERY,
                "create_lead": RequestType.LEAD_CREATE,
                "update_lead": RequestType.LEAD_UPDATE,
                "get_leads": RequestType.LEAD_GET,
                "get_stats": RequestType.REPORT,
                "export_data": RequestType.EXPORT,
            }

            if action in standard_actions:
                result = leg.process_request(
                    standard_actions[action],
                    data,
                    user_id=user.id if user else None
                )
            else:
                # Industry-specific action
                result = leg.process_industry_request(action, data)

            duration_ms = int((time.time() - start_time) * 1000)

            self._log_action(
                user_id=user.id if user else "unknown",
                client_id=client_id,
                action=action,
                success=True,
                details={"duration_ms": duration_ms}
            )

            return RouteResult(
                success=True,
                client_id=client_id,
                action=action,
                data=result,
                duration_ms=duration_ms
            )

        except Exception as e:
            logger.error(f"Error routing request: {e}")
            duration_ms = int((time.time() - start_time) * 1000)

            self._log_action(
                user_id=user.id if user else "unknown",
                client_id=client_id,
                action=action,
                success=False,
                details={"error": str(e)}
            )

            return RouteResult(
                success=False,
                client_id=client_id,
                action=action,
                error=str(e),
                duration_ms=duration_ms
            )

    def validate_access(
        self,
        user: Any,
        client_id: str,
        action: str
    ) -> bool:
        """
        Validate user access to a client and action.

        Args:
            user: User object
            client_id: Target client
            action: Requested action

        Returns:
            True if access is permitted
        """
        if not user:
            return False

        # Check via access control if available
        if self.access_control:
            return self.access_control.can_access_client(user, client_id)

        # Fallback: check user's assigned clients
        if hasattr(user, 'assigned_clients'):
            if "*" in user.assigned_clients:
                return True
            return client_id in user.assigned_clients

        return False

    def aggregate_stats(self, user: Any) -> Dict[str, Any]:
        """
        Get aggregate statistics across all clients.

        HEAD access only - provides overview of all clients.

        Args:
            user: User requesting stats (must be HEAD level)

        Returns:
            Aggregate statistics dictionary
        """
        # Verify HEAD access
        if not self._is_head_user(user):
            return {"error": "HEAD access required"}

        all_stats = {
            "generated_at": datetime.now().isoformat(),
            "clients": {},
            "totals": {
                "total_leads": 0,
                "new_leads": 0,
                "converted_leads": 0,
                "total_value": 0.0,
                "ai_queries": 0,
            }
        }

        # Gather stats from each leg
        for client_id in self._leg_classes.keys():
            leg = self.get_leg(client_id)
            if not leg:
                continue

            try:
                stats = leg.get_stats()
                client_stats = {
                    "total_leads": getattr(stats, 'total_leads', 0),
                    "new_leads": getattr(stats, 'new_leads', 0),
                    "converted_leads": getattr(stats, 'converted_leads', 0),
                    "total_value": getattr(stats, 'total_value', 0),
                    "ai_queries": getattr(stats, 'ai_queries', 0),
                    "conversion_rate": getattr(stats, 'conversion_rate', 0),
                }

                all_stats["clients"][client_id] = client_stats

                # Accumulate totals
                for key in all_stats["totals"]:
                    all_stats["totals"][key] += client_stats.get(key, 0)

            except Exception as e:
                logger.error(f"Error getting stats for {client_id}: {e}")
                all_stats["clients"][client_id] = {"error": str(e)}

        # Calculate overall conversion rate
        total_leads = all_stats["totals"]["total_leads"]
        converted = all_stats["totals"]["converted_leads"]
        all_stats["totals"]["conversion_rate"] = (
            round(converted / total_leads * 100, 2) if total_leads > 0 else 0
        )

        self._log_action(
            user_id=user.id,
            client_id="all",
            action="aggregate_stats",
            success=True,
            details={"client_count": len(all_stats["clients"])}
        )

        return all_stats

    def get_all_legs(self, user: Any) -> List[Dict[str, Any]]:
        """
        Get information about all active legs.

        HEAD access only.

        Args:
            user: User requesting info (must be HEAD level)

        Returns:
            List of leg information dictionaries
        """
        if not self._is_head_user(user):
            return []

        legs_info = []
        for client_id in self._leg_classes.keys():
            leg = self.get_leg(client_id)
            if leg:
                legs_info.append(leg.get_leg_info())

        return legs_info

    def broadcast_message(
        self,
        user: Any,
        message: str,
        client_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Broadcast a message to multiple clients.

        HEAD access only.

        Args:
            user: User sending broadcast (must be HEAD level)
            message: Message to broadcast
            client_ids: List of target clients (None = all)

        Returns:
            Broadcast result
        """
        if not self._is_head_user(user):
            return {"error": "HEAD access required"}

        targets = client_ids or list(self._leg_classes.keys())
        results = {}

        for client_id in targets:
            leg = self.get_leg(client_id)
            if not leg:
                results[client_id] = {"sent": False, "error": "Leg not found"}
                continue

            try:
                # Log the broadcast as an activity
                leg.log_activity(
                    action="broadcast_received",
                    details={
                        "message": message[:100],
                        "from": user.id
                    }
                )
                results[client_id] = {"sent": True}
            except Exception as e:
                results[client_id] = {"sent": False, "error": str(e)}

        self._log_action(
            user_id=user.id,
            client_id="broadcast",
            action="broadcast_message",
            success=True,
            details={
                "target_count": len(targets),
                "success_count": sum(1 for r in results.values() if r.get("sent"))
            }
        )

        return {
            "message": message[:100] + "..." if len(message) > 100 else message,
            "targets": len(targets),
            "results": results
        }

    def _is_head_user(self, user: Any) -> bool:
        """Check if user has HEAD level access."""
        if not user:
            return False

        # Check access level
        if hasattr(user, 'level'):
            from tail.labienus.access_control import AccessLevel
            return user.level == AccessLevel.HEAD

        # Check by client assignment
        if hasattr(user, 'assigned_clients'):
            return "*" in user.assigned_clients

        return False

    def _log_action(
        self,
        user_id: str,
        client_id: str,
        action: str,
        success: bool,
        details: Dict[str, Any]
    ) -> None:
        """Log an action to the audit log."""
        if self.audit_log:
            self.audit_log.log_access(
                user_id=user_id,
                action=f"route_{action}",
                resource=f"client:{client_id}",
                details=details,
                client_id=client_id,
                success=success
            )

    def register_leg(self, client_id: str, leg_instance: Any) -> None:
        """
        Register a pre-initialized leg instance.

        Args:
            client_id: Client identifier
            leg_instance: Initialized leg object
        """
        self._legs[client_id] = leg_instance
        logger.info(f"Registered leg instance for {client_id}")

    def unregister_leg(self, client_id: str) -> bool:
        """
        Unregister and remove a leg instance.

        Args:
            client_id: Client identifier

        Returns:
            True if removed, False if not found
        """
        if client_id in self._legs:
            del self._legs[client_id]
            logger.info(f"Unregistered leg for {client_id}")
            return True
        return False

    def get_client_ids(self) -> List[str]:
        """Get list of all registered client IDs."""
        return list(self._leg_classes.keys())

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components.

        Returns:
            Health status dictionary
        """
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "router": "ok",
                "access_control": "ok" if self.access_control else "not_configured",
                "audit_log": "ok" if self.audit_log else "not_configured",
            },
            "clients": {}
        }

        for client_id in self._leg_classes.keys():
            try:
                leg = self.get_leg(client_id)
                if leg:
                    health["clients"][client_id] = {
                        "status": "ok",
                        "baby_model": leg.baby_model,
                        "industry": leg.industry.value
                    }
                else:
                    health["clients"][client_id] = {"status": "not_initialized"}
            except Exception as e:
                health["clients"][client_id] = {"status": "error", "error": str(e)}

        # Determine overall status
        if any(c.get("status") == "error" for c in health["clients"].values()):
            health["status"] = "degraded"

        return health
