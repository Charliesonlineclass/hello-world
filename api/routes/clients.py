"""
SCORPION AI - Clients API Routes
Handle client management endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crm.clients import ClientManager
from crm.projects import ProjectManager
from crm.communications import CommunicationManager
from crm.models import ClientTier, ProjectStatus, CommunicationType, CommunicationDirection

router = APIRouter()
client_manager = ClientManager()
project_manager = ProjectManager()
comm_manager = CommunicationManager()


class ClientCreate(BaseModel):
    """Schema for creating a client"""
    name: str
    email: EmailStr
    phone: Optional[str] = ""
    company: Optional[str] = ""
    tier: Optional[str] = "starter"
    notes: Optional[str] = ""


class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    tier: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectCreate(BaseModel):
    """Schema for creating a project"""
    name: str
    description: Optional[str] = ""
    status: Optional[str] = "planning"
    due_date: Optional[str] = None
    notes: Optional[str] = ""


class BabyAssign(BaseModel):
    """Schema for assigning an AI baby"""
    baby_name: str


class PaymentRecord(BaseModel):
    """Schema for recording a payment"""
    amount: Optional[float] = None


class CommunicationLog(BaseModel):
    """Schema for logging a communication"""
    type: str  # email, call, chat, meeting, note
    direction: Optional[str] = "outbound"
    subject: Optional[str] = ""
    content: str


@router.get("")
async def list_clients(
    tier: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_owned: Optional[bool] = None,
    search: Optional[str] = None,
    limit: Optional[int] = 100
):
    """List all clients with optional filters"""
    filters = {}
    if tier:
        filters['tier'] = tier
    if is_active is not None:
        filters['is_active'] = is_active
    if is_owned is not None:
        filters['is_owned'] = is_owned
    if search:
        filters['search'] = search
    if limit:
        filters['limit'] = limit

    clients = client_manager.list_clients(filters if filters else None)
    return {
        "clients": [client.to_dict() for client in clients],
        "count": len(clients)
    }


@router.post("")
async def create_client(client: ClientCreate):
    """Create a new client"""
    try:
        data = client.model_dump()
        new_client = client_manager.create_client(data)
        return {
            "success": True,
            "message": "Client created",
            "client": new_client.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
async def get_client_stats():
    """Get client statistics"""
    stats = client_manager.get_client_stats()
    return stats


@router.get("/{client_id}")
async def get_client(client_id: int):
    """Get a specific client"""
    client = client_manager.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client.to_dict()


@router.put("/{client_id}")
async def update_client(client_id: int, client: ClientUpdate):
    """Update a client"""
    data = {k: v for k, v in client.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No update data provided")

    updated = client_manager.update_client(client_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Client not found")
    return updated.to_dict()


@router.get("/{client_id}/projects")
async def get_client_projects(client_id: int):
    """Get projects for a client"""
    client = client_manager.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    projects = client_manager.get_client_projects(client_id)
    return {
        "client_id": client_id,
        "projects": [project.to_dict() for project in projects],
        "count": len(projects)
    }


@router.post("/{client_id}/projects")
async def create_project(client_id: int, project: ProjectCreate):
    """Create a project for a client"""
    client = client_manager.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    data = project.model_dump()
    new_project = project_manager.create_project(client_id, data)
    return {
        "success": True,
        "message": "Project created",
        "project": new_project.to_dict()
    }


@router.get("/{client_id}/communications")
async def get_client_communications(client_id: int, limit: int = 50):
    """Get communications for a client"""
    client = client_manager.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    comms = client_manager.get_client_communications(client_id, limit)
    return {
        "client_id": client_id,
        "communications": [comm.to_dict() for comm in comms],
        "count": len(comms)
    }


@router.post("/{client_id}/communications")
async def log_communication(client_id: int, comm: CommunicationLog):
    """Log a communication for a client"""
    client = client_manager.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    try:
        comm_type = CommunicationType(comm.type)
        direction = CommunicationDirection(comm.direction)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid communication type or direction")

    new_comm = comm_manager.log_communication(
        client_id=client_id,
        comm_type=comm_type,
        content=comm.content,
        direction=direction,
        subject=comm.subject
    )
    return {
        "success": True,
        "message": "Communication logged",
        "communication": new_comm.to_dict()
    }


@router.get("/{client_id}/ownership")
async def get_ownership_status(client_id: int):
    """Get ownership status for a client"""
    status = client_manager.check_ownership_status(client_id)
    if not status:
        raise HTTPException(status_code=404, detail="Client not found")
    return status


@router.post("/{client_id}/baby")
async def assign_baby(client_id: int, baby: BabyAssign):
    """Assign an AI baby to a client"""
    valid_babies = ['HERMES', 'VULCAN', 'MARCUS']
    if baby.baby_name.upper() not in valid_babies:
        raise HTTPException(status_code=400, detail=f"Invalid baby name. Choose from: {valid_babies}")

    updated = client_manager.assign_baby(client_id, baby.baby_name.upper())
    if not updated:
        raise HTTPException(status_code=404, detail="Client not found")
    return {
        "success": True,
        "message": f"Baby {baby.baby_name.upper()} assigned",
        "client": updated.to_dict()
    }


@router.post("/{client_id}/payment")
async def record_payment(client_id: int, payment: PaymentRecord):
    """Record a monthly payment"""
    updated = client_manager.record_payment(client_id, payment.amount)
    if not updated:
        raise HTTPException(status_code=404, detail="Client not found")
    return {
        "success": True,
        "message": "Payment recorded",
        "client": updated.to_dict(),
        "ownership_status": client_manager.check_ownership_status(client_id)
    }


@router.get("/{client_id}/invoices")
async def get_client_invoices(client_id: int):
    """Get invoices for a client"""
    client = client_manager.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    invoices = client_manager.get_client_invoices(client_id)
    return {
        "client_id": client_id,
        "invoices": [inv.to_dict() for inv in invoices],
        "count": len(invoices)
    }


@router.get("/{client_id}/ltv")
async def get_lifetime_value(client_id: int):
    """Get lifetime value for a client"""
    ltv = client_manager.calculate_lifetime_value(client_id)
    return {
        "client_id": client_id,
        "lifetime_value": ltv
    }
