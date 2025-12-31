"""
SCORPION Configuration Validator
================================

Validates all configuration, environment variables, ports, paths,
and connections before starting the system.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import os
import re
import socket
import logging
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCORPION-VALIDATOR")


# =============================================================================
# CONFIGURATION
# =============================================================================

# Required environment variables
REQUIRED_ENV_VARS = [
    "API_SECRET_KEY",
    "POSTGRES_PASSWORD",
]

# Optional but recommended
RECOMMENDED_ENV_VARS = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "REDIS_HOST",
    "REDIS_PORT",
    "OLLAMA_HOST",
    "OLLAMA_PORT",
    "CHROMADB_HOST",
    "CHROMADB_PORT",
    "API_HOST",
    "API_PORT",
]

# Required ports
REQUIRED_PORTS = {
    "chromadb": 8000,
    "ollama": 11434,
    "api": 8080,
}

# Optional ports
OPTIONAL_PORTS = {
    "postgres": 5432,
    "redis": 6379,
    "n8n": 5678,
}

# Required directories
REQUIRED_DIRS = [
    "./data",
    "./logs",
    "./backups",
]

# Required Ollama models
REQUIRED_MODELS = [
    "mistral",
    "phi",
    "codellama",
    "llama2",
]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ValidationResult:
    """Result of a validation check."""
    check_name: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationReport:
    """Complete validation report."""
    timestamp: str
    passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: int
    results: List[ValidationResult] = field(default_factory=list)


# =============================================================================
# CONFIG VALIDATOR CLASS
# =============================================================================

class ConfigValidator:
    """
    Validates SCORPION configuration and environment.

    Checks:
    - Environment variables
    - Port availability/conflicts
    - Directory existence
    - Ollama models
    - Service connections (ChromaDB, PostgreSQL, etc.)
    """

    def __init__(self):
        self.results: List[ValidationResult] = []
        logger.info("ConfigValidator initialized")

    # -------------------------------------------------------------------------
    # Environment Validation
    # -------------------------------------------------------------------------

    def validate_env(self) -> List[ValidationResult]:
        """Validate environment variables."""
        results = []

        # Check required variables
        for var in REQUIRED_ENV_VARS:
            value = os.getenv(var)
            if not value:
                results.append(ValidationResult(
                    check_name=f"env_{var}",
                    passed=False,
                    message=f"Required environment variable {var} is not set",
                    severity="error"
                ))
            elif var == "API_SECRET_KEY" and value == "change-me-in-production":
                results.append(ValidationResult(
                    check_name=f"env_{var}",
                    passed=False,
                    message=f"{var} is using default value - please change for production",
                    severity="warning"
                ))
            else:
                results.append(ValidationResult(
                    check_name=f"env_{var}",
                    passed=True,
                    message=f"{var} is set",
                    severity="info"
                ))

        # Check recommended variables
        missing_recommended = []
        for var in RECOMMENDED_ENV_VARS:
            if not os.getenv(var):
                missing_recommended.append(var)

        if missing_recommended:
            results.append(ValidationResult(
                check_name="env_recommended",
                passed=True,  # Not a failure
                message=f"Missing recommended variables: {', '.join(missing_recommended)}",
                details={"missing": missing_recommended},
                severity="warning"
            ))

        self.results.extend(results)
        return results

    # -------------------------------------------------------------------------
    # Port Validation
    # -------------------------------------------------------------------------

    def _check_port_in_use(self, port: int, host: str = "localhost") -> bool:
        """Check if a port is in use."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            sock.close()
            return False

    def _check_port_available(self, port: int) -> bool:
        """Check if a port is available for binding."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("", port))
            sock.close()
            return True
        except OSError:
            return False

    def validate_ports(self) -> List[ValidationResult]:
        """Validate port availability and conflicts."""
        results = []

        all_ports = {**REQUIRED_PORTS, **OPTIONAL_PORTS}
        used_ports = []

        for name, port in all_ports.items():
            in_use = self._check_port_in_use(port)

            if name in REQUIRED_PORTS:
                # For required services, port should either be available or service running
                if in_use:
                    results.append(ValidationResult(
                        check_name=f"port_{name}",
                        passed=True,
                        message=f"{name} service detected on port {port}",
                        details={"port": port, "in_use": True},
                        severity="info"
                    ))
                    used_ports.append(port)
                else:
                    # Check if we can bind to it
                    available = self._check_port_available(port)
                    results.append(ValidationResult(
                        check_name=f"port_{name}",
                        passed=available,
                        message=f"Port {port} for {name}: {'available' if available else 'blocked'}",
                        details={"port": port, "available": available},
                        severity="info" if available else "warning"
                    ))
            else:
                # Optional ports
                if in_use:
                    results.append(ValidationResult(
                        check_name=f"port_{name}",
                        passed=True,
                        message=f"{name} service detected on port {port}",
                        details={"port": port},
                        severity="info"
                    ))

        # Check for port conflicts
        port_counts = {}
        for port in used_ports:
            port_counts[port] = port_counts.get(port, 0) + 1

        for port, count in port_counts.items():
            if count > 1:
                results.append(ValidationResult(
                    check_name="port_conflict",
                    passed=False,
                    message=f"Port {port} has a conflict ({count} services)",
                    severity="error"
                ))

        self.results.extend(results)
        return results

    # -------------------------------------------------------------------------
    # Path Validation
    # -------------------------------------------------------------------------

    def validate_paths(self) -> List[ValidationResult]:
        """Validate required directories exist or can be created."""
        results = []

        for dir_path in REQUIRED_DIRS:
            path = Path(dir_path)

            if path.exists():
                if path.is_dir():
                    # Check if writable
                    test_file = path / ".write_test"
                    try:
                        test_file.touch()
                        test_file.unlink()
                        results.append(ValidationResult(
                            check_name=f"path_{dir_path}",
                            passed=True,
                            message=f"Directory {dir_path} exists and is writable",
                            severity="info"
                        ))
                    except Exception:
                        results.append(ValidationResult(
                            check_name=f"path_{dir_path}",
                            passed=False,
                            message=f"Directory {dir_path} exists but is not writable",
                            severity="error"
                        ))
                else:
                    results.append(ValidationResult(
                        check_name=f"path_{dir_path}",
                        passed=False,
                        message=f"Path {dir_path} exists but is not a directory",
                        severity="error"
                    ))
            else:
                # Try to create
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    results.append(ValidationResult(
                        check_name=f"path_{dir_path}",
                        passed=True,
                        message=f"Directory {dir_path} created",
                        severity="info"
                    ))
                except Exception as e:
                    results.append(ValidationResult(
                        check_name=f"path_{dir_path}",
                        passed=False,
                        message=f"Cannot create directory {dir_path}: {e}",
                        severity="error"
                    ))

        # Check for key files
        key_files = [
            (".env", "warning"),  # OK if missing, using defaults
            ("body/docker/docker-compose.yml", "warning"),
            ("daemon/agenda.json", "info"),
        ]

        for file_path, severity in key_files:
            exists = Path(file_path).exists()
            results.append(ValidationResult(
                check_name=f"file_{file_path.replace('/', '_')}",
                passed=True,  # Not a failure even if missing
                message=f"File {file_path}: {'found' if exists else 'not found'}",
                details={"exists": exists},
                severity="info" if exists else severity
            ))

        self.results.extend(results)
        return results

    # -------------------------------------------------------------------------
    # Ollama Model Validation
    # -------------------------------------------------------------------------

    def validate_models(self) -> List[ValidationResult]:
        """Validate required Ollama models are installed."""
        results = []

        # First check if Ollama is running
        ollama_url = os.getenv("OLLAMA_HOST", "localhost")
        ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))

        try:
            response = requests.get(
                f"http://{ollama_url}:{ollama_port}/api/tags",
                timeout=5
            )

            if response.status_code != 200:
                results.append(ValidationResult(
                    check_name="ollama_connection",
                    passed=False,
                    message="Cannot connect to Ollama",
                    severity="error"
                ))
                self.results.extend(results)
                return results

            data = response.json()
            installed_models = [m["name"].split(":")[0] for m in data.get("models", [])]

            results.append(ValidationResult(
                check_name="ollama_connection",
                passed=True,
                message=f"Ollama connected, {len(installed_models)} models installed",
                details={"models": installed_models},
                severity="info"
            ))

            # Check each required model
            for model in REQUIRED_MODELS:
                if model in installed_models:
                    results.append(ValidationResult(
                        check_name=f"model_{model}",
                        passed=True,
                        message=f"Model {model} is installed",
                        severity="info"
                    ))
                else:
                    results.append(ValidationResult(
                        check_name=f"model_{model}",
                        passed=False,
                        message=f"Model {model} is not installed. Run: ollama pull {model}",
                        severity="warning"
                    ))

        except requests.exceptions.ConnectionError:
            results.append(ValidationResult(
                check_name="ollama_connection",
                passed=False,
                message="Ollama is not running",
                severity="error"
            ))
        except Exception as e:
            results.append(ValidationResult(
                check_name="ollama_connection",
                passed=False,
                message=f"Ollama check failed: {e}",
                severity="error"
            ))

        self.results.extend(results)
        return results

    # -------------------------------------------------------------------------
    # ChromaDB Validation
    # -------------------------------------------------------------------------

    def validate_chromadb(self) -> List[ValidationResult]:
        """Validate ChromaDB connection and collections."""
        results = []

        chromadb_url = os.getenv("CHROMADB_HOST", "localhost")
        chromadb_port = int(os.getenv("CHROMADB_PORT", "8000"))

        try:
            # Test heartbeat
            response = requests.get(
                f"http://{chromadb_url}:{chromadb_port}/api/v1/heartbeat",
                timeout=5
            )

            if response.status_code == 200:
                results.append(ValidationResult(
                    check_name="chromadb_connection",
                    passed=True,
                    message=f"ChromaDB connected at {chromadb_url}:{chromadb_port}",
                    severity="info"
                ))

                # Check collections
                try:
                    collections_response = requests.get(
                        f"http://{chromadb_url}:{chromadb_port}/api/v1/collections",
                        timeout=5
                    )

                    if collections_response.status_code == 200:
                        collections = collections_response.json()
                        results.append(ValidationResult(
                            check_name="chromadb_collections",
                            passed=True,
                            message=f"ChromaDB has {len(collections)} collections",
                            details={"count": len(collections)},
                            severity="info"
                        ))
                except Exception:
                    pass

            else:
                results.append(ValidationResult(
                    check_name="chromadb_connection",
                    passed=False,
                    message=f"ChromaDB returned status {response.status_code}",
                    severity="warning"
                ))

        except requests.exceptions.ConnectionError:
            results.append(ValidationResult(
                check_name="chromadb_connection",
                passed=False,
                message="ChromaDB is not running",
                severity="warning"
            ))
        except Exception as e:
            results.append(ValidationResult(
                check_name="chromadb_connection",
                passed=False,
                message=f"ChromaDB check failed: {e}",
                severity="warning"
            ))

        self.results.extend(results)
        return results

    # -------------------------------------------------------------------------
    # Full Validation
    # -------------------------------------------------------------------------

    def full_validation(self) -> ValidationReport:
        """Run all validation checks."""
        logger.info("=" * 50)
        logger.info("  SCORPION CONFIGURATION VALIDATION")
        logger.info("=" * 50)

        self.results = []  # Reset

        # Run all validations
        logger.info("\n[1/5] Validating environment variables...")
        self.validate_env()

        logger.info("\n[2/5] Validating ports...")
        self.validate_ports()

        logger.info("\n[3/5] Validating paths...")
        self.validate_paths()

        logger.info("\n[4/5] Validating Ollama models...")
        self.validate_models()

        logger.info("\n[5/5] Validating ChromaDB...")
        self.validate_chromadb()

        # Generate report
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed and r.severity == "error")
        warnings = sum(1 for r in self.results if not r.passed and r.severity == "warning")

        report = ValidationReport(
            timestamp=datetime.now().isoformat(),
            passed=failed == 0,
            total_checks=len(self.results),
            passed_checks=passed,
            failed_checks=failed,
            warnings=warnings,
            results=self.results
        )

        logger.info("\n" + "=" * 50)
        logger.info(f"  Validation {'PASSED' if report.passed else 'FAILED'}")
        logger.info(f"  Checks: {passed}/{len(self.results)} passed, {failed} errors, {warnings} warnings")
        logger.info("=" * 50)

        return report

    def print_report(self, report: Optional[ValidationReport] = None):
        """Print validation report to console."""
        if report is None:
            report = self.full_validation()

        print("\n" + "=" * 60)
        print("  SCORPION VALIDATION REPORT")
        print("=" * 60)
        print(f"  Status: {'PASSED' if report.passed else 'FAILED'}")
        print(f"  Time: {report.timestamp}")
        print("-" * 60)

        # Group by severity
        errors = [r for r in report.results if not r.passed and r.severity == "error"]
        warnings = [r for r in report.results if not r.passed and r.severity == "warning"]

        if errors:
            print("\n  ERRORS:")
            for r in errors:
                print(f"    ✗ {r.message}")

        if warnings:
            print("\n  WARNINGS:")
            for r in warnings:
                print(f"    ⚠ {r.message}")

        print("-" * 60)
        print(f"  Total: {report.passed_checks}/{report.total_checks} passed")
        print(f"  Errors: {report.failed_checks}")
        print(f"  Warnings: {report.warnings}")
        print("=" * 60 + "\n")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run validator from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="SCORPION Configuration Validator")
    parser.add_argument("--env", action="store_true", help="Validate environment only")
    parser.add_argument("--ports", action="store_true", help="Validate ports only")
    parser.add_argument("--paths", action="store_true", help="Validate paths only")
    parser.add_argument("--models", action="store_true", help="Validate models only")
    parser.add_argument("--chromadb", action="store_true", help="Validate ChromaDB only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    validator = ConfigValidator()

    if args.env:
        validator.validate_env()
    elif args.ports:
        validator.validate_ports()
    elif args.paths:
        validator.validate_paths()
    elif args.models:
        validator.validate_models()
    elif args.chromadb:
        validator.validate_chromadb()
    else:
        report = validator.full_validation()
        if args.json:
            import json
            print(json.dumps({
                "passed": report.passed,
                "total": report.total_checks,
                "errors": report.failed_checks,
                "warnings": report.warnings
            }, indent=2))
        else:
            validator.print_report(report)


if __name__ == "__main__":
    main()
