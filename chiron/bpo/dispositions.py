"""
CHIRON BPO - Standard Disposition Codes
Call outcome tracking for healthcare campaigns

⚔️ Color-coded for quick visual recognition
"""

from typing import Dict, Any
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════
# DISPOSITION CATEGORIES
# ═══════════════════════════════════════════════════════════════════════

class DispositionCategory(Enum):
    """High-level disposition groupings"""
    POSITIVE = "positive"      # Leads to revenue/appointment
    NEUTRAL = "neutral"        # No decision made
    NEGATIVE = "negative"      # Definite no
    SPECIAL = "special"        # Requires attention


# ═══════════════════════════════════════════════════════════════════════
# HEALTHCARE DISPOSITIONS (NSIPA, Medicare, etc.)
# ═══════════════════════════════════════════════════════════════════════

HEALTHCARE_DISPOSITIONS: Dict[str, Dict[str, Any]] = {
    # ─────────────────────────────────────────────────────────────────
    # POSITIVE OUTCOMES
    # ─────────────────────────────────────────────────────────────────
    "APT_SET": {
        "code": "APT_SET",
        "label": "Appointment Set",
        "category": DispositionCategory.POSITIVE,
        "color": "#00ff41",  # Terminal green
        "points": 10,
        "counts_as_conversion": True,
        "description": "Patient agreed to appointment"
    },
    "APT_CONFIRMED": {
        "code": "APT_CONFIRMED",
        "label": "Appointment Confirmed",
        "category": DispositionCategory.POSITIVE,
        "color": "#00ff41",
        "points": 5,
        "counts_as_conversion": False,
        "description": "Existing appointment verified"
    },
    "TRANSFER": {
        "code": "TRANSFER",
        "label": "Transferred to Closer",
        "category": DispositionCategory.POSITIVE,
        "color": "#9b59b6",  # Purple
        "points": 5,
        "counts_as_conversion": True,
        "description": "Hot lead transferred to senior agent"
    },
    "CALLBACK_HOT": {
        "code": "CALLBACK_HOT",
        "label": "Hot Callback",
        "category": DispositionCategory.POSITIVE,
        "color": "#00d4ff",  # Cyan
        "points": 4,
        "counts_as_conversion": False,
        "description": "Interested, specific callback time set"
    },

    # ─────────────────────────────────────────────────────────────────
    # NEUTRAL OUTCOMES
    # ─────────────────────────────────────────────────────────────────
    "CALLBACK": {
        "code": "CALLBACK",
        "label": "Callback Scheduled",
        "category": DispositionCategory.NEUTRAL,
        "color": "#3498db",  # Blue
        "points": 3,
        "counts_as_conversion": False,
        "description": "General callback request"
    },
    "INTERESTED": {
        "code": "INTERESTED",
        "label": "Interested - Send Info",
        "category": DispositionCategory.NEUTRAL,
        "color": "#3498db",
        "points": 2,
        "counts_as_conversion": False,
        "description": "Wants information mailed/emailed"
    },
    "VOICEMAIL": {
        "code": "VOICEMAIL",
        "label": "Left Voicemail",
        "category": DispositionCategory.NEUTRAL,
        "color": "#f1c40f",  # Yellow
        "points": 1,
        "counts_as_conversion": False,
        "description": "Voicemail message left"
    },
    "NO_ANSWER": {
        "code": "NO_ANSWER",
        "label": "No Answer",
        "category": DispositionCategory.NEUTRAL,
        "color": "#f1c40f",
        "points": 0,
        "counts_as_conversion": False,
        "description": "Phone rang, no pickup"
    },
    "BUSY": {
        "code": "BUSY",
        "label": "Busy Signal",
        "category": DispositionCategory.NEUTRAL,
        "color": "#f1c40f",
        "points": 0,
        "counts_as_conversion": False,
        "description": "Line busy"
    },
    "NO_VM": {
        "code": "NO_VM",
        "label": "No Answer - No VM",
        "category": DispositionCategory.NEUTRAL,
        "color": "#f1c40f",
        "points": 0,
        "counts_as_conversion": False,
        "description": "No answer, voicemail not available"
    },

    # ─────────────────────────────────────────────────────────────────
    # NEGATIVE OUTCOMES
    # ─────────────────────────────────────────────────────────────────
    "NOT_INTERESTED": {
        "code": "NOT_INTERESTED",
        "label": "Not Interested",
        "category": DispositionCategory.NEGATIVE,
        "color": "#e74c3c",  # Red
        "points": 0,
        "counts_as_conversion": False,
        "description": "Declined offer"
    },
    "DO_NOT_CALL": {
        "code": "DO_NOT_CALL",
        "label": "Do Not Call",
        "category": DispositionCategory.NEGATIVE,
        "color": "#c0392b",  # Dark red
        "points": -1,
        "counts_as_conversion": False,
        "description": "Requested removal from list - MUST COMPLY"
    },
    "WRONG_NUMBER": {
        "code": "WRONG_NUMBER",
        "label": "Wrong Number",
        "category": DispositionCategory.NEGATIVE,
        "color": "#7f8c8d",  # Gray
        "points": 0,
        "counts_as_conversion": False,
        "description": "Number doesn't belong to target"
    },
    "DISCONNECTED": {
        "code": "DISCONNECTED",
        "label": "Disconnected",
        "category": DispositionCategory.NEGATIVE,
        "color": "#7f8c8d",
        "points": 0,
        "counts_as_conversion": False,
        "description": "Number no longer in service"
    },
    "DECEASED": {
        "code": "DECEASED",
        "label": "Deceased",
        "category": DispositionCategory.NEGATIVE,
        "color": "#2c3e50",  # Dark gray
        "points": 0,
        "counts_as_conversion": False,
        "description": "Patient is deceased - remove from list"
    },
    "INELIGIBLE": {
        "code": "INELIGIBLE",
        "label": "Ineligible",
        "category": DispositionCategory.NEGATIVE,
        "color": "#7f8c8d",
        "points": 0,
        "counts_as_conversion": False,
        "description": "Does not meet campaign criteria"
    },

    # ─────────────────────────────────────────────────────────────────
    # SPECIAL OUTCOMES
    # ─────────────────────────────────────────────────────────────────
    "ESCALATE": {
        "code": "ESCALATE",
        "label": "Escalated to Supervisor",
        "category": DispositionCategory.SPECIAL,
        "color": "#f39c12",  # Orange
        "points": 0,
        "counts_as_conversion": False,
        "description": "Issue requires supervisor attention"
    },
    "COMPLAINT": {
        "code": "COMPLAINT",
        "label": "Complaint Filed",
        "category": DispositionCategory.SPECIAL,
        "color": "#e67e22",  # Dark orange
        "points": -2,
        "counts_as_conversion": False,
        "description": "Customer filed complaint - document thoroughly"
    },
    "LANGUAGE": {
        "code": "LANGUAGE",
        "label": "Language Barrier",
        "category": DispositionCategory.SPECIAL,
        "color": "#9b59b6",
        "points": 0,
        "counts_as_conversion": False,
        "description": "Needs agent with different language"
    },
    "TECHNICAL": {
        "code": "TECHNICAL",
        "label": "Technical Issue",
        "category": DispositionCategory.SPECIAL,
        "color": "#95a5a6",
        "points": 0,
        "counts_as_conversion": False,
        "description": "Call dropped, system issue, etc."
    }
}


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def get_disposition(code: str) -> Dict[str, Any]:
    """Get disposition details by code"""
    return HEALTHCARE_DISPOSITIONS.get(code, {
        "code": code,
        "label": "Unknown",
        "category": DispositionCategory.NEUTRAL,
        "color": "#7f8c8d",
        "points": 0
    })


def get_dispositions_by_category(category: DispositionCategory) -> list:
    """Get all dispositions in a category"""
    return [
        d for d in HEALTHCARE_DISPOSITIONS.values()
        if d["category"] == category
    ]


def get_positive_dispositions() -> list:
    """Get all positive outcome codes"""
    return get_dispositions_by_category(DispositionCategory.POSITIVE)


def get_conversion_dispositions() -> list:
    """Get dispositions that count as conversions"""
    return [
        d for d in HEALTHCARE_DISPOSITIONS.values()
        if d.get("counts_as_conversion", False)
    ]


def calculate_points(disposition_code: str) -> int:
    """Get point value for a disposition"""
    disp = get_disposition(disposition_code)
    return disp.get("points", 0)


# ═══════════════════════════════════════════════════════════════════════
# QUICK REFERENCE
# ═══════════════════════════════════════════════════════════════════════

DISPOSITION_CODES = list(HEALTHCARE_DISPOSITIONS.keys())
POSITIVE_CODES = [d["code"] for d in get_positive_dispositions()]
CONVERSION_CODES = [d["code"] for d in get_conversion_dispositions()]
