"""
J3 Quote Generator
==================

Calculate construction estimates and generate professional PDF quotes.
Supports framing, drywall, full remodels, and additions.

Requirements:
    pip install reportlab jinja2
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("J3.quote_generator")

# Job type configurations
JOB_TYPES = {
    "framing": {
        "name": "Framing",
        "description": "Structural framing including walls, floors, and roof",
        "base_rate_sqft": 8.50,  # Base labor rate per sqft
        "complexity_multiplier": 1.0,
        "typical_duration_days_per_1000sqft": 5
    },
    "drywall": {
        "name": "Drywall Installation",
        "description": "Drywall hanging, taping, and finishing",
        "base_rate_sqft": 4.25,
        "complexity_multiplier": 1.0,
        "typical_duration_days_per_1000sqft": 3
    },
    "full_remodel": {
        "name": "Full Remodel",
        "description": "Complete room remodel including demo, framing, electrical, plumbing, drywall, and finish",
        "base_rate_sqft": 75.00,
        "complexity_multiplier": 1.5,
        "typical_duration_days_per_1000sqft": 20
    },
    "addition": {
        "name": "Room Addition",
        "description": "New construction addition to existing structure",
        "base_rate_sqft": 150.00,
        "complexity_multiplier": 1.75,
        "typical_duration_days_per_1000sqft": 30
    },
    "kitchen": {
        "name": "Kitchen Remodel",
        "description": "Complete kitchen renovation",
        "base_rate_sqft": 125.00,
        "complexity_multiplier": 1.5,
        "typical_duration_days_per_1000sqft": 15
    },
    "bathroom": {
        "name": "Bathroom Remodel",
        "description": "Complete bathroom renovation",
        "base_rate_sqft": 175.00,
        "complexity_multiplier": 1.4,
        "typical_duration_days_per_1000sqft": 10
    },
    "deck": {
        "name": "Deck Construction",
        "description": "New deck or patio construction",
        "base_rate_sqft": 35.00,
        "complexity_multiplier": 1.0,
        "typical_duration_days_per_1000sqft": 5
    },
    "siding": {
        "name": "Siding Installation",
        "description": "Exterior siding replacement or installation",
        "base_rate_sqft": 12.00,
        "complexity_multiplier": 1.0,
        "typical_duration_days_per_1000sqft": 4
    }
}

# Material cost lookup table (per sqft or unit)
MATERIAL_COSTS = {
    "lumber_standard": {
        "name": "Standard Lumber",
        "cost_per_sqft": 3.50,
        "description": "SPF framing lumber"
    },
    "lumber_premium": {
        "name": "Premium Lumber",
        "cost_per_sqft": 5.25,
        "description": "Douglas Fir or better"
    },
    "drywall_standard": {
        "name": "Standard Drywall",
        "cost_per_sqft": 0.85,
        "description": "1/2\" standard drywall"
    },
    "drywall_moisture": {
        "name": "Moisture Resistant",
        "cost_per_sqft": 1.25,
        "description": "Green board for wet areas"
    },
    "insulation_standard": {
        "name": "Fiberglass Insulation",
        "cost_per_sqft": 1.50,
        "description": "R-19 fiberglass batts"
    },
    "insulation_spray": {
        "name": "Spray Foam Insulation",
        "cost_per_sqft": 3.75,
        "description": "Closed cell spray foam"
    },
    "flooring_laminate": {
        "name": "Laminate Flooring",
        "cost_per_sqft": 4.00,
        "description": "Quality laminate with pad"
    },
    "flooring_hardwood": {
        "name": "Hardwood Flooring",
        "cost_per_sqft": 8.50,
        "description": "Solid hardwood"
    },
    "flooring_tile": {
        "name": "Tile Flooring",
        "cost_per_sqft": 6.50,
        "description": "Ceramic or porcelain tile"
    },
    "paint_standard": {
        "name": "Standard Paint",
        "cost_per_sqft": 0.75,
        "description": "Interior latex paint"
    },
    "paint_premium": {
        "name": "Premium Paint",
        "cost_per_sqft": 1.25,
        "description": "High-quality paint with primer"
    },
    "deck_pressure_treated": {
        "name": "Pressure Treated Deck",
        "cost_per_sqft": 12.00,
        "description": "Pressure treated lumber"
    },
    "deck_composite": {
        "name": "Composite Deck",
        "cost_per_sqft": 22.00,
        "description": "Trex or similar composite"
    },
    "siding_vinyl": {
        "name": "Vinyl Siding",
        "cost_per_sqft": 4.50,
        "description": "Standard vinyl siding"
    },
    "siding_fiber_cement": {
        "name": "Fiber Cement Siding",
        "cost_per_sqft": 8.00,
        "description": "HardiePlank or similar"
    }
}

# Labor rate configuration
LABOR_CONFIG = {
    "base_hourly_rate": 65.00,
    "overtime_multiplier": 1.5,
    "weekend_multiplier": 1.25,
    "crew_size_default": 2,
    "hours_per_day": 8
}


@dataclass
class ClientInfo:
    """Client information for quotes."""
    name: str
    email: str
    phone: str
    address: str
    city: str = ""
    state: str = ""
    zip_code: str = ""
    notes: str = ""


@dataclass
class QuoteLineItem:
    """Individual line item in a quote."""
    description: str
    quantity: float
    unit: str
    unit_price: float
    total: float
    category: str = "general"


@dataclass
class Quote:
    """Complete quote structure."""
    quote_number: str
    client: ClientInfo
    job_type: str
    job_description: str
    line_items: List[QuoteLineItem]
    labor_cost: float
    materials_cost: float
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float
    estimated_duration: str
    valid_until: str
    created_at: str
    notes: str = ""
    terms: str = ""


class QuoteGenerator:
    """
    Generate professional construction quotes.

    Usage:
        gen = QuoteGenerator()
        quote = gen.calculate_estimate("framing", sqft=1500)
        pdf_path = gen.generate_quote_pdf(client_info, quote)
    """

    def __init__(
        self,
        company_name: str = "J3 Construction",
        company_address: str = "",
        company_phone: str = "",
        company_email: str = "",
        tax_rate: float = 0.0825,  # 8.25% default
        output_dir: str = "quotes"
    ):
        self.company_name = company_name
        self.company_address = company_address
        self.company_phone = company_phone
        self.company_email = company_email
        self.tax_rate = tax_rate
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self._quote_counter = self._load_counter()

    def _load_counter(self) -> int:
        """Load quote counter from file."""
        counter_file = self.output_dir / ".quote_counter"
        if counter_file.exists():
            return int(counter_file.read_text().strip())
        return 1000

    def _save_counter(self):
        """Save quote counter to file."""
        counter_file = self.output_dir / ".quote_counter"
        counter_file.write_text(str(self._quote_counter))

    def _generate_quote_number(self) -> str:
        """Generate unique quote number."""
        self._quote_counter += 1
        self._save_counter()
        date_prefix = datetime.now().strftime("%Y%m")
        return f"Q-{date_prefix}-{self._quote_counter:04d}"

    def calculate_estimate(
        self,
        job_type: str,
        sqft: float,
        materials: str = "standard",
        complexity: str = "normal",
        include_materials: bool = True,
        additional_items: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Calculate a job estimate.

        Args:
            job_type: Type of job (framing, drywall, full_remodel, etc.)
            sqft: Square footage
            materials: Material grade (standard, premium)
            complexity: Job complexity (simple, normal, complex)
            include_materials: Whether to include material costs
            additional_items: Extra line items to add

        Returns:
            Estimate dictionary with breakdown
        """
        if job_type not in JOB_TYPES:
            raise ValueError(f"Unknown job type: {job_type}. Available: {list(JOB_TYPES.keys())}")

        job_config = JOB_TYPES[job_type]

        # Complexity multipliers
        complexity_mults = {
            "simple": 0.85,
            "normal": 1.0,
            "complex": 1.3,
            "very_complex": 1.5
        }
        complexity_mult = complexity_mults.get(complexity, 1.0)

        # Calculate labor
        base_labor = job_config["base_rate_sqft"] * sqft
        labor_cost = base_labor * job_config["complexity_multiplier"] * complexity_mult

        # Calculate materials
        materials_cost = 0
        material_items = []

        if include_materials:
            materials_cost, material_items = self._calculate_materials(
                job_type, sqft, materials
            )

        # Calculate duration
        days = (sqft / 1000) * job_config["typical_duration_days_per_1000sqft"]
        days = max(1, int(days * complexity_mult))

        # Build line items
        line_items = [
            QuoteLineItem(
                description=f"{job_config['name']} Labor",
                quantity=sqft,
                unit="sq ft",
                unit_price=round(labor_cost / sqft, 2),
                total=round(labor_cost, 2),
                category="labor"
            )
        ]

        line_items.extend(material_items)

        # Add additional items
        if additional_items:
            for item in additional_items:
                line_items.append(QuoteLineItem(
                    description=item.get("description", "Additional Item"),
                    quantity=item.get("quantity", 1),
                    unit=item.get("unit", "ea"),
                    unit_price=item.get("unit_price", 0),
                    total=item.get("total", item.get("quantity", 1) * item.get("unit_price", 0)),
                    category=item.get("category", "other")
                ))

        # Calculate totals
        subtotal = labor_cost + materials_cost
        for item in (additional_items or []):
            subtotal += item.get("total", item.get("quantity", 1) * item.get("unit_price", 0))

        tax_amount = subtotal * self.tax_rate
        total = subtotal + tax_amount

        return {
            "job_type": job_type,
            "job_name": job_config["name"],
            "job_description": job_config["description"],
            "sqft": sqft,
            "materials_grade": materials,
            "complexity": complexity,
            "line_items": [asdict(item) for item in line_items],
            "labor_cost": round(labor_cost, 2),
            "materials_cost": round(materials_cost, 2),
            "subtotal": round(subtotal, 2),
            "tax_rate": self.tax_rate,
            "tax_amount": round(tax_amount, 2),
            "total": round(total, 2),
            "estimated_days": days,
            "estimated_duration": f"{days} business days"
        }

    def _calculate_materials(
        self,
        job_type: str,
        sqft: float,
        grade: str
    ) -> tuple:
        """Calculate material costs based on job type."""
        materials_cost = 0
        items = []

        # Job-specific material mappings
        material_mappings = {
            "framing": [
                ("lumber_standard" if grade == "standard" else "lumber_premium", 1.0),
            ],
            "drywall": [
                ("drywall_standard" if grade == "standard" else "drywall_moisture", 1.0),
            ],
            "full_remodel": [
                ("lumber_standard" if grade == "standard" else "lumber_premium", 0.3),
                ("drywall_standard", 0.8),
                ("insulation_standard" if grade == "standard" else "insulation_spray", 0.6),
                ("paint_standard" if grade == "standard" else "paint_premium", 1.0),
            ],
            "addition": [
                ("lumber_premium", 0.4),
                ("drywall_standard", 0.8),
                ("insulation_spray", 0.6),
                ("paint_premium", 1.0),
            ],
            "deck": [
                ("deck_pressure_treated" if grade == "standard" else "deck_composite", 1.0),
            ],
            "siding": [
                ("siding_vinyl" if grade == "standard" else "siding_fiber_cement", 1.0),
            ],
            "kitchen": [
                ("drywall_moisture", 0.3),
                ("flooring_tile", 1.0),
                ("paint_premium", 0.5),
            ],
            "bathroom": [
                ("drywall_moisture", 0.5),
                ("flooring_tile", 1.0),
                ("paint_premium", 0.5),
            ]
        }

        materials = material_mappings.get(job_type, [])

        for material_key, coverage in materials:
            if material_key in MATERIAL_COSTS:
                material = MATERIAL_COSTS[material_key]
                qty = sqft * coverage
                cost = material["cost_per_sqft"] * qty
                materials_cost += cost

                items.append(QuoteLineItem(
                    description=material["name"],
                    quantity=round(qty, 1),
                    unit="sq ft",
                    unit_price=material["cost_per_sqft"],
                    total=round(cost, 2),
                    category="materials"
                ))

        return materials_cost, items

    def create_quote(
        self,
        client_info: Union[ClientInfo, Dict],
        estimate: Dict,
        notes: str = "",
        valid_days: int = 30
    ) -> Quote:
        """
        Create a formal quote from an estimate.

        Args:
            client_info: Client information
            estimate: Estimate dictionary from calculate_estimate()
            notes: Additional notes
            valid_days: Number of days quote is valid

        Returns:
            Quote object
        """
        if isinstance(client_info, dict):
            client_info = ClientInfo(**client_info)

        # Convert line items
        line_items = [
            QuoteLineItem(**item) for item in estimate["line_items"]
        ]

        quote = Quote(
            quote_number=self._generate_quote_number(),
            client=client_info,
            job_type=estimate["job_type"],
            job_description=estimate["job_description"],
            line_items=line_items,
            labor_cost=estimate["labor_cost"],
            materials_cost=estimate["materials_cost"],
            subtotal=estimate["subtotal"],
            tax_rate=estimate["tax_rate"],
            tax_amount=estimate["tax_amount"],
            total=estimate["total"],
            estimated_duration=estimate["estimated_duration"],
            valid_until=(datetime.now() + timedelta(days=valid_days)).strftime("%B %d, %Y"),
            created_at=datetime.now().isoformat(),
            notes=notes,
            terms=self._get_default_terms()
        )

        return quote

    def _get_default_terms(self) -> str:
        """Get default quote terms and conditions."""
        return """TERMS AND CONDITIONS:
1. Quote valid for 30 days from issue date
2. 50% deposit required to begin work
3. Balance due upon completion
4. All work guaranteed for 1 year
5. Permits and inspections included where required
6. Customer responsible for clearing work area
7. Changes to scope may affect pricing and timeline
8. Payment accepted: Check, Credit Card, or Bank Transfer"""

    def generate_quote_pdf(
        self,
        quote: Quote,
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Generate a PDF quote document.

        Args:
            quote: Quote object
            output_path: Optional output path

        Returns:
            Path to generated PDF
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        except ImportError:
            logger.error("reportlab not installed. Run: pip install reportlab")
            # Fall back to text file
            return self._generate_quote_text(quote, output_path)

        if output_path is None:
            output_path = self.output_dir / f"{quote.quote_number}.pdf"

        output_path = Path(output_path)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        styles = getSampleStyleSheet()
        story = []

        # Header
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=12
        )
        story.append(Paragraph(self.company_name, header_style))

        if self.company_address:
            story.append(Paragraph(self.company_address, styles['Normal']))
        if self.company_phone:
            story.append(Paragraph(f"Phone: {self.company_phone}", styles['Normal']))
        if self.company_email:
            story.append(Paragraph(f"Email: {self.company_email}", styles['Normal']))

        story.append(Spacer(1, 0.25*inch))

        # Quote number and date
        story.append(Paragraph(f"<b>Quote #:</b> {quote.quote_number}", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Paragraph(f"<b>Valid Until:</b> {quote.valid_until}", styles['Normal']))

        story.append(Spacer(1, 0.25*inch))

        # Client info
        story.append(Paragraph("<b>PREPARED FOR:</b>", styles['Heading3']))
        story.append(Paragraph(quote.client.name, styles['Normal']))
        story.append(Paragraph(quote.client.address, styles['Normal']))
        if quote.client.city:
            story.append(Paragraph(
                f"{quote.client.city}, {quote.client.state} {quote.client.zip_code}",
                styles['Normal']
            ))
        story.append(Paragraph(f"Phone: {quote.client.phone}", styles['Normal']))
        story.append(Paragraph(f"Email: {quote.client.email}", styles['Normal']))

        story.append(Spacer(1, 0.25*inch))

        # Job description
        story.append(Paragraph("<b>PROJECT DESCRIPTION:</b>", styles['Heading3']))
        story.append(Paragraph(quote.job_description, styles['Normal']))

        story.append(Spacer(1, 0.25*inch))

        # Line items table
        table_data = [['Description', 'Qty', 'Unit', 'Unit Price', 'Total']]

        for item in quote.line_items:
            table_data.append([
                item.description,
                f"{item.quantity:.1f}",
                item.unit,
                f"${item.unit_price:.2f}",
                f"${item.total:.2f}"
            ])

        # Totals
        table_data.append(['', '', '', 'Subtotal:', f"${quote.subtotal:.2f}"])
        table_data.append(['', '', '', f'Tax ({quote.tax_rate*100:.2f}%):', f"${quote.tax_amount:.2f}"])
        table_data.append(['', '', '', 'TOTAL:', f"${quote.total:.2f}"])

        table = Table(table_data, colWidths=[3*inch, 0.75*inch, 0.75*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -4), 1, colors.black),
            ('FONTNAME', (3, -1), (4, -1), 'Helvetica-Bold'),
        ]))

        story.append(table)
        story.append(Spacer(1, 0.25*inch))

        # Duration
        story.append(Paragraph(
            f"<b>Estimated Duration:</b> {quote.estimated_duration}",
            styles['Normal']
        ))

        story.append(Spacer(1, 0.25*inch))

        # Notes
        if quote.notes:
            story.append(Paragraph("<b>NOTES:</b>", styles['Heading3']))
            story.append(Paragraph(quote.notes, styles['Normal']))
            story.append(Spacer(1, 0.25*inch))

        # Terms
        story.append(Paragraph("<b>TERMS AND CONDITIONS:</b>", styles['Heading3']))
        for line in quote.terms.split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(), styles['Normal']))

        story.append(Spacer(1, 0.5*inch))

        # Signature lines
        story.append(Paragraph("_" * 40 + "          " + "_" * 20, styles['Normal']))
        story.append(Paragraph("Customer Signature                                    Date", styles['Normal']))

        # Build PDF
        doc.build(story)

        logger.info(f"Quote PDF generated: {output_path}")
        return output_path

    def _generate_quote_text(
        self,
        quote: Quote,
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Generate a text version of the quote (fallback)."""
        if output_path is None:
            output_path = self.output_dir / f"{quote.quote_number}.txt"

        output_path = Path(output_path)

        lines = [
            "=" * 60,
            self.company_name.center(60),
            "=" * 60,
            "",
            f"Quote #: {quote.quote_number}",
            f"Date: {datetime.now().strftime('%B %d, %Y')}",
            f"Valid Until: {quote.valid_until}",
            "",
            "-" * 60,
            "PREPARED FOR:",
            f"  {quote.client.name}",
            f"  {quote.client.address}",
            f"  Phone: {quote.client.phone}",
            f"  Email: {quote.client.email}",
            "",
            "-" * 60,
            "PROJECT DESCRIPTION:",
            f"  {quote.job_description}",
            "",
            "-" * 60,
            "LINE ITEMS:",
            ""
        ]

        for item in quote.line_items:
            lines.append(f"  {item.description}")
            lines.append(f"    {item.quantity} {item.unit} @ ${item.unit_price:.2f} = ${item.total:.2f}")

        lines.extend([
            "",
            "-" * 60,
            f"  Subtotal: ${quote.subtotal:.2f}",
            f"  Tax ({quote.tax_rate*100:.2f}%): ${quote.tax_amount:.2f}",
            f"  TOTAL: ${quote.total:.2f}",
            "",
            f"Estimated Duration: {quote.estimated_duration}",
            "",
            "-" * 60,
            quote.terms,
            "",
            "=" * 60
        ])

        output_path.write_text('\n'.join(lines))
        logger.info(f"Quote text generated: {output_path}")
        return output_path

    def save_quote(self, quote: Quote) -> Path:
        """Save quote as JSON for future reference."""
        json_path = self.output_dir / f"{quote.quote_number}.json"

        quote_dict = {
            "quote_number": quote.quote_number,
            "client": asdict(quote.client),
            "job_type": quote.job_type,
            "job_description": quote.job_description,
            "line_items": [asdict(item) for item in quote.line_items],
            "labor_cost": quote.labor_cost,
            "materials_cost": quote.materials_cost,
            "subtotal": quote.subtotal,
            "tax_rate": quote.tax_rate,
            "tax_amount": quote.tax_amount,
            "total": quote.total,
            "estimated_duration": quote.estimated_duration,
            "valid_until": quote.valid_until,
            "created_at": quote.created_at,
            "notes": quote.notes,
            "terms": quote.terms
        }

        with open(json_path, 'w') as f:
            json.dump(quote_dict, f, indent=2)

        logger.info(f"Quote saved: {json_path}")
        return json_path


# Convenience functions
def calculate_estimate(job_type: str, sqft: float, **kwargs) -> Dict:
    """Calculate estimate using default generator."""
    gen = QuoteGenerator()
    return gen.calculate_estimate(job_type, sqft, **kwargs)


def generate_quote_pdf(client_info: Dict, estimate: Dict, **kwargs) -> Path:
    """Generate PDF quote using default generator."""
    gen = QuoteGenerator(**kwargs)
    quote = gen.create_quote(client_info, estimate)
    return gen.generate_quote_pdf(quote)


if __name__ == "__main__":
    import sys

    # Demo usage
    print("J3 Quote Generator - Demo")
    print("=" * 40)

    # Sample client
    client = ClientInfo(
        name="John Smith",
        email="john@example.com",
        phone="555-123-4567",
        address="123 Main Street",
        city="Austin",
        state="TX",
        zip_code="78701"
    )

    # Generate estimates for different job types
    gen = QuoteGenerator(
        company_name="J3 Construction",
        company_phone="555-987-6543",
        company_email="quotes@j3construction.com"
    )

    for job_type in ["framing", "drywall", "full_remodel"]:
        print(f"\n{job_type.upper()} - 1500 sqft:")
        estimate = gen.calculate_estimate(job_type, 1500)
        print(f"  Labor: ${estimate['labor_cost']:,.2f}")
        print(f"  Materials: ${estimate['materials_cost']:,.2f}")
        print(f"  Total: ${estimate['total']:,.2f}")
        print(f"  Duration: {estimate['estimated_duration']}")

    # Generate a full quote
    print("\n" + "=" * 40)
    print("Generating sample quote PDF...")

    estimate = gen.calculate_estimate("full_remodel", 1200, materials="premium")
    quote = gen.create_quote(client, estimate, notes="Customer prefers morning work hours.")
    pdf_path = gen.generate_quote_pdf(quote)
    json_path = gen.save_quote(quote)

    print(f"Quote PDF: {pdf_path}")
    print(f"Quote JSON: {json_path}")
