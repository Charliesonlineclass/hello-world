"""
SCORPION Multi-Tenant System - Base Client Leg
===============================================

In the SCORPION architecture, a "Leg" represents a client's dedicated interface
to the system. Each leg is assigned a specific "Baby" (Ollama AI model) and
provides industry-specific functionality.

Architecture Overview:
- HEAD (Master Charlie) oversees all operations
- BODY (Core systems) processes requests
- LEGS (Client interfaces) - this module - handle client-specific logic
- TAIL (Security/Labienus) controls access and audit
- BABIES (Ollama models) provide AI responses

Each client gets exactly ONE leg, connected to ONE baby, with isolated data.
The leg acts as an API between the client and their assigned AI assistant.

Author: SCORPION System
Version: 1.0.0
"""

import os
import json
import hashlib
import requests
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import uuid
import logging

# Configure logging for the legs module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scorpion.legs")


class Industry(Enum):
    """
    Supported industry types for SCORPION clients.
    Each industry has specific workflows and terminology.
    """
    CALL_CENTER = "call_center"
    BANKING = "banking"
    CONSTRUCTION = "construction"
    ROOFING = "roofing"
    REAL_ESTATE = "real_estate"
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    INSURANCE = "insurance"


class LeadStatus(Enum):
    """Standard lead statuses across all legs."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATING = "negotiating"
    WON = "won"
    LOST = "lost"
    NURTURING = "nurturing"
    UNRESPONSIVE = "unresponsive"


class RequestType(Enum):
    """Types of requests a leg can process."""
    QUERY = "query"
    LEAD_CREATE = "lead_create"
    LEAD_UPDATE = "lead_update"
    LEAD_GET = "lead_get"
    REPORT = "report"
    EXPORT = "export"
    SCHEDULE = "schedule"
    NOTIFY = "notify"
    ANALYZE = "analyze"


@dataclass
class Lead:
    """
    Universal lead structure used across all SCORPION legs.
    Industry-specific fields stored in 'custom_data'.
    """
    id: str
    client_id: str
    name: str
    email: str
    phone: str
    status: LeadStatus
    source: str
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    value: float = 0.0
    priority: int = 5  # 1-10, 10 highest

    def to_dict(self) -> Dict[str, Any]:
        """Convert lead to dictionary for serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lead':
        """Create Lead from dictionary."""
        data['status'] = LeadStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class ActivityLog:
    """Record of an action taken on a leg."""
    id: str
    client_id: str
    user_id: str
    action: str
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ClientStats:
    """Statistics for a client over a date range."""
    client_id: str
    start_date: datetime
    end_date: datetime
    total_leads: int
    new_leads: int
    converted_leads: int
    total_value: float
    ai_queries: int
    conversion_rate: float
    avg_response_time: float  # seconds
    top_sources: List[Tuple[str, int]] = field(default_factory=list)


class OllamaConnection:
    """
    Manages connection to Ollama for AI queries.
    Each leg uses this to communicate with its assigned baby.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama connection.

        Args:
            base_url: Ollama server URL (default localhost)
        """
        self.base_url = base_url
        self.timeout = 60

    def query(self, model: str, prompt: str, system_prompt: Optional[str] = None,
              temperature: float = 0.7, max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Send a query to an Ollama model (baby).

        Args:
            model: The model name (e.g., 'tinyllama', 'phi3:mini')
            prompt: User prompt to send
            system_prompt: Optional system context
            temperature: Creativity level (0-1)
            max_tokens: Maximum response length

        Returns:
            Dict with 'response', 'model', 'duration', 'success'
        """
        endpoint = f"{self.base_url}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            return {
                "success": True,
                "response": result.get("response", ""),
                "model": model,
                "duration": result.get("total_duration", 0) / 1e9,  # Convert to seconds
                "tokens_generated": result.get("eval_count", 0)
            }

        except requests.exceptions.Timeout:
            logger.error(f"Ollama query timeout for model {model}")
            return {
                "success": False,
                "response": "Query timed out. Please try again.",
                "model": model,
                "duration": 0,
                "error": "timeout"
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            return {
                "success": False,
                "response": "AI service unavailable.",
                "model": model,
                "duration": 0,
                "error": "connection_failed"
            }
        except Exception as e:
            logger.error(f"Ollama query error: {str(e)}")
            return {
                "success": False,
                "response": f"Query failed: {str(e)}",
                "model": model,
                "duration": 0,
                "error": str(e)
            }

    def check_model_available(self, model: str) -> bool:
        """Check if a model is available in Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.ok:
                models = response.json().get("models", [])
                return any(m.get("name", "").startswith(model) for m in models)
        except:
            pass
        return False


class BaseClientLeg(ABC):
    """
    Base class for all SCORPION client legs.

    A leg provides the interface between a client and the SCORPION system.
    Each leg is assigned a specific Ollama "baby" model for AI queries.

    SCORPION Architecture Role:
    - Legs are the "limbs" that reach out to serve individual clients
    - Each leg is isolated - clients cannot see other clients' data
    - All actions are logged for audit by Labienus (tail security)
    - HEAD (Master Charlie) can access all legs

    Subclasses must implement industry-specific methods.
    """

    # Baby model assignments (Ollama model names)
    BABIES = {
        "HERMES": "tinyllama",      # Fast, good for communication
        "MARCUS": "qwen2.5:7b",     # Deep analysis, banking/finance
        "VULCAN": "phi3:mini",      # Building/patterns, construction
        "APOLLO": "mistral:7b",     # General purpose
        "ATHENA": "llama3.2:3b",    # Strategy and planning
    }

    def __init__(
        self,
        client_id: str,
        client_name: str,
        baby_model: str,
        industry: Industry,
        access_token: str,
        data_dir: Optional[str] = None,
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize a client leg.

        Args:
            client_id: Unique identifier for this client
            client_name: Human-readable client name
            baby_model: Ollama model name for AI queries
            industry: Client's industry type
            access_token: Authentication token for this leg
            data_dir: Directory for storing client data
            ollama_url: URL for Ollama server
        """
        self.client_id = client_id
        self.client_name = client_name
        self.baby_model = baby_model
        self.industry = industry
        self._access_token_hash = hashlib.sha256(access_token.encode()).hexdigest()

        # Initialize data storage
        self.data_dir = Path(data_dir) if data_dir else Path(f"./data/clients/{client_id}")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Ollama connection
        self.ollama = OllamaConnection(ollama_url)

        # In-memory caches (would use Redis in production)
        self._leads_cache: Dict[str, Lead] = {}
        self._activity_log: List[ActivityLog] = []

        # Load existing data
        self._load_data()

        logger.info(f"Initialized leg for client '{client_name}' ({client_id}) with baby '{baby_model}'")

    def _load_data(self) -> None:
        """Load client data from disk."""
        leads_file = self.data_dir / "leads.json"
        if leads_file.exists():
            try:
                with open(leads_file, 'r') as f:
                    leads_data = json.load(f)
                    for lead_data in leads_data:
                        lead = Lead.from_dict(lead_data)
                        self._leads_cache[lead.id] = lead
                logger.info(f"Loaded {len(self._leads_cache)} leads for {self.client_id}")
            except Exception as e:
                logger.error(f"Error loading leads: {e}")

    def _save_data(self) -> None:
        """Persist client data to disk."""
        leads_file = self.data_dir / "leads.json"
        try:
            leads_data = [lead.to_dict() for lead in self._leads_cache.values()]
            with open(leads_file, 'w') as f:
                json.dump(leads_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving leads: {e}")

    def authenticate(self, token: str) -> bool:
        """
        Verify an access token for this leg.

        Args:
            token: The token to verify

        Returns:
            True if token is valid, False otherwise
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        is_valid = token_hash == self._access_token_hash

        if not is_valid:
            self.log_activity(
                action="auth_failed",
                details={"reason": "invalid_token"}
            )

        return is_valid

    def process_request(
        self,
        request_type: RequestType,
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route a request to the appropriate handler.

        This is the main entry point for processing client requests.
        All requests are logged for audit purposes.

        Args:
            request_type: Type of request to process
            data: Request payload
            user_id: ID of user making request (for logging)

        Returns:
            Response dictionary with 'success' and 'data' or 'error'
        """
        self.log_activity(
            action=f"request_{request_type.value}",
            details={"data_keys": list(data.keys())},
            user_id=user_id
        )

        handlers = {
            RequestType.QUERY: self._handle_query,
            RequestType.LEAD_CREATE: self._handle_lead_create,
            RequestType.LEAD_UPDATE: self._handle_lead_update,
            RequestType.LEAD_GET: self._handle_lead_get,
            RequestType.REPORT: self._handle_report,
            RequestType.EXPORT: self._handle_export,
            RequestType.SCHEDULE: self._handle_schedule,
            RequestType.NOTIFY: self._handle_notify,
            RequestType.ANALYZE: self._handle_analyze,
        }

        handler = handlers.get(request_type)
        if not handler:
            return {"success": False, "error": f"Unknown request type: {request_type}"}

        try:
            result = handler(data)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Error processing {request_type}: {e}")
            return {"success": False, "error": str(e)}

    def _handle_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AI query request."""
        prompt = data.get("prompt", "")
        return self.query_baby(prompt)

    def _handle_lead_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle lead creation."""
        lead = Lead(
            id=str(uuid.uuid4()),
            client_id=self.client_id,
            name=data.get("name", "Unknown"),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            status=LeadStatus.NEW,
            source=data.get("source", "direct"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            custom_data=data.get("custom_data", {}),
            value=data.get("value", 0.0)
        )
        self._leads_cache[lead.id] = lead
        self._save_data()
        return lead.to_dict()

    def _handle_lead_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle lead update."""
        lead_id = data.get("lead_id")
        return self.update_lead(lead_id, data.get("status"), data.get("updates", {}))

    def _handle_lead_get(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle lead retrieval."""
        lead_id = data.get("lead_id")
        if lead_id:
            lead = self._leads_cache.get(lead_id)
            return lead.to_dict() if lead else {"error": "Lead not found"}
        status_filter = data.get("status_filter")
        return {"leads": [l.to_dict() for l in self.get_leads(status_filter)]}

    def _handle_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report generation."""
        date_range = data.get("date_range", {})
        return asdict(self.get_stats(date_range))

    def _handle_export(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data export (logged as potential flight risk)."""
        export_format = data.get("format", "json")
        return self.export_data(export_format)

    def _handle_schedule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scheduling - must be implemented by subclass."""
        return {"error": "Scheduling not implemented for this leg"}

    def _handle_notify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification - must be implemented by subclass."""
        return {"error": "Notifications not implemented for this leg"}

    def _handle_analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analysis request using AI."""
        subject = data.get("subject", "")
        context = data.get("context", "")
        prompt = f"Analyze the following for a {self.industry.value} business:\n\n{subject}\n\nContext: {context}"
        return self.query_baby(prompt)

    def query_baby(self, prompt: str, system_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a query to this leg's assigned Ollama baby.

        Args:
            prompt: The question or request
            system_context: Optional additional context

        Returns:
            AI response with metadata
        """
        # Build system prompt with industry context
        base_system = f"""You are an AI assistant for a {self.industry.value} business called {self.client_name}.
You help with customer inquiries, lead management, and business operations.
Be professional, helpful, and concise. Focus on actionable advice."""

        if system_context:
            base_system = f"{base_system}\n\nAdditional context: {system_context}"

        result = self.ollama.query(
            model=self.baby_model,
            prompt=prompt,
            system_prompt=base_system
        )

        # Log the AI query
        self.log_activity(
            action="baby_query",
            details={
                "model": self.baby_model,
                "prompt_length": len(prompt),
                "success": result.get("success", False),
                "duration": result.get("duration", 0)
            }
        )

        return result

    def log_activity(
        self,
        action: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> ActivityLog:
        """
        Record an activity for audit purposes.

        All leg activities are logged for review by Labienus (tail security).
        Certain actions (like exports) trigger additional scrutiny.

        Args:
            action: Type of action performed
            details: Additional information about the action
            user_id: ID of user performing action
            ip_address: Client IP address

        Returns:
            The created ActivityLog entry
        """
        log_entry = ActivityLog(
            id=str(uuid.uuid4()),
            client_id=self.client_id,
            user_id=user_id or "system",
            action=action,
            details=details,
            timestamp=datetime.now(),
            ip_address=ip_address
        )

        self._activity_log.append(log_entry)

        # Keep only last 10000 entries in memory
        if len(self._activity_log) > 10000:
            self._activity_log = self._activity_log[-10000:]

        # Flag potential security concerns
        if action in ["export", "bulk_download", "api_key_view"]:
            logger.warning(f"FLIGHT RISK ALERT: {action} by {user_id} for {self.client_id}")
            details["_security_flag"] = "potential_data_exfiltration"

        return log_entry

    def get_stats(self, date_range: Optional[Dict[str, Any]] = None) -> ClientStats:
        """
        Get statistics for this client.

        Args:
            date_range: Optional dict with 'start' and 'end' datetime strings

        Returns:
            ClientStats object with metrics
        """
        # Parse date range
        now = datetime.now()
        if date_range:
            start = datetime.fromisoformat(date_range.get('start', (now - timedelta(days=30)).isoformat()))
            end = datetime.fromisoformat(date_range.get('end', now.isoformat()))
        else:
            start = now - timedelta(days=30)
            end = now

        # Filter leads by date range
        period_leads = [
            lead for lead in self._leads_cache.values()
            if start <= lead.created_at <= end
        ]

        # Calculate metrics
        total_leads = len(period_leads)
        new_leads = len([l for l in period_leads if l.status == LeadStatus.NEW])
        converted = len([l for l in period_leads if l.status == LeadStatus.WON])
        total_value = sum(l.value for l in period_leads if l.status == LeadStatus.WON)

        # Count AI queries in period
        ai_queries = len([
            log for log in self._activity_log
            if log.action == "baby_query" and start <= log.timestamp <= end
        ])

        # Calculate conversion rate
        conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0.0

        # Get top sources
        source_counts: Dict[str, int] = {}
        for lead in period_leads:
            source_counts[lead.source] = source_counts.get(lead.source, 0) + 1
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return ClientStats(
            client_id=self.client_id,
            start_date=start,
            end_date=end,
            total_leads=total_leads,
            new_leads=new_leads,
            converted_leads=converted,
            total_value=total_value,
            ai_queries=ai_queries,
            conversion_rate=conversion_rate,
            avg_response_time=0.0,  # Would need timing data
            top_sources=top_sources
        )

    def get_leads(self, status_filter: Optional[str] = None) -> List[Lead]:
        """
        Get leads for this client.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of Lead objects
        """
        leads = list(self._leads_cache.values())

        if status_filter:
            try:
                status = LeadStatus(status_filter)
                leads = [l for l in leads if l.status == status]
            except ValueError:
                logger.warning(f"Invalid status filter: {status_filter}")

        # Sort by created date, newest first
        leads.sort(key=lambda l: l.created_at, reverse=True)

        return leads

    def update_lead(
        self,
        lead_id: str,
        status: Optional[str] = None,
        updates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a lead's information.

        Args:
            lead_id: ID of lead to update
            status: New status (optional)
            updates: Dict of fields to update (optional)

        Returns:
            Updated lead data or error
        """
        lead = self._leads_cache.get(lead_id)
        if not lead:
            return {"error": f"Lead {lead_id} not found"}

        # Update status if provided
        if status:
            try:
                lead.status = LeadStatus(status)
            except ValueError:
                return {"error": f"Invalid status: {status}"}

        # Apply other updates
        if updates:
            for key, value in updates.items():
                if key == 'notes' and isinstance(value, str):
                    lead.notes.append(value)
                elif key == 'custom_data' and isinstance(value, dict):
                    lead.custom_data.update(value)
                elif hasattr(lead, key) and key not in ['id', 'client_id', 'created_at']:
                    setattr(lead, key, value)

        lead.updated_at = datetime.now()
        self._save_data()

        self.log_activity(
            action="lead_updated",
            details={"lead_id": lead_id, "changes": updates or {}, "new_status": status}
        )

        return lead.to_dict()

    def export_data(self, export_format: str = "json") -> Dict[str, Any]:
        """
        Export client data. THIS ACTION IS LOGGED AS POTENTIAL FLIGHT RISK.

        Args:
            export_format: 'json' or 'csv'

        Returns:
            Exported data or file path
        """
        # Log this as a potential security concern
        self.log_activity(
            action="export",
            details={
                "format": export_format,
                "lead_count": len(self._leads_cache),
                "_alert": "DATA_EXPORT_PERFORMED"
            }
        )

        leads_data = [lead.to_dict() for lead in self._leads_cache.values()]

        if export_format == "csv":
            # Generate CSV content
            if not leads_data:
                return {"data": "", "format": "csv", "count": 0}

            headers = list(leads_data[0].keys())
            csv_lines = [",".join(headers)]
            for lead in leads_data:
                row = [str(lead.get(h, "")).replace(",", ";") for h in headers]
                csv_lines.append(",".join(row))

            return {
                "data": "\n".join(csv_lines),
                "format": "csv",
                "count": len(leads_data)
            }
        else:
            return {
                "data": leads_data,
                "format": "json",
                "count": len(leads_data)
            }

    @abstractmethod
    def get_industry_actions(self) -> List[str]:
        """
        Return list of industry-specific actions this leg supports.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def process_industry_request(
        self,
        action: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an industry-specific request.
        Must be implemented by subclasses.
        """
        pass

    def get_leg_info(self) -> Dict[str, Any]:
        """Get information about this leg."""
        return {
            "client_id": self.client_id,
            "client_name": self.client_name,
            "industry": self.industry.value,
            "baby_model": self.baby_model,
            "lead_count": len(self._leads_cache),
            "activity_count": len(self._activity_log),
            "supported_actions": self.get_industry_actions()
        }
