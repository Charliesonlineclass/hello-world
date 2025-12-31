"""
SCORPION_BRAIN LEGs Module
==========================
Client-specific LEGs (Local Extension Groups) that connect
to the CLAW pipelines for specialized business operations.

LEGs:
- joe: IPC Solutions - Call center operations
- jonathan: J3 Structural Solutions - Construction business
"""

from .joe import IPCSolutionsLeg, lead_capture, agent_performance, shift_scheduler
from .jonathan import J3StructuralLeg, project_tracker, invoice_generator, material_calculator

__all__ = [
    # IPC Solutions
    'IPCSolutionsLeg',
    'lead_capture',
    'agent_performance',
    'shift_scheduler',
    # J3 Structural
    'J3StructuralLeg',
    'project_tracker',
    'invoice_generator',
    'material_calculator',
]
