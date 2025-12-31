"""
SCORPION LEG Template - Client Container Template
=================================================

Template for creating new client-specific LEG containers.
Each LEG handles client-specific integrations, data flows, and automations.

This template provides:
- Client configuration management
- Service connections to HEAD (ChromaDB) and MOUTH (API)
- Webhook handling for client-specific events
- Data sync with central SCORPION system
- Client-specific automation workflows

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import os
import json
import asyncio
import logging
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from pathlib import Path
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ClientConfig:
    """Configuration for a client LEG container."""

    # Client identification
    client_id: str
    client_name: str
    client_industry: str  # construction, healthcare, education, etc.

    # Connection settings
    scorpion_api_url: str = "http://localhost:8080"
    scorpion_api_key: str = ""
    chromadb_url: str = "http://localhost:8000"
    chromadb_token: str = ""

    # Client-specific settings
    timezone: str = "America/New_York"
    business_hours_start: int = 9  # 9 AM
    business_hours_end: int = 17   # 5 PM
    working_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])  # Mon-Fri

    # Integration settings
    webhook_secret: str = ""
    notification_email: str = ""
    notification_phone: str = ""

    # Feature flags
    enable_auto_responses: bool = True
    enable_lead_capture: bool = True
    enable_appointment_booking: bool = True
    enable_quote_generation: bool = True
    enable_call_logging: bool = True

    # Data retention
    data_retention_days: int = 365
    backup_frequency_hours: int = 24

    @classmethod
    def from_file(cls, filepath: str) -> 'ClientConfig':
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def to_file(self, filepath: str) -> None:
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def is_business_hours(self) -> bool:
        """Check if current time is within business hours."""
        now = datetime.now()
        if now.weekday() not in self.working_days:
            return False
        current_hour = now.hour
        return self.business_hours_start <= current_hour < self.business_hours_end


# =============================================================================
# BASE CLIENT LEG
# =============================================================================

class BaseClientLeg(ABC):
    """
    Base class for all client LEG containers.

    Inherit from this class to create client-specific LEGs.
    """

    def __init__(self, config: ClientConfig):
        self.config = config
        self.logger = logging.getLogger(f"LEG-{config.client_id}")
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_queue: queue.Queue = queue.Queue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

        # Initialize connections
        self._init_connections()

        # Register default handlers
        self._register_default_handlers()

        self.logger.info(f"LEG initialized for client: {config.client_name}")

    def _init_connections(self) -> None:
        """Initialize connections to SCORPION services."""
        self.api_headers = {
            "Authorization": f"Bearer {self.config.scorpion_api_key}",
            "Content-Type": "application/json",
            "X-Client-ID": self.config.client_id
        }

        self.chromadb_headers = {
            "Authorization": f"Bearer {self.config.chromadb_token}",
            "Content-Type": "application/json"
        }

    def _register_default_handlers(self) -> None:
        """Register default event handlers."""
        self.register_handler("lead_received", self._handle_lead)
        self.register_handler("call_received", self._handle_call)
        self.register_handler("appointment_requested", self._handle_appointment)
        self.register_handler("quote_requested", self._handle_quote)
        self.register_handler("message_received", self._handle_message)

    # -------------------------------------------------------------------------
    # Event System
    # -------------------------------------------------------------------------

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Register a handler for an event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        self.logger.debug(f"Registered handler for: {event_type}")

    def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to be processed."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "client_id": self.config.client_id
        }
        self.event_queue.put(event)
        self.logger.info(f"Event emitted: {event_type}")

    def _process_events(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                event = self.event_queue.get(timeout=1.0)
                event_type = event.get("type")

                if event_type in self.event_handlers:
                    for handler in self.event_handlers[event_type]:
                        try:
                            handler(event.get("data", {}))
                        except Exception as e:
                            self.logger.error(f"Handler error: {e}")

                self.event_queue.task_done()
            except queue.Empty:
                continue

    # -------------------------------------------------------------------------
    # Default Event Handlers
    # -------------------------------------------------------------------------

    def _handle_lead(self, data: Dict[str, Any]) -> None:
        """Handle incoming lead."""
        if not self.config.enable_lead_capture:
            return

        lead = {
            "name": data.get("name", "Unknown"),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "source": data.get("source", "unknown"),
            "notes": data.get("notes", ""),
            "client_id": self.config.client_id,
            "created_at": datetime.now().isoformat()
        }

        # Send to central API
        self._api_post("/leads", lead)

        # Store in ChromaDB for semantic search
        self._store_memory("lead", lead)

        self.logger.info(f"Lead captured: {lead['name']}")

    def _handle_call(self, data: Dict[str, Any]) -> None:
        """Handle incoming call log."""
        if not self.config.enable_call_logging:
            return

        call_log = {
            "caller_name": data.get("caller_name", "Unknown"),
            "caller_phone": data.get("caller_phone", ""),
            "duration": data.get("duration", 0),
            "summary": data.get("summary", ""),
            "outcome": data.get("outcome", "logged"),
            "client_id": self.config.client_id,
            "logged_at": datetime.now().isoformat()
        }

        self._api_post("/calls", call_log)
        self._store_memory("call", call_log)

        self.logger.info(f"Call logged: {call_log['caller_name']}")

    def _handle_appointment(self, data: Dict[str, Any]) -> None:
        """Handle appointment request."""
        if not self.config.enable_appointment_booking:
            return

        appointment = {
            "contact_name": data.get("contact_name", "Unknown"),
            "contact_phone": data.get("contact_phone", ""),
            "contact_email": data.get("contact_email", ""),
            "requested_date": data.get("requested_date", ""),
            "requested_time": data.get("requested_time", ""),
            "service_type": data.get("service_type", ""),
            "notes": data.get("notes", ""),
            "status": "pending",
            "client_id": self.config.client_id,
            "created_at": datetime.now().isoformat()
        }

        self._api_post("/appointments", appointment)

        self.logger.info(f"Appointment requested: {appointment['contact_name']}")

    def _handle_quote(self, data: Dict[str, Any]) -> None:
        """Handle quote request."""
        if not self.config.enable_quote_generation:
            return

        quote_request = {
            "contact_name": data.get("contact_name", "Unknown"),
            "contact_email": data.get("contact_email", ""),
            "project_type": data.get("project_type", ""),
            "project_details": data.get("project_details", ""),
            "budget_range": data.get("budget_range", ""),
            "timeline": data.get("timeline", ""),
            "status": "pending",
            "client_id": self.config.client_id,
            "created_at": datetime.now().isoformat()
        }

        self._api_post("/quotes/request", quote_request)

        self.logger.info(f"Quote requested: {quote_request['contact_name']}")

    def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle incoming message."""
        message = {
            "sender": data.get("sender", "Unknown"),
            "channel": data.get("channel", "unknown"),  # email, sms, chat, etc.
            "content": data.get("content", ""),
            "client_id": self.config.client_id,
            "received_at": datetime.now().isoformat()
        }

        # Store for context
        self._store_memory("message", message)

        # Generate auto-response if enabled
        if self.config.enable_auto_responses and self.config.is_business_hours():
            self._generate_auto_response(message)

        self.logger.info(f"Message received from: {message['sender']}")

    # -------------------------------------------------------------------------
    # API Communication
    # -------------------------------------------------------------------------

    def _api_get(self, endpoint: str) -> Optional[Dict]:
        """Make GET request to SCORPION API."""
        try:
            url = f"{self.config.scorpion_api_url}{endpoint}"
            response = requests.get(url, headers=self.api_headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"API GET error: {e}")
            return None

    def _api_post(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Make POST request to SCORPION API."""
        try:
            url = f"{self.config.scorpion_api_url}{endpoint}"
            response = requests.post(
                url,
                headers=self.api_headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"API POST error: {e}")
            return None

    # -------------------------------------------------------------------------
    # ChromaDB Memory Storage
    # -------------------------------------------------------------------------

    def _store_memory(self, memory_type: str, data: Dict) -> None:
        """Store data in ChromaDB for semantic search."""
        try:
            collection_name = f"{self.config.client_id}_{memory_type}"

            # Create document ID
            doc_id = hashlib.md5(
                f"{data}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]

            # Prepare document
            document = json.dumps(data)

            payload = {
                "documents": [document],
                "ids": [doc_id],
                "metadatas": [{
                    "type": memory_type,
                    "client_id": self.config.client_id,
                    "timestamp": datetime.now().isoformat()
                }]
            }

            # Add to collection
            url = f"{self.config.chromadb_url}/api/v1/collections/{collection_name}/add"
            requests.post(url, headers=self.chromadb_headers, json=payload, timeout=30)

        except Exception as e:
            self.logger.error(f"Memory storage error: {e}")

    def search_memory(self, query: str, memory_type: str, n_results: int = 5) -> List[Dict]:
        """Search ChromaDB for relevant memories."""
        try:
            collection_name = f"{self.config.client_id}_{memory_type}"

            payload = {
                "query_texts": [query],
                "n_results": n_results
            }

            url = f"{self.config.chromadb_url}/api/v1/collections/{collection_name}/query"
            response = requests.post(
                url,
                headers=self.chromadb_headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                documents = result.get("documents", [[]])[0]
                return [json.loads(doc) for doc in documents]

        except Exception as e:
            self.logger.error(f"Memory search error: {e}")

        return []

    # -------------------------------------------------------------------------
    # Auto-Response Generation
    # -------------------------------------------------------------------------

    def _generate_auto_response(self, message: Dict) -> Optional[str]:
        """Generate an auto-response using SCORPION AI."""
        try:
            # Get relevant context from memory
            context = self.search_memory(message.get("content", ""), "message", 3)

            payload = {
                "baby": "MARCUS",  # Use MARCUS for customer interactions
                "prompt": f"Generate a helpful response to: {message.get('content', '')}",
                "context": context,
                "client_id": self.config.client_id
            }

            result = self._api_post("/ask", payload)

            if result and result.get("response"):
                return result["response"]

        except Exception as e:
            self.logger.error(f"Auto-response error: {e}")

        return None

    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------

    def start(self) -> None:
        """Start the LEG container."""
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_events)
        self._worker_thread.daemon = True
        self._worker_thread.start()

        self.logger.info(f"LEG started: {self.config.client_name}")

        # Call subclass startup
        self.on_start()

    def stop(self) -> None:
        """Stop the LEG container."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)

        self.logger.info(f"LEG stopped: {self.config.client_name}")

        # Call subclass shutdown
        self.on_stop()

    @abstractmethod
    def on_start(self) -> None:
        """Called when LEG starts. Override in subclass."""
        pass

    @abstractmethod
    def on_stop(self) -> None:
        """Called when LEG stops. Override in subclass."""
        pass

    # -------------------------------------------------------------------------
    # Webhook Handling
    # -------------------------------------------------------------------------

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""
        expected = hashlib.sha256(
            f"{self.config.webhook_secret}{payload.decode()}".encode()
        ).hexdigest()
        return signature == expected

    def handle_webhook(self, event_type: str, payload: Dict) -> Dict[str, Any]:
        """Handle incoming webhook."""
        self.logger.info(f"Webhook received: {event_type}")

        # Emit as internal event
        self.emit_event(event_type, payload)

        return {"status": "received", "event_type": event_type}


# =============================================================================
# EXAMPLE CLIENT LEG IMPLEMENTATION
# =============================================================================

class ExampleClientLeg(BaseClientLeg):
    """
    Example implementation of a client LEG.

    Copy and customize this class for new clients.
    """

    def __init__(self, config: ClientConfig):
        super().__init__(config)

        # Client-specific initialization
        self.custom_data: Dict[str, Any] = {}

    def on_start(self) -> None:
        """Custom startup logic."""
        self.logger.info("Example client LEG custom startup")

        # Load any client-specific data
        self._load_client_data()

        # Register client-specific handlers
        self.register_handler("custom_event", self._handle_custom_event)

    def on_stop(self) -> None:
        """Custom shutdown logic."""
        self.logger.info("Example client LEG custom shutdown")

        # Save any pending data
        self._save_client_data()

    def _load_client_data(self) -> None:
        """Load client-specific data."""
        data_file = Path(f"data/{self.config.client_id}_data.json")
        if data_file.exists():
            with open(data_file, 'r') as f:
                self.custom_data = json.load(f)

    def _save_client_data(self) -> None:
        """Save client-specific data."""
        data_file = Path(f"data/{self.config.client_id}_data.json")
        data_file.parent.mkdir(exist_ok=True)
        with open(data_file, 'w') as f:
            json.dump(self.custom_data, f, indent=2)

    def _handle_custom_event(self, data: Dict[str, Any]) -> None:
        """Handle client-specific custom event."""
        self.logger.info(f"Custom event: {data}")
        # Add custom handling logic here


# =============================================================================
# LEG FACTORY
# =============================================================================

class LegFactory:
    """Factory for creating client LEG instances."""

    _leg_classes: Dict[str, type] = {
        "default": ExampleClientLeg
    }

    @classmethod
    def register_leg(cls, industry: str, leg_class: type) -> None:
        """Register a LEG class for an industry."""
        cls._leg_classes[industry] = leg_class

    @classmethod
    def create_leg(cls, config: ClientConfig) -> BaseClientLeg:
        """Create a LEG instance based on client config."""
        leg_class = cls._leg_classes.get(
            config.client_industry,
            cls._leg_classes["default"]
        )
        return leg_class(config)


# =============================================================================
# MAIN - Example Usage
# =============================================================================

def main():
    """Example usage of client LEG template."""

    # Create configuration
    config = ClientConfig(
        client_id="example_client_001",
        client_name="Example Construction Co",
        client_industry="construction",
        scorpion_api_url="http://localhost:8080",
        scorpion_api_key="your-api-key-here",
        chromadb_url="http://localhost:8000",
        chromadb_token="your-chromadb-token",
        webhook_secret="your-webhook-secret",
        notification_email="contact@example.com"
    )

    # Create LEG instance
    leg = LegFactory.create_leg(config)

    # Start LEG
    leg.start()

    # Simulate events
    leg.emit_event("lead_received", {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-0100",
        "source": "website",
        "notes": "Interested in kitchen remodel"
    })

    leg.emit_event("quote_requested", {
        "contact_name": "Jane Smith",
        "contact_email": "jane@example.com",
        "project_type": "bathroom_renovation",
        "project_details": "Full master bathroom renovation",
        "budget_range": "$15,000 - $25,000",
        "timeline": "2 months"
    })

    # Let events process
    import time
    time.sleep(5)

    # Stop LEG
    leg.stop()


if __name__ == "__main__":
    main()
