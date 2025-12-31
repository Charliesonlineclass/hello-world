"""
SCORPION Constants
==================

Centralized constants for the SCORPION automation platform.
All magic numbers and strings should be defined here.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from typing import Dict, Any
from enum import Enum, IntEnum


# =============================================================================
# SERVICE PORTS
# =============================================================================

PORTS: Dict[str, int] = {
    # Core Services
    "api": 8080,
    "chromadb": 8000,
    "ollama": 11434,
    "n8n": 5678,

    # Data Services
    "postgres": 5432,
    "redis": 6379,

    # Web Services
    "nginx": 80,
    "nginx_ssl": 443,

    # Bridge Services
    "phone_bridge": 8888,
    "termux_sync": 8889,

    # Monitoring
    "health_check": 9090,
    "metrics": 9091,
}


# =============================================================================
# AI BABIES CONFIGURATION
# =============================================================================

BABIES: Dict[str, Dict[str, Any]] = {
    "MARCUS": {
        "model": "mistral",
        "role": "General intelligence and customer interaction",
        "temperature": 0.7,
        "max_tokens": 2048,
        "system_prompt": "You are MARCUS, a helpful AI assistant for business automation.",
        "color": "blue"
    },
    "HERMES": {
        "model": "phi",
        "role": "Fast responses and quick tasks",
        "temperature": 0.5,
        "max_tokens": 1024,
        "system_prompt": "You are HERMES, a fast and efficient AI for quick queries.",
        "color": "green"
    },
    "ATHENA": {
        "model": "codellama",
        "role": "Code generation and technical analysis",
        "temperature": 0.3,
        "max_tokens": 4096,
        "system_prompt": "You are ATHENA, a technical AI specialized in code and analysis.",
        "color": "purple"
    },
    "APOLLO": {
        "model": "llama2",
        "role": "Creative writing and content generation",
        "temperature": 0.9,
        "max_tokens": 2048,
        "system_prompt": "You are APOLLO, a creative AI for content and writing.",
        "color": "orange"
    }
}


# =============================================================================
# ACCESS LEVELS
# =============================================================================

class AccessLevel(IntEnum):
    """Access level hierarchy for SCORPION components."""
    PUBLIC = 10
    LEG = 50
    CLAW = 75
    HEAD = 100


ACCESS_LEVELS: Dict[str, int] = {
    "PUBLIC": AccessLevel.PUBLIC,
    "LEG": AccessLevel.LEG,
    "CLAW": AccessLevel.CLAW,
    "HEAD": AccessLevel.HEAD,
}

# Component to access level mapping
COMPONENT_ACCESS: Dict[str, int] = {
    "head": AccessLevel.HEAD,
    "chromadb": AccessLevel.HEAD,
    "ollama": AccessLevel.HEAD,
    "claw1": AccessLevel.CLAW,
    "claw2": AccessLevel.CLAW,
    "tail": AccessLevel.HEAD,
    "mouth": AccessLevel.CLAW,
    "legs": AccessLevel.LEG,
    "bridge": AccessLevel.LEG,
}


# =============================================================================
# FILE PATHS
# =============================================================================

FILE_PATHS: Dict[str, str] = {
    # Data directories
    "data_root": "./data",
    "chromadb_data": "./data/chromadb",
    "postgres_data": "./data/postgres",
    "redis_data": "./data/redis",
    "uploads": "./data/uploads",
    "exports": "./data/exports",

    # Log directories
    "logs_root": "./logs",
    "api_logs": "./logs/api",
    "scheduler_logs": "./logs/scheduler",
    "health_logs": "./logs/health",

    # Backup directories
    "backups_root": "./backups",
    "db_backups": "./backups/database",
    "chromadb_backups": "./backups/chromadb",
    "config_backups": "./backups/config",

    # Config files
    "env_file": "./.env",
    "agenda_file": "./daemon/agenda.json",
    "health_status": "./data/health/latest_status.json",

    # Templates
    "email_templates": "./templates/email",
    "quote_templates": "./templates/quotes",
    "report_templates": "./templates/reports",
}


# =============================================================================
# PIPELINE STAGES
# =============================================================================

class PipelineStage(str, Enum):
    """CRM pipeline stages."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    QUOTED = "quoted"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


PIPELINE_STAGES: Dict[str, Dict[str, Any]] = {
    "new": {"order": 1, "color": "gray", "label": "New Lead"},
    "contacted": {"order": 2, "color": "blue", "label": "Contacted"},
    "qualified": {"order": 3, "color": "cyan", "label": "Qualified"},
    "quoted": {"order": 4, "color": "yellow", "label": "Quote Sent"},
    "negotiating": {"order": 5, "color": "orange", "label": "Negotiating"},
    "closed_won": {"order": 6, "color": "green", "label": "Closed Won"},
    "closed_lost": {"order": 7, "color": "red", "label": "Closed Lost"},
}


# =============================================================================
# SERVICE NAMES
# =============================================================================

SERVICE_NAMES: Dict[str, str] = {
    # Docker service names
    "brain": "scorpion-brain",
    "chromadb": "scorpion-chromadb",
    "ollama": "ollama-proxy",
    "n8n": "scorpion-n8n",
    "postgres": "scorpion-postgres",
    "redis": "scorpion-redis",
    "nginx": "scorpion-nginx",
    "health": "scorpion-health",
}


# =============================================================================
# HTTP STATUS CODES
# =============================================================================

HTTP_STATUS: Dict[str, int] = {
    "ok": 200,
    "created": 201,
    "accepted": 202,
    "no_content": 204,
    "bad_request": 400,
    "unauthorized": 401,
    "forbidden": 403,
    "not_found": 404,
    "conflict": 409,
    "internal_error": 500,
    "service_unavailable": 503,
}


# =============================================================================
# TIME CONSTANTS
# =============================================================================

TIME_SECONDS: Dict[str, int] = {
    "minute": 60,
    "hour": 3600,
    "day": 86400,
    "week": 604800,
    "month": 2592000,  # 30 days
}

DEFAULT_TIMEOUTS: Dict[str, int] = {
    "api_request": 30,
    "ollama_request": 120,
    "db_query": 30,
    "health_check": 5,
    "webhook": 10,
}


# =============================================================================
# REGEX PATTERNS
# =============================================================================

PATTERNS: Dict[str, str] = {
    "email": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
    "phone": r"^\+?1?\d{10,14}$",
    "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    "date_iso": r"^\d{4}-\d{2}-\d{2}$",
    "datetime_iso": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
}
