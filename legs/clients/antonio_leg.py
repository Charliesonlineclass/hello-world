"""
Antonio Leg - Banking Services
==============================

Client leg implementation for Antonio's banking services.
Handles lead scoring, compliance verification, and appointment scheduling.

Services:
- Financial lead scoring and risk assessment
- Compliance verification
- Consultation scheduling
- Client onboarding
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import uuid

from .base_leg import BaseClientLeg, ClientConfig, Industry, Lead, LeadStatus


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ComplianceStatus(Enum):
    """Compliance check status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_additional_info"


@dataclass
class FinancialProfile:
    """Financial profile for lead scoring."""
    client_id: str
    annual_income: float = 0.0
    credit_score: int = 0
    employment_status: str = ""
    debt_to_income: float = 0.0
    assets: float = 0.0
    existing_accounts: int = 0
    risk_score: int = 0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "annual_income": self.annual_income,
            "credit_score": self.credit_score,
            "employment_status": self.employment_status,
            "debt_to_income": self.debt_to_income,
            "assets": self.assets,
            "existing_accounts": self.existing_accounts,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ComplianceCheck:
    """Compliance verification record."""
    id: str
    client_id: str
    check_type: str  # kyc, aml, credit
    status: ComplianceStatus
    documents_required: List[str] = field(default_factory=list)
    documents_received: List[str] = field(default_factory=list)
    notes: str = ""
    reviewer_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "check_type": self.check_type,
            "status": self.status.value,
            "documents_required": self.documents_required,
            "documents_received": self.documents_received,
            "notes": self.notes,
            "reviewer_id": self.reviewer_id,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class Consultation:
    """Scheduled consultation appointment."""
    id: str
    client_id: str
    advisor_id: str
    scheduled_time: datetime
    duration_minutes: int = 30
    consultation_type: str = "general"
    confirmed: bool = False
    completed: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "advisor_id": self.advisor_id,
            "scheduled_time": self.scheduled_time.isoformat(),
            "duration_minutes": self.duration_minutes,
            "consultation_type": self.consultation_type,
            "confirmed": self.confirmed,
            "completed": self.completed,
            "notes": self.notes,
        }


class AntonioLeg(BaseClientLeg):
    """
    Banking services integration.

    Antonio's banking services handles:
    - Lead qualification and scoring
    - Compliance verification (KYC/AML)
    - Consultation scheduling
    - Risk assessment
    """

    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize Antonio's leg with optional config."""
        if config is None:
            config = ClientConfig(
                name="Antonio Banking Services",
                industry=Industry.BANKING,
                integrations=["credit_bureau", "compliance_api", "calendar"],
                notification_emails=["antonio@bankingservices.com"],
            )
        super().__init__(config)

        # Banking specific tracking
        self._profiles: Dict[str, FinancialProfile] = {}
        self._compliance_checks: Dict[str, ComplianceCheck] = {}
        self._consultations: Dict[str, Consultation] = {}
        self._advisors: List[str] = ["advisor_001", "advisor_002"]

        # Metrics specific to banking
        self._metrics.update({
            "leads_scored": 0,
            "compliance_checks_initiated": 0,
            "compliance_approved": 0,
            "consultations_scheduled": 0,
            "consultations_completed": 0,
        })

    @property
    def industry(self) -> Industry:
        return Industry.BANKING

    @property
    def services(self) -> List[str]:
        return [
            "lead_scoring",
            "compliance_verification",
            "consultation_scheduling",
            "risk_assessment",
        ]

    def _setup_integrations(self) -> None:
        """Set up banking integrations."""
        self.logger.info("Setting up credit bureau integration...")
        self.logger.info("Setting up compliance API...")
        self.logger.info("Setting up advisor calendar...")

    def process_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Process incoming lead with financial scoring.

        Args:
            lead: The lead to process

        Returns:
            Dict with scoring and compliance requirements
        """
        self.logger.info(f"Processing lead {lead.id} for banking services")
        self._metrics["leads_processed"] += 1

        # Store the lead
        self.add_lead(lead)

        # Score the lead
        score_result = self.score_financial_lead(lead)

        # Determine next steps based on score
        if score_result["risk_level"] == "low":
            lead.status = LeadStatus.QUALIFIED
            next_action = "schedule_consultation"
        elif score_result["risk_level"] == "medium":
            lead.status = LeadStatus.CONTACTED
            next_action = "request_documents"
        else:
            lead.status = LeadStatus.NURTURING
            next_action = "credit_improvement_resources"

        return {
            "lead_id": lead.id,
            "score_result": score_result,
            "status": lead.status.value,
            "next_action": next_action,
        }

    def score_financial_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Score a lead based on financial indicators.

        Args:
            lead: Lead with financial data

        Returns:
            Dict with risk assessment
        """
        data = lead.data
        self._metrics["leads_scored"] += 1

        # Extract financial data
        income = data.get("annual_income", 0)
        credit_score = data.get("credit_score", 0)
        employment = data.get("employment_status", "unknown")
        dti = data.get("debt_to_income", 0.5)

        # Calculate risk score (0-100, lower is better)
        risk_score = 50  # Base score

        # Credit score impact
        if credit_score >= 750:
            risk_score -= 20
        elif credit_score >= 700:
            risk_score -= 10
        elif credit_score >= 650:
            risk_score += 0
        elif credit_score >= 600:
            risk_score += 15
        else:
            risk_score += 30

        # Income impact
        if income >= 150000:
            risk_score -= 15
        elif income >= 100000:
            risk_score -= 10
        elif income >= 75000:
            risk_score -= 5
        elif income >= 50000:
            risk_score += 0
        else:
            risk_score += 10

        # Employment impact
        if employment in ["employed_full_time", "self_employed"]:
            risk_score -= 5
        elif employment == "employed_part_time":
            risk_score += 5
        else:
            risk_score += 15

        # DTI impact
        if dti <= 0.3:
            risk_score -= 10
        elif dti <= 0.4:
            risk_score -= 5
        elif dti <= 0.5:
            risk_score += 5
        else:
            risk_score += 15

        # Normalize score
        risk_score = max(0, min(100, risk_score))

        # Determine risk level
        if risk_score <= 30:
            risk_level = RiskLevel.LOW
        elif risk_score <= 50:
            risk_level = RiskLevel.MEDIUM
        elif risk_score <= 70:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH

        # Create profile
        profile = FinancialProfile(
            client_id=lead.id,
            annual_income=income,
            credit_score=credit_score,
            employment_status=employment,
            debt_to_income=dti,
            risk_score=risk_score,
            risk_level=risk_level,
        )
        self._profiles[lead.id] = profile

        lead.score = 100 - risk_score  # Higher lead score = lower risk

        return {
            "client_id": lead.id,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "lead_score": lead.score,
            "factors": {
                "credit_score": credit_score,
                "income": income,
                "employment": employment,
                "dti": dti,
            },
        }

    def compliance_check(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate compliance verification (KYC/AML).

        Args:
            client_data: Client information for verification

        Returns:
            Compliance check status and requirements
        """
        client_id = client_data.get("client_id", str(uuid.uuid4()))
        check_id = str(uuid.uuid4())

        # Determine required documents
        documents_required = [
            "government_id",
            "proof_of_address",
            "proof_of_income",
        ]

        # Check for additional requirements
        if client_data.get("high_value", False):
            documents_required.extend([
                "source_of_funds",
                "tax_returns",
            ])

        check = ComplianceCheck(
            id=check_id,
            client_id=client_id,
            check_type="kyc_aml",
            status=ComplianceStatus.PENDING,
            documents_required=documents_required,
        )

        self._compliance_checks[check_id] = check
        self._metrics["compliance_checks_initiated"] += 1

        self.logger.info(f"Initiated compliance check {check_id} for {client_id}")

        return {
            "check_id": check_id,
            "client_id": client_id,
            "status": check.status.value,
            "documents_required": documents_required,
            "next_steps": "Upload required documents for verification",
        }

    def update_compliance_status(
        self,
        check_id: str,
        status: str,
        documents_received: Optional[List[str]] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Update compliance check status."""
        check = self._compliance_checks.get(check_id)
        if not check:
            return {"success": False, "error": "Check not found"}

        check.status = ComplianceStatus(status)
        if documents_received:
            check.documents_received.extend(documents_received)
        if notes:
            check.notes = notes

        if status == "approved":
            check.completed_at = datetime.now()
            self._metrics["compliance_approved"] += 1

        return {
            "success": True,
            "check_id": check_id,
            "status": status,
            "documents_received": check.documents_received,
        }

    def schedule_consultation(
        self,
        client_id: str,
        scheduled_time: Optional[datetime] = None,
        consultation_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Schedule a consultation with a financial advisor.

        Args:
            client_id: Client ID
            scheduled_time: Requested time (defaults to next available)
            consultation_type: Type of consultation

        Returns:
            Scheduling confirmation
        """
        consultation_id = str(uuid.uuid4())

        # Default to next available slot if not specified
        if scheduled_time is None:
            scheduled_time = self._find_next_available_slot()

        # Select advisor
        advisor = self._select_advisor(scheduled_time)

        consultation = Consultation(
            id=consultation_id,
            client_id=client_id,
            advisor_id=advisor,
            scheduled_time=scheduled_time,
            consultation_type=consultation_type,
        )

        self._consultations[consultation_id] = consultation
        self._metrics["consultations_scheduled"] += 1

        # Send confirmation
        self.send_notification(
            f"Consultation scheduled for {scheduled_time.strftime('%B %d at %I:%M %p')}",
            channels=["email", "sms"]
        )

        self.logger.info(f"Scheduled consultation {consultation_id}")

        return {
            "consultation_id": consultation_id,
            "client_id": client_id,
            "advisor_id": advisor,
            "scheduled_time": scheduled_time.isoformat(),
            "consultation_type": consultation_type,
            "confirmation_sent": True,
        }

    def _find_next_available_slot(self) -> datetime:
        """Find next available consultation slot."""
        # Start from next business hour
        now = datetime.now()
        next_slot = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

        # Skip to next business day if needed
        while next_slot.weekday() >= 5:  # Saturday or Sunday
            next_slot += timedelta(days=1)

        # Business hours 9am - 5pm
        if next_slot.hour < 9:
            next_slot = next_slot.replace(hour=9)
        elif next_slot.hour >= 17:
            next_slot = next_slot.replace(hour=9) + timedelta(days=1)

        return next_slot

    def _select_advisor(self, scheduled_time: datetime) -> str:
        """Select available advisor."""
        return self._advisors[len(self._consultations) % len(self._advisors)]

    def daily_report(self) -> Dict[str, Any]:
        """
        Generate Antonio's daily metrics report.

        Returns:
            Dict containing daily performance metrics
        """
        today = datetime.now().date()

        # Today's consultations
        today_consultations = [
            c for c in self._consultations.values()
            if c.scheduled_time.date() == today
        ]

        # Compliance stats
        compliance_stats = {
            status.value: len([
                c for c in self._compliance_checks.values()
                if c.status == status
            ])
            for status in ComplianceStatus
        }

        # Risk distribution
        risk_distribution = {
            level.value: len([
                p for p in self._profiles.values()
                if p.risk_level == level
            ])
            for level in RiskLevel
        }

        report = {
            "client": "Antonio Banking Services",
            "date": today.isoformat(),
            "generated_at": datetime.now().isoformat(),

            "leads": {
                "total": len(self._leads),
                "scored": self._metrics["leads_scored"],
                "by_risk_level": risk_distribution,
            },

            "compliance": {
                "total_checks": len(self._compliance_checks),
                "by_status": compliance_stats,
            },

            "consultations": {
                "scheduled_today": len(today_consultations),
                "confirmed": len([c for c in today_consultations if c.confirmed]),
                "completed_total": self._metrics["consultations_completed"],
            },

            "overall_metrics": self._metrics.copy(),
        }

        self.logger.info(f"Generated daily report for {today}")
        return report
