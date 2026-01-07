"""
CHIRON BPO CORE - Business Process Outsourcing Engine
Military-grade performance tracking and operations management

⚔️ CHIRON - The wise centaur who trained heroes
"""

from __future__ import annotations
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import os


# ═══════════════════════════════════════════════════════════════════════
# ENUMS - Status and Type Definitions
# ═══════════════════════════════════════════════════════════════════════

class AgentStatus(Enum):
    """Agent availability states"""
    AVAILABLE = "available"
    ON_CALL = "on_call"
    WRAP = "wrap"
    BREAK = "break"
    TRAINING = "training"
    OFFLINE = "offline"


class AgentRole(Enum):
    """Agent roles in the call center"""
    COORDINATOR = "coordinator"
    SUPERVISOR = "supervisor"
    QA = "qa"
    TRAINER = "trainer"
    ADMIN = "admin"


class CampaignType(Enum):
    """Campaign operation modes"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BLENDED = "blended"


class CallState(Enum):
    """Call lifecycle states"""
    RINGING = "ringing"
    CONNECTED = "connected"
    HOLD = "hold"
    WRAP = "wrap"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# ═══════════════════════════════════════════════════════════════════════
# DATA CLASSES - Core Entities
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class AgentMetrics:
    """Real-time performance metrics for a single agent"""
    calls_today: int = 0
    talk_time: int = 0      # seconds
    hold_time: int = 0      # seconds
    wrap_time: int = 0      # seconds
    appointments: int = 0
    conversions: int = 0
    quality_score: float = 0.0
    points: int = 0

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion percentage"""
        if self.calls_today == 0:
            return 0.0
        return round((self.appointments / self.calls_today) * 100, 1)

    @property
    def aht(self) -> int:
        """Average Handle Time in seconds"""
        if self.calls_today == 0:
            return 0
        total = self.talk_time + self.hold_time + self.wrap_time
        return total // self.calls_today

    @property
    def aht_formatted(self) -> str:
        """AHT as MM:SS string"""
        seconds = self.aht
        return f"{seconds // 60}:{seconds % 60:02d}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "calls_today": self.calls_today,
            "talk_time": self.talk_time,
            "hold_time": self.hold_time,
            "wrap_time": self.wrap_time,
            "appointments": self.appointments,
            "conversions": self.conversions,
            "quality_score": self.quality_score,
            "points": self.points,
            "conversion_rate": self.conversion_rate,
            "aht": self.aht,
            "aht_formatted": self.aht_formatted
        }


@dataclass
class BPOAgent:
    """Single agent/coordinator in the system"""
    id: str
    name: str
    role: AgentRole
    shift: str
    campaign_id: Optional[str] = None
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    status: AgentStatus = AgentStatus.OFFLINE
    clock_in_time: Optional[datetime] = None
    current_call_id: Optional[str] = None

    def clock_in(self) -> None:
        """Start agent shift"""
        self.status = AgentStatus.AVAILABLE
        self.clock_in_time = datetime.now()
        self.metrics = AgentMetrics()  # Reset daily metrics

    def clock_out(self) -> None:
        """End agent shift"""
        self.status = AgentStatus.OFFLINE
        self.clock_in_time = None
        self.current_call_id = None

    def start_call(self, call_id: str) -> None:
        """Begin handling a call"""
        self.status = AgentStatus.ON_CALL
        self.current_call_id = call_id

    def end_call(self) -> None:
        """Finish handling a call"""
        self.status = AgentStatus.WRAP
        self.current_call_id = None

    def go_available(self) -> None:
        """Return to available status"""
        self.status = AgentStatus.AVAILABLE

    def take_break(self) -> None:
        """Go on break"""
        self.status = AgentStatus.BREAK

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "shift": self.shift,
            "campaign_id": self.campaign_id,
            "status": self.status.value,
            "clock_in_time": self.clock_in_time.isoformat() if self.clock_in_time else None,
            "current_call_id": self.current_call_id,
            "metrics": self.metrics.to_dict()
        }


@dataclass
class Call:
    """Active or completed call record"""
    id: str
    agent_id: str
    lead_id: str
    campaign_id: str
    state: CallState = CallState.RINGING
    start_time: datetime = field(default_factory=datetime.now)
    connect_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    talk_duration: int = 0
    hold_duration: int = 0
    wrap_duration: int = 0
    disposition: Optional[str] = None
    notes: str = ""

    def connect(self) -> None:
        """Call connected to customer"""
        self.state = CallState.CONNECTED
        self.connect_time = datetime.now()

    def put_on_hold(self) -> None:
        """Put call on hold"""
        self.state = CallState.HOLD

    def resume(self) -> None:
        """Resume from hold"""
        self.state = CallState.CONNECTED

    def complete(self, disposition: str, notes: str = "") -> None:
        """End the call"""
        self.state = CallState.COMPLETED
        self.end_time = datetime.now()
        self.disposition = disposition
        self.notes = notes

        if self.connect_time:
            total_seconds = (self.end_time - self.connect_time).total_seconds()
            self.talk_duration = int(total_seconds - self.hold_duration)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "lead_id": self.lead_id,
            "campaign_id": self.campaign_id,
            "state": self.state.value,
            "start_time": self.start_time.isoformat(),
            "connect_time": self.connect_time.isoformat() if self.connect_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "talk_duration": self.talk_duration,
            "hold_duration": self.hold_duration,
            "wrap_duration": self.wrap_duration,
            "disposition": self.disposition,
            "notes": self.notes
        }


@dataclass
class QueuedLead:
    """Lead waiting in queue"""
    id: str
    name: str
    phone: str
    campaign_id: str
    priority: int = 0
    entered_queue: datetime = field(default_factory=datetime.now)

    @property
    def wait_time(self) -> int:
        """Wait time in seconds"""
        return int((datetime.now() - self.entered_queue).total_seconds())

    @property
    def wait_time_formatted(self) -> str:
        """Wait time as M:SS"""
        seconds = self.wait_time
        return f"{seconds // 60}:{seconds % 60:02d}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "campaign_id": self.campaign_id,
            "priority": self.priority,
            "wait_time": self.wait_time,
            "wait_time_formatted": self.wait_time_formatted
        }


@dataclass
class Campaign:
    """Call campaign/account configuration"""
    id: str
    name: str
    client: str
    campaign_type: CampaignType
    script_id: Optional[str] = None
    disposition_codes: List[str] = field(default_factory=list)
    sla_targets: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "client": self.client,
            "campaign_type": self.campaign_type.value,
            "script_id": self.script_id,
            "disposition_codes": self.disposition_codes,
            "sla_targets": self.sla_targets,
            "active": self.active
        }


# ═══════════════════════════════════════════════════════════════════════
# BPO ENGINE - Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════

class BPOEngine:
    """
    Main orchestrator for BPO operations
    Handles agents, calls, queues, and real-time metrics
    """

    def __init__(self, db_path: str = "bpo_data.db"):
        self.db_path = db_path
        self.agents: Dict[str, BPOAgent] = {}
        self.campaigns: Dict[str, Campaign] = {}
        self.active_calls: Dict[str, Call] = {}
        self.queue: List[QueuedLead] = []
        self._init_db()
        self._load_demo_data()

    def _init_db(self) -> None:
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_log (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                lead_id TEXT,
                campaign_id TEXT,
                start_time TEXT,
                end_time TEXT,
                talk_duration INTEGER,
                hold_duration INTEGER,
                disposition TEXT,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_daily (
                agent_id TEXT,
                date TEXT,
                calls INTEGER,
                appointments INTEGER,
                talk_time INTEGER,
                points INTEGER,
                PRIMARY KEY (agent_id, date)
            )
        """)

        conn.commit()
        conn.close()

    def _load_demo_data(self) -> None:
        """Load demo agents and campaigns"""
        # NSIPA Campaign
        self.campaigns["nsipa"] = Campaign(
            id="nsipa",
            name="NSIPA Healthcare",
            client="IPC Solutions",
            campaign_type=CampaignType.OUTBOUND,
            script_id="nsipa_wellness",
            sla_targets={"answer_time": 30, "abandon_rate": 5, "conversion": 15}
        )

        # Demo Agents (Carlos's team)
        demo_agents = [
            ("carlos_b", "Carlos Barahona", AgentRole.COORDINATOR, "AM"),
            ("denisse_d", "Denisse Diaz", AgentRole.COORDINATOR, "AM"),
            ("gerson_c", "Gerson Castro", AgentRole.COORDINATOR, "AM"),
            ("edvaldo_e", "Edvaldo Espinoza", AgentRole.COORDINATOR, "PM"),
            ("ana_m", "Ana Mejia", AgentRole.COORDINATOR, "PM"),
            ("teresa_t", "Teresa Tovar", AgentRole.COORDINATOR, "PM"),
        ]

        for agent_id, name, role, shift in demo_agents:
            self.agents[agent_id] = BPOAgent(
                id=agent_id,
                name=name,
                role=role,
                shift=shift,
                campaign_id="nsipa"
            )

        # Set demo metrics
        self._set_demo_metrics()

    def _set_demo_metrics(self) -> None:
        """Set realistic demo metrics"""
        demo_metrics = {
            "carlos_b": {"calls": 38, "appts": 9, "quality": 98, "status": AgentStatus.ON_CALL},
            "denisse_d": {"calls": 32, "appts": 4, "quality": 92, "status": AgentStatus.WRAP},
            "gerson_c": {"calls": 28, "appts": 5, "quality": 95, "status": AgentStatus.BREAK},
            "edvaldo_e": {"calls": 25, "appts": 2, "quality": 88, "status": AgentStatus.AVAILABLE},
            "ana_m": {"calls": 30, "appts": 6, "quality": 94, "status": AgentStatus.ON_CALL},
            "teresa_t": {"calls": 0, "appts": 0, "quality": 0, "status": AgentStatus.OFFLINE},
        }

        for agent_id, data in demo_metrics.items():
            agent = self.agents[agent_id]
            agent.status = data["status"]
            agent.metrics.calls_today = data["calls"]
            agent.metrics.appointments = data["appts"]
            agent.metrics.quality_score = data["quality"]
            agent.metrics.talk_time = data["calls"] * 180  # ~3min avg
            agent.metrics.wrap_time = data["calls"] * 45   # ~45sec wrap
            if agent.status != AgentStatus.OFFLINE:
                agent.clock_in_time = datetime.now() - timedelta(hours=4)

        # Demo queue
        self.queue = [
            QueuedLead("lead_1", "Maria Garcia", "(555) 123-4567", "nsipa", 1,
                      datetime.now() - timedelta(seconds=45)),
            QueuedLead("lead_2", "Robert Smith", "(555) 234-5678", "nsipa", 0,
                      datetime.now() - timedelta(seconds=32)),
            QueuedLead("lead_3", "John Davis", "(555) 345-6789", "nsipa", 0,
                      datetime.now() - timedelta(seconds=15)),
        ]

    # ─────────────────────────────────────────────────────────────────
    # AGENT MANAGEMENT
    # ─────────────────────────────────────────────────────────────────

    def clock_in(self, agent_id: str) -> bool:
        """Agent starts shift"""
        if agent_id not in self.agents:
            return False
        self.agents[agent_id].clock_in()
        return True

    def clock_out(self, agent_id: str) -> bool:
        """Agent ends shift"""
        if agent_id not in self.agents:
            return False
        self.agents[agent_id].clock_out()
        return True

    def set_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        if agent_id not in self.agents:
            return False
        self.agents[agent_id].status = status
        return True

    def get_agent(self, agent_id: str) -> Optional[BPOAgent]:
        """Get single agent"""
        return self.agents.get(agent_id)

    def get_all_agents(self, campaign_id: Optional[str] = None) -> List[BPOAgent]:
        """Get all agents, optionally filtered by campaign"""
        agents = list(self.agents.values())
        if campaign_id:
            agents = [a for a in agents if a.campaign_id == campaign_id]
        return agents

    # ─────────────────────────────────────────────────────────────────
    # CALL MANAGEMENT
    # ─────────────────────────────────────────────────────────────────

    def start_call(self, agent_id: str, lead_id: str, campaign_id: str) -> Optional[Call]:
        """Begin call tracking"""
        if agent_id not in self.agents:
            return None

        call_id = f"call_{datetime.now().strftime('%Y%m%d%H%M%S')}_{agent_id}"
        call = Call(
            id=call_id,
            agent_id=agent_id,
            lead_id=lead_id,
            campaign_id=campaign_id
        )
        call.connect()

        self.active_calls[call_id] = call
        self.agents[agent_id].start_call(call_id)
        self.agents[agent_id].metrics.calls_today += 1

        return call

    def end_call(self, call_id: str, disposition: str, notes: str = "") -> bool:
        """End call with disposition"""
        if call_id not in self.active_calls:
            return False

        call = self.active_calls[call_id]
        call.complete(disposition, notes)

        # Update agent metrics
        agent = self.agents.get(call.agent_id)
        if agent:
            agent.end_call()
            agent.metrics.talk_time += call.talk_duration
            agent.metrics.hold_time += call.hold_duration

            # Check if appointment was set
            if disposition in ["APT_SET", "TRANSFER"]:
                agent.metrics.appointments += 1

        # Log to database
        self._log_call(call)

        # Remove from active calls
        del self.active_calls[call_id]

        return True

    def _log_call(self, call: Call) -> None:
        """Save call to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO call_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            call.id, call.agent_id, call.lead_id, call.campaign_id,
            call.start_time.isoformat(), call.end_time.isoformat() if call.end_time else None,
            call.talk_duration, call.hold_duration, call.disposition, call.notes
        ))
        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────────────────────────
    # QUEUE MANAGEMENT
    # ─────────────────────────────────────────────────────────────────

    def add_to_queue(self, lead: QueuedLead) -> None:
        """Add lead to queue"""
        self.queue.append(lead)
        self.queue.sort(key=lambda x: (-x.priority, x.entered_queue))

    def get_next_from_queue(self) -> Optional[QueuedLead]:
        """Get next lead from queue"""
        if not self.queue:
            return None
        return self.queue.pop(0)

    def get_queue_status(self) -> Dict[str, Any]:
        """Current queue depth and wait times"""
        if not self.queue:
            return {"depth": 0, "avg_wait": 0, "longest_wait": 0, "leads": []}

        wait_times = [lead.wait_time for lead in self.queue]
        return {
            "depth": len(self.queue),
            "avg_wait": sum(wait_times) // len(wait_times),
            "longest_wait": max(wait_times),
            "leads": [lead.to_dict() for lead in self.queue]
        }

    # ─────────────────────────────────────────────────────────────────
    # ANALYTICS
    # ─────────────────────────────────────────────────────────────────

    def get_leaderboard(self, campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Real-time performance ranking"""
        agents = self.get_all_agents(campaign_id)

        # Sort by appointments (primary), then conversion rate
        ranked = sorted(
            agents,
            key=lambda a: (a.metrics.appointments, a.metrics.conversion_rate),
            reverse=True
        )

        return [
            {
                "rank": i + 1,
                "agent": a.to_dict()
            }
            for i, a in enumerate(ranked)
        ]

    def get_realtime_stats(self, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """Dashboard real-time statistics"""
        agents = self.get_all_agents(campaign_id)
        online_agents = [a for a in agents if a.status != AgentStatus.OFFLINE]

        total_calls = sum(a.metrics.calls_today for a in agents)
        total_appts = sum(a.metrics.appointments for a in agents)

        return {
            "agents_total": len(agents),
            "agents_online": len(online_agents),
            "agents_on_call": len([a for a in agents if a.status == AgentStatus.ON_CALL]),
            "calls_today": total_calls,
            "appointments_today": total_appts,
            "conversion_rate": round((total_appts / total_calls * 100), 1) if total_calls > 0 else 0,
            "queue_depth": len(self.queue),
            "active_calls": len(self.active_calls),
            "sla_percentage": 94.2  # Demo value
        }

    def get_hourly_stats(self, campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Hourly breakdown for charts"""
        # Demo data - in production, query from database
        hours = []
        for hour in range(8, 18):  # 8 AM to 5 PM
            hours.append({
                "hour": f"{hour}:00",
                "calls": 15 + (hour % 5) * 3,
                "appointments": 2 + (hour % 3)
            })
        return hours


# ═══════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════

_engine: Optional[BPOEngine] = None

def get_engine() -> BPOEngine:
    """Get or create BPO engine singleton"""
    global _engine
    if _engine is None:
        _engine = BPOEngine()
    return _engine
