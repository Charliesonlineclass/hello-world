#!/usr/bin/env python3
"""
J3 Interior Design - Lead Qualification System
GroomBridge-Style Algorithm for Interior Design Lead Scoring

PRODUCTION-READY VERSION with:
- Real geographic scoring using Houston zip code database
- Budget parsing for multiple input formats
- JSON file persistence (survives restarts)
- Full scoring algorithm (0-100 points)
"""

import json
import os
import re
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    HOT = "hot"           # 90-100: Immediate attention (4 hours)
    WARM = "warm"         # 70-89: High priority (24 hours)
    LUKEWARM = "lukewarm" # 50-69: Standard follow-up (48 hours)
    COLD = "cold"         # 30-49: Nurture sequence (7 days)
    DISQUALIFIED = "disqualified"  # <30 or outside service area


@dataclass
class Lead:
    """Complete lead record with all scoring data"""
    lead_id: str
    name: str
    email: str
    phone: str
    address: str
    city: str = ""
    zip_code: str = ""
    project_type: str = "other"
    budget_input: str = ""
    budget_min: int = 0
    budget_max: int = 0
    timeline: str = "exploring"
    description: str = ""
    has_photos: bool = False
    source: str = "website"

    # Scoring
    score: int = 0
    geo_score: int = 0
    budget_score: int = 0
    timeline_score: int = 0
    clarity_score: int = 0
    contact_score: int = 0
    distance_miles: float = 999.0

    priority: LeadPriority = LeadPriority.COLD
    status: LeadStatus = LeadStatus.NEW
    disqualification_reason: str = ""

    created_at: datetime = field(default_factory=datetime.now)
    next_followup: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)


class LeadQualifier:
    """
    GroomBridge-Style Lead Qualification Algorithm

    Scoring System (0-100 points total):
    - Geographic Score: 0-20 points (distance from Houston)
    - Budget Alignment: 0-25 points (project value)
    - Timeline Urgency: 0-20 points (how soon they want to start)
    - Project Clarity: 0-15 points (description quality)
    - Contact Completeness: 0-20 points (phone, email, etc.)
    """

    MAX_SERVICE_RADIUS = 120  # miles

    # Complete Houston area zip code database with distance estimates (miles from downtown)
    HOUSTON_ZIP_DISTANCES = {
        # Inner Houston (0-10 miles) - FULL 20 POINTS
        '77001': 0, '77002': 0, '77003': 2, '77004': 3, '77005': 4, '77006': 2,
        '77007': 3, '77008': 5, '77009': 5, '77010': 0, '77011': 4, '77012': 6,
        '77016': 8, '77017': 10, '77018': 8, '77019': 3, '77020': 5, '77021': 5,
        '77022': 6, '77023': 4, '77024': 10, '77025': 6, '77026': 6, '77027': 4,
        '77028': 7, '77029': 8, '77030': 5, '77031': 10, '77033': 8, '77034': 12,
        '77035': 8, '77036': 10, '77037': 12, '77038': 15, '77039': 15, '77040': 15,
        '77041': 18, '77042': 12, '77043': 15, '77044': 20, '77045': 10, '77046': 5,
        '77047': 12, '77048': 15, '77049': 20, '77050': 18, '77051': 8, '77053': 15,
        '77054': 6, '77055': 8, '77056': 6, '77057': 7, '77058': 25, '77059': 25,
        '77060': 18, '77061': 10, '77062': 25, '77063': 10, '77064': 20, '77065': 22,
        '77066': 20, '77067': 18, '77068': 22, '77069': 25, '77070': 25, '77071': 12,
        '77072': 15, '77073': 22, '77074': 10, '77075': 12, '77076': 8, '77077': 15,
        '77078': 12, '77079': 15, '77080': 12, '77081': 8, '77082': 18, '77083': 20,
        '77084': 22, '77085': 12, '77086': 18, '77087': 8, '77088': 15, '77089': 18,
        '77090': 22, '77091': 8, '77092': 10, '77093': 12, '77094': 22, '77095': 25,
        '77096': 10, '77098': 4, '77099': 18,

        # Sugar Land / Missouri City (15-25 miles)
        '77459': 22, '77478': 20, '77479': 22, '77489': 18, '77498': 20,

        # Katy (25-35 miles)
        '77449': 28, '77450': 25, '77493': 30, '77494': 32,

        # The Woodlands / Spring (25-40 miles)
        '77373': 28, '77375': 30, '77379': 28, '77380': 32, '77381': 35,
        '77382': 35, '77384': 38, '77385': 35, '77386': 35, '77388': 25, '77389': 30,

        # Pearland / Friendswood (15-25 miles)
        '77546': 22, '77581': 18, '77584': 20, '77578': 25,

        # Pasadena / Deer Park / Baytown (15-30 miles)
        '77502': 15, '77503': 18, '77504': 18, '77505': 20, '77506': 15,
        '77507': 22, '77520': 28, '77521': 30, '77530': 25, '77536': 20,

        # League City / Clear Lake (25-35 miles)
        '77058': 25, '77059': 28, '77062': 25, '77573': 30, '77586': 28,

        # Conroe / Montgomery (40-50 miles)
        '77301': 40, '77302': 42, '77303': 45, '77304': 42, '77306': 48,
        '77316': 50, '77318': 52, '77356': 50,

        # Galveston (45-55 miles)
        '77550': 50, '77551': 50, '77554': 55, '77563': 55,

        # Huntsville / outlying (60-80 miles)
        '77320': 70, '77340': 75, '77341': 75,

        # Beaumont area (85+ miles)
        '77701': 85, '77702': 85, '77703': 88,
    }

    def __init__(self):
        pass

    def calculate_geographic_score(self, address: str, zip_code: str = "") -> Tuple[int, float]:
        """
        Calculate distance from Houston and assign geographic score.

        Returns: (score, distance_miles)
        - 20 points: Within 10 miles (inner Houston)
        - 15 points: 10-30 miles (greater Houston)
        - 10 points: 30-60 miles (suburbs)
        - 5 points: 60-120 miles (extended area)
        - 0 points: Outside 120 miles (disqualified)
        """
        # Try to extract zip from address if not provided
        if not zip_code:
            zip_match = re.search(r'\b(\d{5})\b', address)
            if zip_match:
                zip_code = zip_match.group(1)

        if not zip_code:
            logger.warning(f"No zip code found in address: {address}")
            return 5, 999.0  # Unknown location gets minimal points

        # Look up distance from our database
        if zip_code in self.HOUSTON_ZIP_DISTANCES:
            distance = self.HOUSTON_ZIP_DISTANCES[zip_code]
        elif zip_code.startswith('77'):
            # Unknown 77xxx zip - assume ~25 miles (greater Houston area)
            distance = 25.0
            logger.info(f"Unknown Houston-area zip {zip_code}, assuming 25 miles")
        else:
            # Non-Houston zip code - check if in Texas
            if zip_code.startswith('75') or zip_code.startswith('76'):
                # Dallas/Fort Worth area - too far
                distance = 250.0
            elif zip_code.startswith('78'):
                # Austin/San Antonio area
                distance = 165.0
            else:
                # Unknown - assume far
                distance = 999.0

        # Assign score based on distance
        if distance <= 10:
            return 20, distance
        elif distance <= 30:
            return 15, distance
        elif distance <= 60:
            return 10, distance
        elif distance <= self.MAX_SERVICE_RADIUS:
            return 5, distance
        else:
            return 0, distance

    def parse_budget(self, budget_string: str) -> Tuple[int, int]:
        """
        Parse budget from various input formats into (min, max) tuple.

        Handles:
        - "$50,000" -> (50000, 50000)
        - "50k" -> (50000, 50000)
        - "50k-100k" -> (50000, 100000)
        - "$50,000 to $100,000" -> (50000, 100000)
        - "30k-50k" -> (30000, 50000)
        - "not sure" -> (0, 0)
        """
        if not budget_string:
            return 0, 0

        budget_lower = budget_string.lower().strip()

        # Check for "not sure" type responses
        if budget_lower in ['not sure', 'unsure', 'unknown', 'not-sure', 'tbd', '']:
            return 0, 0

        # Remove dollar signs, commas, spaces
        cleaned = budget_string.replace('$', '').replace(',', '').replace(' ', '').lower()

        # Handle ranges like "50k-100k" or "50000-100000" or "50k to 100k"
        range_match = re.match(r'(\d+\.?\d*)(k|K)?[\s\-to]+(\d+\.?\d*)(k|K)?', cleaned)
        if range_match:
            min_val = self._parse_single_amount(range_match.group(1), range_match.group(2))
            max_val = self._parse_single_amount(range_match.group(3), range_match.group(4))
            return min_val, max_val

        # Handle single value like "50k" or "50000"
        single_match = re.match(r'(\d+\.?\d*)(k|K)?', cleaned)
        if single_match:
            amount = self._parse_single_amount(single_match.group(1), single_match.group(2))
            return amount, amount

        # Couldn't parse
        logger.warning(f"Could not parse budget: {budget_string}")
        return 0, 0

    def _parse_single_amount(self, number_str: str, suffix: str = None) -> int:
        """Convert '50' with 'k' suffix to 50000"""
        try:
            number = float(number_str)
            if suffix and suffix.lower() == 'k':
                number *= 1000
            return int(number)
        except ValueError:
            return 0

    def calculate_budget_score(self, budget_min: int, budget_max: int) -> int:
        """
        Calculate budget alignment score (0-25 points).

        - 25 points: $50k+
        - 20 points: $30k-$50k
        - 15 points: $15k-$30k
        - 10 points: $5k-$15k
        - 5 points: Under $5k or unknown
        """
        # Use max budget for scoring (benefit of the doubt)
        budget = budget_max if budget_max > 0 else budget_min

        if budget >= 50000:
            return 25
        elif budget >= 30000:
            return 20
        elif budget >= 15000:
            return 15
        elif budget >= 5000:
            return 10
        elif budget > 0:
            return 5
        else:
            return 5  # Unknown budget gets minimal points

    def calculate_timeline_score(self, timeline: str, project_type: str) -> int:
        """
        Calculate timeline urgency score (0-20 points).

        - 20 points: ASAP or storm damage
        - 15 points: 1-3 months
        - 10 points: 3-6 months
        - 5 points: 6-12 months
        - 2 points: Just exploring
        """
        # Storm damage always gets maximum urgency
        if project_type.lower() in ['storm', 'storm damage', 'water damage', 'flood']:
            return 20

        timeline_lower = timeline.lower()

        if 'asap' in timeline_lower or 'immediate' in timeline_lower or 'urgent' in timeline_lower:
            return 20
        elif '1-3' in timeline_lower or '1 to 3' in timeline_lower or 'within 3' in timeline_lower:
            return 15
        elif '3-6' in timeline_lower or '3 to 6' in timeline_lower:
            return 10
        elif '6-12' in timeline_lower or '6 to 12' in timeline_lower or 'year' in timeline_lower:
            return 5
        elif 'explor' in timeline_lower or 'not sure' in timeline_lower:
            return 2
        else:
            return 5  # Default to middle value

    def calculate_clarity_score(self, description: str, has_photos: bool) -> int:
        """
        Calculate project clarity score (0-15 points).

        - Up to 10 points based on description length/quality
        - 5 bonus points for including photos
        """
        desc_len = len(description.strip())

        if desc_len > 200:
            score = 10
        elif desc_len > 100:
            score = 8
        elif desc_len > 50:
            score = 6
        elif desc_len > 20:
            score = 4
        else:
            score = 2

        if has_photos:
            score += 5

        return min(score, 15)

    def calculate_contact_score(self, phone: str, email: str) -> int:
        """
        Calculate contact completeness score (0-20 points).

        - 10 points: Valid phone number
        - 10 points: Valid email
        """
        score = 0

        # Check phone (at least 10 digits)
        phone_digits = re.sub(r'\D', '', phone)
        if len(phone_digits) >= 10:
            score += 10

        # Check email (contains @)
        if email and '@' in email and '.' in email.split('@')[-1]:
            score += 10

        return score

    def qualify_lead(self, form_data: Dict[str, Any]) -> Tuple['Lead', int, LeadPriority]:
        """
        Main qualification method - takes form data and returns scored Lead.

        Returns: (Lead object, total_score, priority)
        """
        # Extract data from form
        name = form_data.get('name', form_data.get('full_name', ''))
        email = form_data.get('email', '')
        phone = form_data.get('phone', '')
        address = form_data.get('address', form_data.get('property_address', ''))
        city = form_data.get('city', '')
        zip_code = form_data.get('zip', form_data.get('zip_code', ''))
        project_type = form_data.get('project_type', 'other')
        budget_input = form_data.get('budget', '')
        timeline = form_data.get('timeline', 'exploring')
        description = form_data.get('description', '')
        has_photos = bool(form_data.get('photos', form_data.get('has_photos', False)))
        source = form_data.get('source', 'website')

        # Parse budget
        budget_min, budget_max = self.parse_budget(budget_input)

        # Calculate individual scores
        geo_score, distance = self.calculate_geographic_score(address, zip_code)
        budget_score = self.calculate_budget_score(budget_min, budget_max)
        timeline_score = self.calculate_timeline_score(timeline, project_type)
        clarity_score = self.calculate_clarity_score(description, has_photos)
        contact_score = self.calculate_contact_score(phone, email)

        # Calculate total score
        total_score = geo_score + budget_score + timeline_score + clarity_score + contact_score

        # Determine priority
        disqualification_reason = ""
        if geo_score == 0:
            priority = LeadPriority.DISQUALIFIED
            disqualification_reason = "outside_service_area"
        elif contact_score == 0:
            priority = LeadPriority.DISQUALIFIED
            disqualification_reason = "missing_contact_info"
        elif total_score >= 90:
            priority = LeadPriority.HOT
        elif total_score >= 70:
            priority = LeadPriority.WARM
        elif total_score >= 50:
            priority = LeadPriority.LUKEWARM
        elif total_score >= 30:
            priority = LeadPriority.COLD
        else:
            priority = LeadPriority.DISQUALIFIED
            disqualification_reason = "low_score"

        # Calculate next followup time
        now = datetime.now()
        if priority == LeadPriority.HOT:
            next_followup = now + timedelta(hours=4)
        elif priority == LeadPriority.WARM:
            next_followup = now + timedelta(hours=24)
        elif priority == LeadPriority.LUKEWARM:
            next_followup = now + timedelta(hours=48)
        elif priority == LeadPriority.COLD:
            next_followup = now + timedelta(days=7)
        else:
            next_followup = None

        # Create Lead object
        lead = Lead(
            lead_id=f"J3-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            name=name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            zip_code=zip_code,
            project_type=project_type,
            budget_input=budget_input,
            budget_min=budget_min,
            budget_max=budget_max,
            timeline=timeline,
            description=description,
            has_photos=has_photos,
            source=source,
            score=total_score,
            geo_score=geo_score,
            budget_score=budget_score,
            timeline_score=timeline_score,
            clarity_score=clarity_score,
            contact_score=contact_score,
            distance_miles=distance,
            priority=priority,
            status=LeadStatus.NEW,
            disqualification_reason=disqualification_reason,
            created_at=now,
            next_followup=next_followup,
        )

        logger.info(f"Lead {lead.lead_id} qualified: score={total_score}, priority={priority.value}, distance={distance:.1f}mi")

        return lead, total_score, priority

    def _get_response_time(self, priority: LeadPriority) -> str:
        """Get human-readable response time based on priority"""
        times = {
            LeadPriority.HOT: "4 hours",
            LeadPriority.WARM: "24 hours",
            LeadPriority.LUKEWARM: "2 business days",
            LeadPriority.COLD: "soon",
        }
        return times.get(priority, "soon")


class LeadRepository:
    """
    Lead storage with JSON file persistence.
    Survives server restarts.
    """

    def __init__(self, data_file: str = 'leads_data.json'):
        self.data_file = data_file
        self.leads: Dict[str, Lead] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        """Load leads from JSON file on startup"""
        if not os.path.exists(self.data_file):
            logger.info(f"No existing data file at {self.data_file}")
            return

        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)

            for lead_dict in data:
                # Convert datetime strings back to datetime objects
                if 'created_at' in lead_dict and isinstance(lead_dict['created_at'], str):
                    lead_dict['created_at'] = datetime.fromisoformat(lead_dict['created_at'])
                if 'next_followup' in lead_dict and lead_dict['next_followup']:
                    lead_dict['next_followup'] = datetime.fromisoformat(lead_dict['next_followup'])

                # Convert enum strings back to enums
                if 'priority' in lead_dict and isinstance(lead_dict['priority'], str):
                    lead_dict['priority'] = LeadPriority(lead_dict['priority'])
                if 'status' in lead_dict and isinstance(lead_dict['status'], str):
                    lead_dict['status'] = LeadStatus(lead_dict['status'])

                lead = Lead(**lead_dict)
                self.leads[lead.lead_id] = lead

            logger.info(f"Loaded {len(self.leads)} leads from {self.data_file}")
        except Exception as e:
            logger.error(f"Error loading leads from disk: {e}")

    def _save_to_disk(self):
        """Save all leads to JSON file"""
        try:
            # Ensure directory exists
            data_dir = os.path.dirname(self.data_file)
            if data_dir:
                os.makedirs(data_dir, exist_ok=True)

            # Convert leads to dicts with serializable types
            data = []
            for lead in self.leads.values():
                lead_dict = asdict(lead)
                # Convert datetime to ISO string
                lead_dict['created_at'] = lead.created_at.isoformat()
                lead_dict['next_followup'] = lead.next_followup.isoformat() if lead.next_followup else None
                # Convert enums to strings
                lead_dict['priority'] = lead.priority.value
                lead_dict['status'] = lead.status.value
                data.append(lead_dict)

            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(data)} leads to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving leads to disk: {e}")

    def save(self, lead: Lead) -> Lead:
        """Save or update a lead"""
        self.leads[lead.lead_id] = lead
        self._save_to_disk()
        return lead

    def get(self, lead_id: str) -> Optional[Lead]:
        """Get lead by ID"""
        return self.leads.get(lead_id)

    def get_all(self, status: Optional[LeadStatus] = None) -> List[Lead]:
        """Get all leads, optionally filtered by status"""
        leads = list(self.leads.values())
        if status:
            leads = [l for l in leads if l.status == status]
        # Sort by score descending, then by created date descending
        return sorted(leads, key=lambda x: (x.score, x.created_at), reverse=True)

    def get_by_priority(self, priority: LeadPriority) -> List[Lead]:
        """Get leads by priority level"""
        return [l for l in self.leads.values() if l.priority == priority]

    def update_status(self, lead_id: str, status: LeadStatus, note: str = "") -> Optional[Lead]:
        """Update lead status"""
        lead = self.leads.get(lead_id)
        if not lead:
            return None

        lead.status = status
        if note:
            lead.notes.append(f"{datetime.now().isoformat()}: {note}")

        self._save_to_disk()
        return lead


# =============================================================================
# TEST / DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("J3 LEAD QUALIFICATION SYSTEM - TEST")
    print("=" * 60)

    qualifier = LeadQualifier()
    repository = LeadRepository(data_file='data/test_leads.json')

    # Test Case 1: HOT LEAD - Inner Houston, high budget, urgent
    print("\n[TEST 1] Hot Lead - Inner Houston")
    test1 = {
        "name": "John Smith",
        "email": "john@email.com",
        "phone": "(713) 555-1234",
        "address": "1234 Main St",
        "city": "Houston",
        "zip": "77002",
        "project_type": "kitchen",
        "budget": "50k",
        "timeline": "asap",
        "description": "Complete kitchen renovation with custom cabinets, quartz countertops, new appliances",
        "photos": True
    }
    lead1, score1, priority1 = qualifier.qualify_lead(test1)
    repository.save(lead1)
    print(f"  Lead ID: {lead1.lead_id}")
    print(f"  Score: {score1}/100 (Geo:{lead1.geo_score} + Budget:{lead1.budget_score} + Timeline:{lead1.timeline_score} + Clarity:{lead1.clarity_score} + Contact:{lead1.contact_score})")
    print(f"  Priority: {priority1.value}")
    print(f"  Distance: {lead1.distance_miles} miles")

    # Test Case 2: WARM LEAD - Suburbs, medium budget
    print("\n[TEST 2] Warm Lead - Sugar Land")
    test2 = {
        "name": "Sarah Johnson",
        "email": "sarah@email.com",
        "phone": "281-555-5678",
        "address": "456 Oak Lane, Sugar Land TX 77479",
        "project_type": "bathroom",
        "budget": "25k-35k",
        "timeline": "1-3 months",
        "description": "Master bathroom remodel"
    }
    lead2, score2, priority2 = qualifier.qualify_lead(test2)
    repository.save(lead2)
    print(f"  Lead ID: {lead2.lead_id}")
    print(f"  Score: {score2}/100")
    print(f"  Priority: {priority2.value}")
    print(f"  Budget parsed: ${lead2.budget_min:,} - ${lead2.budget_max:,}")

    # Test Case 3: DISQUALIFIED - Outside service area
    print("\n[TEST 3] Disqualified - Austin (outside area)")
    test3 = {
        "name": "Mike Davis",
        "email": "mike@email.com",
        "phone": "512-555-9999",
        "address": "789 Congress Ave, Austin TX 78701",
        "project_type": "kitchen",
        "budget": "100k",
        "timeline": "asap"
    }
    lead3, score3, priority3 = qualifier.qualify_lead(test3)
    repository.save(lead3)
    print(f"  Lead ID: {lead3.lead_id}")
    print(f"  Score: {score3}/100")
    print(f"  Priority: {priority3.value}")
    print(f"  Reason: {lead3.disqualification_reason}")
    print(f"  Distance: {lead3.distance_miles} miles")

    # Summary
    print("\n" + "=" * 60)
    print("REPOSITORY SUMMARY")
    print("=" * 60)
    all_leads = repository.get_all()
    print(f"Total Leads: {len(all_leads)}")
    print(f"HOT: {len(repository.get_by_priority(LeadPriority.HOT))}")
    print(f"WARM: {len(repository.get_by_priority(LeadPriority.WARM))}")
    print(f"COLD: {len(repository.get_by_priority(LeadPriority.COLD))}")
    print(f"DISQUALIFIED: {len(repository.get_by_priority(LeadPriority.DISQUALIFIED))}")
