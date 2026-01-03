"""
SCORPION Multi-Tenant System - Joe's IPC Call Center Leg
=========================================================

This leg serves Joe's IPC (Insurance Premium Collections) call center,
specializing in lead generation and call tracking.

SCORPION Architecture Role:
- LEG: Client interface for Joe's IPC Call Center
- BABY: HERMES (tinyllama) - optimized for fast responses
- Industry: CALL_CENTER
- Owner: Master Charlie (HEAD access)

Joe's IPC specializes in:
- Outbound sales calls
- Lead qualification
- Credit repair referrals
- Agent performance tracking

This leg handles call leads, generates scripts, tracks agent performance,
and manages referrals to partner services like Credit Pros.

Author: SCORPION System
Version: 1.0.0
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import uuid
import random

from .base_leg import (
    BaseClientLeg, Industry, Lead, LeadStatus,
    RequestType, logger
)


class CallOutcome(Enum):
    """Possible outcomes for a call."""
    CONNECTED = "connected"
    VOICEMAIL = "voicemail"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    DISCONNECTED = "disconnected"
    WRONG_NUMBER = "wrong_number"
    DO_NOT_CALL = "do_not_call"
    CALLBACK_SCHEDULED = "callback_scheduled"
    SALE = "sale"
    NOT_INTERESTED = "not_interested"
    QUALIFIED = "qualified"
    REFERRED = "referred"


class LeadType(Enum):
    """Types of leads handled."""
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    REFERRAL = "referral"
    CALLBACK = "callback"
    TRANSFER = "transfer"


class AgentStatus(Enum):
    """Agent availability status."""
    AVAILABLE = "available"
    ON_CALL = "on_call"
    BREAK = "break"
    TRAINING = "training"
    OFFLINE = "offline"


@dataclass
class CallRecord:
    """Record of a single call."""
    id: str
    lead_id: str
    agent_id: str
    caller_id: str
    outcome: CallOutcome
    duration_seconds: int
    notes: str
    timestamp: datetime
    recording_url: Optional[str] = None
    disposition_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['outcome'] = self.outcome.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class Agent:
    """Call center agent."""
    id: str
    name: str
    email: str
    extension: str
    status: AgentStatus
    calls_today: int = 0
    sales_today: int = 0
    talk_time_today: int = 0  # seconds
    shift_start: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['shift_start'] = self.shift_start.isoformat() if self.shift_start else None
        return data


@dataclass
class CallScript:
    """Call script template."""
    id: str
    name: str
    lead_type: LeadType
    opening: str
    qualification_questions: List[str]
    objection_handlers: Dict[str, str]
    closing: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['lead_type'] = self.lead_type.value
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class Referral:
    """Referral to partner service."""
    id: str
    lead_id: str
    partner: str
    referral_type: str
    status: str
    commission: float
    created_at: datetime
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


class JoeLeg(BaseClientLeg):
    """
    SCORPION Leg for Joe's IPC Call Center.

    Connects to HERMES (tinyllama) for fast response generation.
    Handles call leads, scripts, agent tracking, and referrals.

    SCORPION Security:
    - All calls logged to Labienus audit system
    - Only Joe's staff can access this leg (LEG level access)
    - HEAD (Master Charlie) has full oversight
    - Call recordings access is logged
    """

    # Partner commission rates
    PARTNER_COMMISSIONS = {
        "credit_pros": 0.15,
        "insurance_partner": 0.10,
        "legal_services": 0.12,
    }

    def __init__(
        self,
        access_token: str,
        data_dir: Optional[str] = None,
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize Joe's IPC leg.

        Args:
            access_token: Authentication token
            data_dir: Data storage directory
            ollama_url: Ollama server URL
        """
        super().__init__(
            client_id="joe_ipc",
            client_name="Joe's IPC Call Center",
            baby_model="tinyllama",  # HERMES
            industry=Industry.CALL_CENTER,
            access_token=access_token,
            data_dir=data_dir,
            ollama_url=ollama_url
        )

        # Joe-specific data storage
        self._calls: Dict[str, CallRecord] = {}
        self._agents: Dict[str, Agent] = {}
        self._scripts: Dict[str, CallScript] = {}
        self._referrals: Dict[str, Referral] = {}

        # Load Joe's data
        self._load_joe_data()
        self._initialize_default_scripts()

        logger.info(f"Joe's IPC leg initialized with HERMES (tinyllama)")

    def _load_joe_data(self) -> None:
        """Load Joe-specific data from disk."""
        calls_file = self.data_dir / "calls.json"
        if calls_file.exists():
            try:
                with open(calls_file, 'r') as f:
                    data = json.load(f)
                    for call in data:
                        call['outcome'] = CallOutcome(call['outcome'])
                        call['timestamp'] = datetime.fromisoformat(call['timestamp'])
                        self._calls[call['id']] = CallRecord(**call)
            except Exception as e:
                logger.error(f"Error loading calls: {e}")

        agents_file = self.data_dir / "agents.json"
        if agents_file.exists():
            try:
                with open(agents_file, 'r') as f:
                    data = json.load(f)
                    for agent in data:
                        agent['status'] = AgentStatus(agent['status'])
                        if agent['shift_start']:
                            agent['shift_start'] = datetime.fromisoformat(agent['shift_start'])
                        self._agents[agent['id']] = Agent(**agent)
            except Exception as e:
                logger.error(f"Error loading agents: {e}")

    def _save_joe_data(self) -> None:
        """Save Joe-specific data to disk."""
        calls_file = self.data_dir / "calls.json"
        with open(calls_file, 'w') as f:
            json.dump([c.to_dict() for c in self._calls.values()], f, indent=2)

        agents_file = self.data_dir / "agents.json"
        with open(agents_file, 'w') as f:
            json.dump([a.to_dict() for a in self._agents.values()], f, indent=2)

    def _initialize_default_scripts(self) -> None:
        """Set up default call scripts."""
        if not self._scripts:
            cold_script = CallScript(
                id="script_cold_001",
                name="Cold Lead Introduction",
                lead_type=LeadType.COLD,
                opening="""Hi, this is {agent_name} calling from IPC.
I'm reaching out because you recently inquired about lowering your monthly expenses.
Do you have a quick moment?""",
                qualification_questions=[
                    "Are you currently employed?",
                    "Do you have any outstanding debts you're looking to manage?",
                    "What's your current credit situation like?",
                    "Are you the decision maker for your household finances?"
                ],
                objection_handlers={
                    "not interested": "I completely understand. Many of our happiest clients felt the same way initially. May I ask what your main concern is?",
                    "no time": "I appreciate that you're busy. When would be a better time to reach you? I only need about 5 minutes.",
                    "already have service": "That's great that you're already working on this. How satisfied are you with your current results?",
                    "how did you get my number": "You submitted an inquiry through one of our partner websites. We're following up to see how we can help."
                },
                closing="Based on what you've shared, I think we can really help you. Can I go ahead and schedule a consultation with one of our specialists?",
                created_at=datetime.now()
            )
            self._scripts[cold_script.id] = cold_script

            warm_script = CallScript(
                id="script_warm_001",
                name="Warm Lead Follow-up",
                lead_type=LeadType.WARM,
                opening="""Hi {lead_name}, this is {agent_name} from IPC.
I'm following up on the information you requested about our services.
Did you have a chance to review it?""",
                qualification_questions=[
                    "What questions do you have about what we offer?",
                    "What's your timeline for making a decision?",
                    "Have you compared us with any other services?"
                ],
                objection_handlers={
                    "still thinking": "Of course, this is an important decision. What specific concerns are you weighing?",
                    "too expensive": "I understand budget is a concern. Let me show you how this actually saves you money in the long run.",
                    "need to discuss with spouse": "Absolutely, that's smart. When can the both of you be available for a brief call?"
                },
                closing="I'd love to get you started today since we have a special offer running. Can I set up the next step for you?",
                created_at=datetime.now()
            )
            self._scripts[warm_script.id] = warm_script

    def get_industry_actions(self) -> List[str]:
        """Return Joe-specific actions."""
        return [
            "process_call_lead",
            "log_call",
            "generate_followup",
            "credit_repair_referral",
            "daily_report",
            "get_scripts",
            "track_agent_performance"
        ]

    def process_industry_request(
        self,
        action: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route Joe-specific requests."""
        handlers = {
            "process_call_lead": self.process_call_lead,
            "log_call": lambda d: self.log_call(
                d['caller_id'],
                CallOutcome(d['outcome']),
                d['duration'],
                d.get('notes', ''),
                d.get('agent_id'),
                d.get('lead_id')
            ),
            "generate_followup": lambda d: self.generate_followup(d['lead_id']),
            "credit_repair_referral": lambda d: self.credit_repair_referral(d['lead_id']),
            "daily_report": lambda d: self.daily_report(),
            "get_scripts": lambda d: self.get_scripts(LeadType(d.get('lead_type', 'cold'))),
            "track_agent_performance": lambda d: self.track_agent_performance(d['agent_id']),
        }

        handler = handlers.get(action)
        if not handler:
            return {"error": f"Unknown Joe's IPC action: {action}"}

        return handler(data)

    def process_call_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new call lead.

        Creates a lead and generates an initial call script.

        Args:
            lead_data: Lead information including:
                - name: Lead name
                - phone: Phone number
                - source: Lead source
                - lead_type: Type of lead (cold, warm, hot)
                - notes: Any initial notes

        Returns:
            Lead info with generated script
        """
        lead_id = str(uuid.uuid4())
        lead_type_str = lead_data.get('lead_type', 'cold')

        try:
            lead_type = LeadType(lead_type_str)
        except ValueError:
            lead_type = LeadType.COLD

        lead = Lead(
            id=lead_id,
            client_id=self.client_id,
            name=lead_data.get('name', 'Unknown'),
            email=lead_data.get('email', ''),
            phone=lead_data.get('phone', ''),
            status=LeadStatus.NEW,
            source=lead_data.get('source', 'direct'),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            custom_data={
                'lead_type': lead_type.value,
                'call_attempts': 0,
                'best_time_to_call': lead_data.get('best_time', 'any'),
                'initial_notes': lead_data.get('notes', '')
            }
        )

        self._leads_cache[lead_id] = lead
        self._save_data()

        # Generate personalized script using HERMES
        script = self._scripts.get(f"script_{lead_type.value}_001")
        personalized_opening = ""

        if script:
            prompt = f"""Personalize this call script opening for the lead:
Lead name: {lead.name}
Lead type: {lead_type.value}
Source: {lead.source}

Original opening: {script.opening}

Make it natural and conversational. Keep it under 50 words."""

            ai_response = self.query_baby(prompt)
            personalized_opening = ai_response.get('response', script.opening)

        self.log_activity(
            action="call_lead_processed",
            details={
                "lead_id": lead_id,
                "lead_type": lead_type.value,
                "source": lead.source
            }
        )

        return {
            "lead": lead.to_dict(),
            "script": script.to_dict() if script else None,
            "personalized_opening": personalized_opening,
            "recommended_action": f"Call within 5 minutes for {lead_type.value} lead"
        }

    def log_call(
        self,
        caller_id: str,
        outcome: CallOutcome,
        duration: int,
        notes: str,
        agent_id: Optional[str] = None,
        lead_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log a completed call.

        Args:
            caller_id: The phone number called
            outcome: Call outcome
            duration: Call duration in seconds
            notes: Agent notes
            agent_id: ID of agent who made the call
            lead_id: Associated lead ID

        Returns:
            Call record details
        """
        call_id = str(uuid.uuid4())

        call = CallRecord(
            id=call_id,
            lead_id=lead_id or "",
            agent_id=agent_id or "unknown",
            caller_id=caller_id,
            outcome=outcome,
            duration_seconds=duration,
            notes=notes,
            timestamp=datetime.now()
        )

        self._calls[call_id] = call

        # Update agent stats if agent_id provided
        if agent_id and agent_id in self._agents:
            agent = self._agents[agent_id]
            agent.calls_today += 1
            agent.talk_time_today += duration
            if outcome == CallOutcome.SALE:
                agent.sales_today += 1

        # Update lead if lead_id provided
        if lead_id and lead_id in self._leads_cache:
            lead = self._leads_cache[lead_id]
            lead.custom_data['call_attempts'] = lead.custom_data.get('call_attempts', 0) + 1
            lead.custom_data['last_call_outcome'] = outcome.value
            lead.custom_data['last_call_date'] = datetime.now().isoformat()

            # Update lead status based on outcome
            if outcome == CallOutcome.SALE:
                lead.status = LeadStatus.WON
            elif outcome == CallOutcome.QUALIFIED:
                lead.status = LeadStatus.QUALIFIED
            elif outcome == CallOutcome.CALLBACK_SCHEDULED:
                lead.status = LeadStatus.CONTACTED
            elif outcome in [CallOutcome.DO_NOT_CALL, CallOutcome.NOT_INTERESTED]:
                lead.status = LeadStatus.LOST

            lead.updated_at = datetime.now()
            self._save_data()

        self._save_joe_data()

        self.log_activity(
            action="call_logged",
            details={
                "call_id": call_id,
                "outcome": outcome.value,
                "duration": duration,
                "agent_id": agent_id
            }
        )

        return {
            "call": call.to_dict(),
            "status": "logged"
        }

    def generate_followup(self, lead_id: str) -> Dict[str, Any]:
        """
        Generate follow-up email/SMS template.

        Args:
            lead_id: Lead ID to follow up with

        Returns:
            Email and SMS templates
        """
        lead = self._leads_cache.get(lead_id)
        if not lead:
            return {"error": f"Lead {lead_id} not found"}

        last_outcome = lead.custom_data.get('last_call_outcome', 'unknown')
        call_attempts = lead.custom_data.get('call_attempts', 0)

        # Generate email template using HERMES
        email_prompt = f"""Generate a short follow-up email for this situation:
Customer name: {lead.name}
Last call outcome: {last_outcome}
Number of call attempts: {call_attempts}
Industry: Call center sales

Keep it under 100 words, professional but warm. Include a clear call to action."""

        email_response = self.query_baby(email_prompt)

        # Generate SMS template
        sms_prompt = f"""Generate a follow-up SMS (under 160 characters) for:
Customer: {lead.name}
Last outcome: {last_outcome}
Make it friendly but professional."""

        sms_response = self.query_baby(sms_prompt)

        self.log_activity(
            action="followup_generated",
            details={"lead_id": lead_id, "last_outcome": last_outcome}
        )

        return {
            "lead_id": lead_id,
            "email_template": email_response.get('response', ''),
            "sms_template": sms_response.get('response', ''),
            "recommended_channel": "sms" if call_attempts >= 3 else "email",
            "recommended_delay_hours": 24 if last_outcome == "voicemail" else 48
        }

    def credit_repair_referral(self, lead_id: str) -> Dict[str, Any]:
        """
        Create a referral to Credit Pros partner.

        Args:
            lead_id: Lead ID to refer

        Returns:
            Referral details and commission info
        """
        lead = self._leads_cache.get(lead_id)
        if not lead:
            return {"error": f"Lead {lead_id} not found"}

        referral_id = str(uuid.uuid4())
        commission_rate = self.PARTNER_COMMISSIONS.get("credit_pros", 0.15)

        # Estimate commission based on lead value (average credit repair sale: $500)
        estimated_sale = 500.00
        estimated_commission = estimated_sale * commission_rate

        referral = Referral(
            id=referral_id,
            lead_id=lead_id,
            partner="Credit Pros",
            referral_type="credit_repair",
            status="pending",
            commission=estimated_commission,
            created_at=datetime.now(),
            notes=f"Referred from IPC. Lead: {lead.name}"
        )

        self._referrals[referral_id] = referral

        # Update lead status
        lead.status = LeadStatus.QUALIFIED
        lead.custom_data['referral_id'] = referral_id
        lead.custom_data['referred_to'] = "Credit Pros"
        lead.updated_at = datetime.now()
        self._save_data()

        self.log_activity(
            action="credit_repair_referral",
            details={
                "referral_id": referral_id,
                "lead_id": lead_id,
                "partner": "Credit Pros",
                "estimated_commission": estimated_commission
            }
        )

        return {
            "referral": referral.to_dict(),
            "estimated_commission": estimated_commission,
            "partner_contact": {
                "company": "Credit Pros",
                "phone": "(888) 555-CREDIT",
                "email": "referrals@creditpros.example.com"
            },
            "next_steps": [
                "Credit Pros will contact lead within 24 hours",
                "Commission paid upon successful enrollment",
                "Track status in referral dashboard"
            ]
        }

    def daily_report(self) -> Dict[str, Any]:
        """
        Generate daily call center report.

        Returns:
            Calls, conversions, and revenue estimate
        """
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        # Filter today's calls
        today_calls = [
            c for c in self._calls.values()
            if today_start <= c.timestamp <= today_end
        ]

        # Calculate metrics
        total_calls = len(today_calls)
        connected_calls = len([c for c in today_calls if c.outcome == CallOutcome.CONNECTED])
        sales = len([c for c in today_calls if c.outcome == CallOutcome.SALE])
        total_talk_time = sum(c.duration_seconds for c in today_calls)

        # Outcome breakdown
        outcome_counts = {}
        for call in today_calls:
            outcome_counts[call.outcome.value] = outcome_counts.get(call.outcome.value, 0) + 1

        # Agent performance
        agent_stats = {}
        for call in today_calls:
            if call.agent_id not in agent_stats:
                agent_stats[call.agent_id] = {"calls": 0, "sales": 0, "talk_time": 0}
            agent_stats[call.agent_id]["calls"] += 1
            agent_stats[call.agent_id]["talk_time"] += call.duration_seconds
            if call.outcome == CallOutcome.SALE:
                agent_stats[call.agent_id]["sales"] += 1

        # Revenue estimate (average sale value: $150)
        avg_sale_value = 150.00
        revenue_estimate = sales * avg_sale_value

        # Referral commissions
        today_referrals = [
            r for r in self._referrals.values()
            if r.created_at.date() == today
        ]
        referral_commissions = sum(r.commission for r in today_referrals)

        report = {
            "date": today.isoformat(),
            "calls": {
                "total": total_calls,
                "connected": connected_calls,
                "connection_rate": (connected_calls / total_calls * 100) if total_calls > 0 else 0,
                "by_outcome": outcome_counts
            },
            "sales": {
                "count": sales,
                "conversion_rate": (sales / connected_calls * 100) if connected_calls > 0 else 0,
                "estimated_revenue": revenue_estimate
            },
            "talk_time": {
                "total_seconds": total_talk_time,
                "total_hours": round(total_talk_time / 3600, 2),
                "avg_per_call": round(total_talk_time / total_calls, 1) if total_calls > 0 else 0
            },
            "agents": agent_stats,
            "referrals": {
                "count": len(today_referrals),
                "estimated_commissions": referral_commissions
            },
            "total_estimated_revenue": revenue_estimate + referral_commissions
        }

        self.log_activity(
            action="daily_report_generated",
            details={"date": today.isoformat(), "total_calls": total_calls}
        )

        return report

    def get_scripts(self, lead_type: LeadType) -> Dict[str, Any]:
        """
        Get call scripts for a lead type.

        Args:
            lead_type: Type of lead

        Returns:
            Matching scripts
        """
        matching_scripts = [
            s.to_dict() for s in self._scripts.values()
            if s.lead_type == lead_type
        ]

        return {
            "lead_type": lead_type.value,
            "scripts": matching_scripts,
            "count": len(matching_scripts)
        }

    def track_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """
        Get performance stats for an agent.

        Args:
            agent_id: Agent ID to track

        Returns:
            Agent performance metrics
        """
        agent = self._agents.get(agent_id)

        # Get agent's calls from last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        agent_calls = [
            c for c in self._calls.values()
            if c.agent_id == agent_id and c.timestamp >= thirty_days_ago
        ]

        # Calculate metrics
        total_calls = len(agent_calls)
        sales = len([c for c in agent_calls if c.outcome == CallOutcome.SALE])
        connected = len([c for c in agent_calls if c.outcome == CallOutcome.CONNECTED])
        total_talk_time = sum(c.duration_seconds for c in agent_calls)

        # Daily breakdown
        daily_stats = {}
        for call in agent_calls:
            day = call.timestamp.date().isoformat()
            if day not in daily_stats:
                daily_stats[day] = {"calls": 0, "sales": 0}
            daily_stats[day]["calls"] += 1
            if call.outcome == CallOutcome.SALE:
                daily_stats[day]["sales"] += 1

        performance = {
            "agent_id": agent_id,
            "agent_info": agent.to_dict() if agent else None,
            "period": "last_30_days",
            "metrics": {
                "total_calls": total_calls,
                "total_sales": sales,
                "conversion_rate": (sales / connected * 100) if connected > 0 else 0,
                "connection_rate": (connected / total_calls * 100) if total_calls > 0 else 0,
                "total_talk_time_hours": round(total_talk_time / 3600, 2),
                "avg_calls_per_day": round(total_calls / 30, 1),
                "avg_sales_per_day": round(sales / 30, 2)
            },
            "daily_breakdown": daily_stats,
            "ranking_score": self._calculate_agent_score(total_calls, sales, total_talk_time)
        }

        self.log_activity(
            action="agent_performance_tracked",
            details={"agent_id": agent_id}
        )

        return performance

    def _calculate_agent_score(
        self,
        calls: int,
        sales: int,
        talk_time: int
    ) -> float:
        """Calculate agent performance score (0-100)."""
        # Weighted scoring:
        # - Calls: 30%
        # - Sales: 50%
        # - Talk time: 20%

        # Normalize based on expected monthly targets
        calls_target = 500  # Expected calls per month
        sales_target = 25   # Expected sales per month
        talk_target = 40 * 3600  # 40 hours per month

        calls_score = min(100, (calls / calls_target) * 100) * 0.30
        sales_score = min(100, (sales / sales_target) * 100) * 0.50
        talk_score = min(100, (talk_time / talk_target) * 100) * 0.20

        return round(calls_score + sales_score + talk_score, 1)

    def add_agent(
        self,
        name: str,
        email: str,
        extension: str
    ) -> Dict[str, Any]:
        """
        Add a new agent to the call center.

        Args:
            name: Agent name
            email: Agent email
            extension: Phone extension

        Returns:
            Created agent details
        """
        agent_id = str(uuid.uuid4())[:8]

        agent = Agent(
            id=agent_id,
            name=name,
            email=email,
            extension=extension,
            status=AgentStatus.OFFLINE,
            calls_today=0,
            sales_today=0,
            talk_time_today=0
        )

        self._agents[agent_id] = agent
        self._save_joe_data()

        self.log_activity(
            action="agent_added",
            details={"agent_id": agent_id, "name": name}
        )

        return {
            "agent": agent.to_dict(),
            "status": "created"
        }

    def set_agent_status(
        self,
        agent_id: str,
        status: AgentStatus
    ) -> Dict[str, Any]:
        """
        Update an agent's status.

        Args:
            agent_id: Agent ID
            status: New status

        Returns:
            Updated agent info
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return {"error": f"Agent {agent_id} not found"}

        old_status = agent.status
        agent.status = status

        if status == AgentStatus.AVAILABLE and not agent.shift_start:
            agent.shift_start = datetime.now()
        elif status == AgentStatus.OFFLINE:
            agent.shift_start = None

        self._save_joe_data()

        self.log_activity(
            action="agent_status_changed",
            details={
                "agent_id": agent_id,
                "old_status": old_status.value,
                "new_status": status.value
            }
        )

        return {
            "agent": agent.to_dict(),
            "status_changed": True
        }
