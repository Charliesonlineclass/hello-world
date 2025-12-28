"""
SCORPION_BRAIN Action Output
============================
Execute actions in the environment.

Features:
- Shell command execution
- File operations
- Docker management
- API calls
- System control
"""

import subprocess
import shutil
import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result from a shell command."""
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration: float
    success: bool


@dataclass
class FileOperationResult:
    """Result from a file operation."""
    operation: str
    path: str
    success: bool
    message: str
    size: Optional[int] = None


@dataclass
class DockerResult:
    """Result from a Docker operation."""
    operation: str
    container: Optional[str]
    success: bool
    output: str
    error: Optional[str] = None


@dataclass
class APIResult:
    """Result from an API call."""
    url: str
    method: str
    status_code: int
    response: Any
    duration: float
    success: bool


def run_shell(
    command: str,
    timeout: int = 60,
    cwd: str = None,
    env: Dict[str, str] = None,
    shell: bool = True
) -> Dict[str, Any]:
    """
    Execute a shell command.

    Args:
        command: Command to execute
        timeout: Timeout in seconds
        cwd: Working directory
        env: Environment variables
        shell: Use shell execution

    Returns:
        Dict with command results
    """
    result = {
        "command": command,
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }

    start_time = datetime.now()

    try:
        # Merge environment
        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        # Execute command
        proc = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=run_env
        )

        duration = (datetime.now() - start_time).total_seconds()

        result["status"] = "success" if proc.returncode == 0 else "failed"
        result["returncode"] = proc.returncode
        result["stdout"] = proc.stdout[:10000]  # Limit output size
        result["stderr"] = proc.stderr[:5000]
        result["duration"] = duration
        result["success"] = proc.returncode == 0

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = f"Command timed out after {timeout} seconds"
        result["success"] = False

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["success"] = False

    return result


def file_operation(
    operation: str,
    path: str,
    content: str = None,
    destination: str = None,
    mode: str = None
) -> Dict[str, Any]:
    """
    Perform file operations.

    Args:
        operation: read, write, append, delete, copy, move, mkdir, exists
        path: Target path
        content: Content for write/append
        destination: Destination for copy/move
        mode: File mode (e.g., "755")

    Returns:
        Dict with operation results
    """
    result = {
        "operation": operation,
        "path": path,
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }

    path_obj = Path(path)

    try:
        if operation == "read":
            if not path_obj.exists():
                result["status"] = "error"
                result["error"] = "File not found"
            else:
                content = path_obj.read_text()
                result["status"] = "success"
                result["content"] = content[:50000]  # Limit size
                result["size"] = len(content)
                result["truncated"] = len(content) > 50000

        elif operation == "write":
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.write_text(content or "")
            result["status"] = "success"
            result["size"] = len(content or "")

        elif operation == "append":
            with open(path, 'a') as f:
                f.write(content or "")
            result["status"] = "success"
            result["appended"] = len(content or "")

        elif operation == "delete":
            if path_obj.is_dir():
                shutil.rmtree(path)
            else:
                path_obj.unlink()
            result["status"] = "success"

        elif operation == "copy":
            if not destination:
                result["status"] = "error"
                result["error"] = "Destination required for copy"
            else:
                dest_obj = Path(destination)
                dest_obj.parent.mkdir(parents=True, exist_ok=True)
                if path_obj.is_dir():
                    shutil.copytree(path, destination)
                else:
                    shutil.copy2(path, destination)
                result["status"] = "success"
                result["destination"] = destination

        elif operation == "move":
            if not destination:
                result["status"] = "error"
                result["error"] = "Destination required for move"
            else:
                dest_obj = Path(destination)
                dest_obj.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(path, destination)
                result["status"] = "success"
                result["destination"] = destination

        elif operation == "mkdir":
            path_obj.mkdir(parents=True, exist_ok=True)
            result["status"] = "success"

        elif operation == "exists":
            result["status"] = "success"
            result["exists"] = path_obj.exists()
            if path_obj.exists():
                result["is_file"] = path_obj.is_file()
                result["is_dir"] = path_obj.is_dir()
                stat = path_obj.stat()
                result["size"] = stat.st_size
                result["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        elif operation == "chmod":
            if mode:
                os.chmod(path, int(mode, 8))
                result["status"] = "success"
                result["mode"] = mode
            else:
                result["status"] = "error"
                result["error"] = "Mode required for chmod"

        elif operation == "list":
            if not path_obj.is_dir():
                result["status"] = "error"
                result["error"] = "Path is not a directory"
            else:
                files = []
                for item in path_obj.iterdir():
                    files.append({
                        "name": item.name,
                        "is_dir": item.is_dir(),
                        "size": item.stat().st_size if item.is_file() else 0
                    })
                result["status"] = "success"
                result["files"] = files[:100]  # Limit
                result["count"] = len(files)

        else:
            result["status"] = "error"
            result["error"] = f"Unknown operation: {operation}"

        result["success"] = result["status"] == "success"

    except PermissionError:
        result["status"] = "error"
        result["error"] = "Permission denied"
        result["success"] = False

    except FileNotFoundError:
        result["status"] = "error"
        result["error"] = "File not found"
        result["success"] = False

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["success"] = False

    return result


def docker_operation(
    operation: str,
    container: str = None,
    image: str = None,
    command: str = None,
    options: Dict = None
) -> Dict[str, Any]:
    """
    Perform Docker operations.

    Args:
        operation: ps, run, exec, stop, start, rm, images, pull, logs
        container: Container name/ID
        image: Image name
        command: Command to run
        options: Additional options

    Returns:
        Dict with Docker results
    """
    options = options or {}

    result = {
        "operation": operation,
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }

    # Check if Docker is available
    if not _has_command("docker"):
        result["status"] = "error"
        result["error"] = "Docker not installed"
        return result

    try:
        if operation == "ps":
            cmd = ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"]
            if options.get("all"):
                cmd.append("-a")

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if proc.returncode == 0:
                containers = []
                for line in proc.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            containers.append({
                                "id": parts[0],
                                "name": parts[1],
                                "image": parts[2],
                                "status": parts[3]
                            })
                result["status"] = "success"
                result["containers"] = containers

        elif operation == "run":
            if not image:
                result["status"] = "error"
                result["error"] = "Image required for run"
            else:
                cmd = ["docker", "run"]
                if options.get("detach"):
                    cmd.append("-d")
                if options.get("name"):
                    cmd.extend(["--name", options["name"]])
                if options.get("ports"):
                    for port in options["ports"]:
                        cmd.extend(["-p", port])
                if options.get("volumes"):
                    for vol in options["volumes"]:
                        cmd.extend(["-v", vol])

                cmd.append(image)
                if command:
                    cmd.extend(command.split())

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                result["status"] = "success" if proc.returncode == 0 else "failed"
                result["output"] = proc.stdout
                result["error"] = proc.stderr if proc.returncode != 0 else None

        elif operation == "exec":
            if not container:
                result["status"] = "error"
                result["error"] = "Container required for exec"
            else:
                cmd = ["docker", "exec", container]
                if command:
                    cmd.extend(command.split())
                else:
                    cmd.append("sh")

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                result["status"] = "success" if proc.returncode == 0 else "failed"
                result["output"] = proc.stdout
                result["error"] = proc.stderr if proc.returncode != 0 else None

        elif operation == "stop":
            if not container:
                result["status"] = "error"
                result["error"] = "Container required for stop"
            else:
                proc = subprocess.run(
                    ["docker", "stop", container],
                    capture_output=True, text=True, timeout=30
                )
                result["status"] = "success" if proc.returncode == 0 else "failed"
                result["output"] = proc.stdout

        elif operation == "start":
            if not container:
                result["status"] = "error"
                result["error"] = "Container required for start"
            else:
                proc = subprocess.run(
                    ["docker", "start", container],
                    capture_output=True, text=True, timeout=30
                )
                result["status"] = "success" if proc.returncode == 0 else "failed"
                result["output"] = proc.stdout

        elif operation == "rm":
            if not container:
                result["status"] = "error"
                result["error"] = "Container required for rm"
            else:
                cmd = ["docker", "rm"]
                if options.get("force"):
                    cmd.append("-f")
                cmd.append(container)

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                result["status"] = "success" if proc.returncode == 0 else "failed"

        elif operation == "images":
            proc = subprocess.run(
                ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}\t{{.Size}}"],
                capture_output=True, text=True, timeout=30
            )
            images = []
            for line in proc.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        images.append({"name": parts[0], "size": parts[1]})
            result["status"] = "success"
            result["images"] = images

        elif operation == "pull":
            if not image:
                result["status"] = "error"
                result["error"] = "Image required for pull"
            else:
                proc = subprocess.run(
                    ["docker", "pull", image],
                    capture_output=True, text=True, timeout=300
                )
                result["status"] = "success" if proc.returncode == 0 else "failed"
                result["output"] = proc.stdout

        elif operation == "logs":
            if not container:
                result["status"] = "error"
                result["error"] = "Container required for logs"
            else:
                cmd = ["docker", "logs"]
                if options.get("tail"):
                    cmd.extend(["--tail", str(options["tail"])])
                cmd.append(container)

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                result["status"] = "success"
                result["logs"] = proc.stdout[-10000:]  # Limit size

        else:
            result["status"] = "error"
            result["error"] = f"Unknown operation: {operation}"

        result["success"] = result.get("status") == "success"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Operation timed out"
        result["success"] = False

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["success"] = False

    return result


def api_call(
    url: str,
    method: str = "GET",
    data: Dict = None,
    headers: Dict = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Make an HTTP API call.

    Args:
        url: Target URL
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request body (for POST/PUT)
        headers: HTTP headers
        timeout: Request timeout

    Returns:
        Dict with API response
    """
    result = {
        "url": url,
        "method": method,
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }

    start_time = datetime.now()

    try:
        # Prepare request
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        req_data = None
        if data and method in ["POST", "PUT", "PATCH"]:
            req_data = json.dumps(data).encode('utf-8')

        request = urllib.request.Request(
            url,
            data=req_data,
            headers=req_headers,
            method=method
        )

        # Make request
        with urllib.request.urlopen(request, timeout=timeout) as response:
            duration = (datetime.now() - start_time).total_seconds()

            result["status"] = "success"
            result["status_code"] = response.status
            result["duration"] = duration

            # Read response
            response_data = response.read().decode('utf-8')

            # Try to parse as JSON
            try:
                result["response"] = json.loads(response_data)
            except json.JSONDecodeError:
                result["response"] = response_data[:10000]

            result["success"] = 200 <= response.status < 300

    except urllib.error.HTTPError as e:
        result["status"] = "error"
        result["status_code"] = e.code
        result["error"] = str(e)
        result["success"] = False

    except urllib.error.URLError as e:
        result["status"] = "error"
        result["error"] = str(e.reason)
        result["success"] = False

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["success"] = False

    return result


def _has_command(cmd: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class ActionOutput:
    """
    High-level interface for action output.

    Usage:
        action = ActionOutput()
        result = action.shell("ls -la")
        action.write_file("/tmp/test.txt", "Hello")
        action.docker_run("python:3.9", "python --version")
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.history: List[Dict] = []

    def shell(self, command: str, timeout: int = 60) -> CommandResult:
        """Execute a shell command."""
        if self.dry_run:
            return CommandResult(
                command=command,
                returncode=0,
                stdout="[DRY RUN]",
                stderr="",
                duration=0,
                success=True
            )

        result = run_shell(command, timeout)
        self.history.append({"type": "shell", **result})

        return CommandResult(
            command=result["command"],
            returncode=result.get("returncode", -1),
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            duration=result.get("duration", 0),
            success=result.get("success", False)
        )

    def read_file(self, path: str) -> str:
        """Read a file."""
        result = file_operation("read", path)
        return result.get("content", "")

    def write_file(self, path: str, content: str) -> bool:
        """Write to a file."""
        if self.dry_run:
            return True

        result = file_operation("write", path, content=content)
        self.history.append({"type": "file", **result})
        return result.get("success", False)

    def delete_file(self, path: str) -> bool:
        """Delete a file or directory."""
        if self.dry_run:
            return True

        result = file_operation("delete", path)
        self.history.append({"type": "file", **result})
        return result.get("success", False)

    def docker_ps(self, all_containers: bool = False) -> List[Dict]:
        """List Docker containers."""
        result = docker_operation("ps", options={"all": all_containers})
        return result.get("containers", [])

    def docker_run(self, image: str, command: str = None, **options) -> DockerResult:
        """Run a Docker container."""
        if self.dry_run:
            return DockerResult(
                operation="run",
                container=None,
                success=True,
                output="[DRY RUN]"
            )

        result = docker_operation("run", image=image, command=command, options=options)
        self.history.append({"type": "docker", **result})

        return DockerResult(
            operation="run",
            container=result.get("output", "").strip(),
            success=result.get("success", False),
            output=result.get("output", ""),
            error=result.get("error")
        )

    def api_get(self, url: str, headers: Dict = None) -> APIResult:
        """Make a GET request."""
        result = api_call(url, "GET", headers=headers)
        self.history.append({"type": "api", **result})

        return APIResult(
            url=url,
            method="GET",
            status_code=result.get("status_code", 0),
            response=result.get("response"),
            duration=result.get("duration", 0),
            success=result.get("success", False)
        )

    def api_post(self, url: str, data: Dict, headers: Dict = None) -> APIResult:
        """Make a POST request."""
        result = api_call(url, "POST", data=data, headers=headers)
        self.history.append({"type": "api", **result})

        return APIResult(
            url=url,
            method="POST",
            status_code=result.get("status_code", 0),
            response=result.get("response"),
            duration=result.get("duration", 0),
            success=result.get("success", False)
        )

    def get_history(self) -> List[Dict]:
        """Get action history."""
        return self.history

    def clear_history(self):
        """Clear action history."""
        self.history = []


if __name__ == "__main__":
    # Demo
    action = ActionOutput()

    print("=== Shell Command ===")
    result = action.shell("echo 'Hello from SCORPION_BRAIN'")
    print(f"Success: {result.success}")
    print(f"Output: {result.stdout}")

    print("\n=== File Operations ===")
    test_file = "/tmp/scorpion_test.txt"
    action.write_file(test_file, "Test content from SCORPION_BRAIN\n")
    content = action.read_file(test_file)
    print(f"Written and read: {content}")

    print("\n=== Docker Status ===")
    docker_result = docker_operation("ps")
    print(f"Docker status: {docker_result['status']}")
    if docker_result.get("containers"):
        for c in docker_result["containers"][:3]:
            print(f"  - {c['name']}: {c['status']}")
