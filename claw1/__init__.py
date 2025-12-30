"""
SCORPION CLAW 1 - Sales & CRM
=============================

Business development and customer relationship management.
Lead capture, scoring, pipeline tracking, and client management.

Modules:
    - sales.lead_capture: Lead processing and scoring
    - crm.pipeline: Sales pipeline management

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .sales.lead_capture import (
    LeadCapture,
    process_form,
    score_lead,
    assign_to_leg
)

from .crm.pipeline import (
    Pipeline,
    PIPELINE_STAGES,
    move_stage,
    get_pipeline_stats
)

__version__ = "1.0.0"
__codename__ = "TESTUDO"
