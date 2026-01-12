"""
SCORPION_BRAIN Universal CRM API
================================
FastAPI-based CRM system for lead management across all client LEGs.

Endpoints:
- POST /leads - Create new lead
- GET /leads - List all leads
- GET /leads/{id} - Get specific lead
- PUT /leads/{id} - Update lead
- GET /pipeline - Get pipeline view
- GET /agents - List agents
- POST /agents - Create agent
- GET /stats - Get conversion stats

Run: uvicorn crm_api:app --host 0.0.0.0 --port 9999 --reload
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from contextlib import contextmanager
from enum import Enum

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "crm.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# Enums
class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class ProjectType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    RENOVATION = "renovation"
    CONSULTATION = "consultation"
    OTHER = "other"


class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Pydantic Models
class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1)
    contact: str = Field(..., description="Phone or email")
    project_type: ProjectType = ProjectType.OTHER
    source: str = Field(default="website", description="Lead source")
    urgency: Urgency = Urgency.MEDIUM
    budget: float = Field(default=0.0, ge=0)
    notes: str = ""
    assigned_agent: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    project_type: Optional[ProjectType] = None
    source: Optional[str] = None
    urgency: Optional[Urgency] = None
    budget: Optional[float] = None
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None
    assigned_agent: Optional[str] = None


class Lead(BaseModel):
    id: int
    name: str
    contact: str
    project_type: str
    source: str
    urgency: str
    budget: float
    score: int
    status: str
    assigned_agent: Optional[str]
    notes: str
    created_at: str
    updated_at: str


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = ""
    phone: str = ""
    specialties: str = ""  # Comma-separated


class Agent(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    specialties: str
    active: bool
    created_at: str


# Score calculation
def calculate_score(urgency: str, budget: float, project_type: str) -> int:
    """
    Calculate lead score (0-100) based on factors.

    Urgency: low=10, medium=20, high=35, critical=50
    Budget: 0-5k=5, 5-25k=15, 25-100k=25, 100k+=35
    Project Type: residential=5, commercial=10, industrial=15
    """
    score = 0

    # Urgency score (max 50)
    urgency_scores = {"low": 10, "medium": 20, "high": 35, "critical": 50}
    score += urgency_scores.get(urgency, 10)

    # Budget score (max 35)
    if budget >= 100000:
        score += 35
    elif budget >= 25000:
        score += 25
    elif budget >= 5000:
        score += 15
    else:
        score += 5

    # Project type score (max 15)
    type_scores = {
        "industrial": 15,
        "commercial": 12,
        "residential": 8,
        "renovation": 10,
        "consultation": 5,
        "other": 5
    }
    score += type_scores.get(project_type, 5)

    return min(100, score)


# Database functions
@contextmanager
def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database tables."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Leads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT NOT NULL,
                project_type TEXT DEFAULT 'other',
                source TEXT DEFAULT 'website',
                urgency TEXT DEFAULT 'medium',
                budget REAL DEFAULT 0,
                score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'new',
                assigned_agent TEXT,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Agents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                specialties TEXT DEFAULT '',
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)

        # Activity log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                agent_name TEXT,
                action TEXT,
                details TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        """)

        conn.commit()


# FastAPI app
app = FastAPI(
    title="SCORPION CRM API",
    description="Universal CRM for SCORPION_BRAIN lead management",
    version="1.0.0"
)

# CORS middleware - allow all origins for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()


# Lead endpoints
@app.post("/leads", response_model=Lead)
async def create_lead(lead: LeadCreate):
    """Create a new lead."""
    now = datetime.now().isoformat()
    score = calculate_score(lead.urgency.value, lead.budget, lead.project_type.value)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO leads (name, contact, project_type, source, urgency, budget, score, status, assigned_agent, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead.name,
            lead.contact,
            lead.project_type.value,
            lead.source,
            lead.urgency.value,
            lead.budget,
            score,
            LeadStatus.NEW.value,
            lead.assigned_agent,
            lead.notes,
            now,
            now
        ))
        conn.commit()
        lead_id = cursor.lastrowid

        # Log activity
        cursor.execute("""
            INSERT INTO activity_log (lead_id, action, details, timestamp)
            VALUES (?, ?, ?, ?)
        """, (lead_id, "created", f"Lead created: {lead.name}", now))
        conn.commit()

        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        row = cursor.fetchone()

    return dict(row)


@app.get("/leads", response_model=List[Lead])
async def get_leads(
    status: Optional[LeadStatus] = None,
    assigned_agent: Optional[str] = None,
    source: Optional[str] = None,
    min_score: Optional[int] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0
):
    """Get all leads with optional filters."""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM leads WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if assigned_agent:
            query += " AND assigned_agent = ?"
            params.append(assigned_agent)

        if source:
            query += " AND source = ?"
            params.append(source)

        if min_score:
            query += " AND score >= ?"
            params.append(min_score)

        query += " ORDER BY score DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


@app.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: int):
    """Get a specific lead."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")

    return dict(row)


@app.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(lead_id: int, lead: LeadUpdate):
    """Update a lead."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if lead exists
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Build update query dynamically
        updates = []
        params = []

        if lead.name is not None:
            updates.append("name = ?")
            params.append(lead.name)

        if lead.contact is not None:
            updates.append("contact = ?")
            params.append(lead.contact)

        if lead.project_type is not None:
            updates.append("project_type = ?")
            params.append(lead.project_type.value)

        if lead.source is not None:
            updates.append("source = ?")
            params.append(lead.source)

        if lead.urgency is not None:
            updates.append("urgency = ?")
            params.append(lead.urgency.value)

        if lead.budget is not None:
            updates.append("budget = ?")
            params.append(lead.budget)

        if lead.status is not None:
            updates.append("status = ?")
            params.append(lead.status.value)

        if lead.notes is not None:
            updates.append("notes = ?")
            params.append(lead.notes)

        if lead.assigned_agent is not None:
            updates.append("assigned_agent = ?")
            params.append(lead.assigned_agent)

        if not updates:
            return dict(existing)

        # Recalculate score
        urgency = lead.urgency.value if lead.urgency else existing["urgency"]
        budget = lead.budget if lead.budget is not None else existing["budget"]
        project_type = lead.project_type.value if lead.project_type else existing["project_type"]
        new_score = calculate_score(urgency, budget, project_type)

        updates.append("score = ?")
        params.append(new_score)

        updates.append("updated_at = ?")
        now = datetime.now().isoformat()
        params.append(now)

        params.append(lead_id)

        query = f"UPDATE leads SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)

        # Log activity
        cursor.execute("""
            INSERT INTO activity_log (lead_id, agent_name, action, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (lead_id, lead.assigned_agent, "updated", f"Lead updated", now))

        conn.commit()

        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        row = cursor.fetchone()

    return dict(row)


@app.delete("/leads/{lead_id}")
async def delete_lead(lead_id: int):
    """Delete a lead."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        conn.commit()

    return {"message": "Lead deleted", "id": lead_id}


# Pipeline endpoint
@app.get("/pipeline")
async def get_pipeline():
    """Get leads grouped by status (pipeline view)."""
    with get_db() as conn:
        cursor = conn.cursor()

        pipeline = {}
        for status in LeadStatus:
            cursor.execute("""
                SELECT * FROM leads WHERE status = ? ORDER BY score DESC
            """, (status.value,))
            rows = cursor.fetchall()
            pipeline[status.value] = {
                "count": len(rows),
                "total_value": sum(r["budget"] for r in rows),
                "leads": [dict(r) for r in rows]
            }

    return pipeline


# Agent endpoints
@app.post("/agents", response_model=Agent)
async def create_agent(agent: AgentCreate):
    """Create a new agent."""
    now = datetime.now().isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO agents (name, email, phone, specialties, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (agent.name, agent.email, agent.phone, agent.specialties, now))
            conn.commit()
            agent_id = cursor.lastrowid

            cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
            row = cursor.fetchone()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Agent name already exists")

    return dict(row)


@app.get("/agents", response_model=List[Agent])
async def get_agents(active_only: bool = True):
    """Get all agents."""
    with get_db() as conn:
        cursor = conn.cursor()
        if active_only:
            cursor.execute("SELECT * FROM agents WHERE active = 1 ORDER BY name")
        else:
            cursor.execute("SELECT * FROM agents ORDER BY name")
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


@app.get("/agents/{agent_name}/leads", response_model=List[Lead])
async def get_agent_leads(agent_name: str):
    """Get leads assigned to a specific agent."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM leads WHERE assigned_agent = ? ORDER BY score DESC
        """, (agent_name,))
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


# Stats endpoint
@app.get("/stats")
async def get_stats():
    """Get CRM statistics."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Total leads
        cursor.execute("SELECT COUNT(*) as count FROM leads")
        total_leads = cursor.fetchone()["count"]

        # Leads by status
        cursor.execute("""
            SELECT status, COUNT(*) as count, SUM(budget) as total_value
            FROM leads GROUP BY status
        """)
        by_status = {row["status"]: {"count": row["count"], "value": row["total_value"] or 0}
                     for row in cursor.fetchall()}

        # Conversion rate
        won = by_status.get("won", {}).get("count", 0)
        lost = by_status.get("lost", {}).get("count", 0)
        conversion_rate = (won / (won + lost) * 100) if (won + lost) > 0 else 0

        # Top agents
        cursor.execute("""
            SELECT assigned_agent, COUNT(*) as lead_count,
                   SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins
            FROM leads WHERE assigned_agent IS NOT NULL
            GROUP BY assigned_agent ORDER BY wins DESC LIMIT 5
        """)
        top_agents = [dict(row) for row in cursor.fetchall()]

        # Recent activity
        cursor.execute("""
            SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 20
        """)
        recent_activity = [dict(row) for row in cursor.fetchall()]

        # Leads by source
        cursor.execute("""
            SELECT source, COUNT(*) as count FROM leads GROUP BY source
        """)
        by_source = {row["source"]: row["count"] for row in cursor.fetchall()}

    return {
        "total_leads": total_leads,
        "by_status": by_status,
        "conversion_rate": round(conversion_rate, 2),
        "top_agents": top_agents,
        "by_source": by_source,
        "recent_activity": recent_activity[:10]
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": str(DB_PATH),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    print("🦂 SCORPION CRM API Starting...")
    print(f"📊 Database: {DB_PATH}")
    print(f"🌐 API Docs: http://localhost:9999/docs")
    uvicorn.run(app, host="0.0.0.0", port=9999)
