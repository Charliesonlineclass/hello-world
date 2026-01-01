"""
Joe Leg - IPC Solutions Call Center
====================================

Client leg implementation for Joe's IPC Solutions call center.
Handles lead routing, call tracking, and credit repair referrals.

Services:
- Lead routing to credit professionals
- Call tracking and logging
- Credit repair referral management
- Email campaign integration
- NSIPA call logger integration
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

from .base_leg import BaseClientLeg, ClientConfig, Industry, Lead, LeadStatus


@dataclass
class CallRecord:
    """Represents a call in the system."""
    id: str
    lead_id: str
    agent_id: str
    duration_seconds: int
    disposition: str
    notes: str
    recorded: bool
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "agent_id": self.agent_id,
            "duration_seconds": self.duration_seconds,
            "disposition": self.disposition,
            "notes": self.notes,
            "recorded": self.recorded,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CreditRepairReferral:
    """Tracks credit repair referrals."""
    id: str
    lead_id: str
    credit_pro_id: str
    status: str  # pending, accepted, in_progress, completed
    commission: float
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "credit_pro_id": self.credit_pro_id,
            "status": self.status,
            "commission": self.commission,
            "created_at": self.created_at.isoformat(),
        }


class JoeLeg(BaseClientLeg):
    """
    IPC Solutions Call Center integration.

    Joe's call center handles:
    - Inbound/outbound call campaigns
    - Lead qualification and routing
    - Credit repair referrals
    - Campaign performance tracking
    """

    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize Joe's leg with optional config."""
        if config is None:
            config = ClientConfig(
                name="IPC Solutions",
                industry=Industry.CALL_CENTER,
                integrations=["nsipa", "email_campaigns", "sms"],
                notification_emails=["joe@ipcsolutions.com"],
            )
        super().__init__(config)

        # Call center specific tracking
        self._calls: Dict[str, CallRecord] = {}
        self._referrals: Dict[str, CreditRepairReferral] = {}
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._campaigns: Dict[str, Dict[str, Any]] = {}

        # Metrics specific to call center
        self._metrics.update({
            "calls_made": 0,
            "calls_answered": 0,
            "average_call_duration": 0,
            "referrals_made": 0,
            "referrals_converted": 0,
        })

    @property
    def industry(self) -> Industry:
        return Industry.CALL_CENTER

    @property
    def services(self) -> List[str]:
        return [
            "lead_routing",
            "call_tracking",
            "credit_repair_referrals",
            "email_campaigns",
            "nsipa_integration",
        ]

    def _setup_integrations(self) -> None:
        """Set up NSIPA and email campaign integrations."""
        self.logger.info("Setting up NSIPA call logger integration...")
        self.logger.info("Setting up email campaign integration...")
        # In production, would initialize actual API connections

    def process_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Process incoming lead and route to appropriate credit pro.

        Args:
            lead: The lead to process

        Returns:
            Dict with routing decision and next steps
        """
        self.logger.info(f"Processing lead {lead.id} for IPC Solutions")
        self._metrics["leads_processed"] += 1

        # Score the lead for credit repair potential
        credit_score = self._assess_credit_potential(lead)
        lead.score = credit_score

        # Store the lead
        self.add_lead(lead)

        # Determine routing
        if credit_score >= 70:
            routing = self._route_to_credit_pro(lead)
            lead.status = LeadStatus.QUALIFIED
        elif credit_score >= 40:
            routing = self._add_to_nurture_campaign(lead)
            lead.status = LeadStatus.NURTURING
        else:
            routing = {"action": "low_priority", "queue": "general"}
            lead.status = LeadStatus.CONTACTED

        return {
            "lead_id": lead.id,
            "credit_score": credit_score,
            "routing": routing,
            "status": lead.status.value,
            "next_action": routing.get("next_action", "follow_up_call"),
        }

    def _assess_credit_potential(self, lead: Lead) -> int:
        """Score lead based on credit repair potential."""
        score = 50  # Base score

        # Adjust based on lead data
        data = lead.data

        if data.get("has_debt", False):
            score += 15
        if data.get("credit_issues", False):
            score += 20
        if data.get("employed", True):
            score += 10
        if data.get("income", 0) > 50000:
            score += 10
        if data.get("homeowner", False):
            score -= 5  # Less likely to need credit repair

        return min(max(score, 0), 100)

    def _route_to_credit_pro(self, lead: Lead) -> Dict[str, Any]:
        """Route qualified lead to credit professional."""
        # Select best credit pro based on availability
        credit_pro = self._select_credit_pro(lead)

        return {
            "action": "route_to_credit_pro",
            "credit_pro_id": credit_pro,
            "next_action": "schedule_consultation",
            "priority": "high",
        }

    def _select_credit_pro(self, lead: Lead) -> str:
        """Select the best credit professional for this lead."""
        # In production, would check availability, specialty, etc.
        return "credit_pro_001"

    def _add_to_nurture_campaign(self, lead: Lead) -> Dict[str, Any]:
        """Add lead to nurture email campaign."""
        return {
            "action": "nurture_campaign",
            "campaign_id": "credit_awareness_2025",
            "next_action": "email_sequence",
            "touchpoints": 5,
        }

    def track_conversion(self, lead_id: str) -> Dict[str, Any]:
        """
        Track when a lead converts to credit repair signup.

        Args:
            lead_id: ID of the converting lead

        Returns:
            Conversion details
        """
        lead = self.get_lead(lead_id)
        if not lead:
            return {"success": False, "error": "Lead not found"}

        lead.status = LeadStatus.CONVERTED
        self._metrics["leads_converted"] += 1
        self._metrics["referrals_converted"] += 1

        self.logger.info(f"Lead {lead_id} converted to credit repair client!")

        # Send notification to Joe
        self.send_notification(
            f"New conversion! Lead {lead.name} signed up for credit repair.",
            channels=["email", "sms"]
        )

        return {
            "success": True,
            "lead_id": lead_id,
            "conversion_date": datetime.now().isoformat(),
            "commission_eligible": True,
        }

    def log_call(
        self,
        lead_id: str,
        agent_id: str,
        duration: int,
        disposition: str,
        notes: str = "",
        recorded: bool = True
    ) -> str:
        """
        Log a call to the NSIPA system.

        Args:
            lead_id: ID of the lead called
            agent_id: ID of the calling agent
            duration: Call duration in seconds
            disposition: Call outcome
            notes: Agent notes
            recorded: Whether call was recorded

        Returns:
            Call record ID
        """
        import uuid
        call_id = str(uuid.uuid4())

        call = CallRecord(
            id=call_id,
            lead_id=lead_id,
            agent_id=agent_id,
            duration_seconds=duration,
            disposition=disposition,
            notes=notes,
            recorded=recorded,
            timestamp=datetime.now(),
        )

        self._calls[call_id] = call
        self._metrics["calls_made"] += 1

        if disposition in ["answered", "connected", "callback_scheduled"]:
            self._metrics["calls_answered"] += 1

        # Update average call duration
        total_duration = sum(c.duration_seconds for c in self._calls.values())
        self._metrics["average_call_duration"] = total_duration // len(self._calls)

        self.logger.debug(f"Logged call {call_id} for lead {lead_id}")
        return call_id

    def create_referral(
        self,
        lead_id: str,
        credit_pro_id: str,
        commission: float = 100.0
    ) -> str:
        """
        Create a credit repair referral.

        Args:
            lead_id: Lead being referred
            credit_pro_id: Credit professional receiving referral
            commission: Commission amount for successful conversion

        Returns:
            Referral ID
        """
        import uuid
        referral_id = str(uuid.uuid4())

        referral = CreditRepairReferral(
            id=referral_id,
            lead_id=lead_id,
            credit_pro_id=credit_pro_id,
            status="pending",
            commission=commission,
            created_at=datetime.now(),
        )

        self._referrals[referral_id] = referral
        self._metrics["referrals_made"] += 1

        self.logger.info(f"Created referral {referral_id} to {credit_pro_id}")
        return referral_id

    def daily_report(self) -> Dict[str, Any]:
        """
        Generate Joe's daily metrics report.

        Returns:
            Dict containing daily performance metrics
        """
        today = datetime.now().date()

        # Calculate today's stats
        today_calls = [
            c for c in self._calls.values()
            if c.timestamp.date() == today
        ]

        today_referrals = [
            r for r in self._referrals.values()
            if r.created_at.date() == today
        ]

        report = {
            "client": "IPC Solutions",
            "date": today.isoformat(),
            "generated_at": datetime.now().isoformat(),

            "calls": {
                "total": len(today_calls),
                "answered": len([c for c in today_calls if c.disposition == "answered"]),
                "avg_duration_seconds": (
                    sum(c.duration_seconds for c in today_calls) // len(today_calls)
                    if today_calls else 0
                ),
            },

            "leads": {
                "total": len(self._leads),
                "new_today": len([
                    l for l in self._leads.values()
                    if l.created_at.date() == today
                ]),
                "converted_today": len([
                    l for l in self._leads.values()
                    if l.status == LeadStatus.CONVERTED
                    and l.updated_at.date() == today
                ]),
            },

            "referrals": {
                "made_today": len(today_referrals),
                "pending": len([r for r in self._referrals.values() if r.status == "pending"]),
                "converted": self._metrics["referrals_converted"],
            },

            "overall_metrics": self._metrics.copy(),
        }

        self.logger.info(f"Generated daily report for {today}")
        return report

    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get performance stats for a specific agent."""
        agent_calls = [c for c in self._calls.values() if c.agent_id == agent_id]

        return {
            "agent_id": agent_id,
            "total_calls": len(agent_calls),
            "total_duration": sum(c.duration_seconds for c in agent_calls),
            "avg_duration": (
                sum(c.duration_seconds for c in agent_calls) // len(agent_calls)
                if agent_calls else 0
            ),
            "dispositions": {
                disposition: len([c for c in agent_calls if c.disposition == disposition])
                for disposition in set(c.disposition for c in agent_calls)
            },
        }
