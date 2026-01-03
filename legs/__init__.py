"""
SCORPION Multi-Tenant System - Client Legs Module
==================================================

This module contains all client "legs" - the interfaces between SCORPION
and individual client businesses.

SCORPION Architecture:
    HEAD - Master Charlie (oversees all operations)
    BODY - Core processing systems
    LEGS - Client interfaces (this module)
    TAIL - Security/Labienus (access control, audit)
    BABIES - Ollama AI models (HERMES, MARCUS, VULCAN, etc.)

Each leg connects a client to their assigned AI "baby" and provides
industry-specific functionality. Legs are isolated from each other -
clients cannot access other clients' data.

Available Legs:
    - JoeLeg: Call center operations (HERMES/tinyllama)
    - AntonioLeg: Banking services (MARCUS/qwen2.5:7b)
    - J3Leg: Construction management (VULCAN/phi3:mini)
    - WillLeg: Real estate operations (HERMES/tinyllama)

Usage:
    from legs import J3Leg, JoeLeg, AntonioLeg, WillLeg
    from legs.base_leg import Industry, LeadStatus

    # Initialize a leg
    j3 = J3Leg(access_token="secret_token")

    # Process an inquiry
    result = j3.process_inquiry({
        'name': 'Customer Name',
        'email': 'customer@example.com',
        'job_type': 'framing'
    })

Author: SCORPION System
Version: 1.0.0
"""

# Base classes and enums
from .base_leg import (
    BaseClientLeg,
    Industry,
    LeadStatus,
    RequestType,
    Lead,
    ActivityLog,
    ClientStats,
    OllamaConnection,
)

# Client legs
from .joe_leg import (
    JoeLeg,
    CallOutcome,
    LeadType,
    AgentStatus,
    CallRecord,
    Agent,
    CallScript,
    Referral,
)

from .antonio_leg import (
    AntonioLeg,
    RiskLevel,
    LoanType,
    ApplicationStatus,
    ConsultationType,
    RiskAssessment,
    ComplianceResult,
    LoanApplication,
    Consultation,
    SuspiciousActivity,
)

from .j3_leg import (
    J3Leg,
    JobType,
    ProjectStatus,
    Complexity,
    MaterialEstimate,
    JobEstimate,
    Project,
    WalkthroughAppointment,
)

from .will_leg import (
    WillLeg,
    PropertyType,
    BuyerStage,
    SequenceType,
    Property,
    BuyerCriteria,
    Showing,
    NurtureSequence,
    MarketReport,
)

# All available legs
AVAILABLE_LEGS = {
    'joe_ipc': JoeLeg,
    'antonio_banking': AntonioLeg,
    'j3_structural': J3Leg,
    'will_realestate': WillLeg,
}

# Baby model assignments
BABY_ASSIGNMENTS = {
    'joe_ipc': 'tinyllama',       # HERMES - fast responses
    'antonio_banking': 'qwen2.5:7b',  # MARCUS - deep analysis
    'j3_structural': 'phi3:mini',  # VULCAN - building patterns
    'will_realestate': 'tinyllama',   # HERMES - fast communication
}

__all__ = [
    # Base
    'BaseClientLeg',
    'Industry',
    'LeadStatus',
    'RequestType',
    'Lead',
    'ActivityLog',
    'ClientStats',
    'OllamaConnection',
    # Joe's IPC
    'JoeLeg',
    'CallOutcome',
    'LeadType',
    'AgentStatus',
    'CallRecord',
    'Agent',
    'CallScript',
    'Referral',
    # Antonio's Banking
    'AntonioLeg',
    'RiskLevel',
    'LoanType',
    'ApplicationStatus',
    'ConsultationType',
    'RiskAssessment',
    'ComplianceResult',
    'LoanApplication',
    'Consultation',
    'SuspiciousActivity',
    # J3 Structural
    'J3Leg',
    'JobType',
    'ProjectStatus',
    'Complexity',
    'MaterialEstimate',
    'JobEstimate',
    'Project',
    'WalkthroughAppointment',
    # Will's Real Estate
    'WillLeg',
    'PropertyType',
    'BuyerStage',
    'SequenceType',
    'Property',
    'BuyerCriteria',
    'Showing',
    'NurtureSequence',
    'MarketReport',
    # Registry
    'AVAILABLE_LEGS',
    'BABY_ASSIGNMENTS',
]
