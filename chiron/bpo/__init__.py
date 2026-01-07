"""
CHIRON BPO - Business Process Outsourcing Command
Military-grade call center operations management
"""

from .bpo_core import BPOEngine, BPOAgent, AgentMetrics, Campaign, get_engine
from .dispositions import HEALTHCARE_DISPOSITIONS, get_disposition
from .scripts import Script, get_script_repository

__all__ = [
    "BPOEngine",
    "BPOAgent",
    "AgentMetrics",
    "Campaign",
    "get_engine",
    "HEALTHCARE_DISPOSITIONS",
    "get_disposition",
    "Script",
    "get_script_repository"
]
