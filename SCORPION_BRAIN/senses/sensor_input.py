"""
SCORPION_BRAIN Sensor Input
===========================
System and environment sensing capabilities.

Features:
- System metrics (CPU, memory, disk)
- File system watching
- Network monitoring
- Process monitoring
"""

import os
import subprocess
import time
import socket
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """Current system metrics snapshot."""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_percent: float
    disk_free_gb: float
    load_average: Tuple = (0.0, 0.0, 0.0)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class NetworkStatus:
    """Network connectivity status."""
    connected: bool
    local_ip: str
    gateway: Optional[str]
    dns_working: bool
    latency_ms: Optional[float]


@dataclass
class FileChange:
    """A detected file change."""
    path: str
    event_type: str  # created, modified, deleted
    timestamp: datetime
    size: Optional[int] = None


@dataclass
class ProcessInfo:
    """Information about a running process."""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str


# Import Tuple for type hints
from typing import Tuple


def get_system_metrics() -> Dict[str, Any]:
    """
    Get current system metrics.

    Returns:
        Dict with CPU, memory, disk, and load info
    """
    result = {
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }

    try:
        # Try psutil first
        if _has_python_module("psutil"):
            import psutil

            result["cpu_percent"] = psutil.cpu_percent(interval=0.5)
            result["cpu_count"] = psutil.cpu_count()

            mem = psutil.virtual_memory()
            result["memory_percent"] = mem.percent
            result["memory_available_mb"] = mem.available / (1024 * 1024)
            result["memory_total_mb"] = mem.total / (1024 * 1024)

            disk = psutil.disk_usage('/')
            result["disk_percent"] = disk.percent
            result["disk_free_gb"] = disk.free / (1024 * 1024 * 1024)
            result["disk_total_gb"] = disk.total / (1024 * 1024 * 1024)

            result["load_average"] = os.getloadavg()
            result["status"] = "success"

        else:
            # Fallback to system commands
            result.update(_get_metrics_from_commands())

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _get_metrics_from_commands() -> Dict:
    """Get metrics using system commands."""
    result = {"status": "success"}

    try:
        # CPU - from /proc/stat
        if Path("/proc/stat").exists():
            with open("/proc/stat") as f:
                cpu_line = f.readline()
                values = cpu_line.split()[1:5]
                values = [int(v) for v in values]
                total = sum(values)
                idle = values[3]
                result["cpu_percent"] = round((1 - idle / total) * 100, 1) if total > 0 else 0

        # Memory - from /proc/meminfo
        if Path("/proc/meminfo").exists():
            meminfo = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = int(parts[1].strip().split()[0])  # in kB
                        meminfo[key] = value

            total = meminfo.get("MemTotal", 1)
            available = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
            result["memory_percent"] = round((1 - available / total) * 100, 1)
            result["memory_available_mb"] = available / 1024

        # Disk - from df
        proc = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        if proc.returncode == 0:
            lines = proc.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    result["disk_percent"] = int(parts[4].rstrip('%'))

        # Load average
        result["load_average"] = os.getloadavg()

    except Exception as e:
        result["status"] = "partial"
        result["error"] = str(e)

    return result


def watch_file(
    path: str,
    callback: Callable[[FileChange], None] = None,
    timeout: float = 60.0
) -> Dict[str, Any]:
    """
    Watch a file or directory for changes.

    Args:
        path: Path to watch
        callback: Function to call on changes
        timeout: How long to watch (seconds)

    Returns:
        Dict with watch results and any detected changes
    """
    result = {
        "status": "pending",
        "path": path,
        "timeout": timeout,
        "changes": []
    }

    if not Path(path).exists():
        result["status"] = "error"
        result["error"] = f"Path not found: {path}"
        return result

    try:
        # Try inotifywait (Linux)
        if _has_command("inotifywait"):
            changes = _watch_with_inotify(path, timeout)
            result["changes"] = changes
            result["status"] = "success"
            result["method"] = "inotify"

        # Try fswatch (macOS/cross-platform)
        elif _has_command("fswatch"):
            changes = _watch_with_fswatch(path, timeout)
            result["changes"] = changes
            result["status"] = "success"
            result["method"] = "fswatch"

        # Fallback to polling
        else:
            changes = _watch_with_polling(path, timeout)
            result["changes"] = changes
            result["status"] = "success"
            result["method"] = "polling"

        # Call callback for each change
        if callback:
            for change in result["changes"]:
                try:
                    callback(FileChange(**change))
                except Exception as e:
                    logger.error(f"Callback error: {e}")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _watch_with_inotify(path: str, timeout: float) -> List[Dict]:
    """Watch using inotifywait."""
    changes = []
    try:
        proc = subprocess.run(
            ["inotifywait", "-t", str(int(timeout)), "-e", "modify,create,delete", "--format", "%e %w%f", path],
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )

        for line in proc.stdout.strip().split('\n'):
            if line:
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    event_type = parts[0].lower()
                    file_path = parts[1]
                    changes.append({
                        "path": file_path,
                        "event_type": event_type,
                        "timestamp": datetime.now().isoformat()
                    })

    except subprocess.TimeoutExpired:
        pass  # Normal timeout

    return changes


def _watch_with_fswatch(path: str, timeout: float) -> List[Dict]:
    """Watch using fswatch."""
    changes = []
    try:
        proc = subprocess.run(
            ["fswatch", "-1", "-r", path],
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )

        for line in proc.stdout.strip().split('\n'):
            if line:
                changes.append({
                    "path": line,
                    "event_type": "modified",
                    "timestamp": datetime.now().isoformat()
                })

    except subprocess.TimeoutExpired:
        pass

    return changes


def _watch_with_polling(path: str, timeout: float) -> List[Dict]:
    """Watch using polling (fallback)."""
    changes = []
    path_obj = Path(path)

    if path_obj.is_file():
        paths = [path_obj]
    else:
        paths = list(path_obj.iterdir())

    # Record initial states
    initial_states = {}
    for p in paths:
        try:
            initial_states[str(p)] = p.stat().st_mtime
        except Exception:
            pass

    # Poll for changes
    end_time = time.time() + timeout
    check_interval = 1.0

    while time.time() < end_time:
        time.sleep(check_interval)

        for p in paths:
            try:
                current_mtime = p.stat().st_mtime
                if str(p) in initial_states:
                    if current_mtime != initial_states[str(p)]:
                        changes.append({
                            "path": str(p),
                            "event_type": "modified",
                            "timestamp": datetime.now().isoformat()
                        })
                        initial_states[str(p)] = current_mtime
            except FileNotFoundError:
                if str(p) in initial_states:
                    changes.append({
                        "path": str(p),
                        "event_type": "deleted",
                        "timestamp": datetime.now().isoformat()
                    })
                    del initial_states[str(p)]

        # Check for new files
        if path_obj.is_dir():
            for p in path_obj.iterdir():
                if str(p) not in initial_states:
                    changes.append({
                        "path": str(p),
                        "event_type": "created",
                        "timestamp": datetime.now().isoformat()
                    })
                    try:
                        initial_states[str(p)] = p.stat().st_mtime
                    except Exception:
                        pass

    return changes


def check_network(
    hosts: List[str] = None,
    timeout: float = 5.0
) -> Dict[str, Any]:
    """
    Check network connectivity.

    Args:
        hosts: Hosts to check (default: common DNS servers)
        timeout: Timeout for each check

    Returns:
        Dict with network status
    """
    hosts = hosts or ["8.8.8.8", "1.1.1.1", "google.com"]

    result = {
        "status": "pending",
        "timestamp": datetime.now().isoformat(),
        "hosts_checked": hosts
    }

    try:
        # Get local IP
        result["local_ip"] = _get_local_ip()

        # Check connectivity to each host
        host_results = []
        for host in hosts:
            host_result = _ping_host(host, timeout)
            host_results.append(host_result)

        result["host_results"] = host_results

        # Overall connectivity
        result["connected"] = any(h["reachable"] for h in host_results)

        # DNS check
        try:
            socket.gethostbyname("google.com")
            result["dns_working"] = True
        except socket.gaierror:
            result["dns_working"] = False

        # Average latency
        latencies = [h["latency_ms"] for h in host_results if h.get("latency_ms")]
        if latencies:
            result["avg_latency_ms"] = sum(latencies) / len(latencies)

        result["status"] = "success"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["connected"] = False

    return result


def _get_local_ip() -> str:
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _ping_host(host: str, timeout: float) -> Dict:
    """Ping a host and return result."""
    result = {
        "host": host,
        "reachable": False,
        "latency_ms": None
    }

    try:
        start = time.time()

        # Try socket connection first (faster)
        port = 443 if "." in host and not host.replace(".", "").isdigit() else 53
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        try:
            resolved = socket.gethostbyname(host) if not host.replace(".", "").isdigit() else host
            sock.connect((resolved, port))
            sock.close()
            result["reachable"] = True
            result["latency_ms"] = round((time.time() - start) * 1000, 2)
        except (socket.timeout, socket.error):
            # Fallback to ping command
            proc = subprocess.run(
                ["ping", "-c", "1", "-W", str(int(timeout)), host],
                capture_output=True,
                timeout=timeout + 1
            )
            result["reachable"] = proc.returncode == 0

    except Exception as e:
        result["error"] = str(e)

    return result


def get_processes(filter_name: str = None, top_n: int = 10) -> Dict[str, Any]:
    """
    Get running processes.

    Args:
        filter_name: Filter by process name
        top_n: Number of processes to return (sorted by CPU)

    Returns:
        Dict with process list
    """
    result = {
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }

    try:
        if _has_python_module("psutil"):
            import psutil

            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    info = proc.info
                    if filter_name and filter_name.lower() not in info['name'].lower():
                        continue

                    processes.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "cpu_percent": info['cpu_percent'] or 0,
                        "memory_percent": round(info['memory_percent'] or 0, 2),
                        "status": info['status']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            result["processes"] = processes[:top_n]

        else:
            # Fallback to ps command
            proc = subprocess.run(
                ["ps", "aux", "--sort=-%cpu"],
                capture_output=True,
                text=True
            )
            lines = proc.stdout.strip().split('\n')[1:top_n+1]
            processes = []
            for line in lines:
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    processes.append({
                        "pid": int(parts[1]),
                        "name": parts[10][:50],
                        "cpu_percent": float(parts[2]),
                        "memory_percent": float(parts[3]),
                        "status": "running"
                    })
            result["processes"] = processes

        result["status"] = "success"
        result["count"] = len(result.get("processes", []))

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _has_command(cmd: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _has_python_module(module: str) -> bool:
    """Check if a Python module is available."""
    try:
        __import__(module)
        return True
    except ImportError:
        return False


class SensorInput:
    """
    High-level interface for sensor input.

    Usage:
        sensor = SensorInput()
        metrics = sensor.get_metrics()
        sensor.watch_path("/tmp", on_change=handler)
    """

    def __init__(self):
        self.watchers: Dict[str, threading.Thread] = {}
        self.metrics_history: List[SystemMetrics] = []

    def get_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        result = get_system_metrics()

        metrics = SystemMetrics(
            cpu_percent=result.get("cpu_percent", 0),
            memory_percent=result.get("memory_percent", 0),
            memory_available_mb=result.get("memory_available_mb", 0),
            disk_percent=result.get("disk_percent", 0),
            disk_free_gb=result.get("disk_free_gb", 0),
            load_average=result.get("load_average", (0, 0, 0))
        )

        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-500:]

        return metrics

    def check_network(self) -> NetworkStatus:
        """Check network connectivity."""
        result = check_network()

        return NetworkStatus(
            connected=result.get("connected", False),
            local_ip=result.get("local_ip", "unknown"),
            gateway=result.get("gateway"),
            dns_working=result.get("dns_working", False),
            latency_ms=result.get("avg_latency_ms")
        )

    def watch_path(
        self,
        path: str,
        on_change: Callable[[FileChange], None],
        timeout: float = 60.0
    ):
        """Start watching a path for changes."""
        watch_file(path, on_change, timeout)

    def get_top_processes(self, n: int = 10) -> List[ProcessInfo]:
        """Get top N processes by CPU usage."""
        result = get_processes(top_n=n)
        return [
            ProcessInfo(
                pid=p["pid"],
                name=p["name"],
                cpu_percent=p["cpu_percent"],
                memory_percent=p["memory_percent"],
                status=p["status"]
            )
            for p in result.get("processes", [])
        ]


if __name__ == "__main__":
    # Demo
    sensor = SensorInput()

    print("=== System Metrics ===")
    metrics = sensor.get_metrics()
    print(f"CPU: {metrics.cpu_percent}%")
    print(f"Memory: {metrics.memory_percent}%")
    print(f"Disk: {metrics.disk_percent}%")
    print(f"Load: {metrics.load_average}")

    print("\n=== Network Status ===")
    network = sensor.check_network()
    print(f"Connected: {network.connected}")
    print(f"Local IP: {network.local_ip}")
    print(f"DNS: {network.dns_working}")

    print("\n=== Top Processes ===")
    processes = sensor.get_top_processes(5)
    for p in processes:
        print(f"  {p.name} (PID {p.pid}): CPU {p.cpu_percent}%, MEM {p.memory_percent}%")
