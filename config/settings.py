"""
SCORPION AI - Settings Configuration
Central configuration for Pandora's Castle
"""

from pathlib import Path
from typing import List
import os

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database
DATABASE_PATH = DATA_DIR / "castle.db"

# Server ports
API_PORT = int(os.getenv("API_PORT", "9999"))
WEBSITE_PORT = int(os.getenv("WEBSITE_PORT", "8080"))

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_TIMEOUT = 30

# Default AI models for each baby
AI_MODELS = {
    "HERMES": "tinyllama",      # Fast, lightweight for public chat
    "VULCAN": "phi3:mini",      # Builder, problem solver
    "MARCUS": "qwen2.5:7b"      # Strategic analyst
}

# Rate limits
PUBLIC_CHAT_RATE_LIMIT = 20      # requests per hour
PUBLIC_CHAT_WINDOW = 3600       # 1 hour in seconds

# CORS origins
CORS_ORIGINS: List[str] = [
    "http://localhost:8080",
    "http://localhost:9999",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:9999",
]

# JWT Settings (for future auth implementation)
JWT_SECRET = os.getenv("JWT_SECRET", "scorpion-ai-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# Admin credentials (hashed in production)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@ometeolt.com")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")  # Set in production

# Tier pricing
TIER_PRICING = {
    "starter": 100.0,
    "pro": 200.0,
    "empire": 500.0
}

# Tier to baby mapping
TIER_BABIES = {
    "starter": "HERMES",
    "pro": "VULCAN",
    "empire": "MARCUS"
}

# Ownership months
OWNERSHIP_MONTHS = 12

# Business info
BUSINESS_NAME = "Ometeolt"
BUSINESS_EMAIL = "info@ometeolt.com"
BUSINESS_LOCATION = "El Salvador"


def get_baby_model(baby_name: str) -> str:
    """Get the AI model for a given baby name"""
    return AI_MODELS.get(baby_name.upper(), AI_MODELS["HERMES"])


def get_tier_rate(tier: str) -> float:
    """Get monthly rate for a tier"""
    return TIER_PRICING.get(tier.lower(), TIER_PRICING["starter"])


def get_tier_baby(tier: str) -> str:
    """Get default baby for a tier"""
    return TIER_BABIES.get(tier.lower(), TIER_BABIES["starter"])
