"""
SCORPION AI - CRM Models
Data models for leads, clients, projects, invoices, and communications
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import json


class LeadStatus(str, Enum):
    """Lead pipeline stages"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class ClientTier(str, Enum):
    """Client subscription tiers"""
    STARTER = "starter"
    PRO = "pro"
    EMPIRE = "empire"


class ProjectStatus(str, Enum):
    """Project lifecycle stages"""
    PLANNING = "planning"
    ACTIVE = "active"
    REVIEW = "review"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class CommunicationType(str, Enum):
    """Types of communications"""
    EMAIL = "email"
    CALL = "call"
    CHAT = "chat"
    MEETING = "meeting"
    NOTE = "note"


class CommunicationDirection(str, Enum):
    """Direction of communication"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


@dataclass
class Lead:
    """Lead/prospect model"""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    source: str = ""  # website, chat, referral, etc.
    status: LeadStatus = LeadStatus.NEW
    score: int = 0  # 1-100 lead quality score
    notes: str = ""
    service_interest: str = ""
    tier_interest: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'source': self.source,
            'status': self.status.value if isinstance(self.status, LeadStatus) else self.status,
            'score': self.score,
            'notes': self.notes,
            'service_interest': self.service_interest,
            'tier_interest': self.tier_interest,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lead':
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            company=data.get('company', ''),
            source=data.get('source', ''),
            status=LeadStatus(data.get('status', 'new')),
            score=data.get('score', 0),
            notes=data.get('notes', ''),
            service_interest=data.get('service_interest', ''),
            tier_interest=data.get('tier_interest', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


@dataclass
class Client:
    """Client/customer model"""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    tier: ClientTier = ClientTier.STARTER
    start_date: Optional[datetime] = None
    monthly_rate: float = 100.0
    months_paid: int = 0
    balance_paid: float = 0.0
    baby_assigned: str = ""  # AI assistant name
    notes: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def ownership_percent(self) -> float:
        """Calculate ownership percentage based on payments"""
        return min((self.months_paid / 12) * 100, 100)

    @property
    def is_owned(self) -> bool:
        """Check if client fully owns their system"""
        return self.months_paid >= 12

    @property
    def remaining_months(self) -> int:
        """Months remaining until ownership"""
        return max(12 - self.months_paid, 0)

    @property
    def total_value(self) -> float:
        """Total cost for full ownership"""
        return self.monthly_rate * 12

    @property
    def remaining_balance(self) -> float:
        """Remaining balance to ownership"""
        return max(self.total_value - self.balance_paid, 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'tier': self.tier.value if isinstance(self.tier, ClientTier) else self.tier,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'monthly_rate': self.monthly_rate,
            'months_paid': self.months_paid,
            'balance_paid': self.balance_paid,
            'baby_assigned': self.baby_assigned,
            'notes': self.notes,
            'is_active': self.is_active,
            'ownership_percent': self.ownership_percent,
            'is_owned': self.is_owned,
            'remaining_months': self.remaining_months,
            'remaining_balance': self.remaining_balance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            company=data.get('company', ''),
            tier=ClientTier(data.get('tier', 'starter')),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
            monthly_rate=data.get('monthly_rate', 100.0),
            months_paid=data.get('months_paid', 0),
            balance_paid=data.get('balance_paid', 0.0),
            baby_assigned=data.get('baby_assigned', ''),
            notes=data.get('notes', ''),
            is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


@dataclass
class Project:
    """Project model for tracking client work"""
    id: Optional[int] = None
    client_id: int = 0
    name: str = ""
    description: str = ""
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_overdue(self) -> bool:
        """Check if project is past due date"""
        if not self.due_date or self.status == ProjectStatus.COMPLETED:
            return False
        return datetime.now() > self.due_date

    @property
    def days_remaining(self) -> Optional[int]:
        """Days until due date"""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.now()
        return delta.days

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'client_id': self.client_id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value if isinstance(self.status, ProjectStatus) else self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'notes': self.notes,
            'is_overdue': self.is_overdue,
            'days_remaining': self.days_remaining,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        return cls(
            id=data.get('id'),
            client_id=data.get('client_id', 0),
            name=data.get('name', ''),
            description=data.get('description', ''),
            status=ProjectStatus(data.get('status', 'planning')),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
            completed_date=datetime.fromisoformat(data['completed_date']) if data.get('completed_date') else None,
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


@dataclass
class Invoice:
    """Invoice model for billing"""
    id: Optional[int] = None
    client_id: int = 0
    amount: float = 0.0
    description: str = ""
    status: str = "pending"  # pending, paid, overdue, cancelled
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @property
    def is_overdue(self) -> bool:
        if self.status == "paid" or not self.due_date:
            return False
        return datetime.now() > self.due_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'client_id': self.client_id,
            'amount': self.amount,
            'description': self.description,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Invoice':
        return cls(
            id=data.get('id'),
            client_id=data.get('client_id', 0),
            amount=data.get('amount', 0.0),
            description=data.get('description', ''),
            status=data.get('status', 'pending'),
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
            paid_date=datetime.fromisoformat(data['paid_date']) if data.get('paid_date') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )


@dataclass
class Communication:
    """Communication log model"""
    id: Optional[int] = None
    client_id: int = 0
    comm_type: CommunicationType = CommunicationType.NOTE
    direction: CommunicationDirection = CommunicationDirection.OUTBOUND
    subject: str = ""
    content: str = ""
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'client_id': self.client_id,
            'type': self.comm_type.value if isinstance(self.comm_type, CommunicationType) else self.comm_type,
            'direction': self.direction.value if isinstance(self.direction, CommunicationDirection) else self.direction,
            'subject': self.subject,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Communication':
        return cls(
            id=data.get('id'),
            client_id=data.get('client_id', 0),
            comm_type=CommunicationType(data.get('type', 'note')),
            direction=CommunicationDirection(data.get('direction', 'outbound')),
            subject=data.get('subject', ''),
            content=data.get('content', ''),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None
        )
