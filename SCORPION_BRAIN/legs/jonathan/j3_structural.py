"""
J3 Structural Solutions - Construction Operations
=================================================
Complete construction project management with invoice
generation and material calculations.

Connects to j3/quote_generator for automated quotes.
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


class ProjectStatus(Enum):
    """Status of a construction project."""
    QUOTE = "quote"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InvoiceStatus(Enum):
    """Status of an invoice."""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


@dataclass
class Material:
    """A construction material."""
    id: str
    name: str
    unit: str  # sqft, linear_ft, each, cubic_yard
    unit_price: float
    quantity: float = 0.0
    supplier: str = ""
    lead_time_days: int = 0

    @property
    def total_cost(self) -> float:
        return self.unit_price * self.quantity

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "unit": self.unit,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "total_cost": round(self.total_cost, 2),
            "supplier": self.supplier,
            "lead_time_days": self.lead_time_days
        }


@dataclass
class Project:
    """A construction project."""
    id: str
    name: str
    client_name: str
    client_phone: str
    client_email: str
    address: str
    status: ProjectStatus = ProjectStatus.QUOTE
    description: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    estimated_hours: float = 0.0
    hourly_rate: float = 75.0
    materials: List[Material] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def labor_cost(self) -> float:
        return self.estimated_hours * self.hourly_rate

    @property
    def materials_cost(self) -> float:
        return sum(m.total_cost for m in self.materials)

    @property
    def total_cost(self) -> float:
        return self.labor_cost + self.materials_cost

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "client_name": self.client_name,
            "client_phone": self.client_phone,
            "client_email": self.client_email,
            "address": self.address,
            "status": self.status.value,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "estimated_hours": self.estimated_hours,
            "hourly_rate": self.hourly_rate,
            "labor_cost": round(self.labor_cost, 2),
            "materials_cost": round(self.materials_cost, 2),
            "total_cost": round(self.total_cost, 2),
            "materials": [m.to_dict() for m in self.materials],
            "notes": self.notes
        }


@dataclass
class Invoice:
    """An invoice for a project."""
    id: str
    project_id: str
    client_name: str
    client_email: str
    items: List[Dict] = field(default_factory=list)
    subtotal: float = 0.0
    tax_rate: float = 0.0825  # 8.25%
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))
    created_at: datetime = field(default_factory=datetime.now)
    paid_at: Optional[datetime] = None
    notes: str = ""

    @property
    def tax_amount(self) -> float:
        return self.subtotal * self.tax_rate

    @property
    def total(self) -> float:
        return self.subtotal + self.tax_amount

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "client_name": self.client_name,
            "client_email": self.client_email,
            "items": self.items,
            "subtotal": round(self.subtotal, 2),
            "tax_rate": self.tax_rate,
            "tax_amount": round(self.tax_amount, 2),
            "total": round(self.total, 2),
            "status": self.status.value,
            "due_date": self.due_date.strftime("%Y-%m-%d"),
            "created_at": self.created_at.isoformat(),
            "notes": self.notes
        }


# Standard materials catalog
MATERIALS_CATALOG = {
    "concrete": Material("MAT001", "Concrete Mix", "cubic_yard", 125.00, supplier="BuildCo"),
    "rebar": Material("MAT002", "Rebar #4", "linear_ft", 0.85, supplier="SteelMax"),
    "lumber_2x4": Material("MAT003", "Lumber 2x4x8", "each", 4.50, supplier="Lumber Yard"),
    "lumber_2x6": Material("MAT004", "Lumber 2x6x8", "each", 6.75, supplier="Lumber Yard"),
    "plywood": Material("MAT005", "Plywood 4x8 3/4\"", "each", 45.00, supplier="Lumber Yard"),
    "drywall": Material("MAT006", "Drywall 4x8", "each", 12.50, supplier="BuildCo"),
    "insulation": Material("MAT007", "R-19 Insulation", "sqft", 0.75, supplier="InsulPro"),
    "roofing": Material("MAT008", "Shingles Bundle", "each", 35.00, supplier="RoofSupply"),
    "paint": Material("MAT009", "Exterior Paint Gallon", "each", 45.00, supplier="PaintPro"),
    "nails": Material("MAT010", "Framing Nails Box", "each", 55.00, supplier="BuildCo"),
}


class J3StructuralLeg:
    """
    J3 Structural Solutions Construction Management.

    Connects to j3/quote_generator for automated quotes.
    """

    def __init__(self, data_dir: str = "/tmp/j3_structural"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.projects: Dict[str, Project] = {}
        self.invoices: Dict[str, Invoice] = {}
        self._load_data()

    def _load_data(self):
        """Load existing data."""
        projects_file = self.data_dir / "projects.json"
        if projects_file.exists():
            with open(projects_file) as f:
                data = json.load(f)
                for p in data:
                    p["status"] = ProjectStatus(p["status"])
                    p["created_at"] = datetime.fromisoformat(p["created_at"])
                    if p.get("start_date"):
                        p["start_date"] = datetime.fromisoformat(p["start_date"])
                    if p.get("end_date"):
                        p["end_date"] = datetime.fromisoformat(p["end_date"])
                    p["materials"] = [Material(**m) for m in p.get("materials", [])]
                    self.projects[p["id"]] = Project(**{k: v for k, v in p.items() if k not in ["labor_cost", "materials_cost", "total_cost"]})

    def _save_data(self):
        """Save data to disk."""
        with open(self.data_dir / "projects.json", "w") as f:
            json.dump([p.to_dict() for p in self.projects.values()], f, indent=2)

    def create_project(self, name: str, client_name: str, client_phone: str,
                       client_email: str, address: str, **kwargs) -> Project:
        """Create a new project."""
        project_id = f"J3-{datetime.now().strftime('%Y%m')}-{len(self.projects) + 1:04d}"

        project = Project(
            id=project_id,
            name=name,
            client_name=client_name,
            client_phone=client_phone,
            client_email=client_email,
            address=address,
            description=kwargs.get("description", ""),
            estimated_hours=kwargs.get("estimated_hours", 0.0),
            hourly_rate=kwargs.get("hourly_rate", 75.0)
        )

        self.projects[project_id] = project
        self._save_data()
        logger.info(f"Project created: {project_id}")
        return project

    def add_material(self, project_id: str, material_code: str, quantity: float) -> bool:
        """Add material to a project."""
        if project_id not in self.projects:
            return False

        if material_code not in MATERIALS_CATALOG:
            return False

        template = MATERIALS_CATALOG[material_code]
        material = Material(
            id=template.id,
            name=template.name,
            unit=template.unit,
            unit_price=template.unit_price,
            quantity=quantity,
            supplier=template.supplier
        )

        self.projects[project_id].materials.append(material)
        self._save_data()
        return True

    def calculate_materials(self, project_type: str, sqft: float) -> Dict[str, float]:
        """Calculate materials needed based on project type and size."""
        calculations = {
            "foundation": {
                "concrete": sqft * 0.5 / 27,  # cubic yards
                "rebar": sqft * 2.0,  # linear feet
            },
            "framing": {
                "lumber_2x4": sqft * 0.75,  # per sqft
                "lumber_2x6": sqft * 0.25,
                "plywood": sqft / 32,  # sheets
                "nails": sqft / 500,  # boxes
            },
            "roofing": {
                "roofing": sqft / 33.3,  # bundles per 100 sqft
                "plywood": sqft / 32,
            },
            "interior": {
                "drywall": sqft / 32,
                "insulation": sqft,
                "paint": sqft / 350,  # gallons
            }
        }

        if project_type not in calculations:
            return {}

        result = {}
        for material, quantity in calculations[project_type].items():
            if material in MATERIALS_CATALOG:
                mat = MATERIALS_CATALOG[material]
                result[material] = {
                    "quantity": round(quantity, 2),
                    "unit": mat.unit,
                    "unit_price": mat.unit_price,
                    "total": round(quantity * mat.unit_price, 2)
                }

        return result

    def generate_invoice(self, project_id: str) -> Optional[Invoice]:
        """Generate invoice for a project."""
        if project_id not in self.projects:
            return None

        project = self.projects[project_id]
        invoice_id = f"INV-{project_id}-{len(self.invoices) + 1:03d}"

        items = []
        if project.labor_cost > 0:
            items.append({
                "description": f"Labor ({project.estimated_hours} hours @ ${project.hourly_rate}/hr)",
                "amount": project.labor_cost
            })

        for material in project.materials:
            items.append({
                "description": f"{material.name} ({material.quantity} {material.unit})",
                "amount": material.total_cost
            })

        invoice = Invoice(
            id=invoice_id,
            project_id=project_id,
            client_name=project.client_name,
            client_email=project.client_email,
            items=items,
            subtotal=project.total_cost
        )

        self.invoices[invoice_id] = invoice
        return invoice

    def get_project_summary(self, project_id: str) -> Dict:
        """Get project summary."""
        if project_id not in self.projects:
            return {}

        project = self.projects[project_id]
        return project.to_dict()

    def get_dashboard(self) -> Dict:
        """Get business dashboard."""
        active = [p for p in self.projects.values() if p.status == ProjectStatus.IN_PROGRESS]
        pending = [p for p in self.projects.values() if p.status in [ProjectStatus.QUOTE, ProjectStatus.APPROVED]]
        completed = [p for p in self.projects.values() if p.status == ProjectStatus.COMPLETED]

        return {
            "active_projects": len(active),
            "pending_projects": len(pending),
            "completed_projects": len(completed),
            "total_revenue": sum(p.total_cost for p in completed),
            "pending_revenue": sum(p.total_cost for p in active + pending),
            "recent_projects": [p.to_dict() for p in list(self.projects.values())[-5:]]
        }


# Convenience functions
def project_tracker(project_id: str = None) -> Dict:
    """Track project or get all projects."""
    leg = J3StructuralLeg()
    if project_id:
        return leg.get_project_summary(project_id)
    return leg.get_dashboard()


def invoice_generator(project_id: str) -> Optional[Invoice]:
    """Generate invoice for project."""
    leg = J3StructuralLeg()
    return leg.generate_invoice(project_id)


def material_calculator(project_type: str, sqft: float) -> Dict:
    """Calculate materials needed."""
    leg = J3StructuralLeg()
    return leg.calculate_materials(project_type, sqft)


if __name__ == "__main__":
    # Demo
    leg = J3StructuralLeg()

    # Create a project
    project = leg.create_project(
        name="Smith Residence Foundation",
        client_name="Bob Smith",
        client_phone="555-9876",
        client_email="bob@email.com",
        address="123 Main St",
        estimated_hours=40,
        hourly_rate=85
    )
    print(f"Project created: {project.id}")

    # Add materials
    leg.add_material(project.id, "concrete", 15)
    leg.add_material(project.id, "rebar", 500)

    # Calculate materials for a framing job
    print("\nMaterials for 2000 sqft framing:")
    materials = leg.calculate_materials("framing", 2000)
    for mat, info in materials.items():
        print(f"  {mat}: {info['quantity']} {info['unit']} = ${info['total']}")

    # Generate invoice
    invoice = leg.generate_invoice(project.id)
    if invoice:
        print(f"\nInvoice: {invoice.id}")
        print(f"Total: ${invoice.total:.2f}")
