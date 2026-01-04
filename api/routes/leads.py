"""
SCORPION AI - Leads API Routes
Handle lead management endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crm.leads import LeadManager
from crm.models import LeadStatus, ClientTier

router = APIRouter()
lead_manager = LeadManager()


class LeadCreate(BaseModel):
    """Schema for creating a lead"""
    name: str
    email: EmailStr
    phone: Optional[str] = ""
    company: Optional[str] = ""
    message: Optional[str] = ""
    source: Optional[str] = "website"
    service_interest: Optional[str] = ""
    tier_interest: Optional[str] = ""


class LeadUpdate(BaseModel):
    """Schema for updating a lead"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None
    notes: Optional[str] = None
    service_interest: Optional[str] = None
    tier_interest: Optional[str] = None


class LeadStatusUpdate(BaseModel):
    """Schema for updating lead status"""
    status: str


class LeadConvert(BaseModel):
    """Schema for converting lead to client"""
    tier: str = "starter"


@router.post("/website")
async def capture_website_lead(lead: LeadCreate):
    """Capture a lead from website contact form"""
    try:
        data = lead.model_dump()
        data['notes'] = lead.message or ""
        new_lead = lead_manager.create_lead(data)
        return {
            "success": True,
            "message": "Thank you! We'll be in touch soon.",
            "lead_id": new_lead.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chat")
async def capture_chat_lead(lead: LeadCreate):
    """Capture a lead from chat widget"""
    try:
        data = lead.model_dump()
        data['source'] = 'chat'
        new_lead = lead_manager.create_lead(data)
        return {
            "success": True,
            "message": "Thanks for sharing your info!",
            "lead_id": new_lead.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_leads(
    status: Optional[str] = None,
    source: Optional[str] = None,
    min_score: Optional[int] = None,
    search: Optional[str] = None,
    limit: Optional[int] = 100
):
    """List all leads with optional filters"""
    filters = {}
    if status:
        filters['status'] = status
    if source:
        filters['source'] = source
    if min_score:
        filters['min_score'] = min_score
    if search:
        filters['search'] = search
    if limit:
        filters['limit'] = limit

    leads = lead_manager.list_leads(filters if filters else None)
    return {
        "leads": [lead.to_dict() for lead in leads],
        "count": len(leads)
    }


@router.get("/pipeline")
async def get_pipeline():
    """Get lead pipeline statistics"""
    stats = lead_manager.get_pipeline_stats()
    return stats


@router.get("/{lead_id}")
async def get_lead(lead_id: int):
    """Get a specific lead"""
    lead = lead_manager.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead.to_dict()


@router.put("/{lead_id}")
async def update_lead(lead_id: int, lead: LeadUpdate):
    """Update a lead"""
    data = {k: v for k, v in lead.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No update data provided")

    updated = lead_manager.update_lead(lead_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Lead not found")
    return updated.to_dict()


@router.put("/{lead_id}/status")
async def change_lead_status(lead_id: int, status_update: LeadStatusUpdate):
    """Change lead status"""
    try:
        status = LeadStatus(status_update.status)
        updated = lead_manager.change_status(lead_id, status)
        if not updated:
            raise HTTPException(status_code=404, detail="Lead not found")
        return updated.to_dict()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_update.status}")


@router.post("/{lead_id}/convert")
async def convert_lead(lead_id: int, convert: LeadConvert):
    """Convert lead to client"""
    try:
        tier = ClientTier(convert.tier)
        client = lead_manager.convert_to_client(lead_id, tier)
        if not client:
            raise HTTPException(status_code=404, detail="Lead not found")
        return {
            "success": True,
            "message": "Lead converted to client",
            "client": client.to_dict()
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {convert.tier}")


@router.post("/{lead_id}/score")
async def rescore_lead(lead_id: int):
    """Recalculate lead score"""
    score = lead_manager.score_lead(lead_id)
    return {"lead_id": lead_id, "score": score}


@router.delete("/{lead_id}")
async def delete_lead(lead_id: int):
    """Delete a lead"""
    success = lead_manager.delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True, "message": "Lead deleted"}
