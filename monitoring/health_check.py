"""
SCORPION Health Monitor - Service Health Check System
=====================================================

Monitors the health of all SCORPION services and reports status.
Can run standalone or be integrated into the Docker health check system.

Features:
- Service availability checks
- Response time monitoring
- Memory and CPU usage tracking
- Alert generation for failures
- Health history logging
- Dashboard metrics export

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import os
import sys
import json
import time
import logging
import threading
import requests
import subprocess
import platform
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCORPION-HEALTH")


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class HealthStatus(Enum):
    """Service health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceType(Enum):
    """Types of services to monitor."""
    HTTP = "http"
    TCP = "tcp"
    DOCKER = "docker"
    PROCESS = "process"
    CUSTOM = "custom"


# Health check configuration
DEFAULT_TIMEOUT = 5  # seconds
DEFAULT_INTERVAL = 30  # seconds
HISTORY_RETENTION = 100  # number of checks to retain


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ServiceConfig:
    """Configuration for a monitored service."""
    name: str
    service_type: ServiceType
    endpoint: str = ""
    port: int = 0
    container_name: str = ""
    process_name: str = ""
    timeout: int = DEFAULT_TIMEOUT
    interval: int = DEFAULT_INTERVAL
    critical: bool = True
    health_path: str = "/health"
    expected_status: int = 200
    custom_check: Optional[Callable] = None


@dataclass
class HealthCheck:
    """Result of a health check."""
    service_name: str
    status: HealthStatus
    response_time_ms: float = 0.0
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    load_average: List[float] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# SERVICE DEFINITIONS
# =============================================================================

# Default SCORPION services to monitor
DEFAULT_SERVICES = [
    ServiceConfig(
        name="scorpion-brain",
        service_type=ServiceType.HTTP,
        endpoint="http://localhost:8080",
        health_path="/health",
        critical=True
    ),
    ServiceConfig(
        name="chromadb",
        service_type=ServiceType.HTTP,
        endpoint="http://localhost:8000",
        health_path="/api/v1/heartbeat",
        critical=True
    ),
    ServiceConfig(
        name="ollama",
        service_type=ServiceType.HTTP,
        endpoint="http://localhost:11434",
        health_path="/api/tags",
        critical=True
    ),
    ServiceConfig(
        name="n8n",
        service_type=ServiceType.HTTP,
        endpoint="http://localhost:5678",
        health_path="/healthz",
        critical=False
    ),
    ServiceConfig(
        name="postgres",
        service_type=ServiceType.TCP,
        endpoint="localhost",
        port=5432,
        critical=True
    ),
    ServiceConfig(
        name="redis",
        service_type=ServiceType.TCP,
        endpoint="localhost",
        port=6379,
        critical=False
    ),
    ServiceConfig(
        name="nginx",
        service_type=ServiceType.TCP,
        endpoint="localhost",
        port=80,
        critical=False
    ),
]


# =============================================================================
# HEALTH CHECKER CLASS
# =============================================================================

class HealthChecker:
    """
    Main health checker that monitors all SCORPION services.
    """

    def __init__(
        self,
        services: Optional[List[ServiceConfig]] = None,
        alerts_callback: Optional[Callable[[HealthCheck], None]] = None,
        data_dir: str = "data/health"
    ):
        self.services = services or DEFAULT_SERVICES
        self.alerts_callback = alerts_callback
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.health_history: Dict[str, List[HealthCheck]] = {}
        self._running = False
        self._check_threads: List[threading.Thread] = []

        logger.info(f"HealthChecker initialized with {len(self.services)} services")

    # -------------------------------------------------------------------------
    # Health Check Methods
    # -------------------------------------------------------------------------

    def check_http_service(self, config: ServiceConfig) -> HealthCheck:
        """Check HTTP service health."""
        start_time = time.time()

        try:
            url = f"{config.endpoint}{config.health_path}"
            response = requests.get(url, timeout=config.timeout)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == config.expected_status:
                status = HealthStatus.HEALTHY
                message = f"OK - {response.status_code}"
            elif response.status_code < 500:
                status = HealthStatus.DEGRADED
                message = f"Degraded - {response.status_code}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Error - {response.status_code}"

            return HealthCheck(
                service_name=config.name,
                status=status,
                response_time_ms=response_time,
                message=message,
                details={"status_code": response.status_code, "url": url}
            )

        except requests.exceptions.Timeout:
            return HealthCheck(
                service_name=config.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                message="Timeout",
                details={"error": "Connection timeout"}
            )

        except requests.exceptions.ConnectionError as e:
            return HealthCheck(
                service_name=config.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                message="Connection failed",
                details={"error": str(e)}
            )

        except Exception as e:
            return HealthCheck(
                service_name=config.name,
                status=HealthStatus.UNKNOWN,
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Error: {str(e)}",
                details={"error": str(e)}
            )

    def check_tcp_service(self, config: ServiceConfig) -> HealthCheck:
        """Check TCP service health by attempting connection."""
        start_time = time.time()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(config.timeout)
            result = sock.connect_ex((config.endpoint, config.port))
            sock.close()

            response_time = (time.time() - start_time) * 1000

            if result == 0:
                return HealthCheck(
                    service_name=config.name,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message=f"Port {config.port} open",
                    details={"port": config.port, "host": config.endpoint}
                )
            else:
                return HealthCheck(
                    service_name=config.name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message=f"Port {config.port} closed",
                    details={"port": config.port, "error_code": result}
                )

        except socket.timeout:
            return HealthCheck(
                service_name=config.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                message="Connection timeout",
                details={"port": config.port}
            )

        except Exception as e:
            return HealthCheck(
                service_name=config.name,
                status=HealthStatus.UNKNOWN,
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Error: {str(e)}",
                details={"error": str(e)}
            )

    def check_docker_container(self, config: ServiceConfig) -> HealthCheck:
        """Check Docker container health."""
        start_time = time.time()

        try:
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Status}}", config.container_name],
                capture_output=True,
                text=True,
                timeout=config.timeout
            )

            response_time = (time.time() - start_time) * 1000

            if result.returncode == 0:
                container_status = result.stdout.strip()

                if container_status == "running":
                    return HealthCheck(
                        service_name=config.name,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        message="Container running",
                        details={"container": config.container_name, "state": container_status}
                    )
                else:
                    return HealthCheck(
                        service_name=config.name,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        message=f"Container {container_status}",
                        details={"container": config.container_name, "state": container_status}
                    )
            else:
                return HealthCheck(
                    service_name=config.name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message="Container not found",
                    details={"error": result.stderr.strip()}
                )

        except subprocess.TimeoutExpired:
            return HealthCheck(
                service_name=config.name,
                status=HealthStatus.UNKNOWN,
                response_time_ms=(time.time() - start_time) * 1000,
                message="Docker command timeout"
            )

        except Exception as e:
            return HealthCheck(
                service_name=config.name,
                status=HealthStatus.UNKNOWN,
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Error: {str(e)}"
            )

    def check_process(self, config: ServiceConfig) -> HealthCheck:
        """Check if a process is running."""
        start_time = time.time()

        try:
            if platform.system() == "Windows":
                cmd = ["tasklist", "/FI", f"IMAGENAME eq {config.process_name}"]
            else:
                cmd = ["pgrep", "-f", config.process_name]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.timeout)
            response_time = (time.time() - start_time) * 1000

            if result.returncode == 0 and result.stdout.strip():
                return HealthCheck(
                    service_name=config.name,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Process running",
                    details={"process": config.process_name}
                )
            else:
                return HealthCheck(
                    service_name=config.name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message="Process not found",
                    details={"process": config.process_name}
                )

        except Exception as e:
            return HealthCheck(
                service_name=config.name,
                status=HealthStatus.UNKNOWN,
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Error: {str(e)}"
            )

    def check_service(self, config: ServiceConfig) -> HealthCheck:
        """Check a service based on its type."""
        if config.service_type == ServiceType.HTTP:
            return self.check_http_service(config)
        elif config.service_type == ServiceType.TCP:
            return self.check_tcp_service(config)
        elif config.service_type == ServiceType.DOCKER:
            return self.check_docker_container(config)
        elif config.service_type == ServiceType.PROCESS:
            return self.check_process(config)
        elif config.service_type == ServiceType.CUSTOM and config.custom_check:
            return config.custom_check(config)
        else:
            return HealthCheck(
                service_name=config.name,
                status=HealthStatus.UNKNOWN,
                message="Unknown service type"
            )

    # -------------------------------------------------------------------------
    # System Metrics
    # -------------------------------------------------------------------------

    def get_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics."""
        metrics = SystemMetrics()

        try:
            # Try to use psutil if available
            import psutil
            metrics.cpu_percent = psutil.cpu_percent(interval=1)
            metrics.memory_percent = psutil.virtual_memory().percent
            metrics.disk_percent = psutil.disk_usage('/').percent
        except ImportError:
            # Fallback to basic methods
            try:
                # CPU from /proc/loadavg
                with open('/proc/loadavg', 'r') as f:
                    load = f.read().split()
                    metrics.load_average = [float(x) for x in load[:3]]

                # Memory from /proc/meminfo
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split(':')
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = int(parts[1].strip().split()[0])
                            meminfo[key] = value

                    total = meminfo.get('MemTotal', 1)
                    available = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))
                    metrics.memory_percent = ((total - available) / total) * 100

                # Disk from df
                result = subprocess.run(['df', '/'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split()
                        if len(parts) >= 5:
                            metrics.disk_percent = float(parts[4].rstrip('%'))

            except Exception as e:
                logger.warning(f"Could not collect system metrics: {e}")

        return metrics

    # -------------------------------------------------------------------------
    # Health Check Runner
    # -------------------------------------------------------------------------

    def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run health checks on all services."""
        results = {}

        for config in self.services:
            check = self.check_service(config)
            results[config.name] = check

            # Store in history
            if config.name not in self.health_history:
                self.health_history[config.name] = []
            self.health_history[config.name].append(check)

            # Trim history
            if len(self.health_history[config.name]) > HISTORY_RETENTION:
                self.health_history[config.name] = self.health_history[config.name][-HISTORY_RETENTION:]

            # Trigger alerts for unhealthy critical services
            if config.critical and check.status == HealthStatus.UNHEALTHY:
                self._trigger_alert(check)

        return results

    def _trigger_alert(self, check: HealthCheck) -> None:
        """Trigger an alert for an unhealthy service."""
        logger.warning(f"ALERT: {check.service_name} is {check.status.value} - {check.message}")

        if self.alerts_callback:
            self.alerts_callback(check)

    # -------------------------------------------------------------------------
    # Continuous Monitoring
    # -------------------------------------------------------------------------

    def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        self._running = True
        logger.info("Starting health monitoring...")

        def monitor_loop():
            while self._running:
                self.run_all_checks()
                self._save_latest_status()
                time.sleep(DEFAULT_INTERVAL)

        thread = threading.Thread(target=monitor_loop)
        thread.daemon = True
        thread.start()
        self._check_threads.append(thread)

    def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        self._running = False
        for thread in self._check_threads:
            thread.join(timeout=5.0)
        logger.info("Health monitoring stopped")

    # -------------------------------------------------------------------------
    # Status Reporting
    # -------------------------------------------------------------------------

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        results = self.run_all_checks()

        critical_unhealthy = any(
            check.status == HealthStatus.UNHEALTHY
            for name, check in results.items()
            if any(s.critical for s in self.services if s.name == name)
        )

        if critical_unhealthy:
            return HealthStatus.UNHEALTHY

        any_degraded = any(check.status == HealthStatus.DEGRADED for check in results.values())
        if any_degraded:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def get_status_report(self) -> Dict[str, Any]:
        """Generate a comprehensive status report."""
        results = self.run_all_checks()
        metrics = self.get_system_metrics()

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self.get_overall_status().value,
            "services": {
                name: {
                    "status": check.status.value,
                    "response_time_ms": check.response_time_ms,
                    "message": check.message
                }
                for name, check in results.items()
            },
            "system_metrics": asdict(metrics),
            "healthy_count": sum(1 for c in results.values() if c.status == HealthStatus.HEALTHY),
            "unhealthy_count": sum(1 for c in results.values() if c.status == HealthStatus.UNHEALTHY),
            "total_services": len(results)
        }

        return report

    def _save_latest_status(self) -> None:
        """Save latest status to file."""
        try:
            report = self.get_status_report()
            status_file = self.data_dir / "latest_status.json"
            with open(status_file, 'w') as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save status: {e}")

    def print_status(self) -> None:
        """Print status to console."""
        report = self.get_status_report()

        print("\n" + "=" * 60)
        print("  SCORPION HEALTH STATUS")
        print("=" * 60)
        print(f"  Time: {report['timestamp']}")
        print(f"  Overall: {report['overall_status'].upper()}")
        print("-" * 60)

        for name, service in report['services'].items():
            status_icon = "✓" if service['status'] == 'healthy' else "✗"
            print(f"  {status_icon} {name}: {service['status']} ({service['response_time_ms']:.1f}ms)")

        print("-" * 60)
        print(f"  Healthy: {report['healthy_count']}/{report['total_services']}")
        print(f"  CPU: {report['system_metrics']['cpu_percent']:.1f}%")
        print(f"  Memory: {report['system_metrics']['memory_percent']:.1f}%")
        print(f"  Disk: {report['system_metrics']['disk_percent']:.1f}%")
        print("=" * 60 + "\n")


# =============================================================================
# MAIN - Standalone Execution
# =============================================================================

def main():
    """Run health checks from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="SCORPION Health Monitor")
    parser.add_argument("--continuous", "-c", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--interval", "-i", type=int, default=30, help="Check interval (seconds)")

    args = parser.parse_args()

    checker = HealthChecker()

    if args.continuous:
        checker.start_monitoring()
        try:
            while True:
                time.sleep(args.interval)
                if not args.json:
                    checker.print_status()
        except KeyboardInterrupt:
            checker.stop_monitoring()
    else:
        if args.json:
            report = checker.get_status_report()
            print(json.dumps(report, indent=2))
        else:
            checker.print_status()

        # Exit with appropriate code
        status = checker.get_overall_status()
        sys.exit(0 if status == HealthStatus.HEALTHY else 1)


if __name__ == "__main__":
    main()
