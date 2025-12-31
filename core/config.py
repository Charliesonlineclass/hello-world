"""
SCORPION Configuration Manager
==============================

Centralized configuration loading from environment variables and .env files.
Provides type-safe access to all SCORPION settings.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

logger = logging.getLogger("SCORPION-CONFIG")


# =============================================================================
# CONFIGURATION DATACLASS
# =============================================================================

@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = "localhost"
    port: int = 5432
    name: str = "scorpion"
    user: str = "scorpion"
    password: str = ""

    @property
    def url(self) -> str:
        """Get database connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class RedisConfig:
    """Redis connection configuration."""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0

    @property
    def url(self) -> str:
        """Get Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class OllamaConfig:
    """Ollama AI service configuration."""
    host: str = "localhost"
    port: int = 11434
    default_model: str = "mistral"
    timeout: int = 120

    @property
    def base_url(self) -> str:
        """Get Ollama API base URL."""
        return f"http://{self.host}:{self.port}"


@dataclass
class ChromaDBConfig:
    """ChromaDB vector database configuration."""
    host: str = "localhost"
    port: int = 8000
    token: str = ""
    persist_directory: str = "./data/chromadb"

    @property
    def base_url(self) -> str:
        """Get ChromaDB API base URL."""
        return f"http://{self.host}:{self.port}"


@dataclass
class APIConfig:
    """SCORPION API configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    secret_key: str = ""
    token_expiry_hours: int = 24
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    debug: bool = False


@dataclass
class BabyConfig:
    """AI Baby configuration."""
    name: str
    model: str
    role: str
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class ScorpionConfig:
    """
    Master configuration for SCORPION platform.

    Loads all settings from environment variables with sensible defaults.
    """

    # Service configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    chromadb: ChromaDBConfig = field(default_factory=ChromaDBConfig)
    api: APIConfig = field(default_factory=APIConfig)

    # AI Babies
    babies: Dict[str, BabyConfig] = field(default_factory=dict)

    # Paths
    data_dir: str = "./data"
    logs_dir: str = "./logs"
    backup_dir: str = "./backups"

    # Features
    enable_n8n: bool = True
    enable_scheduler: bool = True
    enable_health_monitor: bool = True

    # Notifications
    notification_email: str = ""
    notification_phone: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'ScorpionConfig':
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional path to .env file

        Returns:
            ScorpionConfig instance
        """
        # Load .env file if specified or default exists
        if HAS_DOTENV:
            if env_file and Path(env_file).exists():
                load_dotenv(env_file)
            elif Path(".env").exists():
                load_dotenv(".env")

        config = cls()

        # Database
        config.database = DatabaseConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            name=os.getenv("POSTGRES_DB", "scorpion"),
            user=os.getenv("POSTGRES_USER", "scorpion"),
            password=os.getenv("POSTGRES_PASSWORD", "")
        )

        # Redis
        config.redis = RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD", ""),
            db=int(os.getenv("REDIS_DB", "0"))
        )

        # Ollama
        config.ollama = OllamaConfig(
            host=os.getenv("OLLAMA_HOST", "localhost"),
            port=int(os.getenv("OLLAMA_PORT", "11434")),
            default_model=os.getenv("OLLAMA_DEFAULT_MODEL", "mistral"),
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "120"))
        )

        # ChromaDB
        config.chromadb = ChromaDBConfig(
            host=os.getenv("CHROMADB_HOST", "localhost"),
            port=int(os.getenv("CHROMADB_PORT", "8000")),
            token=os.getenv("CHROMADB_TOKEN", ""),
            persist_directory=os.getenv("CHROMADB_PERSIST_DIR", "./data/chromadb")
        )

        # API
        config.api = APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8080")),
            secret_key=os.getenv("API_SECRET_KEY", "change-me-in-production"),
            token_expiry_hours=int(os.getenv("TOKEN_EXPIRY_HOURS", "24")),
            debug=os.getenv("API_DEBUG", "false").lower() == "true"
        )

        # Load babies configuration
        config.babies = {
            "MARCUS": BabyConfig(
                name="MARCUS",
                model=os.getenv("MARCUS_MODEL", "mistral"),
                role="General intelligence and customer interaction",
                temperature=0.7
            ),
            "HERMES": BabyConfig(
                name="HERMES",
                model=os.getenv("HERMES_MODEL", "phi"),
                role="Fast responses and quick tasks",
                temperature=0.5
            ),
            "ATHENA": BabyConfig(
                name="ATHENA",
                model=os.getenv("ATHENA_MODEL", "codellama"),
                role="Code generation and technical analysis",
                temperature=0.3
            ),
            "APOLLO": BabyConfig(
                name="APOLLO",
                model=os.getenv("APOLLO_MODEL", "llama2"),
                role="Creative writing and content generation",
                temperature=0.9
            )
        }

        # Paths
        config.data_dir = os.getenv("DATA_DIR", "./data")
        config.logs_dir = os.getenv("LOGS_DIR", "./logs")
        config.backup_dir = os.getenv("BACKUP_DIR", "./backups")

        # Features
        config.enable_n8n = os.getenv("ENABLE_N8N", "true").lower() == "true"
        config.enable_scheduler = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
        config.enable_health_monitor = os.getenv("ENABLE_HEALTH_MONITOR", "true").lower() == "true"

        # Notifications
        config.notification_email = os.getenv("NOTIFICATION_EMAIL", "")
        config.notification_phone = os.getenv("NOTIFICATION_PHONE", "")
        config.smtp_host = os.getenv("SMTP_HOST", "")
        config.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        config.smtp_user = os.getenv("SMTP_USER", "")
        config.smtp_password = os.getenv("SMTP_PASSWORD", "")

        # Environment
        config.environment = os.getenv("ENVIRONMENT", "development")
        config.log_level = os.getenv("LOG_LEVEL", "INFO")

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding secrets)."""
        return {
            "environment": self.environment,
            "api_port": self.api.port,
            "database_host": self.database.host,
            "redis_host": self.redis.host,
            "ollama_host": self.ollama.host,
            "chromadb_host": self.chromadb.host,
            "babies": list(self.babies.keys()),
            "features": {
                "n8n": self.enable_n8n,
                "scheduler": self.enable_scheduler,
                "health_monitor": self.enable_health_monitor
            }
        }

    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings."""
        warnings = []

        if self.api.secret_key == "change-me-in-production":
            warnings.append("API_SECRET_KEY is using default value")

        if not self.database.password:
            warnings.append("POSTGRES_PASSWORD is not set")

        if self.environment == "production" and self.api.debug:
            warnings.append("API_DEBUG is enabled in production")

        return warnings


# =============================================================================
# GLOBAL CONFIG INSTANCE
# =============================================================================

_config: Optional[ScorpionConfig] = None


def get_config() -> ScorpionConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = ScorpionConfig.from_env()
    return _config


def reload_config(env_file: Optional[str] = None) -> ScorpionConfig:
    """Reload configuration from environment."""
    global _config
    _config = ScorpionConfig.from_env(env_file)
    return _config
