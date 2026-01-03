#!/usr/bin/env python3
"""
SCORPION Multi-Tenant System - Client Setup Script
===================================================

CLI tool to onboard new clients to the SCORPION system.
Creates all necessary components for a new client leg.

Usage:
    python setup_client.py --name "J3" --industry construction --baby vulcan
    python setup_client.py --name "New Client" --industry banking --baby marcus --interactive

Created Components:
    - Client leg file from template
    - Data directory for client
    - Access token
    - Webhook secret
    - Widget embed code
    - Setup instructions

Author: SCORPION System
Version: 1.0.0
"""

import argparse
import os
import sys
import json
import secrets
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Baby model registry
BABY_MODELS = {
    "hermes": "tinyllama",
    "marcus": "qwen2.5:7b",
    "vulcan": "phi3:mini",
    "apollo": "mistral:7b",
    "athena": "llama3.2:3b",
}

# Industry configurations
INDUSTRIES = {
    "call_center": {
        "display": "Call Center",
        "default_baby": "hermes",
        "features": ["call_tracking", "script_management", "agent_performance"],
    },
    "banking": {
        "display": "Banking/Finance",
        "default_baby": "marcus",
        "features": ["loan_assessment", "compliance", "risk_analysis"],
    },
    "construction": {
        "display": "Construction",
        "default_baby": "vulcan",
        "features": ["estimates", "project_tracking", "material_costs"],
    },
    "roofing": {
        "display": "Roofing",
        "default_baby": "vulcan",
        "features": ["estimates", "inspections", "weather_tracking"],
    },
    "real_estate": {
        "display": "Real Estate",
        "default_baby": "hermes",
        "features": ["property_matching", "showing_scheduling", "market_reports"],
    },
    "healthcare": {
        "display": "Healthcare",
        "default_baby": "marcus",
        "features": ["patient_intake", "appointment_scheduling", "hipaa_compliance"],
    },
    "legal": {
        "display": "Legal Services",
        "default_baby": "marcus",
        "features": ["case_intake", "document_management", "billing"],
    },
    "insurance": {
        "display": "Insurance",
        "default_baby": "marcus",
        "features": ["quote_generation", "claims_processing", "policy_management"],
    },
}


def generate_client_id(name: str) -> str:
    """Generate a client ID from the name."""
    # Convert to lowercase, replace spaces with underscores
    client_id = name.lower().replace(" ", "_").replace("-", "_")
    # Remove non-alphanumeric characters except underscores
    client_id = "".join(c for c in client_id if c.isalnum() or c == "_")
    return client_id


def generate_access_token() -> str:
    """Generate a secure access token."""
    return secrets.token_urlsafe(32)


def generate_webhook_secret() -> str:
    """Generate a webhook secret."""
    return secrets.token_hex(32)


def create_data_directory(base_path: Path, client_id: str) -> Path:
    """Create the data directory structure for a client."""
    data_dir = base_path / "data" / "clients" / client_id
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (data_dir / "leads").mkdir(exist_ok=True)
    (data_dir / "quotes").mkdir(exist_ok=True)
    (data_dir / "reports").mkdir(exist_ok=True)

    # Create empty leads.json
    leads_file = data_dir / "leads.json"
    if not leads_file.exists():
        with open(leads_file, 'w') as f:
            json.dump([], f)

    return data_dir


def generate_leg_template(
    client_id: str,
    client_name: str,
    industry: str,
    baby_name: str,
    baby_model: str
) -> str:
    """Generate the Python code for a new client leg."""

    industry_config = INDUSTRIES.get(industry, INDUSTRIES["call_center"])
    features = industry_config.get("features", [])

    template = f'''"""
SCORPION Multi-Tenant System - {client_name} Leg
{'=' * (40 + len(client_name))}

This leg serves {client_name} operations.

SCORPION Architecture Role:
- LEG: Client interface for {client_name}
- BABY: {baby_name.upper()} ({baby_model})
- Industry: {industry.upper()}
- Owner: Master Charlie (HEAD access)

Features: {', '.join(features)}

Author: SCORPION System
Generated: {datetime.now().isoformat()}
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path
import uuid

from legs.base_leg import (
    BaseClientLeg, Industry, Lead, LeadStatus,
    RequestType, logger
)


class {client_name.replace(" ", "")}Leg(BaseClientLeg):
    """
    SCORPION Leg for {client_name}.

    Connects to {baby_name.upper()} ({baby_model}) for AI operations.

    SCORPION Security:
    - All actions logged to Labienus audit system
    - Only {client_name} staff can access this leg (LEG level access)
    - HEAD (Master Charlie) has full oversight
    """

    def __init__(
        self,
        access_token: str,
        data_dir: Optional[str] = None,
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize {client_name} leg.

        Args:
            access_token: Authentication token
            data_dir: Data storage directory
            ollama_url: Ollama server URL
        """
        super().__init__(
            client_id="{client_id}",
            client_name="{client_name}",
            baby_model="{baby_model}",
            industry=Industry.{industry.upper()},
            access_token=access_token,
            data_dir=data_dir,
            ollama_url=ollama_url
        )

        logger.info(f"{client_name} leg initialized with {baby_name.upper()} ({baby_model})")

    def get_industry_actions(self) -> List[str]:
        """Return {client_name}-specific actions."""
        return [
            "process_inquiry",
            "generate_report",
            # Add more industry-specific actions here
        ]

    def process_industry_request(
        self,
        action: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route {client_name}-specific requests."""
        handlers = {{
            "process_inquiry": self.process_inquiry,
            "generate_report": self.generate_report,
        }}

        handler = handlers.get(action)
        if not handler:
            return {{"error": f"Unknown action: {{action}}"}}

        return handler(data)

    def process_inquiry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new inquiry.

        Args:
            data: Inquiry data

        Returns:
            Processing result
        """
        lead_id = str(uuid.uuid4())

        lead = Lead(
            id=lead_id,
            client_id=self.client_id,
            name=data.get('name', 'Unknown'),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            status=LeadStatus.NEW,
            source=data.get('source', 'website'),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            custom_data=data.get('custom_data', {{}})
        )

        self._leads_cache[lead_id] = lead
        self._save_data()

        # Generate auto-response using AI
        ai_response = self.query_baby(
            f"Generate a brief professional response for a new inquiry from {{lead.name}}."
        )

        self.log_activity(
            action="inquiry_processed",
            details={{"lead_id": lead_id}}
        )

        return {{
            "lead": lead.to_dict(),
            "auto_response": ai_response.get('response', ''),
            "status": "success"
        }}

    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a report.

        Args:
            data: Report parameters

        Returns:
            Report data
        """
        report_type = data.get('type', 'summary')
        date_range = data.get('date_range')

        stats = self.get_stats(date_range)

        self.log_activity(
            action="report_generated",
            details={{"type": report_type}}
        )

        return {{
            "report_type": report_type,
            "stats": asdict(stats) if hasattr(stats, '__dataclass_fields__') else stats,
            "generated_at": datetime.now().isoformat()
        }}
'''
    return template


def generate_widget_code(client_id: str, client_name: str, primary_color: str = "#2563eb") -> str:
    """Generate embeddable widget code for the client."""
    return f'''
<!-- SCORPION Chat Widget for {client_name} -->
<script>
(function(w, d) {{
    var config = {{
        clientId: "{client_id}",
        companyName: "{client_name}",
        primaryColor: "{primary_color}",
        greeting: "Hi! How can we help you today?"
    }};
    w.ScorpionWidgetConfig = config;
    var s = d.createElement('script');
    s.src = 'https://widget.scorpion.local/chat.js';
    s.async = true;
    d.head.appendChild(s);
}})(window, document);
</script>
<!-- End SCORPION Widget -->
'''


def setup_client(
    name: str,
    industry: str,
    baby: str,
    base_path: Optional[Path] = None,
    interactive: bool = False
) -> Dict[str, Any]:
    """
    Set up a new client in SCORPION.

    Args:
        name: Client name
        industry: Industry type
        baby: Baby (AI model) name
        base_path: Base path for files
        interactive: Whether to prompt for confirmation

    Returns:
        Setup result dictionary
    """
    base_path = base_path or Path(__file__).parent.parent

    # Validate inputs
    if industry not in INDUSTRIES:
        print(f"Error: Unknown industry '{industry}'")
        print(f"Available: {', '.join(INDUSTRIES.keys())}")
        return {"success": False, "error": "Invalid industry"}

    baby_lower = baby.lower()
    if baby_lower not in BABY_MODELS:
        print(f"Error: Unknown baby '{baby}'")
        print(f"Available: {', '.join(BABY_MODELS.keys())}")
        return {"success": False, "error": "Invalid baby"}

    # Generate identifiers
    client_id = generate_client_id(name)
    access_token = generate_access_token()
    webhook_secret = generate_webhook_secret()
    baby_model = BABY_MODELS[baby_lower]

    print(f"\n{'='*60}")
    print(f"SCORPION Client Setup: {name}")
    print(f"{'='*60}")
    print(f"Client ID: {client_id}")
    print(f"Industry: {INDUSTRIES[industry]['display']}")
    print(f"Baby: {baby.upper()} ({baby_model})")
    print(f"{'='*60}\n")

    if interactive:
        confirm = input("Proceed with setup? (y/n): ")
        if confirm.lower() != 'y':
            print("Setup cancelled.")
            return {"success": False, "error": "Cancelled by user"}

    # Create data directory
    print("Creating data directory...")
    data_dir = create_data_directory(base_path, client_id)
    print(f"  Created: {data_dir}")

    # Generate leg file
    print("Generating client leg...")
    leg_code = generate_leg_template(
        client_id=client_id,
        client_name=name,
        industry=industry,
        baby_name=baby,
        baby_model=baby_model
    )

    leg_file = base_path / "legs" / f"{client_id}_leg.py"
    with open(leg_file, 'w') as f:
        f.write(leg_code)
    print(f"  Created: {leg_file}")

    # Generate widget code
    print("Generating widget embed code...")
    widget_code = generate_widget_code(client_id, name)

    widget_file = data_dir / "widget_embed.html"
    with open(widget_file, 'w') as f:
        f.write(widget_code)
    print(f"  Created: {widget_file}")

    # Save configuration
    print("Saving configuration...")
    config = {
        "client_id": client_id,
        "client_name": name,
        "industry": industry,
        "baby": baby.lower(),
        "baby_model": baby_model,
        "access_token": access_token,
        "webhook_secret": webhook_secret,
        "created_at": datetime.now().isoformat(),
        "webhook_url": f"https://api.scorpion.local/webhook/{client_id}/contact",
        "status": "active"
    }

    config_file = data_dir / "config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"  Created: {config_file}")

    # Print setup instructions
    print(f"\n{'='*60}")
    print("SETUP COMPLETE")
    print(f"{'='*60}")
    print(f"""
Next Steps:

1. Add the new leg to legs/__init__.py:
   from .{client_id}_leg import {name.replace(' ', '')}Leg

2. Configure webhook on client's website:
   URL: {config['webhook_url']}
   Secret: {webhook_secret}

3. Add widget to client's website:
   Copy contents of: {widget_file}

4. Generate access token for client users:
   Token: {access_token}

5. Test the integration:
   python -c "from legs.{client_id}_leg import {name.replace(' ', '')}Leg; print('OK')"

Configuration saved to: {config_file}
""")

    return {
        "success": True,
        "client_id": client_id,
        "config_path": str(config_file),
        "leg_path": str(leg_file),
        "data_dir": str(data_dir),
        "access_token": access_token,
        "webhook_secret": webhook_secret,
    }


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Set up a new SCORPION client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python setup_client.py --name "J3 Structural" --industry construction --baby vulcan
  python setup_client.py --name "New Bank" --industry banking --baby marcus --interactive

Industries: {', '.join(INDUSTRIES.keys())}
Babies: {', '.join(BABY_MODELS.keys())}
        """
    )

    parser.add_argument(
        "--name", "-n",
        required=True,
        help="Client name"
    )

    parser.add_argument(
        "--industry", "-i",
        required=True,
        choices=list(INDUSTRIES.keys()),
        help="Client industry"
    )

    parser.add_argument(
        "--baby", "-b",
        required=True,
        choices=list(BABY_MODELS.keys()),
        help="AI baby model to assign"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for confirmation before setup"
    )

    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output result as JSON"
    )

    args = parser.parse_args()

    result = setup_client(
        name=args.name,
        industry=args.industry,
        baby=args.baby,
        interactive=args.interactive
    )

    if args.output_json:
        print(json.dumps(result, indent=2))

    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
