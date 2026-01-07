"""
SCORPION LEAD ENGINE - Universal Multi-Industry Lead Capture System
Handles leads for J3, Antonio, Will, and any future client

🦂 Website visitor → Baby engages → Qualified → Carlos/Giovanny closes
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import sqlite3
import json
import uuid


# ═══════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════

class Industry(Enum):
    """Supported industry verticals"""
    CONSTRUCTION = "construction"
    INTERIOR_DESIGN = "interior_design"
    REAL_ESTATE = "real_estate"
    ROOFING = "roofing"
    BANKING = "banking"
    HEALTHCARE = "healthcare"
    WEBDEV = "webdev"
    IT_SERVICES = "it"
    OTHER = "other"


class LeadSource(Enum):
    """How the lead came in"""
    WEBSITE = "website"
    CHAT = "chat"
    PHONE = "phone"
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    REFERRAL = "referral"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    DIRECT = "direct"


class LeadStatus(Enum):
    """Lead lifecycle stages"""
    NEW = "new"                   # Just captured
    BABY_ENGAGED = "engaged"      # AI baby is talking to them
    QUALIFIED = "qualified"       # Has budget/timeline/need
    HANDOFF = "handoff"           # Passed to human (Carlos/Giovanny)
    QUOTED = "quoted"             # Quote sent
    NEGOTIATING = "negotiating"   # Back and forth
    WON = "won"                   # Deal closed!
    LOST = "lost"                 # Didn't convert
    NURTURE = "nurture"           # Long-term follow-up


class LeadPriority(Enum):
    """Urgency level"""
    HOT = "hot"       # Contact within 5 min
    WARM = "warm"     # Contact within 1 hour
    COOL = "cool"     # Contact within 24 hours
    COLD = "cold"     # Low priority


# ═══════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Lead:
    """Universal lead object - works for any industry"""
    id: str
    client_id: int
    client_slug: str
    industry: Industry
    source: LeadSource
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    service_needed: str = ""
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    location: Optional[str] = None
    message: str = ""
    status: LeadStatus = LeadStatus.NEW
    priority: LeadPriority = LeadPriority.WARM
    assigned_baby: Optional[str] = None
    assigned_human: Optional[str] = None
    score: int = 0  # 0-100 lead score
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    interactions: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON"""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "client_slug": self.client_slug,
            "industry": self.industry.value,
            "source": self.source.value,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "service_needed": self.service_needed,
            "budget_range": self.budget_range,
            "timeline": self.timeline,
            "location": self.location,
            "message": self.message,
            "status": self.status.value,
            "priority": self.priority.value,
            "assigned_baby": self.assigned_baby,
            "assigned_human": self.assigned_human,
            "score": self.score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "interactions": self.interactions,
            "metadata": self.metadata
        }


# ═══════════════════════════════════════════════════════════════════════
# CLIENT CONFIGURATIONS - Priority Order by Profit
# ═══════════════════════════════════════════════════════════════════════

CLIENTS: Dict[str, Dict[str, Any]] = {
    # PRIORITY 1: J3 Structural - Highest $$$ potential
    "j3": {
        "id": 2,
        "name": "J3 Structural Solutions",
        "industry": Industry.CONSTRUCTION,
        "baby": "VULCAN",
        "services": [
            "interior_design",
            "kitchen_remodel",
            "bathroom_remodel",
            "commercial",
            "residential",
            "addition",
            "renovation"
        ],
        "handoff_primary": "giovanny",
        "handoff_backup": "carlos",
        "priority": "high",
        "response_time": 5,  # minutes
        "status": "active",
        "colors": {
            "primary": "#2c3e50",
            "accent": "#ffd700"
        },
        "budget_tiers": ["under_25k", "25k_50k", "50k_100k", "100k_plus"]
    },

    # PRIORITY 2: Antonio Banking - $500/mo active
    "antonio": {
        "id": 3,
        "name": "Antonio Banking Services",
        "industry": Industry.BANKING,
        "baby": "MARCUS",
        "services": [
            "personal_loan",
            "business_loan",
            "refinance",
            "credit_repair",
            "debt_consolidation",
            "mortgage"
        ],
        "handoff_primary": "carlos",
        "handoff_backup": None,
        "priority": "high",
        "response_time": 10,
        "status": "active",
        "colors": {
            "primary": "#1a5f2a",
            "accent": "#00d97e"
        }
    },

    # PRIORITY 3: Will Real Estate - $100/mo active
    "will": {
        "id": 4,
        "name": "Will Real Estate",
        "industry": Industry.REAL_ESTATE,
        "baby": "MERCURY",
        "services": [
            "buying",
            "selling",
            "investment",
            "rental",
            "commercial_real_estate",
            "property_management"
        ],
        "handoff_primary": "carlos",
        "handoff_backup": None,
        "priority": "medium",
        "response_time": 30,
        "status": "active",
        "colors": {
            "primary": "#2980b9",
            "accent": "#3498db"
        }
    },

    # PAUSED: Cruz Roofing
    "cruz": {
        "id": 5,
        "name": "Cruz Roofing",
        "industry": Industry.ROOFING,
        "baby": None,
        "services": ["roof_repair", "roof_replacement", "inspection"],
        "handoff_primary": "carlos",
        "priority": "none",
        "response_time": 0,
        "status": "paused"
    }
}


# ═══════════════════════════════════════════════════════════════════════
# LEAD SCORING
# ═══════════════════════════════════════════════════════════════════════

def calculate_lead_score(lead: Lead, client: Dict) -> int:
    """
    Score lead 0-100 based on likelihood to convert
    Higher = hotter lead
    """
    score = 50  # Base score

    # Has phone number? +20
    if lead.phone:
        score += 20

    # Has email? +10
    if lead.email:
        score += 10

    # Has budget specified? +15
    if lead.budget_range:
        score += 15
        # Higher budget = higher score
        if "100k" in (lead.budget_range or "").lower():
            score += 10
        elif "50k" in (lead.budget_range or "").lower():
            score += 5

    # Has timeline? +10
    if lead.timeline:
        score += 10
        if any(word in (lead.timeline or "").lower() for word in ["asap", "urgent", "now", "immediately"]):
            score += 10

    # Specific service requested? +5
    if lead.service_needed:
        score += 5

    # Website chat = engaged user +5
    if lead.source == LeadSource.CHAT:
        score += 5

    # Referral = warm lead +15
    if lead.source == LeadSource.REFERRAL:
        score += 15

    return min(score, 100)


def determine_priority(score: int) -> LeadPriority:
    """Convert score to priority level"""
    if score >= 80:
        return LeadPriority.HOT
    elif score >= 60:
        return LeadPriority.WARM
    elif score >= 40:
        return LeadPriority.COOL
    else:
        return LeadPriority.COLD


# ═══════════════════════════════════════════════════════════════════════
# LEAD ENGINE
# ═══════════════════════════════════════════════════════════════════════

class LeadEngine:
    """
    Universal lead capture and management engine
    Works for any client/industry
    """

    def __init__(self, db_path: str = "leads.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Leads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                client_slug TEXT NOT NULL,
                data JSON NOT NULL,
                status TEXT DEFAULT 'new',
                priority TEXT DEFAULT 'warm',
                score INTEGER DEFAULT 50,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Interactions table (chat messages, calls, emails)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                direction TEXT NOT NULL,
                content TEXT,
                baby TEXT,
                human TEXT,
                timestamp TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        """)

        # Index for fast lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_client ON leads(client_slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at)")

        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────────────────────────
    # LEAD CAPTURE
    # ─────────────────────────────────────────────────────────────────

    def capture(self, client_slug: str, data: Dict[str, Any], source: LeadSource) -> Lead:
        """
        Capture a lead from any source
        Works for J3, Antonio, Will, or any future client
        """
        client = CLIENTS.get(client_slug)

        if not client:
            raise ValueError(f"Unknown client: {client_slug}")

        if client.get("status") == "paused":
            raise ValueError(f"Client {client_slug} is currently paused")

        # Create lead object
        lead = Lead(
            id=str(uuid.uuid4())[:8],
            client_id=client["id"],
            client_slug=client_slug,
            industry=client["industry"],
            source=source,
            name=data.get("name", "Unknown"),
            email=data.get("email"),
            phone=data.get("phone"),
            company=data.get("company"),
            service_needed=data.get("service", ""),
            budget_range=data.get("budget"),
            timeline=data.get("timeline"),
            location=data.get("location"),
            message=data.get("message", ""),
            assigned_baby=client.get("baby"),
            metadata=data.get("metadata", {})
        )

        # Calculate score and priority
        lead.score = calculate_lead_score(lead, client)
        lead.priority = determine_priority(lead.score)

        # Determine if HOT lead needs immediate human attention
        if lead.score >= 80 and client.get("priority") == "high":
            lead.assigned_human = client.get("handoff_primary")

        # Save to database
        self._save_lead(lead)

        return lead

    def _save_lead(self, lead: Lead) -> None:
        """Persist lead to database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO leads (id, client_slug, data, status, priority, score, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead.id,
            lead.client_slug,
            json.dumps(lead.to_dict()),
            lead.status.value,
            lead.priority.value,
            lead.score,
            lead.created_at.isoformat(),
            lead.updated_at.isoformat()
        ))
        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────────────────────────
    # LEAD RETRIEVAL
    # ─────────────────────────────────────────────────────────────────

    def get_lead(self, lead_id: str) -> Optional[Dict]:
        """Get single lead by ID"""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT data FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None

    def get_hot_leads(self, limit: int = 20) -> List[Dict]:
        """Get leads needing immediate action"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT data FROM leads
            WHERE status IN ('new', 'engaged')
            ORDER BY score DESC, created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()

        return [json.loads(r[0]) for r in rows]

    def get_by_client(self, client_slug: str, limit: int = 50) -> List[Dict]:
        """Get all leads for a specific client"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT data FROM leads
            WHERE client_slug = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (client_slug, limit)).fetchall()
        conn.close()

        return [json.loads(r[0]) for r in rows]

    def get_by_status(self, status: LeadStatus) -> List[Dict]:
        """Get leads by status"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT data FROM leads
            WHERE status = ?
            ORDER BY created_at DESC
        """, (status.value,)).fetchall()
        conn.close()

        return [json.loads(r[0]) for r in rows]

    # ─────────────────────────────────────────────────────────────────
    # LEAD UPDATES
    # ─────────────────────────────────────────────────────────────────

    def update_status(self, lead_id: str, status: LeadStatus) -> bool:
        """Update lead status"""
        conn = sqlite3.connect(self.db_path)

        # Get current data
        row = conn.execute("SELECT data FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not row:
            conn.close()
            return False

        data = json.loads(row[0])
        data["status"] = status.value
        data["updated_at"] = datetime.now().isoformat()

        conn.execute("""
            UPDATE leads SET data = ?, status = ?, updated_at = ? WHERE id = ?
        """, (json.dumps(data), status.value, data["updated_at"], lead_id))

        conn.commit()
        conn.close()
        return True

    def assign_human(self, lead_id: str, human: str) -> bool:
        """Assign lead to human for handoff"""
        conn = sqlite3.connect(self.db_path)

        row = conn.execute("SELECT data FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not row:
            conn.close()
            return False

        data = json.loads(row[0])
        data["assigned_human"] = human
        data["status"] = LeadStatus.HANDOFF.value
        data["updated_at"] = datetime.now().isoformat()

        conn.execute("""
            UPDATE leads SET data = ?, status = ?, updated_at = ? WHERE id = ?
        """, (json.dumps(data), LeadStatus.HANDOFF.value, data["updated_at"], lead_id))

        conn.commit()
        conn.close()
        return True

    # ─────────────────────────────────────────────────────────────────
    # INTERACTIONS
    # ─────────────────────────────────────────────────────────────────

    def log_interaction(self, lead_id: str, channel: str, direction: str,
                       content: str, baby: Optional[str] = None,
                       human: Optional[str] = None) -> None:
        """Log an interaction (chat, call, email, etc.)"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO interactions (lead_id, channel, direction, content, baby, human, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (lead_id, channel, direction, content, baby, human, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_interactions(self, lead_id: str) -> List[Dict]:
        """Get all interactions for a lead"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT channel, direction, content, baby, human, timestamp
            FROM interactions
            WHERE lead_id = ?
            ORDER BY timestamp ASC
        """, (lead_id,)).fetchall()
        conn.close()

        return [
            {
                "channel": r[0],
                "direction": r[1],
                "content": r[2],
                "baby": r[3],
                "human": r[4],
                "timestamp": r[5]
            }
            for r in rows
        ]

    # ─────────────────────────────────────────────────────────────────
    # STATISTICS
    # ─────────────────────────────────────────────────────────────────

    def get_stats(self, client_slug: Optional[str] = None) -> Dict[str, Any]:
        """Get lead statistics, optionally filtered by client"""
        conn = sqlite3.connect(self.db_path)

        where_clause = "WHERE client_slug = ?" if client_slug else ""
        params = (client_slug,) if client_slug else ()

        # Count by status
        status_counts = {}
        for status in LeadStatus:
            query = f"SELECT COUNT(*) FROM leads {where_clause}"
            if where_clause:
                query += " AND status = ?"
                result = conn.execute(query, (*params, status.value)).fetchone()
            else:
                query += " WHERE status = ?" if not where_clause else " AND status = ?"
                query = f"SELECT COUNT(*) FROM leads WHERE status = ?"
                result = conn.execute(query, (status.value,)).fetchone()
            status_counts[status.value] = result[0]

        # Total leads
        total_query = f"SELECT COUNT(*) FROM leads {where_clause}"
        total = conn.execute(total_query, params).fetchone()[0] if params else conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]

        conn.close()

        return {
            "total": total,
            "by_status": status_counts,
            "client": client_slug
        }


# ═══════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════

_engine: Optional[LeadEngine] = None


def get_engine() -> LeadEngine:
    """Get or create lead engine singleton"""
    global _engine
    if _engine is None:
        _engine = LeadEngine()
    return _engine


# Convenience export
engine = get_engine()
