"""
SCORPION CRM API
================
FastAPI backend for lead management system.
Run: uvicorn crm_api:app --port 9999 --reload
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sqlite3
import os

# Initialize FastAPI
app = FastAPI(
    title="SCORPION CRM API",
    description="Lead management for the SCORPION empire",
    version="1.0.0"
)

# CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "crm.db")

# Status options
VALID_STATUSES = ["new", "contacted", "qualified", "proposal", "won", "lost"]

# =============================================================================
# MODELS
# =============================================================================

class LeadCreate(BaseModel):
    name: str
    contact: str
    project_type: str = "other"  # full, kitchen, bathroom, other
    source: str = "manual"
    urgency: str = "later"  # asap, soon, later
    budget: str = "under5k"  # over30k, 15to30k, 5to15k, under5k
    status: str = "new"
    assigned_agent: Optional[str] = None
    notes: Optional[str] = ""

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    project_type: Optional[str] = None
    source: Optional[str] = None
    urgency: Optional[str] = None
    budget: Optional[str] = None
    status: Optional[str] = None
    assigned_agent: Optional[str] = None
    notes: Optional[str] = None

class Lead(BaseModel):
    id: int
    name: str
    contact: str
    project_type: str
    source: str
    urgency: str
    budget: str
    score: int
    status: str
    assigned_agent: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str

class AgentCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

class Agent(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    created_at: str

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # Create leads table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT NOT NULL,
            project_type TEXT DEFAULT 'other',
            source TEXT DEFAULT 'manual',
            urgency TEXT DEFAULT 'later',
            budget TEXT DEFAULT 'under5k',
            score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'new',
            assigned_agent TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create agents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_agent ON leads(assigned_agent)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC)")

    conn.commit()
    conn.close()

def calculate_score(urgency: str, budget: str, project_type: str) -> int:
    """Calculate lead score based on urgency, budget, and project type."""
    score = 0

    # Urgency scoring
    urgency_scores = {"asap": 30, "soon": 15, "later": 5}
    score += urgency_scores.get(urgency.lower(), 5)

    # Budget scoring
    budget_scores = {"over30k": 25, "15to30k": 20, "5to15k": 10, "under5k": 5}
    score += budget_scores.get(budget.lower(), 5)

    # Project type scoring
    project_scores = {"full": 20, "kitchen": 15, "bathroom": 12, "other": 8}
    score += project_scores.get(project_type.lower(), 8)

    return score

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()

# =============================================================================
# LEAD ENDPOINTS
# =============================================================================

@app.post("/leads", response_model=Lead)
async def create_lead(lead: LeadCreate):
    """Create a new lead with auto-calculated score."""
    conn = get_db()
    cursor = conn.cursor()

    score = calculate_score(lead.urgency, lead.budget, lead.project_type)
    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO leads (name, contact, project_type, source, urgency, budget,
                          score, status, assigned_agent, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (lead.name, lead.contact, lead.project_type, lead.source, lead.urgency,
          lead.budget, score, lead.status, lead.assigned_agent, lead.notes, now, now))

    lead_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row)

@app.get("/leads", response_model=List[Lead])
async def list_leads(
    agent: Optional[str] = Query(None, description="Filter by assigned agent"),
    status: Optional[str] = Query(None, description="Filter by status"),
    min_score: Optional[int] = Query(None, description="Minimum score filter")
):
    """List all leads with optional filters."""
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if agent:
        query += " AND assigned_agent = ?"
        params.append(agent)

    if status:
        query += " AND status = ?"
        params.append(status)

    if min_score:
        query += " AND score >= ?"
        params.append(min_score)

    query += " ORDER BY score DESC, created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

@app.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: int):
    """Get a single lead by ID."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")

    return dict(row)

@app.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(lead_id: int, lead: LeadUpdate):
    """Update an existing lead."""
    conn = get_db()
    cursor = conn.cursor()

    # Get current lead
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    current = cursor.fetchone()

    if not current:
        conn.close()
        raise HTTPException(status_code=404, detail="Lead not found")

    current = dict(current)

    # Build update with new values
    updates = {}
    for field, value in lead.dict(exclude_unset=True).items():
        if value is not None:
            updates[field] = value

    if not updates:
        conn.close()
        return current

    # Recalculate score if relevant fields changed
    urgency = updates.get("urgency", current["urgency"])
    budget = updates.get("budget", current["budget"])
    project_type = updates.get("project_type", current["project_type"])
    updates["score"] = calculate_score(urgency, budget, project_type)
    updates["updated_at"] = datetime.now().isoformat()

    # Build and execute update query
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [lead_id]

    cursor.execute(f"UPDATE leads SET {set_clause} WHERE id = ?", values)
    conn.commit()

    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row)

@app.delete("/leads/{lead_id}")
async def delete_lead(lead_id: int):
    """Delete a lead."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM leads WHERE id = ?", (lead_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Lead not found")

    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()

    return {"message": "Lead deleted", "id": lead_id}

# =============================================================================
# PIPELINE & STATS ENDPOINTS
# =============================================================================

@app.get("/pipeline")
async def get_pipeline():
    """Get leads grouped by status (kanban view)."""
    conn = get_db()
    cursor = conn.cursor()

    pipeline = {}
    for status in VALID_STATUSES:
        cursor.execute(
            "SELECT * FROM leads WHERE status = ? ORDER BY score DESC",
            (status,)
        )
        pipeline[status] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return pipeline

@app.get("/stats")
async def get_stats():
    """Get CRM statistics and agent performance."""
    conn = get_db()
    cursor = conn.cursor()

    # Total leads
    cursor.execute("SELECT COUNT(*) as count FROM leads")
    total_leads = cursor.fetchone()["count"]

    # Hot leads (score > 50)
    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE score > 50")
    hot_leads = cursor.fetchone()["count"]

    # Leads by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM leads
        GROUP BY status
    """)
    by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

    # Conversion rate (won / total closed)
    won = by_status.get("won", 0)
    lost = by_status.get("lost", 0)
    closed = won + lost
    conversion_rate = round((won / closed * 100), 1) if closed > 0 else 0

    # Revenue pipeline (estimated from budget categories)
    budget_values = {"over30k": 35000, "15to30k": 22500, "5to15k": 10000, "under5k": 2500}
    cursor.execute("SELECT budget, COUNT(*) as count FROM leads WHERE status NOT IN ('won', 'lost') GROUP BY budget")
    pipeline_value = sum(budget_values.get(row["budget"], 0) * row["count"] for row in cursor.fetchall())

    # Agent performance
    cursor.execute("""
        SELECT
            assigned_agent,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'contacted' THEN 1 ELSE 0 END) as contacted,
            SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as won,
            SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost
        FROM leads
        WHERE assigned_agent IS NOT NULL AND assigned_agent != ''
        GROUP BY assigned_agent
    """)

    agent_stats = []
    for row in cursor.fetchall():
        agent_closed = row["won"] + row["lost"]
        agent_stats.append({
            "agent": row["assigned_agent"],
            "total": row["total"],
            "contacted": row["contacted"],
            "won": row["won"],
            "lost": row["lost"],
            "conversion": round((row["won"] / agent_closed * 100), 1) if agent_closed > 0 else 0
        })

    conn.close()

    return {
        "total_leads": total_leads,
        "hot_leads": hot_leads,
        "by_status": by_status,
        "conversion_rate": conversion_rate,
        "pipeline_value": pipeline_value,
        "agent_performance": agent_stats
    }

# =============================================================================
# AGENT ENDPOINTS
# =============================================================================

@app.post("/agents", response_model=Agent)
async def create_agent(agent: AgentCreate):
    """Create a new agent."""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO agents (name, email, phone, created_at)
            VALUES (?, ?, ?, ?)
        """, (agent.name, agent.email, agent.phone, datetime.now().isoformat()))

        agent_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row)

    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Agent name already exists")

@app.get("/agents", response_model=List[Agent])
async def list_agents():
    """List all agents."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM agents ORDER BY name")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "alive",
        "service": "SCORPION CRM API",
        "version": "1.0.0",
        "endpoints": [
            "POST /leads",
            "GET /leads",
            "GET /leads/{id}",
            "PUT /leads/{id}",
            "DELETE /leads/{id}",
            "GET /pipeline",
            "GET /stats",
            "POST /agents",
            "GET /agents"
        ]
    }

# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🦂 SCORPION CRM API starting on port 9999...")
    uvicorn.run(app, host="0.0.0.0", port=9999)
