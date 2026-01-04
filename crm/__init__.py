"""
SCORPION AI - CRM Module
Pandora's Castle Client Relationship Management
"""

from .models import Lead, Client, Project, Invoice, Communication
from .models import LeadStatus, ClientTier, ProjectStatus
from .database import init_database, get_connection
from .leads import LeadManager
from .clients import ClientManager
from .projects import ProjectManager
from .communications import CommunicationManager

__all__ = [
    'Lead', 'Client', 'Project', 'Invoice', 'Communication',
    'LeadStatus', 'ClientTier', 'ProjectStatus',
    'init_database', 'get_connection',
    'LeadManager', 'ClientManager', 'ProjectManager', 'CommunicationManager'
]

__version__ = '1.0.0'
