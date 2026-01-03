"""
SCORPION Multi-Tenant System - J3 Structural Construction Leg
=============================================================

This leg serves J3 Structural, a construction company specializing in
framing, drywall, remodeling, and commercial projects.

SCORPION Architecture Role:
- LEG: Client interface for J3 Structural
- BABY: VULCAN (phi3:mini) - optimized for building patterns and structural analysis
- Industry: CONSTRUCTION
- Owner: Master Charlie (HEAD access)

J3 Structural specializes in:
- Residential framing and drywall
- Full home remodels
- Room additions
- Commercial construction

This leg handles leads from the J3 website, provides estimates,
generates quotes, and tracks project progress.

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

from .base_leg import (
    BaseClientLeg, Industry, Lead, LeadStatus,
    RequestType, logger
)


class JobType(Enum):
    """Types of construction jobs J3 handles."""
    FRAMING = "framing"
    DRYWALL = "drywall"
    FULL_REMODEL = "full_remodel"
    ADDITION = "addition"
    COMMERCIAL = "commercial"
    REPAIR = "repair"
    CUSTOM = "custom"


class ProjectStatus(Enum):
    """Status of a construction project."""
    INQUIRY = "inquiry"
    ESTIMATE_SCHEDULED = "estimate_scheduled"
    QUOTE_SENT = "quote_sent"
    NEGOTIATING = "negotiating"
    CONTRACT_SIGNED = "contract_signed"
    PERMIT_PENDING = "permit_pending"
    IN_PROGRESS = "in_progress"
    INSPECTION_PENDING = "inspection_pending"
    COMPLETE = "complete"
    WARRANTY = "warranty"
    CANCELLED = "cancelled"


class Complexity(Enum):
    """Job complexity levels affecting pricing."""
    SIMPLE = 1.0       # Standard work
    MODERATE = 1.25    # Some custom elements
    COMPLEX = 1.5      # Significant customization
    EXPERT = 2.0       # Highly specialized


@dataclass
class MaterialEstimate:
    """Estimate for materials needed."""
    name: str
    quantity: float
    unit: str
    unit_price: float
    total: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JobEstimate:
    """Complete estimate for a construction job."""
    id: str
    lead_id: str
    job_type: JobType
    sqft: float
    complexity: Complexity
    materials: List[MaterialEstimate]
    labor_hours: float
    labor_rate: float
    material_total: float
    labor_total: float
    overhead: float
    profit_margin: float
    total: float
    valid_days: int
    created_at: datetime
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['job_type'] = self.job_type.value
        data['complexity'] = self.complexity.value
        data['created_at'] = self.created_at.isoformat()
        data['materials'] = [m.to_dict() if isinstance(m, MaterialEstimate) else m for m in self.materials]
        return data


@dataclass
class Project:
    """An active construction project."""
    id: str
    lead_id: str
    estimate_id: str
    client_name: str
    address: str
    job_type: JobType
    status: ProjectStatus
    contract_value: float
    start_date: Optional[datetime]
    estimated_completion: Optional[datetime]
    actual_completion: Optional[datetime]
    notes: List[str] = field(default_factory=list)
    milestones: Dict[str, bool] = field(default_factory=dict)
    change_orders: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['job_type'] = self.job_type.value
        data['status'] = self.status.value
        data['start_date'] = self.start_date.isoformat() if self.start_date else None
        data['estimated_completion'] = self.estimated_completion.isoformat() if self.estimated_completion else None
        data['actual_completion'] = self.actual_completion.isoformat() if self.actual_completion else None
        return data


@dataclass
class WalkthroughAppointment:
    """Scheduled estimate walkthrough."""
    id: str
    lead_id: str
    client_name: str
    address: str
    scheduled_datetime: datetime
    estimator: str
    job_type: JobType
    notes: str = ""
    confirmed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['scheduled_datetime'] = self.scheduled_datetime.isoformat()
        data['job_type'] = self.job_type.value
        return data


class J3Leg(BaseClientLeg):
    """
    SCORPION Leg for J3 Structural Construction.

    Connects to VULCAN (phi3:mini) for building/structural analysis.
    Handles construction leads, estimates, quotes, and project tracking.

    SCORPION Security:
    - All actions logged to Labienus audit system
    - Only J3 staff can access this leg (LEG level access)
    - HEAD (Master Charlie) has full oversight
    - Export actions flagged as potential flight risk
    """

    # Base rates for different job types (per sqft)
    BASE_RATES = {
        JobType.FRAMING: 8.50,
        JobType.DRYWALL: 3.75,
        JobType.FULL_REMODEL: 85.00,
        JobType.ADDITION: 150.00,
        JobType.COMMERCIAL: 45.00,
        JobType.REPAIR: 25.00,
        JobType.CUSTOM: 100.00,
    }

    # Standard labor rate per hour
    LABOR_RATE = 65.00

    # Hours per sqft by job type
    LABOR_HOURS_PER_SQFT = {
        JobType.FRAMING: 0.15,
        JobType.DRYWALL: 0.08,
        JobType.FULL_REMODEL: 0.75,
        JobType.ADDITION: 1.0,
        JobType.COMMERCIAL: 0.35,
        JobType.REPAIR: 0.5,
        JobType.CUSTOM: 0.6,
    }

    # Material markup
    MATERIAL_MARKUP = 1.15
    OVERHEAD_RATE = 0.12
    PROFIT_MARGIN = 0.18

    def __init__(
        self,
        access_token: str,
        data_dir: Optional[str] = None,
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize J3 Structural leg.

        Args:
            access_token: Authentication token
            data_dir: Data storage directory
            ollama_url: Ollama server URL
        """
        super().__init__(
            client_id="j3_structural",
            client_name="J3 Structural",
            baby_model="phi3:mini",  # VULCAN
            industry=Industry.CONSTRUCTION,
            access_token=access_token,
            data_dir=data_dir,
            ollama_url=ollama_url
        )

        # J3-specific data storage
        self._estimates: Dict[str, JobEstimate] = {}
        self._projects: Dict[str, Project] = {}
        self._appointments: Dict[str, WalkthroughAppointment] = {}

        # Load J3 data
        self._load_j3_data()

        logger.info(f"J3 Structural leg initialized with VULCAN (phi3:mini)")

    def _load_j3_data(self) -> None:
        """Load J3-specific data from disk."""
        # Load estimates
        estimates_file = self.data_dir / "estimates.json"
        if estimates_file.exists():
            try:
                with open(estimates_file, 'r') as f:
                    data = json.load(f)
                    for est in data:
                        est['job_type'] = JobType(est['job_type'])
                        est['complexity'] = Complexity(est['complexity'])
                        est['created_at'] = datetime.fromisoformat(est['created_at'])
                        est['materials'] = [MaterialEstimate(**m) for m in est['materials']]
                        self._estimates[est['id']] = JobEstimate(**est)
            except Exception as e:
                logger.error(f"Error loading estimates: {e}")

        # Load projects
        projects_file = self.data_dir / "projects.json"
        if projects_file.exists():
            try:
                with open(projects_file, 'r') as f:
                    data = json.load(f)
                    for proj in data:
                        proj['job_type'] = JobType(proj['job_type'])
                        proj['status'] = ProjectStatus(proj['status'])
                        if proj['start_date']:
                            proj['start_date'] = datetime.fromisoformat(proj['start_date'])
                        if proj['estimated_completion']:
                            proj['estimated_completion'] = datetime.fromisoformat(proj['estimated_completion'])
                        if proj['actual_completion']:
                            proj['actual_completion'] = datetime.fromisoformat(proj['actual_completion'])
                        self._projects[proj['id']] = Project(**proj)
            except Exception as e:
                logger.error(f"Error loading projects: {e}")

    def _save_j3_data(self) -> None:
        """Save J3-specific data to disk."""
        # Save estimates
        estimates_file = self.data_dir / "estimates.json"
        with open(estimates_file, 'w') as f:
            json.dump([e.to_dict() for e in self._estimates.values()], f, indent=2)

        # Save projects
        projects_file = self.data_dir / "projects.json"
        with open(projects_file, 'w') as f:
            json.dump([p.to_dict() for p in self._projects.values()], f, indent=2)

    def get_industry_actions(self) -> List[str]:
        """Return J3-specific actions."""
        return [
            "process_inquiry",
            "calculate_estimate",
            "generate_quote_pdf",
            "schedule_walkthrough",
            "update_project_status",
            "send_customer_update",
            "get_material_costs",
            "weekly_pipeline_report"
        ]

    def process_industry_request(
        self,
        action: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route J3-specific requests."""
        handlers = {
            "process_inquiry": self.process_inquiry,
            "calculate_estimate": lambda d: self.calculate_estimate(
                JobType(d['job_type']),
                d['sqft'],
                d.get('materials', []),
                Complexity(d.get('complexity', 1.0)),
                d.get('lead_id')
            ),
            "generate_quote_pdf": lambda d: self.generate_quote_pdf(
                d['client_info'],
                d['estimate_id'],
                d.get('notes', ''),
                d.get('valid_days', 30)
            ),
            "schedule_walkthrough": lambda d: self.schedule_walkthrough(
                d['lead_id'],
                d['address'],
                d['datetime'],
                d.get('estimator', 'J3 Team')
            ),
            "update_project_status": lambda d: self.update_project_status(
                d['project_id'],
                ProjectStatus(d['status']),
                d.get('notes', '')
            ),
            "send_customer_update": lambda d: self.send_customer_update(
                d['project_id'],
                d['message']
            ),
            "get_material_costs": lambda d: self.get_material_costs(d['materials_list']),
            "weekly_pipeline_report": lambda d: self.weekly_pipeline_report(),
        }

        handler = handlers.get(action)
        if not handler:
            return {"error": f"Unknown J3 action: {action}"}

        return handler(data)

    def process_inquiry(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new inquiry from the J3 website or other source.

        Creates a lead and generates an auto-response using VULCAN.

        Args:
            customer_data: Customer information including:
                - name: Customer name
                - email: Email address
                - phone: Phone number
                - job_type: Type of work needed
                - description: Project description
                - address: Project address
                - source: Lead source (website, referral, etc.)

        Returns:
            Dict with lead info and auto-response
        """
        # Create the lead
        lead_id = str(uuid.uuid4())
        job_type_str = customer_data.get('job_type', 'custom')
        try:
            job_type = JobType(job_type_str)
        except ValueError:
            job_type = JobType.CUSTOM

        lead = Lead(
            id=lead_id,
            client_id=self.client_id,
            name=customer_data.get('name', 'Unknown'),
            email=customer_data.get('email', ''),
            phone=customer_data.get('phone', ''),
            status=LeadStatus.NEW,
            source=customer_data.get('source', 'website'),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            custom_data={
                'job_type': job_type.value,
                'description': customer_data.get('description', ''),
                'address': customer_data.get('address', ''),
                'sqft_estimate': customer_data.get('sqft', 0),
                'timeline': customer_data.get('timeline', 'flexible')
            }
        )

        self._leads_cache[lead_id] = lead
        self._save_data()

        # Generate auto-response using VULCAN
        prompt = f"""A customer has inquired about a {job_type.value} project.

Customer: {lead.name}
Project Description: {customer_data.get('description', 'Not provided')}
Address: {customer_data.get('address', 'Not provided')}
Timeline: {customer_data.get('timeline', 'Not specified')}

Generate a brief, professional response that:
1. Thanks them for their inquiry
2. Acknowledges their specific project type
3. Mentions we'll contact them within 24 hours to schedule a free estimate
4. Keep it under 100 words"""

        ai_response = self.query_baby(prompt)

        # Log the inquiry
        self.log_activity(
            action="inquiry_received",
            details={
                "lead_id": lead_id,
                "job_type": job_type.value,
                "source": lead.source,
                "auto_response_sent": ai_response.get('success', False)
            }
        )

        return {
            "lead": lead.to_dict(),
            "auto_response": ai_response.get('response', ''),
            "status": "success",
            "next_steps": [
                "Lead added to pipeline",
                "Auto-response generated",
                "Schedule walkthrough within 24 hours"
            ]
        }

    def calculate_estimate(
        self,
        job_type: JobType,
        sqft: float,
        materials: List[Dict[str, Any]],
        complexity: Complexity = Complexity.MODERATE,
        lead_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate a detailed estimate for a construction job.

        Args:
            job_type: Type of construction job
            sqft: Square footage of the project
            materials: List of material specifications
            complexity: Job complexity multiplier
            lead_id: Optional associated lead ID

        Returns:
            Complete estimate breakdown
        """
        estimate_id = str(uuid.uuid4())

        # Calculate material costs
        material_estimates = []
        material_total = 0.0

        # Default materials if none specified
        if not materials:
            materials = self._get_default_materials(job_type, sqft)

        for mat in materials:
            quantity = mat.get('quantity', 0)
            unit_price = mat.get('unit_price', 0) * self.MATERIAL_MARKUP
            total = quantity * unit_price
            material_total += total

            material_estimates.append(MaterialEstimate(
                name=mat.get('name', 'Unknown'),
                quantity=quantity,
                unit=mat.get('unit', 'each'),
                unit_price=unit_price,
                total=total
            ))

        # Calculate labor
        base_hours = sqft * self.LABOR_HOURS_PER_SQFT.get(job_type, 0.5)
        labor_hours = base_hours * complexity.value
        labor_total = labor_hours * self.LABOR_RATE

        # Calculate overhead and profit
        subtotal = material_total + labor_total
        overhead = subtotal * self.OVERHEAD_RATE
        profit = (subtotal + overhead) * self.PROFIT_MARGIN

        total = subtotal + overhead + profit

        estimate = JobEstimate(
            id=estimate_id,
            lead_id=lead_id or "",
            job_type=job_type,
            sqft=sqft,
            complexity=complexity,
            materials=material_estimates,
            labor_hours=labor_hours,
            labor_rate=self.LABOR_RATE,
            material_total=material_total,
            labor_total=labor_total,
            overhead=overhead,
            profit_margin=profit,
            total=total,
            valid_days=30,
            created_at=datetime.now()
        )

        self._estimates[estimate_id] = estimate
        self._save_j3_data()

        self.log_activity(
            action="estimate_created",
            details={
                "estimate_id": estimate_id,
                "job_type": job_type.value,
                "sqft": sqft,
                "total": total
            }
        )

        return estimate.to_dict()

    def _get_default_materials(
        self,
        job_type: JobType,
        sqft: float
    ) -> List[Dict[str, Any]]:
        """Get default material list for a job type."""
        defaults = {
            JobType.FRAMING: [
                {"name": "2x4 Studs", "quantity": sqft * 0.5, "unit": "each", "unit_price": 4.50},
                {"name": "2x6 Studs", "quantity": sqft * 0.2, "unit": "each", "unit_price": 6.75},
                {"name": "Plywood Sheathing", "quantity": sqft / 32, "unit": "sheet", "unit_price": 45.00},
                {"name": "Nails/Fasteners", "quantity": sqft * 0.1, "unit": "lb", "unit_price": 3.50},
                {"name": "Metal Connectors", "quantity": sqft * 0.05, "unit": "each", "unit_price": 2.25},
            ],
            JobType.DRYWALL: [
                {"name": "Drywall Sheets 4x8", "quantity": sqft / 32, "unit": "sheet", "unit_price": 12.50},
                {"name": "Joint Compound", "quantity": sqft / 100, "unit": "bucket", "unit_price": 18.00},
                {"name": "Drywall Tape", "quantity": sqft / 200, "unit": "roll", "unit_price": 8.50},
                {"name": "Drywall Screws", "quantity": sqft / 50, "unit": "box", "unit_price": 12.00},
                {"name": "Corner Bead", "quantity": sqft / 150, "unit": "piece", "unit_price": 4.50},
            ],
            JobType.FULL_REMODEL: [
                {"name": "Framing Materials", "quantity": 1, "unit": "package", "unit_price": sqft * 4.00},
                {"name": "Drywall Package", "quantity": 1, "unit": "package", "unit_price": sqft * 2.50},
                {"name": "Electrical Supplies", "quantity": 1, "unit": "package", "unit_price": sqft * 3.00},
                {"name": "Plumbing Supplies", "quantity": 1, "unit": "package", "unit_price": sqft * 4.50},
                {"name": "Finish Materials", "quantity": 1, "unit": "package", "unit_price": sqft * 8.00},
            ],
        }

        return defaults.get(job_type, [
            {"name": "General Materials", "quantity": 1, "unit": "package", "unit_price": sqft * 5.00}
        ])

    def generate_quote_pdf(
        self,
        client_info: Dict[str, Any],
        estimate_id: str,
        notes: str = "",
        valid_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a PDF quote document.

        Args:
            client_info: Customer information (name, address, contact)
            estimate_id: ID of the estimate to convert to quote
            notes: Additional notes for the quote
            valid_days: Number of days quote is valid

        Returns:
            Path to generated PDF and quote details
        """
        estimate = self._estimates.get(estimate_id)
        if not estimate:
            return {"error": f"Estimate {estimate_id} not found"}

        quote_id = str(uuid.uuid4())[:8].upper()
        quote_date = datetime.now()
        valid_until = quote_date + timedelta(days=valid_days)

        # Build quote content (would use actual PDF library in production)
        quote_content = f"""
========================================
J3 STRUCTURAL - CONSTRUCTION QUOTE
========================================

Quote #: Q-{quote_id}
Date: {quote_date.strftime('%B %d, %Y')}
Valid Until: {valid_until.strftime('%B %d, %Y')}

PREPARED FOR:
{client_info.get('name', 'Customer')}
{client_info.get('address', '')}
{client_info.get('email', '')}
{client_info.get('phone', '')}

PROJECT TYPE: {estimate.job_type.value.upper()}
SQUARE FOOTAGE: {estimate.sqft:,.0f} sq ft
COMPLEXITY: {estimate.complexity.name}

----------------------------------------
MATERIALS BREAKDOWN
----------------------------------------
"""
        for mat in estimate.materials:
            if isinstance(mat, MaterialEstimate):
                quote_content += f"{mat.name}: {mat.quantity:.1f} {mat.unit} @ ${mat.unit_price:.2f} = ${mat.total:.2f}\n"
            else:
                quote_content += f"{mat['name']}: {mat['quantity']:.1f} {mat['unit']} @ ${mat['unit_price']:.2f} = ${mat['total']:.2f}\n"

        quote_content += f"""
Materials Subtotal: ${estimate.material_total:,.2f}

----------------------------------------
LABOR
----------------------------------------
Estimated Hours: {estimate.labor_hours:.1f} hours
Labor Rate: ${estimate.labor_rate:.2f}/hour
Labor Total: ${estimate.labor_total:,.2f}

----------------------------------------
SUMMARY
----------------------------------------
Materials: ${estimate.material_total:,.2f}
Labor: ${estimate.labor_total:,.2f}
Overhead (12%): ${estimate.overhead:,.2f}
----------------------------------------
TOTAL: ${estimate.total:,.2f}
========================================

{notes if notes else ''}

TERMS & CONDITIONS:
- 50% deposit required to begin work
- Balance due upon completion
- Quote valid for {valid_days} days
- Permits not included unless specified
- J3 Structural is licensed and insured

Thank you for choosing J3 Structural!
Contact: (555) 123-4567 | info@j3structural.com
"""

        # Save quote file
        quotes_dir = self.data_dir / "quotes"
        quotes_dir.mkdir(exist_ok=True)
        quote_path = quotes_dir / f"quote_{quote_id}.txt"

        with open(quote_path, 'w') as f:
            f.write(quote_content)

        self.log_activity(
            action="quote_generated",
            details={
                "quote_id": quote_id,
                "estimate_id": estimate_id,
                "total": estimate.total,
                "valid_until": valid_until.isoformat()
            }
        )

        return {
            "quote_id": quote_id,
            "path": str(quote_path),
            "total": estimate.total,
            "valid_until": valid_until.isoformat(),
            "content_preview": quote_content[:500] + "..."
        }

    def schedule_walkthrough(
        self,
        lead_id: str,
        address: str,
        scheduled_datetime: str,
        estimator: str = "J3 Team"
    ) -> Dict[str, Any]:
        """
        Schedule an estimate walkthrough visit.

        Args:
            lead_id: Associated lead ID
            address: Project address
            scheduled_datetime: ISO datetime string
            estimator: Name of assigned estimator

        Returns:
            Appointment details
        """
        lead = self._leads_cache.get(lead_id)
        if not lead:
            return {"error": f"Lead {lead_id} not found"}

        appt_id = str(uuid.uuid4())
        dt = datetime.fromisoformat(scheduled_datetime)
        job_type_str = lead.custom_data.get('job_type', 'custom')

        try:
            job_type = JobType(job_type_str)
        except ValueError:
            job_type = JobType.CUSTOM

        appointment = WalkthroughAppointment(
            id=appt_id,
            lead_id=lead_id,
            client_name=lead.name,
            address=address,
            scheduled_datetime=dt,
            estimator=estimator,
            job_type=job_type
        )

        self._appointments[appt_id] = appointment

        # Update lead status
        lead.status = LeadStatus.CONTACTED
        lead.custom_data['walkthrough_scheduled'] = scheduled_datetime
        lead.updated_at = datetime.now()
        self._save_data()

        self.log_activity(
            action="walkthrough_scheduled",
            details={
                "appointment_id": appt_id,
                "lead_id": lead_id,
                "datetime": scheduled_datetime,
                "estimator": estimator
            }
        )

        # Generate confirmation message
        prompt = f"""Generate a brief SMS confirmation for a construction estimate appointment:
Customer: {lead.name}
Date/Time: {dt.strftime('%A, %B %d at %I:%M %p')}
Address: {address}
Estimator: {estimator}

Keep it under 160 characters."""

        ai_response = self.query_baby(prompt)

        return {
            "appointment": appointment.to_dict(),
            "confirmation_message": ai_response.get('response', 'Appointment confirmed!'),
            "status": "scheduled"
        }

    def update_project_status(
        self,
        project_id: str,
        status: ProjectStatus,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Update the status of an active project.

        Args:
            project_id: Project ID
            status: New project status
            notes: Optional notes about the update

        Returns:
            Updated project details
        """
        project = self._projects.get(project_id)
        if not project:
            return {"error": f"Project {project_id} not found"}

        old_status = project.status
        project.status = status

        if notes:
            project.notes.append(f"[{datetime.now().isoformat()}] {notes}")

        # Handle status-specific updates
        if status == ProjectStatus.IN_PROGRESS and not project.start_date:
            project.start_date = datetime.now()

        if status == ProjectStatus.COMPLETE:
            project.actual_completion = datetime.now()

        self._save_j3_data()

        self.log_activity(
            action="project_status_updated",
            details={
                "project_id": project_id,
                "old_status": old_status.value,
                "new_status": status.value,
                "notes": notes
            }
        )

        return {
            "project": project.to_dict(),
            "status_changed": True,
            "old_status": old_status.value,
            "new_status": status.value
        }

    def send_customer_update(
        self,
        project_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send an update message to the customer.

        Args:
            project_id: Project ID
            message: Message to send

        Returns:
            Confirmation of message sent
        """
        project = self._projects.get(project_id)
        if not project:
            return {"error": f"Project {project_id} not found"}

        # Get associated lead for contact info
        lead = self._leads_cache.get(project.lead_id)
        contact_info = {
            "name": project.client_name,
            "email": lead.email if lead else "",
            "phone": lead.phone if lead else ""
        }

        # Enhance message with AI
        prompt = f"""Improve this customer update message for a construction project:

Original message: {message}
Project type: {project.job_type.value}
Current status: {project.status.value}

Make it professional but friendly. Keep the same meaning but improve clarity."""

        ai_response = self.query_baby(prompt)
        enhanced_message = ai_response.get('response', message)

        # Log the customer contact
        project.notes.append(f"[{datetime.now().isoformat()}] UPDATE SENT: {message}")
        self._save_j3_data()

        self.log_activity(
            action="customer_update_sent",
            details={
                "project_id": project_id,
                "message_length": len(message),
                "contact": contact_info.get('email', contact_info.get('phone', 'unknown'))
            }
        )

        return {
            "sent": True,
            "project_id": project_id,
            "recipient": contact_info,
            "original_message": message,
            "enhanced_message": enhanced_message,
            "timestamp": datetime.now().isoformat()
        }

    def get_material_costs(self, materials_list: List[str]) -> Dict[str, Any]:
        """
        Get current pricing for specified materials.

        Args:
            materials_list: List of material names to price

        Returns:
            Material pricing information
        """
        # Standard material pricing (would connect to supplier API in production)
        pricing_database = {
            "2x4 stud": {"price": 4.50, "unit": "each", "supplier": "Home Depot"},
            "2x6 stud": {"price": 6.75, "unit": "each", "supplier": "Home Depot"},
            "plywood 4x8": {"price": 45.00, "unit": "sheet", "supplier": "Lowes"},
            "osb 4x8": {"price": 32.00, "unit": "sheet", "supplier": "Home Depot"},
            "drywall 4x8": {"price": 12.50, "unit": "sheet", "supplier": "Home Depot"},
            "drywall 4x12": {"price": 18.75, "unit": "sheet", "supplier": "Lowes"},
            "joint compound 5gal": {"price": 18.00, "unit": "bucket", "supplier": "Home Depot"},
            "drywall tape": {"price": 8.50, "unit": "roll", "supplier": "Home Depot"},
            "drywall screws": {"price": 12.00, "unit": "box", "supplier": "Home Depot"},
            "framing nails": {"price": 45.00, "unit": "box", "supplier": "Home Depot"},
            "insulation r13": {"price": 42.00, "unit": "roll", "supplier": "Lowes"},
            "insulation r19": {"price": 58.00, "unit": "roll", "supplier": "Lowes"},
            "vapor barrier": {"price": 85.00, "unit": "roll", "supplier": "Home Depot"},
            "concrete mix": {"price": 5.50, "unit": "bag", "supplier": "Lowes"},
            "rebar #4": {"price": 8.25, "unit": "20ft", "supplier": "Metal Supply"},
        }

        results = []
        total = 0.0

        for material in materials_list:
            material_lower = material.lower()
            found = False

            for key, data in pricing_database.items():
                if key in material_lower or material_lower in key:
                    results.append({
                        "requested": material,
                        "matched": key,
                        "price": data["price"],
                        "unit": data["unit"],
                        "supplier": data["supplier"]
                    })
                    total += data["price"]
                    found = True
                    break

            if not found:
                results.append({
                    "requested": material,
                    "matched": None,
                    "price": None,
                    "unit": None,
                    "note": "Material not in database - manual quote needed"
                })

        return {
            "materials": results,
            "found_count": len([r for r in results if r.get("matched")]),
            "total_found": total,
            "pricing_date": datetime.now().isoformat(),
            "note": "Prices subject to change. Contact suppliers for current quotes."
        }

    def weekly_pipeline_report(self) -> Dict[str, Any]:
        """
        Generate a weekly pipeline report.

        Returns:
            Comprehensive report of leads, quotes, projects, and revenue
        """
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        # Count leads by status
        lead_counts = {}
        new_leads_this_week = 0
        for lead in self._leads_cache.values():
            status = lead.status.value
            lead_counts[status] = lead_counts.get(status, 0) + 1
            if lead.created_at >= week_ago:
                new_leads_this_week += 1

        # Count estimates
        estimates_this_week = len([
            e for e in self._estimates.values()
            if e.created_at >= week_ago
        ])
        total_quoted = sum(e.total for e in self._estimates.values() if e.created_at >= week_ago)

        # Project stats
        active_projects = [p for p in self._projects.values() if p.status not in [ProjectStatus.COMPLETE, ProjectStatus.CANCELLED]]
        completed_this_week = len([
            p for p in self._projects.values()
            if p.status == ProjectStatus.COMPLETE and p.actual_completion and p.actual_completion >= week_ago
        ])

        active_revenue = sum(p.contract_value for p in active_projects)
        completed_revenue = sum(
            p.contract_value for p in self._projects.values()
            if p.status == ProjectStatus.COMPLETE and p.actual_completion and p.actual_completion >= week_ago
        )

        # Upcoming appointments
        upcoming = [
            a.to_dict() for a in self._appointments.values()
            if a.scheduled_datetime >= now
        ]

        report = {
            "report_date": now.isoformat(),
            "period": {
                "start": week_ago.isoformat(),
                "end": now.isoformat()
            },
            "leads": {
                "total": len(self._leads_cache),
                "new_this_week": new_leads_this_week,
                "by_status": lead_counts
            },
            "estimates": {
                "created_this_week": estimates_this_week,
                "total_quoted_value": total_quoted,
                "total_all_time": len(self._estimates)
            },
            "projects": {
                "active": len(active_projects),
                "completed_this_week": completed_this_week,
                "active_revenue": active_revenue,
                "completed_revenue_this_week": completed_revenue
            },
            "appointments": {
                "upcoming_count": len(upcoming),
                "next_5": sorted(upcoming, key=lambda x: x['scheduled_datetime'])[:5]
            },
            "revenue_summary": {
                "pipeline_value": total_quoted,
                "active_contracts": active_revenue,
                "completed_this_week": completed_revenue
            }
        }

        self.log_activity(
            action="weekly_report_generated",
            details={"report_date": now.isoformat()}
        )

        return report

    def create_project_from_estimate(
        self,
        estimate_id: str,
        contract_value: Optional[float] = None,
        start_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert an accepted estimate into an active project.

        Args:
            estimate_id: Estimate ID to convert
            contract_value: Final contract value (defaults to estimate total)
            start_date: Planned start date

        Returns:
            Created project details
        """
        estimate = self._estimates.get(estimate_id)
        if not estimate:
            return {"error": f"Estimate {estimate_id} not found"}

        lead = self._leads_cache.get(estimate.lead_id)
        if not lead:
            return {"error": f"Associated lead not found"}

        project_id = str(uuid.uuid4())
        start = datetime.fromisoformat(start_date) if start_date else None

        # Estimate completion based on job type and sqft
        days_to_complete = int(estimate.labor_hours / 8 * 1.5)  # Account for non-productive time
        estimated_completion = start + timedelta(days=days_to_complete) if start else None

        project = Project(
            id=project_id,
            lead_id=estimate.lead_id,
            estimate_id=estimate_id,
            client_name=lead.name,
            address=lead.custom_data.get('address', ''),
            job_type=estimate.job_type,
            status=ProjectStatus.CONTRACT_SIGNED,
            contract_value=contract_value or estimate.total,
            start_date=start,
            estimated_completion=estimated_completion,
            actual_completion=None,
            milestones={
                "contract_signed": True,
                "permits_obtained": False,
                "materials_ordered": False,
                "work_started": False,
                "rough_complete": False,
                "final_inspection": False,
                "customer_signoff": False
            }
        )

        self._projects[project_id] = project

        # Update lead status
        lead.status = LeadStatus.WON
        lead.value = project.contract_value
        lead.updated_at = datetime.now()

        self._save_data()
        self._save_j3_data()

        self.log_activity(
            action="project_created",
            details={
                "project_id": project_id,
                "estimate_id": estimate_id,
                "contract_value": project.contract_value
            }
        )

        return {
            "project": project.to_dict(),
            "status": "created",
            "next_steps": [
                "Obtain necessary permits",
                "Order materials",
                "Schedule crew",
                "Confirm start date with customer"
            ]
        }
