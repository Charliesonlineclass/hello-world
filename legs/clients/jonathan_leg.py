"""
Jonathan Leg - J3 Structural Solutions
=======================================

Client leg implementation for Jonathan's J3 Structural Solutions.
Handles construction quotes, scheduling, and project management.

Services:
- Project inquiry processing
- Quote generation
- Estimate scheduling
- Project status tracking
- Client follow-up automation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import uuid

from .base_leg import BaseClientLeg, ClientConfig, Industry, Lead, LeadStatus


class ProjectType(Enum):
    """Types of structural projects."""
    FOUNDATION_REPAIR = "foundation_repair"
    STRUCTURAL_INSPECTION = "structural_inspection"
    BASEMENT_WATERPROOFING = "basement_waterproofing"
    CRAWL_SPACE = "crawl_space"
    CONCRETE_LEVELING = "concrete_leveling"
    RETAINING_WALL = "retaining_wall"
    COMMERCIAL = "commercial"
    OTHER = "other"


class ProjectStatus(Enum):
    """Status of a construction project."""
    INQUIRY = "inquiry"
    ESTIMATE_SCHEDULED = "estimate_scheduled"
    QUOTE_SENT = "quote_sent"
    NEGOTIATION = "negotiation"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Project:
    """Represents a construction project."""
    id: str
    client_id: str
    project_type: ProjectType
    status: ProjectStatus
    address: str
    description: str
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "project_type": self.project_type.value,
            "status": self.status.value,
            "address": self.address,
            "description": self.description,
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "scheduled_start": self.scheduled_start.isoformat() if self.scheduled_start else None,
            "scheduled_end": self.scheduled_end.isoformat() if self.scheduled_end else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Estimate:
    """Represents a scheduled estimate visit."""
    id: str
    project_id: str
    client_id: str
    scheduled_time: datetime
    estimator_id: str
    address: str
    confirmed: bool = False
    completed: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "client_id": self.client_id,
            "scheduled_time": self.scheduled_time.isoformat(),
            "estimator_id": self.estimator_id,
            "address": self.address,
            "confirmed": self.confirmed,
            "completed": self.completed,
            "notes": self.notes,
        }


class JonathanLeg(BaseClientLeg):
    """
    J3 Structural Solutions integration.

    Jonathan's construction company handles:
    - Foundation repairs
    - Structural inspections
    - Basement waterproofing
    - Commercial projects
    """

    # Pricing guidelines (base prices)
    PRICING_GUIDE = {
        ProjectType.FOUNDATION_REPAIR: (5000, 15000),
        ProjectType.STRUCTURAL_INSPECTION: (300, 800),
        ProjectType.BASEMENT_WATERPROOFING: (3000, 12000),
        ProjectType.CRAWL_SPACE: (4000, 10000),
        ProjectType.CONCRETE_LEVELING: (1000, 5000),
        ProjectType.RETAINING_WALL: (3000, 20000),
        ProjectType.COMMERCIAL: (10000, 100000),
        ProjectType.OTHER: (1000, 10000),
    }

    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize Jonathan's leg with optional config."""
        if config is None:
            config = ClientConfig(
                name="J3 Structural Solutions",
                industry=Industry.CONSTRUCTION,
                integrations=["j3_quote_generator", "email", "sms", "calendar"],
                notification_emails=["jonathan@j3structural.com"],
                notification_phones=["+15551234567"],
            )
        super().__init__(config)

        # Construction specific tracking
        self._projects: Dict[str, Project] = {}
        self._estimates: Dict[str, Estimate] = {}
        self._estimators: List[str] = ["estimator_001", "estimator_002"]

        # Metrics specific to construction
        self._metrics.update({
            "quotes_generated": 0,
            "estimates_scheduled": 0,
            "projects_completed": 0,
            "total_revenue": 0.0,
            "conversion_rate": 0.0,
        })

    @property
    def industry(self) -> Industry:
        return Industry.CONSTRUCTION

    @property
    def services(self) -> List[str]:
        return [
            "quote_generation",
            "estimate_scheduling",
            "project_tracking",
            "client_follow_up",
            "j3_integration",
        ]

    def _setup_integrations(self) -> None:
        """Set up J3 quote generator and communication integrations."""
        self.logger.info("Setting up J3 Quote Generator integration...")
        self.logger.info("Setting up calendar integration for estimates...")
        self.logger.info("Setting up SMS/Email for client communication...")

    def process_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Process incoming lead for construction inquiry.

        Args:
            lead: The lead to process

        Returns:
            Dict with inquiry assessment and next steps
        """
        self.logger.info(f"Processing lead {lead.id} for J3 Structural")
        self._metrics["leads_processed"] += 1

        # Store the lead
        self.add_lead(lead)

        # Assess project type and urgency
        assessment = self._assess_inquiry(lead)

        # Determine next action
        if assessment["urgency"] == "high":
            # Schedule immediate estimate
            result = self.schedule_estimate(
                lead.id,
                datetime.now() + timedelta(days=1)
            )
            lead.status = LeadStatus.QUALIFIED
            next_action = "estimate_scheduled"
        elif assessment["urgency"] == "medium":
            # Send preliminary info and schedule
            lead.status = LeadStatus.CONTACTED
            next_action = "send_info_packet"
        else:
            # Add to follow-up queue
            lead.status = LeadStatus.NURTURING
            next_action = "follow_up_call"

        return {
            "lead_id": lead.id,
            "assessment": assessment,
            "status": lead.status.value,
            "next_action": next_action,
        }

    def _assess_inquiry(self, lead: Lead) -> Dict[str, Any]:
        """Assess the construction inquiry."""
        data = lead.data

        # Determine project type
        project_type = self._determine_project_type(data)

        # Assess urgency
        urgency = "low"
        if data.get("water_intrusion", False):
            urgency = "high"
        elif data.get("visible_cracks", False):
            urgency = "high"
        elif data.get("timeline", "") == "immediate":
            urgency = "high"
        elif data.get("timeline", "") == "this_month":
            urgency = "medium"

        # Estimate range
        price_range = self.PRICING_GUIDE.get(project_type, (1000, 10000))

        return {
            "project_type": project_type.value,
            "urgency": urgency,
            "estimated_range": {
                "low": price_range[0],
                "high": price_range[1],
            },
            "factors": data.get("description", "No details provided"),
        }

    def _determine_project_type(self, data: Dict[str, Any]) -> ProjectType:
        """Determine the type of project from inquiry data."""
        description = data.get("description", "").lower()
        service = data.get("service_type", "").lower()

        if "foundation" in description or "foundation" in service:
            return ProjectType.FOUNDATION_REPAIR
        elif "basement" in description or "waterproof" in description:
            return ProjectType.BASEMENT_WATERPROOFING
        elif "inspection" in description or "inspect" in service:
            return ProjectType.STRUCTURAL_INSPECTION
        elif "crawl" in description:
            return ProjectType.CRAWL_SPACE
        elif "concrete" in description or "leveling" in description:
            return ProjectType.CONCRETE_LEVELING
        elif "retaining" in description or "wall" in service:
            return ProjectType.RETAINING_WALL
        elif "commercial" in description or data.get("property_type") == "commercial":
            return ProjectType.COMMERCIAL
        else:
            return ProjectType.OTHER

    def new_project_inquiry(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new project inquiry and generate initial quote.

        Args:
            client_data: Client and project information

        Returns:
            Dict with project details and quote
        """
        project_id = str(uuid.uuid4())
        client_id = client_data.get("client_id", str(uuid.uuid4()))

        # Determine project type
        project_type = self._determine_project_type(client_data)

        # Create project
        project = Project(
            id=project_id,
            client_id=client_id,
            project_type=project_type,
            status=ProjectStatus.INQUIRY,
            address=client_data.get("address", ""),
            description=client_data.get("description", ""),
        )

        self._projects[project_id] = project

        # Generate preliminary quote
        quote = self._generate_quote(project, client_data)

        self.logger.info(f"Created project inquiry {project_id}")

        return {
            "project_id": project_id,
            "client_id": client_id,
            "project_type": project_type.value,
            "quote": quote,
            "next_steps": [
                "Schedule on-site estimate",
                "Review detailed quote",
                "Sign contract",
            ],
        }

    def _generate_quote(
        self,
        project: Project,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a quote for the project."""
        base_range = self.PRICING_GUIDE.get(project.project_type, (1000, 10000))

        # Adjust based on details
        sqft = details.get("square_footage", 1000)
        multiplier = sqft / 1000  # Base is 1000 sqft

        estimated_low = int(base_range[0] * max(0.5, multiplier))
        estimated_high = int(base_range[1] * max(0.5, multiplier))

        project.estimated_cost = (estimated_low + estimated_high) / 2

        self._metrics["quotes_generated"] += 1

        return {
            "quote_id": f"Q-{project.id[:8]}",
            "range_low": estimated_low,
            "range_high": estimated_high,
            "estimate_required": True,
            "valid_for_days": 30,
            "notes": "Final quote after on-site inspection",
        }

    def schedule_estimate(
        self,
        client_id: str,
        scheduled_time: datetime,
        address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule an on-site estimate.

        Args:
            client_id: Client requesting estimate
            scheduled_time: Requested date/time
            address: Property address

        Returns:
            Estimate scheduling details
        """
        estimate_id = str(uuid.uuid4())

        # Find or create project
        project = None
        for p in self._projects.values():
            if p.client_id == client_id:
                project = p
                break

        if not project:
            project = Project(
                id=str(uuid.uuid4()),
                client_id=client_id,
                project_type=ProjectType.OTHER,
                status=ProjectStatus.ESTIMATE_SCHEDULED,
                address=address or "",
                description="Estimate requested",
            )
            self._projects[project.id] = project

        # Select available estimator
        estimator = self._select_estimator(scheduled_time)

        # Create estimate
        estimate = Estimate(
            id=estimate_id,
            project_id=project.id,
            client_id=client_id,
            scheduled_time=scheduled_time,
            estimator_id=estimator,
            address=address or project.address,
        )

        self._estimates[estimate_id] = estimate
        project.status = ProjectStatus.ESTIMATE_SCHEDULED
        self._metrics["estimates_scheduled"] += 1

        # Send confirmation
        self.send_notification(
            f"Estimate scheduled for {scheduled_time.strftime('%B %d at %I:%M %p')}",
            channels=["email", "sms"]
        )

        self.logger.info(f"Scheduled estimate {estimate_id} for {scheduled_time}")

        return {
            "estimate_id": estimate_id,
            "project_id": project.id,
            "scheduled_time": scheduled_time.isoformat(),
            "estimator": estimator,
            "address": estimate.address,
            "confirmation_sent": True,
        }

    def _select_estimator(self, requested_time: datetime) -> str:
        """Select an available estimator."""
        # Simple round-robin for now
        # In production, would check calendar availability
        return self._estimators[len(self._estimates) % len(self._estimators)]

    def project_status_update(
        self,
        project_id: str,
        status: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Update project status.

        Args:
            project_id: Project to update
            status: New status
            notes: Optional notes

        Returns:
            Update confirmation
        """
        project = self._projects.get(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}

        old_status = project.status
        project.status = ProjectStatus(status)
        project.updated_at = datetime.now()

        if notes:
            project.notes.append(f"[{datetime.now().isoformat()}] {notes}")

        # Track completions
        if project.status == ProjectStatus.COMPLETED:
            self._metrics["projects_completed"] += 1
            self._metrics["total_revenue"] += project.actual_cost or project.estimated_cost

        self.logger.info(f"Project {project_id} status: {old_status.value} -> {status}")

        # Notify client of status change
        self.send_notification(
            f"Project status updated to: {status}",
            channels=["email"]
        )

        return {
            "success": True,
            "project_id": project_id,
            "old_status": old_status.value,
            "new_status": status,
            "updated_at": project.updated_at.isoformat(),
        }

    def daily_report(self) -> Dict[str, Any]:
        """
        Generate Jonathan's daily metrics report.

        Returns:
            Dict containing daily performance metrics
        """
        today = datetime.now().date()

        # Today's estimates
        today_estimates = [
            e for e in self._estimates.values()
            if e.scheduled_time.date() == today
        ]

        # Projects by status
        status_counts = {}
        for status in ProjectStatus:
            status_counts[status.value] = len([
                p for p in self._projects.values()
                if p.status == status
            ])

        report = {
            "client": "J3 Structural Solutions",
            "date": today.isoformat(),
            "generated_at": datetime.now().isoformat(),

            "estimates": {
                "scheduled_today": len(today_estimates),
                "confirmed": len([e for e in today_estimates if e.confirmed]),
                "completed": len([e for e in today_estimates if e.completed]),
            },

            "projects": {
                "total": len(self._projects),
                "by_status": status_counts,
                "new_today": len([
                    p for p in self._projects.values()
                    if p.created_at.date() == today
                ]),
            },

            "revenue": {
                "total": self._metrics["total_revenue"],
                "quotes_pending": sum(
                    p.estimated_cost for p in self._projects.values()
                    if p.status in [ProjectStatus.QUOTE_SENT, ProjectStatus.NEGOTIATION]
                ),
            },

            "overall_metrics": self._metrics.copy(),
        }

        self.logger.info(f"Generated daily report for {today}")
        return report

    def get_upcoming_estimates(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get estimates scheduled in the next N days."""
        cutoff = datetime.now() + timedelta(days=days)

        upcoming = [
            e.to_dict() for e in self._estimates.values()
            if datetime.now() <= e.scheduled_time <= cutoff
            and not e.completed
        ]

        return sorted(upcoming, key=lambda x: x["scheduled_time"])
