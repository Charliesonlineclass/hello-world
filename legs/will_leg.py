"""
SCORPION Multi-Tenant System - Will's Real Estate Leg
======================================================

This leg serves Will's Real Estate operations, specializing in
property matching, buyer nurturing, and transaction management.

SCORPION Architecture Role:
- LEG: Client interface for Will's Real Estate
- BABY: HERMES (tinyllama) - optimized for fast communication
- Industry: REAL_ESTATE
- Owner: Master Charlie (HEAD access)

Will's Real Estate specializes in:
- Buyer/seller matching
- Lead nurturing campaigns
- Property showings
- Market analysis

This leg handles property inquiries, buyer matching, showing scheduling,
and generates market reports.

Author: SCORPION System
Version: 1.0.0
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import uuid
import random

from .base_leg import (
    BaseClientLeg, Industry, Lead, LeadStatus,
    RequestType, logger
)


class PropertyType(Enum):
    """Types of properties."""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    LAND = "land"
    COMMERCIAL = "commercial"


class BuyerStage(Enum):
    """Stages in the buyer journey."""
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    EVALUATION = "evaluation"
    DECISION = "decision"
    CLOSED = "closed"
    LOST = "lost"


class SequenceType(Enum):
    """Types of nurture sequences."""
    NEW_BUYER = "new_buyer"
    HOT_LEAD = "hot_lead"
    COLD_REACTIVATION = "cold_reactivation"
    POST_SHOWING = "post_showing"
    SELLER_PREP = "seller_prep"
    JUST_LISTED = "just_listed"


@dataclass
class Property:
    """A property listing."""
    id: str
    address: str
    city: str
    state: str
    zip_code: str
    property_type: PropertyType
    bedrooms: int
    bathrooms: float
    sqft: int
    price: float
    year_built: int
    features: List[str]
    listing_date: datetime
    status: str = "active"
    mls_number: Optional[str] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['property_type'] = self.property_type.value
        data['listing_date'] = self.listing_date.isoformat()
        return data


@dataclass
class BuyerCriteria:
    """Buyer's property search criteria."""
    lead_id: str
    min_price: float
    max_price: float
    property_types: List[PropertyType]
    min_bedrooms: int
    min_bathrooms: float
    min_sqft: int
    max_sqft: int
    preferred_cities: List[str]
    must_have_features: List[str]
    nice_to_have_features: List[str]
    move_in_date: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['property_types'] = [pt.value for pt in self.property_types]
        data['move_in_date'] = self.move_in_date.isoformat() if self.move_in_date else None
        return data


@dataclass
class Showing:
    """A property showing appointment."""
    id: str
    lead_id: str
    property_id: str
    scheduled_datetime: datetime
    agent: str
    notes: str = ""
    status: str = "scheduled"
    feedback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['scheduled_datetime'] = self.scheduled_datetime.isoformat()
        return data


@dataclass
class NurtureSequence:
    """An active nurture sequence for a lead."""
    id: str
    lead_id: str
    sequence_type: SequenceType
    current_step: int
    total_steps: int
    started_at: datetime
    next_action_date: datetime
    paused: bool = False
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['sequence_type'] = self.sequence_type.value
        data['started_at'] = self.started_at.isoformat()
        data['next_action_date'] = self.next_action_date.isoformat()
        return data


@dataclass
class MarketReport:
    """A market analysis report."""
    id: str
    zip_code: str
    generated_at: datetime
    avg_price: float
    median_price: float
    avg_days_on_market: int
    active_listings: int
    sold_last_30: int
    price_trend: str
    inventory_level: str
    analysis: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data


class WillLeg(BaseClientLeg):
    """
    SCORPION Leg for Will's Real Estate.

    Connects to HERMES (tinyllama) for fast communication.
    Handles property matching, showings, and nurture campaigns.

    SCORPION Security:
    - All client interactions logged to Labienus audit system
    - Only Will's team can access this leg (LEG level access)
    - HEAD (Master Charlie) has full oversight
    - MLS data access is logged
    """

    # Nurture sequence configurations
    NURTURE_SEQUENCES = {
        SequenceType.NEW_BUYER: {
            "steps": 7,
            "interval_days": 3,
            "messages": [
                "Welcome email with area guide",
                "Featured listings matching criteria",
                "Buyer tips: What to look for",
                "Financing options overview",
                "Schedule showing invitation",
                "Market update for preferred areas",
                "Personal check-in call"
            ]
        },
        SequenceType.HOT_LEAD: {
            "steps": 4,
            "interval_days": 1,
            "messages": [
                "Immediate property matches",
                "Showing availability",
                "Similar sold properties",
                "Make an offer guidance"
            ]
        },
        SequenceType.POST_SHOWING: {
            "steps": 3,
            "interval_days": 2,
            "messages": [
                "Thank you + feedback request",
                "Similar available properties",
                "Next steps discussion"
            ]
        }
    }

    def __init__(
        self,
        access_token: str,
        data_dir: Optional[str] = None,
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize Will's Real Estate leg.

        Args:
            access_token: Authentication token
            data_dir: Data storage directory
            ollama_url: Ollama server URL
        """
        super().__init__(
            client_id="will_realestate",
            client_name="Will's Real Estate",
            baby_model="tinyllama",  # HERMES
            industry=Industry.REAL_ESTATE,
            access_token=access_token,
            data_dir=data_dir,
            ollama_url=ollama_url
        )

        # Will-specific data storage
        self._properties: Dict[str, Property] = {}
        self._buyer_criteria: Dict[str, BuyerCriteria] = {}
        self._showings: Dict[str, Showing] = {}
        self._nurture_sequences: Dict[str, NurtureSequence] = {}
        self._market_reports: Dict[str, MarketReport] = {}

        # Load Will's data
        self._load_will_data()
        self._load_sample_properties()

        logger.info(f"Will's Real Estate leg initialized with HERMES (tinyllama)")

    def _load_will_data(self) -> None:
        """Load Will-specific data from disk."""
        showings_file = self.data_dir / "showings.json"
        if showings_file.exists():
            try:
                with open(showings_file, 'r') as f:
                    data = json.load(f)
                    for showing in data:
                        showing['scheduled_datetime'] = datetime.fromisoformat(showing['scheduled_datetime'])
                        self._showings[showing['id']] = Showing(**showing)
            except Exception as e:
                logger.error(f"Error loading showings: {e}")

    def _save_will_data(self) -> None:
        """Save Will-specific data to disk."""
        showings_file = self.data_dir / "showings.json"
        with open(showings_file, 'w') as f:
            json.dump([s.to_dict() for s in self._showings.values()], f, indent=2)

    def _load_sample_properties(self) -> None:
        """Load sample property listings."""
        if not self._properties:
            samples = [
                Property(
                    id="prop_001",
                    address="123 Oak Street",
                    city="Austin",
                    state="TX",
                    zip_code="78701",
                    property_type=PropertyType.SINGLE_FAMILY,
                    bedrooms=3,
                    bathrooms=2.5,
                    sqft=2200,
                    price=450000,
                    year_built=2015,
                    features=["Pool", "Garage", "Updated Kitchen"],
                    listing_date=datetime.now() - timedelta(days=14),
                    mls_number="MLS123456"
                ),
                Property(
                    id="prop_002",
                    address="456 Downtown Blvd #12",
                    city="Austin",
                    state="TX",
                    zip_code="78702",
                    property_type=PropertyType.CONDO,
                    bedrooms=2,
                    bathrooms=2.0,
                    sqft=1400,
                    price=325000,
                    year_built=2020,
                    features=["Rooftop Access", "Gym", "Concierge"],
                    listing_date=datetime.now() - timedelta(days=7),
                    mls_number="MLS123457"
                ),
                Property(
                    id="prop_003",
                    address="789 Hill Country Rd",
                    city="Dripping Springs",
                    state="TX",
                    zip_code="78620",
                    property_type=PropertyType.SINGLE_FAMILY,
                    bedrooms=4,
                    bathrooms=3.0,
                    sqft=3500,
                    price=675000,
                    year_built=2018,
                    features=["5 Acres", "Barn", "Guest House", "Views"],
                    listing_date=datetime.now() - timedelta(days=3),
                    mls_number="MLS123458"
                ),
            ]
            for prop in samples:
                self._properties[prop.id] = prop

    def get_industry_actions(self) -> List[str]:
        """Return Will-specific actions."""
        return [
            "match_properties",
            "nurture_sequence",
            "schedule_showing",
            "open_house_notify",
            "generate_market_report",
            "track_buyer_journey"
        ]

    def process_industry_request(
        self,
        action: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route Will-specific requests."""
        handlers = {
            "match_properties": lambda d: self.match_properties(d['buyer_criteria']),
            "nurture_sequence": lambda d: self.nurture_sequence(
                d['lead_id'],
                SequenceType(d.get('sequence_type', 'new_buyer'))
            ),
            "schedule_showing": lambda d: self.schedule_showing(
                d['lead_id'],
                d['property_id'],
                d['datetime']
            ),
            "open_house_notify": lambda d: self.open_house_notify(
                d['property_id'],
                d['date'],
                d.get('attendee_list', [])
            ),
            "generate_market_report": lambda d: self.generate_market_report(d['zip_code']),
            "track_buyer_journey": lambda d: self.track_buyer_journey(d['lead_id']),
        }

        handler = handlers.get(action)
        if not handler:
            return {"error": f"Unknown Will's Real Estate action: {action}"}

        return handler(data)

    def match_properties(
        self,
        buyer_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Match properties to buyer criteria.

        Args:
            buyer_criteria: Dictionary with buyer preferences including:
                - min_price, max_price
                - property_types
                - min_bedrooms, min_bathrooms
                - min_sqft, max_sqft
                - preferred_cities
                - must_have_features

        Returns:
            List of matching properties with match scores
        """
        min_price = buyer_criteria.get('min_price', 0)
        max_price = buyer_criteria.get('max_price', float('inf'))
        property_types = buyer_criteria.get('property_types', [])
        min_beds = buyer_criteria.get('min_bedrooms', 0)
        min_baths = buyer_criteria.get('min_bathrooms', 0)
        min_sqft = buyer_criteria.get('min_sqft', 0)
        max_sqft = buyer_criteria.get('max_sqft', float('inf'))
        cities = [c.lower() for c in buyer_criteria.get('preferred_cities', [])]
        must_have = [f.lower() for f in buyer_criteria.get('must_have_features', [])]
        nice_to_have = [f.lower() for f in buyer_criteria.get('nice_to_have_features', [])]

        matches = []

        for prop in self._properties.values():
            if prop.status != "active":
                continue

            score = 0
            max_score = 100
            match_reasons = []
            miss_reasons = []

            # Price check (30 points)
            if min_price <= prop.price <= max_price:
                score += 30
                match_reasons.append("Within budget")
            else:
                miss_reasons.append("Outside price range")
                continue  # Hard requirement

            # Property type (15 points)
            if not property_types or prop.property_type.value in property_types:
                score += 15
                match_reasons.append("Property type match")
            else:
                miss_reasons.append("Different property type")

            # Bedrooms (15 points)
            if prop.bedrooms >= min_beds:
                score += 15
                match_reasons.append(f"{prop.bedrooms} bedrooms")
            else:
                miss_reasons.append(f"Only {prop.bedrooms} bedrooms")

            # Bathrooms (10 points)
            if prop.bathrooms >= min_baths:
                score += 10
                match_reasons.append(f"{prop.bathrooms} bathrooms")
            else:
                miss_reasons.append(f"Only {prop.bathrooms} bathrooms")

            # Square footage (10 points)
            if min_sqft <= prop.sqft <= max_sqft:
                score += 10
                match_reasons.append(f"{prop.sqft} sqft")
            else:
                miss_reasons.append("Size doesn't match")

            # City preference (10 points)
            if not cities or prop.city.lower() in cities:
                score += 10
                match_reasons.append(f"In {prop.city}")

            # Features (10 points)
            prop_features_lower = [f.lower() for f in prop.features]
            must_have_found = sum(1 for f in must_have if any(f in pf for pf in prop_features_lower))
            nice_found = sum(1 for f in nice_to_have if any(f in pf for pf in prop_features_lower))

            if must_have:
                feature_score = (must_have_found / len(must_have)) * 7
                score += feature_score
                if must_have_found > 0:
                    match_reasons.append(f"{must_have_found} must-have features")

            if nice_to_have:
                nice_score = (nice_found / len(nice_to_have)) * 3
                score += nice_score

            # Only include reasonable matches
            if score >= 50:
                matches.append({
                    "property": prop.to_dict(),
                    "match_score": round(score, 1),
                    "match_reasons": match_reasons,
                    "miss_reasons": miss_reasons
                })

        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        self.log_activity(
            action="property_match",
            details={
                "criteria_price_range": f"${min_price:,.0f}-${max_price:,.0f}",
                "matches_found": len(matches)
            }
        )

        return {
            "matches": matches[:10],  # Top 10
            "total_found": len(matches),
            "search_criteria": buyer_criteria
        }

    def nurture_sequence(
        self,
        lead_id: str,
        sequence_type: SequenceType
    ) -> Dict[str, Any]:
        """
        Start or manage a nurture sequence for a lead.

        Args:
            lead_id: Lead ID
            sequence_type: Type of nurture sequence

        Returns:
            Sequence details and next actions
        """
        lead = self._leads_cache.get(lead_id)
        if not lead:
            return {"error": f"Lead {lead_id} not found"}

        # Check for existing sequence
        existing = next(
            (s for s in self._nurture_sequences.values()
             if s.lead_id == lead_id and not s.completed),
            None
        )

        if existing:
            # Advance existing sequence
            config = self.NURTURE_SEQUENCES.get(existing.sequence_type, {})
            existing.current_step += 1

            if existing.current_step >= existing.total_steps:
                existing.completed = True
                return {
                    "sequence": existing.to_dict(),
                    "status": "completed",
                    "message": "Nurture sequence completed"
                }

            existing.next_action_date = datetime.now() + timedelta(
                days=config.get('interval_days', 3)
            )

            current_message = config.get('messages', [])[existing.current_step] if existing.current_step < len(config.get('messages', [])) else "Custom follow-up"

            # Generate personalized content using HERMES
            prompt = f"""Generate a brief, personalized real estate nurture email for:

Lead: {lead.name}
Sequence Step: {existing.current_step + 1} of {existing.total_steps}
Message Type: {current_message}
Sequence: {sequence_type.value}

Keep it under 100 words, warm and professional."""

            ai_response = self.query_baby(prompt)

            self.log_activity(
                action="nurture_step_advanced",
                details={
                    "lead_id": lead_id,
                    "sequence_type": sequence_type.value,
                    "step": existing.current_step
                }
            )

            return {
                "sequence": existing.to_dict(),
                "status": "advanced",
                "current_step": existing.current_step,
                "message_type": current_message,
                "generated_content": ai_response.get('response', ''),
                "next_action_date": existing.next_action_date.isoformat()
            }

        # Create new sequence
        config = self.NURTURE_SEQUENCES.get(sequence_type, {})
        sequence_id = str(uuid.uuid4())

        sequence = NurtureSequence(
            id=sequence_id,
            lead_id=lead_id,
            sequence_type=sequence_type,
            current_step=0,
            total_steps=config.get('steps', 5),
            started_at=datetime.now(),
            next_action_date=datetime.now()
        )

        self._nurture_sequences[sequence_id] = sequence

        # Update lead status
        lead.status = LeadStatus.NURTURING
        lead.custom_data['nurture_sequence'] = sequence_type.value
        lead.updated_at = datetime.now()
        self._save_data()

        first_message = config.get('messages', ['Welcome'])[0]

        # Generate first message
        prompt = f"""Generate a welcome email for a new real estate lead:

Lead: {lead.name}
Email Type: {first_message}
Sequence: {sequence_type.value}

Keep it under 100 words, warm and inviting."""

        ai_response = self.query_baby(prompt)

        self.log_activity(
            action="nurture_sequence_started",
            details={
                "lead_id": lead_id,
                "sequence_type": sequence_type.value
            }
        )

        return {
            "sequence": sequence.to_dict(),
            "status": "started",
            "first_message_type": first_message,
            "generated_content": ai_response.get('response', ''),
            "schedule": config
        }

    def schedule_showing(
        self,
        lead_id: str,
        property_id: str,
        scheduled_datetime: str
    ) -> Dict[str, Any]:
        """
        Schedule a property showing.

        Args:
            lead_id: Lead ID
            property_id: Property ID
            scheduled_datetime: ISO datetime string

        Returns:
            Showing details
        """
        lead = self._leads_cache.get(lead_id)
        if not lead:
            return {"error": f"Lead {lead_id} not found"}

        prop = self._properties.get(property_id)
        if not prop:
            return {"error": f"Property {property_id} not found"}

        showing_id = str(uuid.uuid4())
        dt = datetime.fromisoformat(scheduled_datetime)

        showing = Showing(
            id=showing_id,
            lead_id=lead_id,
            property_id=property_id,
            scheduled_datetime=dt,
            agent="Will's Team"
        )

        self._showings[showing_id] = showing

        # Update lead
        lead.status = LeadStatus.CONTACTED
        lead.custom_data['showings'] = lead.custom_data.get('showings', []) + [showing_id]
        lead.updated_at = datetime.now()
        self._save_data()
        self._save_will_data()

        # Generate confirmation using HERMES
        prompt = f"""Generate a brief showing confirmation message:

Client: {lead.name}
Property: {prop.address}, {prop.city}
Date/Time: {dt.strftime('%A, %B %d at %I:%M %p')}
Price: ${prop.price:,.0f}

Keep it under 75 words, professional and excited."""

        ai_response = self.query_baby(prompt)

        self.log_activity(
            action="showing_scheduled",
            details={
                "showing_id": showing_id,
                "lead_id": lead_id,
                "property_id": property_id,
                "datetime": scheduled_datetime
            }
        )

        return {
            "showing": showing.to_dict(),
            "property": prop.to_dict(),
            "confirmation_message": ai_response.get('response', 'Showing confirmed!'),
            "status": "scheduled"
        }

    def open_house_notify(
        self,
        property_id: str,
        date: str,
        attendee_list: List[str]
    ) -> Dict[str, Any]:
        """
        Send open house notifications.

        Args:
            property_id: Property ID
            date: Open house date
            attendee_list: List of lead IDs to notify

        Returns:
            Notification results
        """
        prop = self._properties.get(property_id)
        if not prop:
            return {"error": f"Property {property_id} not found"}

        # If no attendee list, notify all leads with matching criteria
        if not attendee_list:
            attendee_list = [
                lead.id for lead in self._leads_cache.values()
                if lead.status not in [LeadStatus.LOST, LeadStatus.WON]
            ]

        notifications_sent = []
        failed = []

        for lead_id in attendee_list:
            lead = self._leads_cache.get(lead_id)
            if not lead:
                failed.append({"lead_id": lead_id, "reason": "Lead not found"})
                continue

            notifications_sent.append({
                "lead_id": lead_id,
                "lead_name": lead.name,
                "email": lead.email,
                "sent": True
            })

        # Generate open house announcement using HERMES
        prompt = f"""Generate an open house invitation email:

Property: {prop.address}, {prop.city} {prop.state}
Price: ${prop.price:,.0f}
Details: {prop.bedrooms} bed, {prop.bathrooms} bath, {prop.sqft:,} sqft
Date: {date}
Features: {', '.join(prop.features[:3])}

Keep it under 100 words, exciting and inviting."""

        ai_response = self.query_baby(prompt)

        self.log_activity(
            action="open_house_notify",
            details={
                "property_id": property_id,
                "date": date,
                "notifications_sent": len(notifications_sent)
            }
        )

        return {
            "property": prop.to_dict(),
            "open_house_date": date,
            "notifications": {
                "sent": len(notifications_sent),
                "failed": len(failed),
                "details": notifications_sent[:10]  # First 10
            },
            "email_template": ai_response.get('response', '')
        }

    def generate_market_report(self, zip_code: str) -> Dict[str, Any]:
        """
        Generate a market analysis report for an area.

        Args:
            zip_code: ZIP code to analyze

        Returns:
            Market report with trends and analysis
        """
        report_id = str(uuid.uuid4())

        # Simulated market data (would connect to MLS in production)
        # Generate realistic-looking data based on zip
        seed = sum(ord(c) for c in zip_code)
        random.seed(seed)

        avg_price = 350000 + random.randint(-100000, 200000)
        median_price = avg_price * random.uniform(0.9, 1.1)
        days_on_market = random.randint(15, 60)
        active_listings = random.randint(20, 150)
        sold_last_30 = random.randint(10, 50)

        # Determine trends
        if sold_last_30 > active_listings * 0.4:
            price_trend = "increasing"
            inventory_level = "low"
        elif sold_last_30 < active_listings * 0.2:
            price_trend = "decreasing"
            inventory_level = "high"
        else:
            price_trend = "stable"
            inventory_level = "balanced"

        # Generate AI analysis using HERMES
        prompt = f"""Generate a brief real estate market analysis:

ZIP Code: {zip_code}
Average Price: ${avg_price:,.0f}
Median Price: ${median_price:,.0f}
Days on Market: {days_on_market}
Active Listings: {active_listings}
Sold Last 30 Days: {sold_last_30}
Price Trend: {price_trend}
Inventory: {inventory_level}

Provide a 100-word market summary with buyer/seller recommendations."""

        ai_response = self.query_baby(prompt)

        report = MarketReport(
            id=report_id,
            zip_code=zip_code,
            generated_at=datetime.now(),
            avg_price=avg_price,
            median_price=median_price,
            avg_days_on_market=days_on_market,
            active_listings=active_listings,
            sold_last_30=sold_last_30,
            price_trend=price_trend,
            inventory_level=inventory_level,
            analysis=ai_response.get('response', 'Analysis pending')
        )

        self._market_reports[report_id] = report

        self.log_activity(
            action="market_report_generated",
            details={
                "report_id": report_id,
                "zip_code": zip_code
            }
        )

        return report.to_dict()

    def track_buyer_journey(self, lead_id: str) -> Dict[str, Any]:
        """
        Track a buyer's journey through the funnel.

        Args:
            lead_id: Lead ID

        Returns:
            Journey stage and activity history
        """
        lead = self._leads_cache.get(lead_id)
        if not lead:
            return {"error": f"Lead {lead_id} not found"}

        # Gather all activities for this lead
        showings = [s.to_dict() for s in self._showings.values() if s.lead_id == lead_id]
        sequences = [s.to_dict() for s in self._nurture_sequences.values() if s.lead_id == lead_id]

        # Determine buyer stage
        if lead.status == LeadStatus.WON:
            stage = BuyerStage.CLOSED
        elif lead.status == LeadStatus.LOST:
            stage = BuyerStage.LOST
        elif len(showings) > 3:
            stage = BuyerStage.DECISION
        elif len(showings) > 1:
            stage = BuyerStage.EVALUATION
        elif len(showings) > 0:
            stage = BuyerStage.CONSIDERATION
        elif sequences:
            stage = BuyerStage.INTEREST
        else:
            stage = BuyerStage.AWARENESS

        # Calculate engagement score
        engagement_score = 0
        engagement_score += len(showings) * 20
        engagement_score += len(sequences) * 10
        engagement_score += min(30, lead.custom_data.get('email_opens', 0) * 5)
        engagement_score = min(100, engagement_score)

        # Recommendations
        recommendations = []
        if stage == BuyerStage.AWARENESS:
            recommendations = ["Start nurture sequence", "Send property matches", "Schedule intro call"]
        elif stage == BuyerStage.INTEREST:
            recommendations = ["Send targeted listings", "Offer buyer consultation", "Share market report"]
        elif stage == BuyerStage.CONSIDERATION:
            recommendations = ["Schedule more showings", "Discuss financing", "Address concerns"]
        elif stage == BuyerStage.EVALUATION:
            recommendations = ["Provide comparable sales", "Discuss offer strategy", "Connect with lender"]
        elif stage == BuyerStage.DECISION:
            recommendations = ["Prepare offer", "Negotiate terms", "Coordinate inspections"]

        journey = {
            "lead_id": lead_id,
            "lead_info": lead.to_dict(),
            "current_stage": stage.value,
            "engagement_score": engagement_score,
            "activity_summary": {
                "showings": len(showings),
                "nurture_sequences": len(sequences),
                "days_in_pipeline": (datetime.now() - lead.created_at).days
            },
            "showings": showings,
            "sequences": sequences,
            "recommendations": recommendations,
            "next_best_action": recommendations[0] if recommendations else "Maintain contact"
        }

        self.log_activity(
            action="buyer_journey_tracked",
            details={
                "lead_id": lead_id,
                "stage": stage.value,
                "engagement_score": engagement_score
            }
        )

        return journey

    def add_property(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        property_type: PropertyType,
        bedrooms: int,
        bathrooms: float,
        sqft: int,
        price: float,
        year_built: int,
        features: List[str],
        mls_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new property listing.

        Args:
            Various property details

        Returns:
            Created property details
        """
        prop_id = str(uuid.uuid4())[:8]

        prop = Property(
            id=f"prop_{prop_id}",
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            property_type=property_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            sqft=sqft,
            price=price,
            year_built=year_built,
            features=features,
            listing_date=datetime.now(),
            mls_number=mls_number
        )

        self._properties[prop.id] = prop

        self.log_activity(
            action="property_added",
            details={
                "property_id": prop.id,
                "address": address,
                "price": price
            }
        )

        return {
            "property": prop.to_dict(),
            "status": "listed"
        }
