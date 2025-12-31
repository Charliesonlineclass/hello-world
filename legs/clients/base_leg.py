"""
Base Client Leg
===============

Abstract base class for all client leg implementations.
Provides common functionality and interface that all legs must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import json
import uuid


class Industry(Enum):
    """Supported industry types for client legs."""
    CALL_CENTER = "call_center"
    CONSTRUCTION = "construction"
    BANKING = "banking"
    REAL_ESTATE = "real_estate"
    HEALTHCARE = "healthcare"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    OTHER = "other"


class LeadStatus(Enum):
    """Status of a lead in the pipeline."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"
    NURTURING = "nurturing"


@dataclass
class Lead:
    """Represents a lead in the system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    phone: str = ""
    source: str = ""
    status: LeadStatus = LeadStatus.NEW
    score: int = 0
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert lead to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "source": self.source,
            "status": self.status.value,
            "score": self.score,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lead":
        """Create lead from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            source=data.get("source", ""),
            status=LeadStatus(data.get("status", "new")),
            score=data.get("score", 0),
            data=data.get("data", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )


@dataclass
class ClientConfig:
    """Configuration for a client leg."""
    name: str
    industry: Industry
    api_keys: Dict[str, str] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    integrations: List[str] = field(default_factory=list)
    notification_emails: List[str] = field(default_factory=list)
    notification_phones: List[str] = field(default_factory=list)


class BaseClientLeg(ABC):
    """
    Abstract base class for client legs.

    Each client leg represents a specific business client with their
    unique requirements, integrations, and workflow logic.
    """

    def __init__(self, config: ClientConfig):
        """Initialize the client leg with configuration."""
        self.config = config
        self.logger = logging.getLogger(f"scorpion.legs.{config.name}")
        self._leads: Dict[str, Lead] = {}
        self._metrics: Dict[str, int] = {
            "leads_processed": 0,
            "leads_converted": 0,
            "notifications_sent": 0,
            "errors": 0,
        }
        self._initialized = False

    @property
    @abstractmethod
    def industry(self) -> Industry:
        """Return the industry type for this leg."""
        pass

    @property
    @abstractmethod
    def services(self) -> List[str]:
        """Return list of services this leg provides."""
        pass

    def initialize(self) -> bool:
        """Initialize the leg and its integrations."""
        self.logger.info(f"Initializing {self.config.name} leg...")
        try:
            self._setup_integrations()
            self._initialized = True
            self.logger.info(f"{self.config.name} leg initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.config.name}: {e}")
            self._metrics["errors"] += 1
            return False

    def _setup_integrations(self) -> None:
        """Set up external integrations. Override in subclasses."""
        pass

    @abstractmethod
    def process_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Process an incoming lead.

        Args:
            lead: The lead to process

        Returns:
            Dict containing processing results
        """
        pass

    @abstractmethod
    def daily_report(self) -> Dict[str, Any]:
        """
        Generate daily report for this client.

        Returns:
            Dict containing report data
        """
        pass

    def add_lead(self, lead: Lead) -> str:
        """Add a lead to the internal store."""
        self._leads[lead.id] = lead
        self.logger.debug(f"Added lead {lead.id}")
        return lead.id

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Retrieve a lead by ID."""
        return self._leads.get(lead_id)

    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """Update a lead with new data."""
        if lead_id not in self._leads:
            return False

        lead = self._leads[lead_id]
        for key, value in updates.items():
            if hasattr(lead, key):
                setattr(lead, key, value)
        lead.updated_at = datetime.now()
        return True

    def get_leads_by_status(self, status: LeadStatus) -> List[Lead]:
        """Get all leads with a specific status."""
        return [l for l in self._leads.values() if l.status == status]

    def send_notification(
        self,
        message: str,
        channels: Optional[List[str]] = None
    ) -> bool:
        """
        Send notification through configured channels.

        Args:
            message: The message to send
            channels: Optional list of channels (email, sms, slack)

        Returns:
            True if notification sent successfully
        """
        channels = channels or ["email"]
        self.logger.info(f"Sending notification via {channels}: {message[:50]}...")
        self._metrics["notifications_sent"] += 1
        return True

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics for this leg."""
        return {
            "client": self.config.name,
            "industry": self.industry.value,
            "metrics": self._metrics.copy(),
            "lead_count": len(self._leads),
            "leads_by_status": {
                status.value: len(self.get_leads_by_status(status))
                for status in LeadStatus
            },
            "timestamp": datetime.now().isoformat(),
        }

    def health_check(self) -> Dict[str, Any]:
        """Check health of this leg and its integrations."""
        return {
            "client": self.config.name,
            "initialized": self._initialized,
            "integrations": self.config.integrations,
            "status": "healthy" if self._initialized else "not_initialized",
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} client='{self.config.name}'>"
