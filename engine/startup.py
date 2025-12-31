"""
SCORPION Startup Sequence
=========================

Handles ordered startup and shutdown of all SCORPION services.
Ensures dependencies are met before starting dependent services.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import os
import sys
import time
import json
import socket
import logging
import subprocess
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCORPION-STARTUP")


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class ServiceStatus(Enum):
    """Service status states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    STOPPING = "stopping"


class StartupPhase(Enum):
    """Startup phase definitions."""
    PREREQUISITES = "prerequisites"
    DATABASE = "database"
    CACHE = "cache"
    AI = "ai"
    API = "api"
    AUTOMATION = "automation"
    COMPLETE = "complete"


# =============================================================================
# SERVICE DEFINITIONS
# =============================================================================

@dataclass
class ServiceConfig:
    """Configuration for a managed service."""
    name: str
    port: int
    command: Optional[str] = None
    docker_service: Optional[str] = None
    health_endpoint: Optional[str] = None
    startup_timeout: int = 60
    dependencies: List[str] = field(default_factory=list)
    phase: StartupPhase = StartupPhase.API
    critical: bool = True


# Default SCORPION services in startup order
SERVICES: Dict[str, ServiceConfig] = {
    "chromadb": ServiceConfig(
        name="ChromaDB",
        port=8000,
        docker_service="scorpion-chromadb",
        health_endpoint="/api/v1/heartbeat",
        phase=StartupPhase.DATABASE,
        critical=True
    ),
    "redis": ServiceConfig(
        name="Redis",
        port=6379,
        docker_service="scorpion-redis",
        phase=StartupPhase.CACHE,
        critical=False
    ),
    "postgres": ServiceConfig(
        name="PostgreSQL",
        port=5432,
        docker_service="scorpion-postgres",
        phase=StartupPhase.DATABASE,
        critical=True
    ),
    "ollama": ServiceConfig(
        name="Ollama",
        port=11434,
        health_endpoint="/api/tags",
        phase=StartupPhase.AI,
        dependencies=["chromadb"],
        critical=True
    ),
    "api": ServiceConfig(
        name="SCORPION API",
        port=8080,
        command="python -m uvicorn mouth.api:app --host 0.0.0.0 --port 8080",
        health_endpoint="/health",
        phase=StartupPhase.API,
        dependencies=["chromadb", "ollama", "postgres"],
        critical=True
    ),
    "n8n": ServiceConfig(
        name="n8n",
        port=5678,
        docker_service="scorpion-n8n",
        health_endpoint="/healthz",
        phase=StartupPhase.AUTOMATION,
        dependencies=["postgres"],
        critical=False
    ),
    "scheduler": ServiceConfig(
        name="JARVIS Scheduler",
        port=0,  # No port
        command="python -m integration.scheduler",
        phase=StartupPhase.AUTOMATION,
        dependencies=["api", "ollama"],
        critical=False
    )
}


# =============================================================================
# STARTUP SEQUENCE CLASS
# =============================================================================

class StartupSequence:
    """
    Manages the SCORPION startup and shutdown sequence.

    Handles:
    - Prerequisite checking (Docker, Python deps, etc.)
    - Ordered service startup based on dependencies
    - Health checking for all services
    - Graceful shutdown in reverse order
    """

    def __init__(self, config_path: Optional[str] = None):
        self.services = SERVICES.copy()
        self.service_status: Dict[str, ServiceStatus] = {}
        self.service_processes: Dict[str, subprocess.Popen] = {}
        self.current_phase = StartupPhase.PREREQUISITES
        self._shutdown_requested = False

        # Initialize all services as stopped
        for name in self.services:
            self.service_status[name] = ServiceStatus.STOPPED

        logger.info("StartupSequence initialized")

    # -------------------------------------------------------------------------
    # Prerequisites
    # -------------------------------------------------------------------------

    def check_prerequisites(self) -> Dict[str, bool]:
        """Check all prerequisites are met before starting."""
        results = {}

        # Check Docker
        results["docker"] = self._check_command("docker --version")
        results["docker_compose"] = self._check_command("docker compose version")

        # Check Python dependencies
        results["python"] = sys.version_info >= (3, 11)

        try:
            import fastapi
            results["fastapi"] = True
        except ImportError:
            results["fastapi"] = False

        try:
            import chromadb
            results["chromadb_client"] = True
        except ImportError:
            results["chromadb_client"] = False

        try:
            import requests
            results["requests"] = True
        except ImportError:
            results["requests"] = False

        # Check Ollama
        results["ollama"] = self._check_command("ollama --version")

        # Check directories
        results["data_dir"] = Path("./data").exists() or self._create_dir("./data")
        results["logs_dir"] = Path("./logs").exists() or self._create_dir("./logs")

        # Log results
        passed = all(results.values())
        for check, result in results.items():
            status = "✓" if result else "✗"
            logger.info(f"  {status} {check}")

        return results

    def _check_command(self, command: str) -> bool:
        """Check if a command is available."""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _create_dir(self, path: str) -> bool:
        """Create directory if it doesn't exist."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Port Checking
    # -------------------------------------------------------------------------

    def _check_port(self, port: int, host: str = "localhost") -> bool:
        """Check if a port is available/listening."""
        if port == 0:
            return True

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            sock.close()
            return False

    def _wait_for_port(self, port: int, timeout: int = 60, host: str = "localhost") -> bool:
        """Wait for a port to become available."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._check_port(port, host):
                return True
            time.sleep(1)
        return False

    # -------------------------------------------------------------------------
    # Health Checking
    # -------------------------------------------------------------------------

    def _check_health_endpoint(self, port: int, endpoint: str) -> bool:
        """Check service health via HTTP endpoint."""
        try:
            import requests
            url = f"http://localhost:{port}{endpoint}"
            response = requests.get(url, timeout=5)
            return response.status_code < 500
        except Exception:
            return False

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all services."""
        results = {}

        for name, config in self.services.items():
            result = {
                "name": config.name,
                "status": "unknown",
                "port": config.port,
                "port_open": False,
                "health_ok": None
            }

            # Check port
            if config.port > 0:
                result["port_open"] = self._check_port(config.port)

            # Check health endpoint
            if config.health_endpoint and result["port_open"]:
                result["health_ok"] = self._check_health_endpoint(
                    config.port, config.health_endpoint
                )

            # Determine status
            if config.port == 0:
                result["status"] = str(self.service_status.get(name, ServiceStatus.STOPPED).value)
            elif result["port_open"]:
                if result["health_ok"] is None or result["health_ok"]:
                    result["status"] = "running"
                else:
                    result["status"] = "degraded"
            else:
                result["status"] = "stopped"

            results[name] = result

        return results

    # -------------------------------------------------------------------------
    # Service Starting
    # -------------------------------------------------------------------------

    def start_services(self) -> bool:
        """Start all services in the correct order."""
        logger.info("=" * 60)
        logger.info("  SCORPION STARTUP SEQUENCE")
        logger.info("=" * 60)

        # Check prerequisites first
        self.current_phase = StartupPhase.PREREQUISITES
        logger.info("\n[Phase 1] Checking prerequisites...")
        prereqs = self.check_prerequisites()

        if not all(prereqs.values()):
            logger.error("Prerequisites check failed!")
            return False

        # Start services by phase
        phases = [
            StartupPhase.DATABASE,
            StartupPhase.CACHE,
            StartupPhase.AI,
            StartupPhase.API,
            StartupPhase.AUTOMATION
        ]

        for phase in phases:
            self.current_phase = phase
            logger.info(f"\n[Phase] Starting {phase.value} services...")

            phase_services = [
                (name, config) for name, config in self.services.items()
                if config.phase == phase
            ]

            for name, config in phase_services:
                if self._shutdown_requested:
                    return False

                success = self._start_service(name, config)
                if not success and config.critical:
                    logger.error(f"Critical service {name} failed to start!")
                    return False

        self.current_phase = StartupPhase.COMPLETE
        logger.info("\n" + "=" * 60)
        logger.info("  SCORPION STARTUP COMPLETE")
        logger.info("=" * 60)

        return True

    def _start_service(self, name: str, config: ServiceConfig) -> bool:
        """Start a single service."""
        logger.info(f"  Starting {config.name}...")
        self.service_status[name] = ServiceStatus.STARTING

        # Check dependencies
        for dep in config.dependencies:
            if self.service_status.get(dep) != ServiceStatus.RUNNING:
                if not self._check_port(self.services[dep].port):
                    logger.warning(f"    Dependency {dep} not running")

        # Check if already running
        if config.port > 0 and self._check_port(config.port):
            logger.info(f"    {config.name} already running on port {config.port}")
            self.service_status[name] = ServiceStatus.RUNNING
            return True

        # Start Docker service
        if config.docker_service:
            try:
                subprocess.run(
                    ["docker", "compose", "-f", "body/docker/docker-compose.yml",
                     "up", "-d", config.docker_service],
                    capture_output=True,
                    timeout=30
                )
            except Exception as e:
                logger.warning(f"    Docker start failed: {e}")

        # Start command-based service
        elif config.command:
            try:
                process = subprocess.Popen(
                    config.command.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
                self.service_processes[name] = process
            except Exception as e:
                logger.error(f"    Failed to start: {e}")
                self.service_status[name] = ServiceStatus.FAILED
                return False

        # Wait for port
        if config.port > 0:
            if self._wait_for_port(config.port, config.startup_timeout):
                logger.info(f"    ✓ {config.name} running on port {config.port}")
                self.service_status[name] = ServiceStatus.RUNNING
                return True
            else:
                logger.error(f"    ✗ {config.name} failed to start")
                self.service_status[name] = ServiceStatus.FAILED
                return False

        # No port to check
        self.service_status[name] = ServiceStatus.RUNNING
        logger.info(f"    ✓ {config.name} started")
        return True

    # -------------------------------------------------------------------------
    # Shutdown
    # -------------------------------------------------------------------------

    def graceful_shutdown(self) -> bool:
        """Shutdown all services in reverse order."""
        logger.info("\n" + "=" * 60)
        logger.info("  SCORPION SHUTDOWN SEQUENCE")
        logger.info("=" * 60)

        self._shutdown_requested = True

        # Reverse order of phases
        phases = [
            StartupPhase.AUTOMATION,
            StartupPhase.API,
            StartupPhase.AI,
            StartupPhase.CACHE,
            StartupPhase.DATABASE
        ]

        for phase in phases:
            logger.info(f"\n[Phase] Stopping {phase.value} services...")

            phase_services = [
                (name, config) for name, config in self.services.items()
                if config.phase == phase
            ]

            for name, config in phase_services:
                self._stop_service(name, config)

        logger.info("\n" + "=" * 60)
        logger.info("  SCORPION SHUTDOWN COMPLETE")
        logger.info("=" * 60)

        return True

    def _stop_service(self, name: str, config: ServiceConfig) -> bool:
        """Stop a single service."""
        logger.info(f"  Stopping {config.name}...")
        self.service_status[name] = ServiceStatus.STOPPING

        # Stop subprocess
        if name in self.service_processes:
            try:
                process = self.service_processes[name]
                process.terminate()
                process.wait(timeout=10)
                del self.service_processes[name]
            except Exception as e:
                logger.warning(f"    Force killing: {e}")
                process.kill()

        # Stop Docker service
        if config.docker_service:
            try:
                subprocess.run(
                    ["docker", "compose", "-f", "body/docker/docker-compose.yml",
                     "stop", config.docker_service],
                    capture_output=True,
                    timeout=30
                )
            except Exception as e:
                logger.warning(f"    Docker stop failed: {e}")

        self.service_status[name] = ServiceStatus.STOPPED
        logger.info(f"    ✓ {config.name} stopped")
        return True

    # -------------------------------------------------------------------------
    # Status Reporting
    # -------------------------------------------------------------------------

    def status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report."""
        health = self.health_check_all()

        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": self.current_phase.value,
            "services": health,
            "summary": {
                "total": len(self.services),
                "running": sum(1 for s in health.values() if s["status"] == "running"),
                "stopped": sum(1 for s in health.values() if s["status"] == "stopped"),
                "failed": sum(1 for s in health.values() if s["status"] in ["failed", "degraded"])
            }
        }

        return report

    def print_status(self):
        """Print status to console."""
        report = self.status_report()

        print("\n" + "=" * 50)
        print("  SCORPION STATUS")
        print("=" * 50)
        print(f"  Phase: {report['phase']}")
        print(f"  Time: {report['timestamp']}")
        print("-" * 50)

        for name, service in report["services"].items():
            icon = "✓" if service["status"] == "running" else "✗"
            port = f":{service['port']}" if service['port'] > 0 else ""
            print(f"  {icon} {service['name']}{port} - {service['status']}")

        print("-" * 50)
        s = report["summary"]
        print(f"  Running: {s['running']}/{s['total']}")
        print("=" * 50 + "\n")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run startup sequence from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="SCORPION Startup Sequence")
    parser.add_argument("--check", action="store_true", help="Check prerequisites only")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--shutdown", action="store_true", help="Shutdown all services")

    args = parser.parse_args()

    startup = StartupSequence()

    if args.check:
        startup.check_prerequisites()
    elif args.status:
        startup.print_status()
    elif args.shutdown:
        startup.graceful_shutdown()
    else:
        startup.start_services()
        startup.print_status()


if __name__ == "__main__":
    main()
