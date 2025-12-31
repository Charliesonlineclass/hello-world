"""
IPC Solutions - Call Center Operations
======================================
Complete call center management system for lead capture,
agent performance tracking, and shift scheduling.

Connects to CLAW1 pipeline for automated processing.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LeadStatus(Enum):
    """Status of a lead in the pipeline."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"
    FOLLOWUP = "followup"


class ShiftType(Enum):
    """Types of shifts."""
    MORNING = "morning"      # 6am - 2pm
    AFTERNOON = "afternoon"  # 2pm - 10pm
    NIGHT = "night"          # 10pm - 6am
    SPLIT = "split"          # Split shift


@dataclass
class Lead:
    """A sales lead."""
    id: str
    name: str
    phone: str
    email: str
    source: str
    status: LeadStatus = LeadStatus.NEW
    assigned_agent: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_contact: Optional[datetime] = None
    value: float = 0.0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "source": self.source,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "last_contact": self.last_contact.isoformat() if self.last_contact else None,
            "value": self.value,
            "tags": self.tags
        }


@dataclass
class Agent:
    """A call center agent."""
    id: str
    name: str
    email: str
    phone_ext: str
    skills: List[str] = field(default_factory=list)
    active: bool = True
    hire_date: datetime = field(default_factory=datetime.now)
    calls_today: int = 0
    conversions_today: int = 0
    total_calls: int = 0
    total_conversions: int = 0

    @property
    def conversion_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return (self.total_conversions / self.total_calls) * 100

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone_ext": self.phone_ext,
            "skills": self.skills,
            "active": self.active,
            "calls_today": self.calls_today,
            "conversions_today": self.conversions_today,
            "conversion_rate": round(self.conversion_rate, 2)
        }


@dataclass
class Shift:
    """A scheduled shift."""
    id: str
    agent_id: str
    date: datetime
    shift_type: ShiftType
    start_time: str
    end_time: str
    break_minutes: int = 30
    notes: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "date": self.date.strftime("%Y-%m-%d"),
            "shift_type": self.shift_type.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "break_minutes": self.break_minutes,
            "notes": self.notes
        }


class IPCSolutionsLeg:
    """
    IPC Solutions Call Center Management.

    Connects to CLAW1 pipeline for automated lead processing.
    """

    def __init__(self, data_dir: str = "/tmp/ipc_solutions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.leads: Dict[str, Lead] = {}
        self.agents: Dict[str, Agent] = {}
        self.shifts: List[Shift] = []
        self._load_data()

    def _load_data(self):
        """Load existing data from disk."""
        leads_file = self.data_dir / "leads.json"
        agents_file = self.data_dir / "agents.json"

        if leads_file.exists():
            with open(leads_file) as f:
                data = json.load(f)
                for lead_data in data:
                    lead_data["status"] = LeadStatus(lead_data["status"])
                    lead_data["created_at"] = datetime.fromisoformat(lead_data["created_at"])
                    if lead_data.get("last_contact"):
                        lead_data["last_contact"] = datetime.fromisoformat(lead_data["last_contact"])
                    self.leads[lead_data["id"]] = Lead(**lead_data)

        if agents_file.exists():
            with open(agents_file) as f:
                data = json.load(f)
                for agent_data in data:
                    agent_data["hire_date"] = datetime.fromisoformat(agent_data.get("hire_date", datetime.now().isoformat()))
                    self.agents[agent_data["id"]] = Agent(**agent_data)

    def _save_data(self):
        """Save data to disk."""
        with open(self.data_dir / "leads.json", "w") as f:
            json.dump([l.to_dict() for l in self.leads.values()], f, indent=2)
        with open(self.data_dir / "agents.json", "w") as f:
            json.dump([a.to_dict() for a in self.agents.values()], f, indent=2)

    def capture_lead(self, name: str, phone: str, email: str, source: str, **kwargs) -> Lead:
        """Capture a new lead."""
        lead_id = hashlib.md5(f"{phone}{email}{datetime.now()}".encode()).hexdigest()[:12]

        lead = Lead(
            id=lead_id,
            name=name,
            phone=phone,
            email=email,
            source=source,
            value=kwargs.get("value", 0.0),
            tags=kwargs.get("tags", [])
        )

        self.leads[lead_id] = lead
        self._save_data()
        logger.info(f"Lead captured: {lead_id} - {name}")
        return lead

    def assign_lead(self, lead_id: str, agent_id: str) -> bool:
        """Assign a lead to an agent."""
        if lead_id not in self.leads or agent_id not in self.agents:
            return False

        self.leads[lead_id].assigned_agent = agent_id
        self._save_data()
        return True

    def update_lead_status(self, lead_id: str, status: LeadStatus, note: str = None) -> bool:
        """Update lead status."""
        if lead_id not in self.leads:
            return False

        lead = self.leads[lead_id]
        lead.status = status
        lead.last_contact = datetime.now()
        if note:
            lead.notes.append(f"{datetime.now().isoformat()}: {note}")

        self._save_data()
        return True

    def get_agent_performance(self, agent_id: str) -> Dict:
        """Get performance metrics for an agent."""
        if agent_id not in self.agents:
            return {}

        agent = self.agents[agent_id]
        assigned_leads = [l for l in self.leads.values() if l.assigned_agent == agent_id]

        return {
            "agent": agent.to_dict(),
            "assigned_leads": len(assigned_leads),
            "converted": len([l for l in assigned_leads if l.status == LeadStatus.CONVERTED]),
            "pending": len([l for l in assigned_leads if l.status in [LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED]]),
            "total_value": sum(l.value for l in assigned_leads if l.status == LeadStatus.CONVERTED)
        }

    def schedule_shift(self, agent_id: str, date: datetime, shift_type: ShiftType) -> Shift:
        """Schedule a shift for an agent."""
        shift_times = {
            ShiftType.MORNING: ("06:00", "14:00"),
            ShiftType.AFTERNOON: ("14:00", "22:00"),
            ShiftType.NIGHT: ("22:00", "06:00"),
            ShiftType.SPLIT: ("10:00", "14:00")
        }

        start, end = shift_times[shift_type]
        shift_id = hashlib.md5(f"{agent_id}{date}{shift_type}".encode()).hexdigest()[:8]

        shift = Shift(
            id=shift_id,
            agent_id=agent_id,
            date=date,
            shift_type=shift_type,
            start_time=start,
            end_time=end
        )

        self.shifts.append(shift)
        return shift

    def get_daily_schedule(self, date: datetime = None) -> List[Dict]:
        """Get all shifts for a given day."""
        date = date or datetime.now()
        date_str = date.strftime("%Y-%m-%d")

        day_shifts = [s for s in self.shifts if s.date.strftime("%Y-%m-%d") == date_str]
        return [s.to_dict() for s in day_shifts]

    def get_dashboard(self) -> Dict:
        """Get call center dashboard data."""
        today = datetime.now().date()

        return {
            "total_leads": len(self.leads),
            "new_today": len([l for l in self.leads.values() if l.created_at.date() == today]),
            "active_agents": len([a for a in self.agents.values() if a.active]),
            "conversion_rate": self._calculate_overall_conversion(),
            "leads_by_status": self._count_by_status(),
            "top_agents": self._get_top_agents(3)
        }

    def _calculate_overall_conversion(self) -> float:
        total = len(self.leads)
        converted = len([l for l in self.leads.values() if l.status == LeadStatus.CONVERTED])
        return round((converted / total * 100) if total > 0 else 0, 2)

    def _count_by_status(self) -> Dict[str, int]:
        counts = {}
        for status in LeadStatus:
            counts[status.value] = len([l for l in self.leads.values() if l.status == status])
        return counts

    def _get_top_agents(self, n: int) -> List[Dict]:
        sorted_agents = sorted(self.agents.values(), key=lambda a: a.conversion_rate, reverse=True)
        return [a.to_dict() for a in sorted_agents[:n]]


# Convenience functions
def lead_capture(name: str, phone: str, email: str, source: str, **kwargs) -> Lead:
    """Quick lead capture."""
    leg = IPCSolutionsLeg()
    return leg.capture_lead(name, phone, email, source, **kwargs)


def agent_performance(agent_id: str) -> Dict:
    """Get agent performance."""
    leg = IPCSolutionsLeg()
    return leg.get_agent_performance(agent_id)


def shift_scheduler(agent_id: str, date: datetime, shift_type: str) -> Shift:
    """Schedule a shift."""
    leg = IPCSolutionsLeg()
    return leg.schedule_shift(agent_id, date, ShiftType(shift_type))


if __name__ == "__main__":
    # Demo
    leg = IPCSolutionsLeg()

    # Add an agent
    agent = Agent(id="A001", name="John Smith", email="john@ipc.com", phone_ext="101")
    leg.agents["A001"] = agent

    # Capture a lead
    lead = leg.capture_lead("Jane Doe", "555-1234", "jane@email.com", "website", value=500)
    print(f"Lead captured: {lead.id}")

    # Assign to agent
    leg.assign_lead(lead.id, "A001")

    # Get dashboard
    print("\nDashboard:")
    print(json.dumps(leg.get_dashboard(), indent=2))
