"""
J3 Construction Quote Generator
===============================

Professional quote generation system for construction businesses.
Generate PDF quotes, manage clients, and automate communications.

Modules:
    - quote_generator: Calculate estimates and generate PDF quotes
    - client_manager: Track clients and projects
    - communicator: Email quotes and follow-up automation

Usage:
    from j3 import QuoteGenerator, ClientManager

    # Generate a quote
    gen = QuoteGenerator()
    quote = gen.calculate_estimate("framing", sqft=1500, materials="premium")
    pdf_path = gen.generate_quote_pdf(client_info, quote)

    # Manage clients
    mgr = ClientManager()
    client_id = mgr.add_client("John Doe", "john@email.com", "555-1234")

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .quote_generator import (
    QuoteGenerator,
    calculate_estimate,
    generate_quote_pdf,
    JOB_TYPES,
    MATERIAL_COSTS
)

from .client_manager import (
    ClientManager,
    Client
)

from .communicator import (
    send_quote,
    send_promo,
    send_reminder,
    schedule_followup
)

__version__ = "1.0.0"
__codename__ = "TESTUDO"
__all__ = [
    'QuoteGenerator',
    'calculate_estimate',
    'generate_quote_pdf',
    'JOB_TYPES',
    'MATERIAL_COSTS',
    'ClientManager',
    'Client',
    'send_quote',
    'send_promo',
    'send_reminder',
    'schedule_followup'
]
