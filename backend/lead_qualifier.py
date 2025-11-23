#!/usr/bin/env python3
"""
J3 Interior Design - Lead Qualification System
GroomBridge-Style Algorithm for Interior Design Lead Scoring
"""

import json
import math
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('J3LeadQualifier')


class LeadStatus(Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONSULTATION_SCHEDULED = "consultation_scheduled"
    QUOTED = "quoted"
    WON = "won"
    LOST = "lost"
    DISQUALIFIED = "disqualified"


class LeadPriority(Enum):
    HOT = "hot"          # 90-100: Immediate attention
    WARM = "warm"        # 70-89: High priority
    LUKEWARM = "lukewarm"  # 50-69: Standard follow-up
    COLD = "cold"        # 30-49: Nurture sequence
    DISQUALIFIED = "disqualified"


@dataclass
class GeoLocation:
    address: str
    city: str
    state: str = "TX"
    zip_code: str = ""
    distance_from_houston: Optional[float] = None


@dataclass
class LeadContact:
    full_name: str
    email: str
    phone: str
    preferred_contact_method: str = "phone"
    best_time_to_reach: str = "anytime"


@dataclass
class ProjectDetails:
    project_type: str
    property_type: str
    description: str = ""
    timeline: str = "exploring"
    budget_range: str = "not-sure"
    has_photos: bool = False
    ai_questions_answered: int = 0
    total_ai_questions: int = 5


@dataclass
class LeadScore:
    geographic_score: float = 0.0
    budget_score: float = 0.0
    timeline_score: float = 0.0
    project_clarity_score: float = 0.0
    engagement_score: float = 0.0
    contact_completeness_score: float = 0.0
    total_score: float = 0.0
    priority: LeadPriority = LeadPriority.COLD
    disqualification_reason: Optional[str] = None


@dataclass
class Lead:
    id: str
    contact: LeadContact
    location: GeoLocation
    project: ProjectDetails
    score: LeadScore = field(default_factory=LeadScore)
    status: LeadStatus = LeadStatus.NEW
    source: str = "website_form"
    submitted_at: datetime = field(default_factory=datetime.now)
    next_followup: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)


class LeadQualifier:
    """GroomBridge-Style Lead Qualification Algorithm (0-100 points)"""

    HOUSTON_LAT = 29.7604
    HOUSTON_LNG = -95.3698
    MAX_SERVICE_RADIUS = 120

    BUDGET_MIDPOINTS = {
        "5k-15k": 10000, "15k-30k": 22500, "30k-50k": 40000,
        "50k+": 75000, "not-sure": 15000,
    }

    # Houston ZIP codes with distance estimates
    HOUSTON_ZIPS = {
        "77001": 0, "77002": 0, "77003": 2, "77004": 3, "77005": 4, "77006": 2,
        "77007": 3, "77019": 3, "77025": 6, "77027": 4, "77030": 5, "77054": 6,
        "77056": 6, "77057": 7, "77098": 4, "77379": 28, "77380": 32, "77494": 30,
    }

    def estimate_distance_from_zip(self, zip_code: str) -> Optional[float]:
        return self.HOUSTON_ZIPS.get(zip_code)

    def score_geographic(self, lead: Lead) -> float:
        distance = lead.location.distance_from_houston
        if distance is None:
            distance = self.estimate_distance_from_zip(lead.location.zip_code)
            if distance is not None:
                lead.location.distance_from_houston = distance

        if distance is None:
            return 10.0
        if distance > self.MAX_SERVICE_RADIUS:
            lead.score.disqualification_reason = "outside_service_area"
            return 0.0
        elif distance <= 10: return 20.0
        elif distance <= 30: return 15.0
        elif distance <= 60: return 10.0
        else: return 5.0

    def score_budget(self, lead: Lead) -> float:
        scores = {"50k+": 25.0, "30k-50k": 20.0, "15k-30k": 15.0, "5k-15k": 10.0, "not-sure": 5.0}
        return scores.get(lead.project.budget_range, 5.0)

    def score_timeline(self, lead: Lead) -> float:
        if lead.project.project_type == "storm": return 20.0
        scores = {"asap": 20.0, "1-3-months": 15.0, "3-6-months": 10.0, "6-12-months": 5.0, "exploring": 2.0}
        return scores.get(lead.project.timeline, 2.0)

    def score_project_clarity(self, lead: Lead) -> float:
        desc = lead.project.description.strip()
        score = 10.0 if len(desc) > 200 else 7.0 if len(desc) > 50 else 4.0 if len(desc) > 10 else 2.0
        if lead.project.has_photos: score += 5.0
        return min(score, 15.0)

    def score_engagement(self, lead: Lead) -> float:
        if lead.project.total_ai_questions == 0: return 5.0
        ratio = lead.project.ai_questions_answered / lead.project.total_ai_questions
        if ratio >= 1.0: return 10.0
        elif ratio >= 0.7: return 7.0
        elif ratio >= 0.4: return 4.0
        return 1.0

    def score_contact_completeness(self, lead: Lead) -> float:
        score = 0.0
        has_phone = bool(lead.contact.phone and len(lead.contact.phone) >= 10)
        has_email = bool(lead.contact.email and "@" in lead.contact.email)
        if not has_phone and not has_email:
            lead.score.disqualification_reason = "missing_contact_info"
            return 0.0
        if has_phone: score += 4.0
        if has_email: score += 3.0
        if lead.contact.best_time_to_reach != "anytime": score += 3.0
        return score

    def calculate_total_score(self, lead: Lead) -> LeadScore:
        score = LeadScore()
        score.geographic_score = self.score_geographic(lead)
        score.budget_score = self.score_budget(lead)
        score.timeline_score = self.score_timeline(lead)
        score.project_clarity_score = self.score_project_clarity(lead)
        score.engagement_score = self.score_engagement(lead)
        score.contact_completeness_score = self.score_contact_completeness(lead)
        score.total_score = sum([
            score.geographic_score, score.budget_score, score.timeline_score,
            score.project_clarity_score, score.engagement_score, score.contact_completeness_score
        ])

        if score.geographic_score == 0 or score.contact_completeness_score == 0:
            score.priority = LeadPriority.DISQUALIFIED
        elif score.total_score >= 90: score.priority = LeadPriority.HOT
        elif score.total_score >= 70: score.priority = LeadPriority.WARM
        elif score.total_score >= 50: score.priority = LeadPriority.LUKEWARM
        elif score.total_score >= 30: score.priority = LeadPriority.COLD
        else: score.priority = LeadPriority.DISQUALIFIED
        return score

    def qualify_lead(self, lead: Lead) -> Lead:
        lead.score = self.calculate_total_score(lead)
        now = datetime.now()
        if lead.score.priority == LeadPriority.HOT:
            lead.next_followup = now + timedelta(hours=4)
        elif lead.score.priority == LeadPriority.WARM:
            lead.next_followup = now + timedelta(hours=24)
        elif lead.score.priority == LeadPriority.LUKEWARM:
            lead.next_followup = now + timedelta(hours=48)
        elif lead.score.priority == LeadPriority.COLD:
            lead.next_followup = now + timedelta(days=7)
        logger.info(f"Lead {lead.id} - Score: {lead.score.total_score:.1f}, Priority: {lead.score.priority.value}")
        return lead

    def get_routing_action(self, lead: Lead) -> Dict[str, Any]:
        priority = lead.score.priority
        if priority == LeadPriority.HOT:
            return {"sms_alert": True, "callback_hours": 4, "customer_response": "We'll call you within 4 hours."}
        elif priority == LeadPriority.WARM:
            return {"email_alert": True, "callback_hours": 24, "customer_response": "We'll call you within 24 hours."}
        elif priority == LeadPriority.LUKEWARM:
            return {"callback_hours": 48, "customer_response": "We'll contact you within 2 business days."}
        elif priority == LeadPriority.COLD:
            return {"nurture_sequence": True, "customer_response": "We'll follow up soon."}
        return {"customer_response": "Thank you for your interest."}


class LeadRepository:
    def __init__(self):
        self.leads: Dict[str, Lead] = {}
        self._counter = 0

    def generate_id(self) -> str:
        self._counter += 1
        return f"J3-{datetime.now().strftime('%Y%m%d')}-{self._counter:04d}"

    def save(self, lead: Lead) -> Lead:
        if not lead.id: lead.id = self.generate_id()
        self.leads[lead.id] = lead
        return lead

    def get(self, lead_id: str) -> Optional[Lead]:
        return self.leads.get(lead_id)

    def get_all(self) -> List[Lead]:
        return list(self.leads.values())

    def get_by_priority(self, priority: LeadPriority) -> List[Lead]:
        return [l for l in self.leads.values() if l.score.priority == priority]


def create_lead_from_form(form_data: Dict[str, Any]) -> Lead:
    contact = LeadContact(
        full_name=form_data.get("full_name", ""),
        email=form_data.get("email", ""),
        phone=form_data.get("phone", ""),
        preferred_contact_method=form_data.get("contact_method", "phone"),
        best_time_to_reach=form_data.get("contact_time", "anytime"),
    )
    location = GeoLocation(
        address=form_data.get("property_address", ""),
        city=form_data.get("city", ""),
        zip_code=form_data.get("zip", ""),
    )
    project = ProjectDetails(
        project_type=form_data.get("project_type", "other"),
        property_type=form_data.get("property_type", "single-family"),
        description=form_data.get("description", ""),
        timeline=form_data.get("timeline", "exploring"),
        budget_range=form_data.get("budget", "not-sure"),
        has_photos=bool(form_data.get("photos")),
        ai_questions_answered=form_data.get("questions_answered", 0),
    )
    return Lead(id="", contact=contact, location=location, project=project)


if __name__ == "__main__":
    qualifier = LeadQualifier()
    repository = LeadRepository()

    test_data = {
        "full_name": "John Smith", "email": "john@email.com", "phone": "(713) 555-1234",
        "city": "Houston", "zip": "77005", "project_type": "kitchen",
        "description": "Complete kitchen renovation with custom cabinets",
        "timeline": "asap", "budget": "30k-50k", "photos": True, "questions_answered": 5,
    }

    lead = create_lead_from_form(test_data)
    lead = repository.save(lead)
    lead = qualifier.qualify_lead(lead)

    print(f"Lead: {lead.id}")
    print(f"Score: {lead.score.total_score}/100")
    print(f"Priority: {lead.score.priority.value}")
