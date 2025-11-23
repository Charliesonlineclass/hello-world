# GroomBridge Algorithm Comparison

## Overview

This document compares the original GroomBridge algorithm (when extracted from Samsung) with the new J3 Interior Design implementation.

---

## Original Cruz Algorithm (From Samsung)

**Location:** `/home/user/FORTRESS/intellectual_property/groombride_original/`
**Status:** ⏳ AWAITING EXTRACTION (Samsung drive not mounted)

### Expected Features (Based on Cruz Roofing Use Case)
- Lead scoring for roofing/storm damage projects
- Geographic filtering for service area
- Weather event correlation
- Insurance claim status tracking
- Urgency scoring based on damage type

### Files to Extract
```
groombride_original/
├── groombride_lead_scorer.py     # Core algorithm
├── cruz_lead_qualifier.py        # Cruz-specific implementation
├── fb_scraper.py                 # Facebook lead scraper
├── whatsapp_notifier.py          # WhatsApp notifications
└── [other files TBD]
```

---

## New J3 Implementation (Production Ready)

**Location:** `/home/user/hello-world/backend/lead_qualifier.py`
**Status:** ✅ TESTED AND WORKING

### Features Implemented

#### 1. Geographic Scoring (0-20 points)
```python
# Houston zip code database with 100+ entries
HOUSTON_ZIP_DISTANCES = {
    '77001': 0, '77002': 0, '77003': 2, '77004': 3, ...
    # Inner Houston: 0-10 miles
    # Sugar Land: 15-25 miles
    # Katy: 25-35 miles
    # The Woodlands: 25-40 miles
    # Conroe: 40-50 miles
    # Galveston: 45-55 miles
}

# Scoring tiers:
# 20 points: Within 10 miles (Inner Houston)
# 15 points: 10-30 miles (Greater Houston)
# 10 points: 30-60 miles (Suburbs)
# 5 points: 60-120 miles (Extended area)
# 0 points: Outside 120 miles (DISQUALIFIED)
```

#### 2. Budget Scoring (0-25 points)
```python
# Budget parsing handles multiple formats:
# "$50,000" -> (50000, 50000)
# "50k" -> (50000, 50000)
# "50k-100k" -> (50000, 100000)
# "$50,000 to $100,000" -> (50000, 100000)

# Scoring tiers:
# 25 points: $50k+
# 20 points: $30k-$50k
# 15 points: $15k-$30k
# 10 points: $5k-$15k
# 5 points: Under $5k or unknown
```

#### 3. Timeline Scoring (0-20 points)
```python
# 20 points: ASAP, immediate, urgent, or storm damage
# 15 points: 1-3 months
# 10 points: 3-6 months
# 5 points: 6-12 months
# 2 points: Just exploring
```

#### 4. Project Clarity Scoring (0-15 points)
```python
# Based on description length:
# 10 points: >200 characters
# 8 points: 100-200 characters
# 6 points: 50-100 characters
# 4 points: 20-50 characters
# 2 points: <20 characters
# +5 bonus: Photos included
```

#### 5. Contact Completeness (0-20 points)
```python
# 10 points: Valid phone number (10+ digits)
# 10 points: Valid email (contains @ and domain)
```

### Priority Classification
```python
class LeadPriority(Enum):
    HOT = "hot"           # 90-100: Response in 4 hours
    WARM = "warm"         # 70-89: Response in 24 hours
    LUKEWARM = "lukewarm" # 50-69: Response in 48 hours
    COLD = "cold"         # 30-49: Response in 7 days
    DISQUALIFIED = "disqualified"  # <30 or outside area
```

### Data Persistence
```python
class LeadRepository:
    def __init__(self, data_file='leads_data.json'):
        self._load_from_disk()

    def save(self, lead: Lead) -> Lead:
        self._save_to_disk()

    # Survives server restarts
    # JSON format for easy backup/inspection
```

---

## Side-by-Side Comparison

| Feature | Original Cruz | New J3 Implementation |
|---------|--------------|----------------------|
| **Industry** | Roofing/Storm | Interior Design |
| **Service Area** | Houston + radius | Houston + 120mi radius |
| **Zip Database** | Unknown | 100+ Houston zips |
| **Budget Parsing** | Unknown | Multi-format (50k, $50,000, ranges) |
| **Score Range** | 0-100 | 0-100 |
| **Priority Levels** | Unknown | 5 levels (HOT→DISQUALIFIED) |
| **Persistence** | Unknown | JSON file |
| **API Server** | Unknown | Flask REST API |
| **Weather Events** | Yes (likely) | No (not relevant) |
| **Insurance Claims** | Yes (likely) | No (not relevant) |

---

## Differences to Investigate

When original GroomBridge is extracted, compare:

1. **Scoring Weights**
   - Does original use same point distribution?
   - Any additional scoring factors?

2. **Geographic Logic**
   - How does original determine distance?
   - API-based vs database lookup?

3. **Lead Sources**
   - Facebook scraper integration?
   - WhatsApp notification system?
   - Multiple input channels?

4. **Urgency Factors**
   - Storm event correlation?
   - Seasonal adjustments?

5. **Follow-up Logic**
   - Automated sequences?
   - Escalation rules?

---

## Recommendations for Merging

### Port FROM Original → New
1. Any Facebook/social media scraping logic
2. WhatsApp notification system
3. Storm/weather event correlation (adapt for "storm damage" projects)
4. Any automated follow-up sequences

### Keep FROM New Implementation
1. Houston zip code database (comprehensive)
2. Budget parsing (handles all formats)
3. JSON persistence (simple, reliable)
4. Flask API structure (clean, tested)

### New Features to Add
1. Integration with Google Calendar (appointment scheduling)
2. Stripe payment verification
3. AI chatbot enhancement (connect to Ollama)
4. Dashboard real-time updates (WebSocket)

---

## Testing Comparison

### Test Case 1: HOT Lead (Inner Houston)
```json
{
    "name": "John Smith",
    "email": "john@email.com",
    "phone": "(713) 555-1234",
    "zip": "77002",
    "project_type": "kitchen",
    "budget": "50k",
    "timeline": "asap",
    "description": "Complete kitchen renovation with custom cabinets"
}
```
**New J3 Result:** Score 89-96, Priority: HOT/WARM
**Original Result:** [TBD when extracted]

### Test Case 2: Outside Service Area
```json
{
    "name": "Mike Davis",
    "email": "mike@email.com",
    "phone": "512-555-9999",
    "zip": "78701",  // Austin
    "project_type": "kitchen",
    "budget": "100k",
    "timeline": "asap"
}
```
**New J3 Result:** DISQUALIFIED (outside_service_area)
**Original Result:** [TBD when extracted]

---

## Action Items

1. [ ] Extract original GroomBridge from Samsung drive
2. [ ] Read and document original algorithm logic
3. [ ] Identify unique features to port
4. [ ] Create merged "best of both" version
5. [ ] Test merged version against both test suites
