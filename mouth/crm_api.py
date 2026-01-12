#!/usr/bin/env python3
"""
SCORPION KING - Universal CRM API
FastAPI server on port 9999 with SQLite backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import sqlite3
import os

# Initialize FastAPI
app = FastAPI(title="Scorpion CRM API", version="1.0.0")

# CORS - Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "crm.db")

# Pydantic Models
class LeadCreate(BaseModel):
    name: str
    contact: str
    project_type: str
    source: str
    urgency: int  # 1-5
    budget: float
    status: Optional[str] = "new"
    assigned_agent: Optional[str] = None
    notes: Optional[str] = ""

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    project_type: Optional[str] = None
    source: Optional[str] = None
    urgency: Optional[int] = None
    budget: Optional[float] = None
    status: Optional[str] = None
    assigned_agent: Optional[str] = None
    notes: Optional[str] = None

class Lead(BaseModel):
    id: int
    name: str
    contact: str
    project_type: str
    source: str
    urgency: int
    budget: float
    score: float
    status: str
    assigned_agent: Optional[str]
    notes: str
    created_at: str

class Agent(BaseModel):
    name: str
    lead_count: int
    conversion_rate: float

# Score calculation
def calculate_score(urgency: int, budget: float, project_type: str) -> float:
    """
    Auto-calculate lead score based on urgency + budget + project_type
    Score range: 0-100
    """
    # Urgency contributes 0-30 points (urgency 1-5 -> 6-30)
    urgency_score = urgency * 6

    # Budget contributes 0-40 points
    if budget >= 100000:
        budget_score = 40
    elif budget >= 50000:
        budget_score = 30
    elif budget >= 25000:
        budget_score = 20
    elif budget >= 10000:
        budget_score = 10
    else:
        budget_score = 5

    # Project type contributes 0-30 points
    project_scores = {
        "full_build": 30,
        "renovation": 25,
        "commercial": 28,
        "residential": 22,
        "repair": 15,
        "consultation": 10,
        "other": 12
    }
    project_score = project_scores.get(project_type.lower(), 12)

    return min(100, urgency_score + budget_score + project_score)

# Database initialization
def init_db():
    """Initialize SQLite database with leads and agents tables"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Leads table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT NOT NULL,
            project_type TEXT NOT NULL,
            source TEXT NOT NULL,
            urgency INTEGER NOT NULL,
            budget REAL NOT NULL,
            score REAL NOT NULL,
            status TEXT DEFAULT 'new',
            assigned_agent TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    # Agents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Insert default agents if none exist
    cursor.execute("SELECT COUNT(*) FROM agents")
    if cursor.fetchone()[0] == 0:
        default_agents = ["CE", "Agent1", "Agent2", "Unassigned"]
        for agent in default_agents:
            cursor.execute(
                "INSERT INTO agents (name, created_at) VALUES (?, ?)",
                (agent, datetime.now().isoformat())
            )

    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()

# ENDPOINTS

@app.get("/")
async def root():
    return {"message": "Scorpion CRM API v1.0", "status": "operational"}

# LEADS ENDPOINTS

@app.post("/leads", response_model=Lead)
async def create_lead(lead: LeadCreate):
    """Create a new lead with auto-calculated score"""
    conn = get_db()
    cursor = conn.cursor()

    score = calculate_score(lead.urgency, lead.budget, lead.project_type)
    created_at = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO leads (name, contact, project_type, source, urgency, budget, score, status, assigned_agent, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead.name, lead.contact, lead.project_type, lead.source,
        lead.urgency, lead.budget, score, lead.status,
        lead.assigned_agent, lead.notes, created_at
    ))

    lead_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row)

@app.get("/leads", response_model=List[Lead])
async def get_leads(agent: Optional[str] = None, status: Optional[str] = None):
    """Get all leads, optionally filtered by agent or status"""
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

    query += " ORDER BY score DESC, created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

@app.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: int):
    """Get a specific lead by ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")

    return dict(row)

@app.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(lead_id: int, lead_update: LeadUpdate):
    """Update a lead"""
    conn = get_db()
    cursor = conn.cursor()

    # Get existing lead
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    existing = cursor.fetchone()

    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Lead not found")

    # Build update query
    updates = []
    params = []

    for field, value in lead_update.dict(exclude_unset=True).items():
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    # Recalculate score if relevant fields changed
    urgency = lead_update.urgency if lead_update.urgency else existing["urgency"]
    budget = lead_update.budget if lead_update.budget else existing["budget"]
    project_type = lead_update.project_type if lead_update.project_type else existing["project_type"]

    new_score = calculate_score(urgency, budget, project_type)
    updates.append("score = ?")
    params.append(new_score)

    if updates:
        params.append(lead_id)
        query = f"UPDATE leads SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()

    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row)

@app.delete("/leads/{lead_id}")
async def delete_lead(lead_id: int):
    """Delete a lead"""
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

# PIPELINE ENDPOINT

@app.get("/pipeline")
async def get_pipeline():
    """Get leads organized by status (pipeline view)"""
    conn = get_db()
    cursor = conn.cursor()

    statuses = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]
    pipeline = {}

    for status in statuses:
        cursor.execute(
            "SELECT * FROM leads WHERE status = ? ORDER BY score DESC",
            (status,)
        )
        pipeline[status] = [dict(row) for row in cursor.fetchall()]

    # Get summary stats
    cursor.execute("SELECT COUNT(*) as total FROM leads")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as won FROM leads WHERE status = 'won'")
    won = cursor.fetchone()["won"]

    cursor.execute("SELECT SUM(budget) as total_value FROM leads WHERE status = 'won'")
    result = cursor.fetchone()
    total_value = result["total_value"] if result["total_value"] else 0

    conn.close()

    return {
        "pipeline": pipeline,
        "stats": {
            "total_leads": total,
            "won_deals": won,
            "conversion_rate": round((won / total * 100) if total > 0 else 0, 2),
            "total_value_won": total_value
        }
    }

# AGENTS ENDPOINTS

@app.get("/agents", response_model=List[Agent])
async def get_agents():
    """Get all agents with their stats"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM agents ORDER BY name")
    agents = cursor.fetchall()

    result = []
    for agent in agents:
        name = agent["name"]

        # Get lead count
        cursor.execute(
            "SELECT COUNT(*) as count FROM leads WHERE assigned_agent = ?",
            (name,)
        )
        lead_count = cursor.fetchone()["count"]

        # Get conversion rate
        cursor.execute(
            "SELECT COUNT(*) as won FROM leads WHERE assigned_agent = ? AND status = 'won'",
            (name,)
        )
        won = cursor.fetchone()["won"]

        conversion_rate = round((won / lead_count * 100) if lead_count > 0 else 0, 2)

        result.append({
            "name": name,
            "lead_count": lead_count,
            "conversion_rate": conversion_rate
        })

    conn.close()
    return result

@app.post("/agents")
async def create_agent(name: str):
    """Create a new agent"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO agents (name, created_at) VALUES (?, ?)",
            (name, datetime.now().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Agent already exists")

    conn.close()
    return {"message": "Agent created", "name": name}

# Run server
if __name__ == "__main__":
    import uvicorn
    print("Starting Scorpion CRM API on http://localhost:9999")
    uvicorn.run(app, host="0.0.0.0", port=9999)
