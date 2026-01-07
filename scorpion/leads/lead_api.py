"""
SCORPION LEAD API - FastAPI Routes for Universal Lead Capture
Handles webhooks, chat, and dashboard for ALL clients

🦂 One API, infinite industries
"""

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import httpx

from .lead_engine import (
    get_engine, CLIENTS, LeadSource, LeadStatus
)


# ═══════════════════════════════════════════════════════════════════════
# ROUTER SETUP
# ═══════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/api/leads", tags=["leads"])


# ═══════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════════

class LeadInput(BaseModel):
    """Universal lead input - works for any industry"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    service: Optional[str] = None
    message: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    location: Optional[str] = None


class ChatMessage(BaseModel):
    """Chat message from widget"""
    message: str
    lead_id: Optional[str] = None


class StatusUpdate(BaseModel):
    """Update lead status"""
    status: str


class HandoffRequest(BaseModel):
    """Hand lead to human"""
    human: str


# ═══════════════════════════════════════════════════════════════════════
# WEBHOOK ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/webhook/{client_slug}")
async def capture_lead(
    client_slug: str,
    data: LeadInput,
    background: BackgroundTasks,
    source: str = Query("website")
):
    """
    Universal webhook - captures leads for ANY client
    Works for J3, Antonio, Will, or any future client

    POST /api/leads/webhook/j3
    POST /api/leads/webhook/antonio
    POST /api/leads/webhook/will
    """
    engine = get_engine()

    # Validate client
    client = CLIENTS.get(client_slug)
    if not client:
        raise HTTPException(status_code=404, detail=f"Unknown client: {client_slug}")

    if client.get("status") == "paused":
        raise HTTPException(status_code=400, detail=f"Client {client_slug} is currently paused")

    try:
        # Determine source
        lead_source = LeadSource.WEBSITE
        if source == "chat":
            lead_source = LeadSource.CHAT
        elif source == "phone":
            lead_source = LeadSource.PHONE
        elif source == "referral":
            lead_source = LeadSource.REFERRAL

        # Capture the lead
        lead = engine.capture(client_slug, data.dict(), lead_source)

        # Queue background tasks
        background.add_task(engage_lead, lead.id, client_slug)

        # Notify human if high priority
        if client.get("priority") == "high" and lead.score >= 70:
            background.add_task(notify_human, lead.to_dict(), client)

        return {
            "status": "captured",
            "lead_id": lead.id,
            "score": lead.score,
            "priority": lead.priority.value,
            "baby": lead.assigned_baby,
            "message": f"Lead captured for {client['name']}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# CHAT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/chat/{client_slug}")
async def chat_with_lead(client_slug: str, data: ChatMessage):
    """
    Real-time chat endpoint for website widgets
    Baby AI responds based on client context
    """
    engine = get_engine()
    client = CLIENTS.get(client_slug)

    if not client:
        return {"response": "Service temporarily unavailable.", "baby": None}

    if client.get("status") == "paused":
        return {"response": "We're not accepting new inquiries at this time.", "baby": None}

    baby = client.get("baby", "HERMES")
    message = data.message

    # Log interaction if we have a lead_id
    if data.lead_id:
        engine.log_interaction(
            data.lead_id, "chat", "inbound", message, baby=None, human=None
        )

    # Build prompt based on client
    prompt = build_chat_prompt(client_slug, message)

    # Call Ollama for AI response
    try:
        async with httpx.AsyncClient(timeout=30) as http:
            response = await http.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "tinyllama",
                    "prompt": prompt,
                    "stream": False
                }
            )
            ai_response = response.json().get("response", "").strip()

            if not ai_response:
                ai_response = get_fallback_response(client_slug)

    except Exception:
        ai_response = get_fallback_response(client_slug)

    # Log AI response
    if data.lead_id:
        engine.log_interaction(
            data.lead_id, "chat", "outbound", ai_response, baby=baby, human=None
        )

    return {"response": ai_response, "baby": baby}


def build_chat_prompt(client_slug: str, message: str) -> str:
    """Build AI prompt based on client context"""
    client = CLIENTS.get(client_slug, {})

    prompts = {
        "j3": f"""You are VULCAN, the AI assistant for J3 Structural Solutions.
J3 specializes in interior design, kitchen remodels, bathroom remodels, and construction.
Be professional, helpful, and enthusiastic about their project.
Always mention that Giovanny will personally call them to discuss details and provide a free quote.
Keep responses concise (2-3 sentences max).

Customer message: {message}

Respond helpfully:""",

        "antonio": f"""You are MARCUS, the AI assistant for Antonio's banking services.
Services include personal loans, business loans, refinancing, and credit repair.
Be professional and reassuring about financial matters.
Don't promise specific rates or terms - mention Carlos will review their options personally.
Keep responses concise (2-3 sentences max).

Customer message: {message}

Respond helpfully:""",

        "will": f"""You are MERCURY, the AI assistant for Will's real estate services.
Services include buying, selling, investment properties, and rentals.
Be enthusiastic about real estate and helpful with their property needs.
Mention that Carlos will reach out to discuss their specific requirements.
Keep responses concise (2-3 sentences max).

Customer message: {message}

Respond helpfully:"""
    }

    return prompts.get(client_slug, f"You are a helpful assistant. User: {message}\nRespond:")


def get_fallback_response(client_slug: str) -> str:
    """Fallback response if AI fails"""
    client = CLIENTS.get(client_slug, {})
    name = client.get("name", "our team")
    handoff = client.get("handoff_primary", "our team")

    fallbacks = {
        "j3": f"Thanks for reaching out! Giovanny from J3 will contact you shortly to discuss your project and provide a free quote.",
        "antonio": f"Thank you for your interest! Carlos will review your options and reach out to discuss the best solution for you.",
        "will": f"Great to hear from you! Carlos will be in touch soon to help with your real estate needs."
    }

    return fallbacks.get(client_slug, f"Thanks for reaching out! Someone from {name} will contact you shortly.")


# ═══════════════════════════════════════════════════════════════════════
# LEAD MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/hot")
async def get_hot_leads(limit: int = Query(20, le=100)):
    """Get leads needing immediate attention (across ALL clients)"""
    engine = get_engine()
    leads = engine.get_hot_leads(limit)
    return {"count": len(leads), "leads": leads}


@router.get("/client/{client_slug}")
async def get_client_leads(client_slug: str, limit: int = Query(50, le=200)):
    """Get all leads for a specific client"""
    engine = get_engine()

    if client_slug not in CLIENTS:
        raise HTTPException(status_code=404, detail=f"Unknown client: {client_slug}")

    leads = engine.get_by_client(client_slug, limit)
    return {
        "client": client_slug,
        "count": len(leads),
        "leads": leads
    }


@router.get("/lead/{lead_id}")
async def get_lead_detail(lead_id: str):
    """Get single lead with full details and interactions"""
    engine = get_engine()

    lead = engine.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    interactions = engine.get_interactions(lead_id)

    return {
        "lead": lead,
        "interactions": interactions
    }


@router.patch("/lead/{lead_id}/status")
async def update_lead_status(lead_id: str, data: StatusUpdate):
    """Update lead status"""
    engine = get_engine()

    try:
        status = LeadStatus(data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {data.status}")

    success = engine.update_status(lead_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {"status": "updated", "lead_id": lead_id, "new_status": data.status}


@router.post("/lead/{lead_id}/handoff")
async def handoff_lead(lead_id: str, data: HandoffRequest, background: BackgroundTasks):
    """Hand off lead to human (Carlos/Giovanny)"""
    engine = get_engine()

    success = engine.assign_human(lead_id, data.human)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Notify the human
    lead = engine.get_lead(lead_id)
    if lead:
        background.add_task(send_handoff_notification, lead, data.human)

    return {"status": "handed_off", "lead_id": lead_id, "assigned_to": data.human}


# ═══════════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/stats")
async def get_all_stats():
    """Get lead statistics for all clients"""
    engine = get_engine()

    stats = {"total": engine.get_stats(), "by_client": {}}

    for client_slug in CLIENTS:
        if CLIENTS[client_slug].get("status") != "paused":
            stats["by_client"][client_slug] = engine.get_stats(client_slug)

    return stats


@router.get("/stats/{client_slug}")
async def get_client_stats(client_slug: str):
    """Get lead statistics for specific client"""
    engine = get_engine()

    if client_slug not in CLIENTS:
        raise HTTPException(status_code=404, detail=f"Unknown client: {client_slug}")

    return engine.get_stats(client_slug)


# ═══════════════════════════════════════════════════════════════════════
# WIDGET ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/widget/{client_slug}", response_class=HTMLResponse)
async def get_widget(client_slug: str):
    """Serve embeddable widget for client website"""
    widget_dir = os.path.join(os.path.dirname(__file__), "widgets")

    # Try client-specific widget first
    client_widget = os.path.join(widget_dir, f"{client_slug}_widget.html")
    if os.path.exists(client_widget):
        with open(client_widget, "r") as f:
            return HTMLResponse(content=f.read())

    # Fall back to generic widget
    generic_widget = os.path.join(widget_dir, "generic_widget.html")
    if os.path.exists(generic_widget):
        with open(generic_widget, "r") as f:
            return HTMLResponse(content=f.read())

    return HTMLResponse(content="<p>Widget not found</p>", status_code=404)


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the lead management dashboard"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")

    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            return HTMLResponse(content=f.read())

    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


# ═══════════════════════════════════════════════════════════════════════
# BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════════════

async def engage_lead(lead_id: str, client_slug: str):
    """Background task: Baby sends initial engagement"""
    # TODO: Integrate with n8n for email/SMS automation
    client = CLIENTS.get(client_slug, {})
    baby = client.get("baby", "HERMES")

    engine = get_engine()
    engine.update_status(lead_id, LeadStatus.BABY_ENGAGED)
    engine.log_interaction(
        lead_id, "system", "outbound",
        f"{baby} assigned and ready to engage",
        baby=baby
    )


async def notify_human(lead: dict, client: dict):
    """Background task: Alert Carlos/Giovanny of hot lead"""
    # TODO: Send SMS via Twilio or n8n
    human = client.get("handoff_primary", "carlos")
    print(f"🚨 HOT LEAD ALERT for {human}: {lead.get('name')} - {client.get('name')}")


async def send_handoff_notification(lead: dict, human: str):
    """Background task: Notify human of handoff"""
    # TODO: Send SMS/notification
    print(f"📞 HANDOFF: {lead.get('name')} assigned to {human}")


# ═══════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """Lead system health check"""
    engine = get_engine()
    stats = engine.get_stats()

    return {
        "status": "operational",
        "service": "SCORPION Lead Engine",
        "version": "1.0.0",
        "total_leads": stats.get("total", 0),
        "active_clients": len([c for c in CLIENTS.values() if c.get("status") != "paused"]),
        "timestamp": datetime.now().isoformat()
    }
