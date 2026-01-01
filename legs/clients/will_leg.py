"""
Will Leg - Real Estate Services
================================

Client leg implementation for Will's real estate business.
Handles property matching, lead nurturing, and open house management.

Services:
- Property matching for buyers
- Lead nurturing campaigns
- Open house reminders and management
- Market analysis
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import uuid

from .base_leg import BaseClientLeg, ClientConfig, Industry, Lead, LeadStatus


class PropertyType(Enum):
    """Types of properties."""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    LAND = "land"
    COMMERCIAL = "commercial"


class BuyerStage(Enum):
    """Buyer journey stages."""
    BROWSING = "browsing"
    INTERESTED = "interested"
    PRE_APPROVED = "pre_approved"
    ACTIVELY_SEARCHING = "actively_searching"
    MAKING_OFFERS = "making_offers"
    UNDER_CONTRACT = "under_contract"
    CLOSED = "closed"


@dataclass
class Property:
    """Represents a property listing."""
    id: str
    address: str
    property_type: PropertyType
    price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    features: List[str] = field(default_factory=list)
    status: str = "active"  # active, pending, sold
    days_on_market: int = 0
    images: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "address": self.address,
            "property_type": self.property_type.value,
            "price": self.price,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "sqft": self.sqft,
            "features": self.features,
            "status": self.status,
            "days_on_market": self.days_on_market,
        }


@dataclass
class BuyerProfile:
    """Buyer preferences and profile."""
    client_id: str
    min_price: float = 0
    max_price: float = 1000000
    min_bedrooms: int = 1
    min_bathrooms: float = 1
    min_sqft: int = 0
    property_types: List[PropertyType] = field(default_factory=list)
    preferred_areas: List[str] = field(default_factory=list)
    must_have_features: List[str] = field(default_factory=list)
    stage: BuyerStage = BuyerStage.BROWSING
    pre_approval_amount: float = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "min_bedrooms": self.min_bedrooms,
            "min_bathrooms": self.min_bathrooms,
            "min_sqft": self.min_sqft,
            "property_types": [pt.value for pt in self.property_types],
            "preferred_areas": self.preferred_areas,
            "must_have_features": self.must_have_features,
            "stage": self.stage.value,
            "pre_approval_amount": self.pre_approval_amount,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class OpenHouse:
    """Open house event."""
    id: str
    property_id: str
    scheduled_time: datetime
    duration_hours: int = 2
    host_agent: str = ""
    attendees: List[str] = field(default_factory=list)
    reminders_sent: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "property_id": self.property_id,
            "scheduled_time": self.scheduled_time.isoformat(),
            "duration_hours": self.duration_hours,
            "host_agent": self.host_agent,
            "attendees": self.attendees,
            "reminders_sent": self.reminders_sent,
        }


@dataclass
class NurtureSequence:
    """Lead nurturing email sequence."""
    id: str
    lead_id: str
    sequence_name: str
    current_step: int = 0
    total_steps: int = 5
    status: str = "active"  # active, paused, completed
    emails_sent: int = 0
    opens: int = 0
    clicks: int = 0
    started_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "sequence_name": self.sequence_name,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "status": self.status,
            "emails_sent": self.emails_sent,
            "opens": self.opens,
            "clicks": self.clicks,
            "started_at": self.started_at.isoformat(),
        }


class WillLeg(BaseClientLeg):
    """
    Real estate services integration.

    Will's real estate business handles:
    - Buyer and seller leads
    - Property matching
    - Open house management
    - Lead nurturing campaigns
    """

    # Nurture sequence templates
    NURTURE_SEQUENCES = {
        "buyer_new": {
            "name": "New Buyer Welcome",
            "steps": 5,
            "emails": [
                "Welcome to your home search!",
                "Understanding the buying process",
                "Getting pre-approved",
                "Hot listings this week",
                "Schedule a consultation",
            ],
        },
        "buyer_active": {
            "name": "Active Buyer Engagement",
            "steps": 4,
            "emails": [
                "New listings matching your criteria",
                "Market update for your areas",
                "Open houses this weekend",
                "Tips for making competitive offers",
            ],
        },
        "seller_new": {
            "name": "New Seller Welcome",
            "steps": 4,
            "emails": [
                "Thinking of selling?",
                "What's your home worth?",
                "Preparing your home for sale",
                "Schedule a listing consultation",
            ],
        },
    }

    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize Will's leg with optional config."""
        if config is None:
            config = ClientConfig(
                name="Will Real Estate",
                industry=Industry.REAL_ESTATE,
                integrations=["mls", "email_campaigns", "sms", "calendar"],
                notification_emails=["will@realestate.com"],
                notification_phones=["+15559876543"],
            )
        super().__init__(config)

        # Real estate specific tracking
        self._properties: Dict[str, Property] = {}
        self._buyer_profiles: Dict[str, BuyerProfile] = {}
        self._open_houses: Dict[str, OpenHouse] = {}
        self._nurture_sequences: Dict[str, NurtureSequence] = {}

        # Metrics specific to real estate
        self._metrics.update({
            "properties_matched": 0,
            "open_houses_scheduled": 0,
            "nurture_emails_sent": 0,
            "showings_booked": 0,
            "offers_submitted": 0,
            "deals_closed": 0,
        })

    @property
    def industry(self) -> Industry:
        return Industry.REAL_ESTATE

    @property
    def services(self) -> List[str]:
        return [
            "property_matching",
            "lead_nurturing",
            "open_house_management",
            "market_analysis",
        ]

    def _setup_integrations(self) -> None:
        """Set up real estate integrations."""
        self.logger.info("Setting up MLS integration...")
        self.logger.info("Setting up email campaign system...")
        self.logger.info("Setting up SMS for reminders...")

    def process_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Process incoming real estate lead.

        Args:
            lead: The lead to process

        Returns:
            Dict with lead assessment and next steps
        """
        self.logger.info(f"Processing lead {lead.id} for real estate")
        self._metrics["leads_processed"] += 1

        # Store the lead
        self.add_lead(lead)

        # Determine lead type and stage
        lead_type = lead.data.get("lead_type", "buyer")
        timeline = lead.data.get("timeline", "6_months")

        # Score based on readiness
        lead.score = self._score_lead(lead)

        # Determine next action
        if lead.score >= 80:
            lead.status = LeadStatus.QUALIFIED
            next_action = "schedule_consultation"
        elif lead.score >= 50:
            lead.status = LeadStatus.CONTACTED
            next_action = "start_nurture_sequence"
        else:
            lead.status = LeadStatus.NURTURING
            next_action = "add_to_drip_campaign"

        # Start appropriate nurture sequence
        if lead_type == "buyer":
            sequence_type = "buyer_new"
        else:
            sequence_type = "seller_new"

        self.nurture_sequence(lead.id, sequence_type)

        return {
            "lead_id": lead.id,
            "lead_type": lead_type,
            "score": lead.score,
            "status": lead.status.value,
            "next_action": next_action,
        }

    def _score_lead(self, lead: Lead) -> int:
        """Score lead based on buying/selling readiness."""
        score = 50
        data = lead.data

        # Timeline impact
        timeline = data.get("timeline", "")
        if timeline == "immediately":
            score += 30
        elif timeline == "1_3_months":
            score += 20
        elif timeline == "3_6_months":
            score += 10

        # Pre-approval status
        if data.get("pre_approved", False):
            score += 20

        # Budget clarity
        if data.get("budget_defined", False):
            score += 10

        # Contact responsiveness
        if data.get("responded_to_outreach", False):
            score += 10

        return min(100, score)

    def match_properties(self, buyer_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Match properties to buyer criteria.

        Args:
            buyer_criteria: Buyer preferences and requirements

        Returns:
            List of matching properties
        """
        client_id = buyer_criteria.get("client_id", str(uuid.uuid4()))

        # Create or update buyer profile
        profile = BuyerProfile(
            client_id=client_id,
            min_price=buyer_criteria.get("min_price", 0),
            max_price=buyer_criteria.get("max_price", 1000000),
            min_bedrooms=buyer_criteria.get("min_bedrooms", 1),
            min_bathrooms=buyer_criteria.get("min_bathrooms", 1),
            min_sqft=buyer_criteria.get("min_sqft", 0),
            property_types=[
                PropertyType(pt) for pt in buyer_criteria.get("property_types", ["single_family"])
            ],
            preferred_areas=buyer_criteria.get("areas", []),
            must_have_features=buyer_criteria.get("must_have", []),
        )
        self._buyer_profiles[client_id] = profile

        # Find matching properties
        matches = []
        for prop in self._properties.values():
            if self._property_matches_criteria(prop, profile):
                match_score = self._calculate_match_score(prop, profile)
                matches.append({
                    "property": prop.to_dict(),
                    "match_score": match_score,
                })

        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        self._metrics["properties_matched"] += len(matches)
        self.logger.info(f"Found {len(matches)} matching properties for {client_id}")

        return matches[:10]  # Return top 10 matches

    def _property_matches_criteria(self, prop: Property, profile: BuyerProfile) -> bool:
        """Check if property matches buyer criteria."""
        if prop.status != "active":
            return False
        if prop.price < profile.min_price or prop.price > profile.max_price:
            return False
        if prop.bedrooms < profile.min_bedrooms:
            return False
        if prop.bathrooms < profile.min_bathrooms:
            return False
        if prop.sqft < profile.min_sqft:
            return False
        if profile.property_types and prop.property_type not in profile.property_types:
            return False
        return True

    def _calculate_match_score(self, prop: Property, profile: BuyerProfile) -> int:
        """Calculate how well property matches buyer preferences."""
        score = 70  # Base score for matching basic criteria

        # Bonus for must-have features
        for feature in profile.must_have_features:
            if feature.lower() in [f.lower() for f in prop.features]:
                score += 5

        # Price positioning (prefer middle of budget)
        budget_midpoint = (profile.min_price + profile.max_price) / 2
        price_diff = abs(prop.price - budget_midpoint) / budget_midpoint
        if price_diff < 0.1:
            score += 10
        elif price_diff < 0.2:
            score += 5

        # Days on market (newer listings score higher)
        if prop.days_on_market < 7:
            score += 10
        elif prop.days_on_market < 30:
            score += 5

        return min(100, score)

    def nurture_sequence(self, lead_id: str, sequence_type: str = "buyer_new") -> Dict[str, Any]:
        """
        Start a nurture drip campaign for a lead.

        Args:
            lead_id: Lead to nurture
            sequence_type: Type of nurture sequence

        Returns:
            Sequence details
        """
        sequence_id = str(uuid.uuid4())
        sequence_config = self.NURTURE_SEQUENCES.get(sequence_type, self.NURTURE_SEQUENCES["buyer_new"])

        sequence = NurtureSequence(
            id=sequence_id,
            lead_id=lead_id,
            sequence_name=sequence_config["name"],
            total_steps=sequence_config["steps"],
        )

        self._nurture_sequences[sequence_id] = sequence
        self.logger.info(f"Started nurture sequence {sequence_id} for lead {lead_id}")

        # Send first email
        self._send_nurture_email(sequence)

        return {
            "sequence_id": sequence_id,
            "lead_id": lead_id,
            "sequence_name": sequence_config["name"],
            "total_steps": sequence_config["steps"],
            "status": "active",
        }

    def _send_nurture_email(self, sequence: NurtureSequence) -> bool:
        """Send next email in nurture sequence."""
        sequence_config = None
        for config in self.NURTURE_SEQUENCES.values():
            if config["name"] == sequence.sequence_name:
                sequence_config = config
                break

        if not sequence_config or sequence.current_step >= sequence.total_steps:
            sequence.status = "completed"
            return False

        # In production, would send actual email
        sequence.emails_sent += 1
        sequence.current_step += 1
        self._metrics["nurture_emails_sent"] += 1

        self.logger.debug(f"Sent nurture email {sequence.current_step} for sequence {sequence.id}")
        return True

    def open_house_reminder(
        self,
        property_id: str,
        attendees: List[str]
    ) -> Dict[str, Any]:
        """
        Send open house reminders to attendees.

        Args:
            property_id: Property with open house
            attendees: List of client IDs to remind

        Returns:
            Reminder status
        """
        # Find open house for property
        open_house = None
        for oh in self._open_houses.values():
            if oh.property_id == property_id:
                open_house = oh
                break

        if not open_house:
            return {"success": False, "error": "No open house found for property"}

        prop = self._properties.get(property_id)
        if not prop:
            return {"success": False, "error": "Property not found"}

        # Send reminders
        reminders_sent = []
        for attendee in attendees:
            if attendee not in open_house.reminders_sent:
                self.send_notification(
                    f"Reminder: Open house at {prop.address} on {open_house.scheduled_time.strftime('%B %d at %I:%M %p')}",
                    channels=["email", "sms"]
                )
                open_house.reminders_sent.append(attendee)
                reminders_sent.append(attendee)

        self.logger.info(f"Sent {len(reminders_sent)} open house reminders")

        return {
            "success": True,
            "property_id": property_id,
            "open_house_time": open_house.scheduled_time.isoformat(),
            "reminders_sent": reminders_sent,
            "total_attendees": len(open_house.attendees),
        }

    def schedule_open_house(
        self,
        property_id: str,
        scheduled_time: datetime,
        host_agent: str = ""
    ) -> Dict[str, Any]:
        """Schedule an open house event."""
        open_house_id = str(uuid.uuid4())

        open_house = OpenHouse(
            id=open_house_id,
            property_id=property_id,
            scheduled_time=scheduled_time,
            host_agent=host_agent or "will",
        )

        self._open_houses[open_house_id] = open_house
        self._metrics["open_houses_scheduled"] += 1

        self.logger.info(f"Scheduled open house {open_house_id} for {scheduled_time}")

        return {
            "open_house_id": open_house_id,
            "property_id": property_id,
            "scheduled_time": scheduled_time.isoformat(),
            "host_agent": open_house.host_agent,
        }

    def daily_report(self) -> Dict[str, Any]:
        """
        Generate Will's daily metrics report.

        Returns:
            Dict containing daily performance metrics
        """
        today = datetime.now().date()

        # Today's open houses
        today_open_houses = [
            oh for oh in self._open_houses.values()
            if oh.scheduled_time.date() == today
        ]

        # Active nurture sequences
        active_sequences = [
            s for s in self._nurture_sequences.values()
            if s.status == "active"
        ]

        # Buyer stage distribution
        stage_distribution = {
            stage.value: len([
                p for p in self._buyer_profiles.values()
                if p.stage == stage
            ])
            for stage in BuyerStage
        }

        report = {
            "client": "Will Real Estate",
            "date": today.isoformat(),
            "generated_at": datetime.now().isoformat(),

            "leads": {
                "total": len(self._leads),
                "new_today": len([
                    l for l in self._leads.values()
                    if l.created_at.date() == today
                ]),
                "by_stage": stage_distribution,
            },

            "properties": {
                "total_listings": len(self._properties),
                "active": len([p for p in self._properties.values() if p.status == "active"]),
            },

            "open_houses": {
                "today": len(today_open_houses),
                "total_attendees_today": sum(len(oh.attendees) for oh in today_open_houses),
            },

            "nurturing": {
                "active_sequences": len(active_sequences),
                "emails_sent_total": self._metrics["nurture_emails_sent"],
            },

            "overall_metrics": self._metrics.copy(),
        }

        self.logger.info(f"Generated daily report for {today}")
        return report
