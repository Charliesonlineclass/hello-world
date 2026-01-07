"""
CHIRON BPO API - FastAPI Routes
Military-grade REST endpoints for BPO operations

⚔️ All endpoints under /api/bpo
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os

from .bpo_core import (
    get_engine, BPOEngine, AgentStatus,
    BPOAgent, Call, QueuedLead
)


# ═══════════════════════════════════════════════════════════════════════
# ROUTER SETUP
# ═══════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/api/bpo", tags=["bpo"])


# ═══════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════

class ClockRequest(BaseModel):
    agent_id: str


class StartCallRequest(BaseModel):
    agent_id: str
    lead_id: str
    campaign_id: str


class EndCallRequest(BaseModel):
    call_id: str
    disposition: str
    notes: Optional[str] = ""


class StatusUpdateRequest(BaseModel):
    agent_id: str
    status: str


class DispositionRequest(BaseModel):
    call_id: str
    disposition: str
    notes: Optional[str] = ""


class QueueLeadRequest(BaseModel):
    lead_id: str
    name: str
    phone: str
    campaign_id: str
    priority: Optional[int] = 0


# ═══════════════════════════════════════════════════════════════════════
# AGENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/clock-in")
async def clock_in(request: ClockRequest):
    """Agent clock in - start shift"""
    engine = get_engine()
    success = engine.clock_in(request.agent_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "status": "success",
        "message": f"Agent {request.agent_id} clocked in",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/clock-out")
async def clock_out(request: ClockRequest):
    """Agent clock out - end shift"""
    engine = get_engine()
    success = engine.clock_out(request.agent_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "status": "success",
        "message": f"Agent {request.agent_id} clocked out",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/status")
async def update_status(request: StatusUpdateRequest):
    """Update agent status"""
    engine = get_engine()

    try:
        status = AgentStatus(request.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")

    success = engine.set_agent_status(request.agent_id, status)

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "status": "success",
        "agent_id": request.agent_id,
        "new_status": request.status
    }


@router.get("/agents")
async def get_agents(campaign_id: Optional[str] = Query(None)):
    """Get all agents with current status"""
    engine = get_engine()
    agents = engine.get_all_agents(campaign_id)

    return {
        "count": len(agents),
        "agents": [a.to_dict() for a in agents]
    }


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get single agent detail"""
    engine = get_engine()
    agent = engine.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent.to_dict()


# ═══════════════════════════════════════════════════════════════════════
# CALL ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/call/start")
async def start_call(request: StartCallRequest):
    """Start call tracking"""
    engine = get_engine()
    call = engine.start_call(request.agent_id, request.lead_id, request.campaign_id)

    if not call:
        raise HTTPException(status_code=400, detail="Failed to start call")

    return {
        "status": "success",
        "call": call.to_dict()
    }


@router.post("/call/end")
async def end_call(request: EndCallRequest):
    """End call with disposition"""
    engine = get_engine()
    success = engine.end_call(request.call_id, request.disposition, request.notes or "")

    if not success:
        raise HTTPException(status_code=404, detail="Call not found")

    return {
        "status": "success",
        "call_id": request.call_id,
        "disposition": request.disposition
    }


@router.post("/disposition")
async def log_disposition(request: DispositionRequest):
    """Log call disposition (alias for end_call)"""
    return await end_call(EndCallRequest(
        call_id=request.call_id,
        disposition=request.disposition,
        notes=request.notes
    ))


# ═══════════════════════════════════════════════════════════════════════
# QUEUE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/queue")
async def get_queue():
    """Get queue status"""
    engine = get_engine()
    return engine.get_queue_status()


@router.post("/queue/add")
async def add_to_queue(request: QueueLeadRequest):
    """Add lead to queue"""
    engine = get_engine()
    lead = QueuedLead(
        id=request.lead_id,
        name=request.name,
        phone=request.phone,
        campaign_id=request.campaign_id,
        priority=request.priority or 0
    )
    engine.add_to_queue(lead)

    return {
        "status": "success",
        "queue_position": len(engine.queue),
        "lead": lead.to_dict()
    }


@router.post("/queue/next")
async def get_next_lead():
    """Get next lead from queue"""
    engine = get_engine()
    lead = engine.get_next_from_queue()

    if not lead:
        return {"status": "empty", "lead": None}

    return {
        "status": "success",
        "lead": lead.to_dict()
    }


# ═══════════════════════════════════════════════════════════════════════
# STATISTICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/leaderboard")
async def get_leaderboard(campaign_id: Optional[str] = Query(None)):
    """Performance ranking"""
    engine = get_engine()
    return {
        "leaderboard": engine.get_leaderboard(campaign_id)
    }


@router.get("/stats/realtime")
async def get_realtime_stats(campaign_id: Optional[str] = Query(None)):
    """Dashboard real-time stats"""
    engine = get_engine()
    return engine.get_realtime_stats(campaign_id)


@router.get("/stats/hourly")
async def get_hourly_stats(campaign_id: Optional[str] = Query(None)):
    """Hourly breakdown for charts"""
    engine = get_engine()
    return {
        "hours": engine.get_hourly_stats(campaign_id)
    }


# ═══════════════════════════════════════════════════════════════════════
# DASHBOARD ROUTE
# ═══════════════════════════════════════════════════════════════════════

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the BPO dashboard"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")

    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            return HTMLResponse(content=f.read())

    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


# ═══════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """BPO system health check"""
    engine = get_engine()
    stats = engine.get_realtime_stats()

    return {
        "status": "operational",
        "service": "CHIRON BPO Command",
        "version": "1.0.0",
        "agents_online": stats["agents_online"],
        "timestamp": datetime.now().isoformat()
    }
