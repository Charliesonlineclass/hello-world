"""
SCORPION Workflows Module
=========================

n8n workflow templates for automating SCORPION operations.
These workflows handle lead intake, daily digests, and appointment reminders.

Available Workflows:
- lead_intake.json: Process incoming leads through MARCUS
- daily_digest.json: Generate and send daily performance reports
- appointment_reminder.json: Send automated appointment reminders
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List

WORKFLOW_DIR = Path(__file__).parent


def load_workflow(name: str) -> Dict[str, Any]:
    """
    Load a workflow template by name.

    Args:
        name: Workflow name (without .json extension)

    Returns:
        Workflow configuration dict
    """
    workflow_path = WORKFLOW_DIR / f"{name}.json"
    if not workflow_path.exists():
        raise FileNotFoundError(f"Workflow not found: {name}")

    with open(workflow_path, "r") as f:
        return json.load(f)


def list_workflows() -> List[str]:
    """List all available workflows."""
    return [
        f.stem for f in WORKFLOW_DIR.glob("*.json")
    ]


def validate_workflow(workflow: Dict[str, Any]) -> bool:
    """
    Validate a workflow configuration.

    Args:
        workflow: Workflow configuration to validate

    Returns:
        True if valid
    """
    required_fields = ["name", "nodes", "connections"]
    return all(field in workflow for field in required_fields)


__all__ = [
    "load_workflow",
    "list_workflows",
    "validate_workflow",
    "WORKFLOW_DIR",
]
