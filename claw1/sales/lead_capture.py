"""
SCORPION CLAW1 - Lead Capture System
=====================================

Process incoming leads, score them by priority, and route to appropriate LEG containers.

No external dependencies - pure Python implementation.
"""

import os
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CLAW1.lead_capture")


class LeadSource(Enum):
    """Lead source channels."""
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL = "social_media"
    COLD_CALL = "cold_call"
    EMAIL = "email_campaign"
    EVENT = "event"
    PARTNER = "partner"
    OTHER = "other"


class LeadStatus(Enum):
    """Lead processing status."""
    NEW = "new"
    VALIDATED = "validated"
    SCORED = "scored"
    ASSIGNED = "assigned"
    REJECTED = "rejected"


@dataclass
class Lead:
    """Lead data structure."""
    id: str
    name: str
    email: str
    phone: str
    company: str = ""
    source: str = "website"
    message: str = ""
    score: int = 0
    priority: int = 5
    status: str = "new"
    assigned_leg: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


# Scoring weights
SCORING_WEIGHTS = {
    "has_phone": 15,
    "has_company": 10,
    "business_email": 20,
    "detailed_message": 15,
    "referral_source": 25,
    "high_value_keywords": 20,
    "repeat_visitor": 15,
    "enterprise_domain": 25
}

# High-value keywords for scoring
HIGH_VALUE_KEYWORDS = [
    "enterprise", "contract", "budget", "urgent", "asap",
    "immediately", "large", "expansion", "multiple", "fleet",
    "commercial", "industrial", "investment", "partnership"
]

# Enterprise domains (B2B indicator)
ENTERPRISE_DOMAINS = [
    "google.com", "microsoft.com", "amazon.com", "apple.com",
    "ibm.com", "oracle.com", "salesforce.com", "adobe.com"
]

# LEG container routing rules
LEG_ROUTING = {
    "j3": {
        "keywords": ["construction", "remodel", "framing", "drywall", "addition", "deck"],
        "priority_threshold": 5
    },
    "nsipa": {
        "keywords": ["healthcare", "medical", "appointment", "patient", "clinic"],
        "priority_threshold": 5
    },
    "default": {
        "keywords": [],
        "priority_threshold": 1
    }
}


class LeadCapture:
    """
    Lead capture and processing system.

    Usage:
        capture = LeadCapture()
        lead = capture.process_form({
            "name": "John Doe",
            "email": "john@company.com",
            "phone": "555-1234",
            "message": "Interested in your services"
        })
        print(f"Lead score: {lead.score}, Priority: {lead.priority}")
    """

    def __init__(self, data_dir: str = "leads"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._leads: Dict[str, Lead] = {}
        self._counter = 0
        self._load_data()

    def _load_data(self):
        """Load existing leads."""
        leads_file = self.data_dir / "leads.json"
        if leads_file.exists():
            try:
                data = json.loads(leads_file.read_text())
                for lead_data in data:
                    lead = Lead(**lead_data)
                    self._leads[lead.id] = lead
                self._counter = len(self._leads)
            except Exception as e:
                logger.error(f"Error loading leads: {e}")

    def _save_data(self):
        """Save leads to file."""
        leads_file = self.data_dir / "leads.json"
        data = [asdict(lead) for lead in self._leads.values()]
        leads_file.write_text(json.dumps(data, indent=2))

    def _generate_id(self) -> str:
        """Generate unique lead ID."""
        self._counter += 1
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"LEAD-{timestamp}-{self._counter:04d}"

    def process_form(
        self,
        data: Dict,
        source: str = "website",
        auto_score: bool = True,
        auto_assign: bool = True
    ) -> Lead:
        """
        Process incoming lead form data.

        Args:
            data: Form data dict with name, email, phone, etc.
            source: Lead source channel
            auto_score: Automatically score the lead
            auto_assign: Automatically assign to LEG

        Returns:
            Validated and processed Lead object
        """
        # Validate required fields
        validated = self._validate_form(data)
        if not validated["valid"]:
            logger.warning(f"Invalid lead data: {validated['errors']}")
            raise ValueError(f"Invalid lead data: {validated['errors']}")

        # Create lead
        lead = Lead(
            id=self._generate_id(),
            name=self._clean_string(data.get("name", "")),
            email=self._clean_email(data.get("email", "")),
            phone=self._clean_phone(data.get("phone", "")),
            company=self._clean_string(data.get("company", "")),
            source=source,
            message=data.get("message", ""),
            metadata=data.get("metadata", {}),
            status=LeadStatus.VALIDATED.value
        )

        # Score if requested
        if auto_score:
            lead = self._score_lead(lead)

        # Assign if requested
        if auto_assign:
            lead = self._assign_to_leg(lead)

        # Save
        self._leads[lead.id] = lead
        self._save_data()

        logger.info(f"Lead captured: {lead.id} - {lead.name} (Score: {lead.score})")
        return lead

    def _validate_form(self, data: Dict) -> Dict:
        """Validate form data."""
        errors = []

        # Required: name
        if not data.get("name") or len(data["name"].strip()) < 2:
            errors.append("Name is required (min 2 characters)")

        # Required: email (valid format)
        email = data.get("email", "")
        if not self._is_valid_email(email):
            errors.append("Valid email is required")

        # Optional but validate if present: phone
        phone = data.get("phone", "")
        if phone and not self._is_valid_phone(phone):
            errors.append("Invalid phone format")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))

    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone format."""
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
        return len(cleaned) >= 10 and cleaned.replace('+', '').isdigit()

    def _clean_string(self, s: str) -> str:
        """Clean and normalize string input."""
        return ' '.join(s.strip().split())

    def _clean_email(self, email: str) -> str:
        """Clean and normalize email."""
        return email.strip().lower()

    def _clean_phone(self, phone: str) -> str:
        """Clean phone number."""
        return re.sub(r'[^\d+]', '', phone.strip())

    def _score_lead(self, lead: Lead) -> Lead:
        """
        Score a lead based on various factors.

        Scoring factors:
        - Has phone number: +15
        - Has company name: +10
        - Business email domain: +20
        - Detailed message: +15
        - Referral source: +25
        - High-value keywords: +20
        - Enterprise domain: +25

        Returns lead with updated score (0-100) and priority (1-10).
        """
        score = 0

        # Has phone
        if lead.phone:
            score += SCORING_WEIGHTS["has_phone"]

        # Has company
        if lead.company:
            score += SCORING_WEIGHTS["has_company"]

        # Business email (not gmail, yahoo, etc.)
        email_domain = lead.email.split('@')[-1] if '@' in lead.email else ""
        free_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]
        if email_domain and email_domain not in free_domains:
            score += SCORING_WEIGHTS["business_email"]

        # Enterprise domain
        if email_domain in ENTERPRISE_DOMAINS:
            score += SCORING_WEIGHTS["enterprise_domain"]

        # Detailed message (over 50 chars)
        if len(lead.message) > 50:
            score += SCORING_WEIGHTS["detailed_message"]

        # Referral source
        if lead.source == LeadSource.REFERRAL.value:
            score += SCORING_WEIGHTS["referral_source"]

        # High-value keywords in message
        message_lower = lead.message.lower()
        if any(kw in message_lower for kw in HIGH_VALUE_KEYWORDS):
            score += SCORING_WEIGHTS["high_value_keywords"]

        # Normalize to 0-100
        max_possible = sum(SCORING_WEIGHTS.values())
        normalized_score = min(100, int((score / max_possible) * 100))

        # Calculate priority (1-10, higher is better)
        priority = max(1, min(10, normalized_score // 10))

        lead.score = normalized_score
        lead.priority = priority
        lead.status = LeadStatus.SCORED.value
        lead.updated_at = datetime.now().isoformat()

        return lead

    def _assign_to_leg(self, lead: Lead) -> Lead:
        """
        Assign lead to appropriate LEG container.

        Routing rules:
        - J3: Construction-related keywords
        - NSIPA: Healthcare-related keywords
        - Default: General leads
        """
        message_lower = (lead.message + " " + lead.company).lower()

        assigned_leg = "default"

        # Check each LEG's routing rules
        for leg, rules in LEG_ROUTING.items():
            if leg == "default":
                continue

            # Check keywords
            if any(kw in message_lower for kw in rules["keywords"]):
                if lead.priority >= rules["priority_threshold"]:
                    assigned_leg = leg
                    break

        lead.assigned_leg = assigned_leg
        lead.status = LeadStatus.ASSIGNED.value
        lead.updated_at = datetime.now().isoformat()

        logger.info(f"Lead {lead.id} assigned to LEG: {assigned_leg}")
        return lead

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get lead by ID."""
        return self._leads.get(lead_id)

    def get_leads_by_leg(self, leg: str) -> List[Lead]:
        """Get all leads assigned to a LEG."""
        return [l for l in self._leads.values() if l.assigned_leg == leg]

    def get_high_priority_leads(self, min_priority: int = 7) -> List[Lead]:
        """Get leads with priority >= threshold."""
        return [l for l in self._leads.values() if l.priority >= min_priority]

    def get_unassigned_leads(self) -> List[Lead]:
        """Get leads not yet assigned."""
        return [l for l in self._leads.values() if l.assigned_leg is None]

    def update_lead(self, lead_id: str, **kwargs) -> bool:
        """Update lead fields."""
        lead = self._leads.get(lead_id)
        if not lead:
            return False

        for key, value in kwargs.items():
            if hasattr(lead, key):
                setattr(lead, key, value)

        lead.updated_at = datetime.now().isoformat()
        self._save_data()
        return True

    def add_tag(self, lead_id: str, tag: str) -> bool:
        """Add tag to lead."""
        lead = self._leads.get(lead_id)
        if not lead:
            return False

        if tag not in lead.tags:
            lead.tags.append(tag)
            lead.updated_at = datetime.now().isoformat()
            self._save_data()
        return True

    def get_stats(self) -> Dict:
        """Get lead capture statistics."""
        leads = list(self._leads.values())
        total = len(leads)

        by_status = {}
        by_source = {}
        by_leg = {}
        total_score = 0

        for lead in leads:
            by_status[lead.status] = by_status.get(lead.status, 0) + 1
            by_source[lead.source] = by_source.get(lead.source, 0) + 1
            if lead.assigned_leg:
                by_leg[lead.assigned_leg] = by_leg.get(lead.assigned_leg, 0) + 1
            total_score += lead.score

        return {
            "total_leads": total,
            "avg_score": round(total_score / total, 1) if total > 0 else 0,
            "high_priority": len([l for l in leads if l.priority >= 7]),
            "by_status": by_status,
            "by_source": by_source,
            "by_leg": by_leg
        }


# Convenience functions
_capture: Optional[LeadCapture] = None


def process_form(data: Dict, **kwargs) -> Lead:
    """Process form using default capture."""
    global _capture
    if _capture is None:
        _capture = LeadCapture()
    return _capture.process_form(data, **kwargs)


def score_lead(lead: Lead) -> Lead:
    """Score lead using default capture."""
    global _capture
    if _capture is None:
        _capture = LeadCapture()
    return _capture._score_lead(lead)


def assign_to_leg(lead: Lead) -> Lead:
    """Assign lead to LEG using default capture."""
    global _capture
    if _capture is None:
        _capture = LeadCapture()
    return _capture._assign_to_leg(lead)


if __name__ == "__main__":
    print("CLAW1 Lead Capture - Demo")
    print("=" * 40)

    capture = LeadCapture()

    # Process sample leads
    lead1 = capture.process_form({
        "name": "John Smith",
        "email": "john@enterprise.com",
        "phone": "555-123-4567",
        "company": "Smith Construction LLC",
        "message": "Need urgent framing work for commercial building expansion"
    }, source="referral")

    lead2 = capture.process_form({
        "name": "Jane Doe",
        "email": "jane@gmail.com",
        "message": "Looking for information about your services"
    }, source="website")

    print(f"\nLead 1: {lead1.name}")
    print(f"  Score: {lead1.score}, Priority: {lead1.priority}")
    print(f"  Assigned to: {lead1.assigned_leg}")

    print(f"\nLead 2: {lead2.name}")
    print(f"  Score: {lead2.score}, Priority: {lead2.priority}")
    print(f"  Assigned to: {lead2.assigned_leg}")

    print("\nStats:")
    stats = capture.get_stats()
    print(f"  Total: {stats['total_leads']}")
    print(f"  Avg Score: {stats['avg_score']}")
    print(f"  By LEG: {stats['by_leg']}")
