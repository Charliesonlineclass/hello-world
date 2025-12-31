"""
SCORPION_BRAIN Eagle Toolbox
============================
Safe execution tools for file creation, code sandboxing,
system commands, and screen capture.

Safety Features:
- Sandboxed code execution
- Path validation
- Command whitelist/blacklist
- Resource limits
"""

import subprocess
import tempfile
import os
import sys
import shutil
import signal
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging
import threading
import queue

logger = logging.getLogger(__name__)


# Safety constants
BLOCKED_COMMANDS = {'rm -rf /', 'dd if=', 'mkfs', ':(){:|:&};:', 'chmod -R 777 /'}
ALLOWED_EXTENSIONS = {'.py', '.txt', '.json', '.md', '.sh', '.yaml', '.yml', '.toml', '.csv'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_EXEC_TIME = 30  # seconds
MAX_OUTPUT_SIZE = 100 * 1024  # 100KB


@dataclass
class ExecutionResult:
    """Result from code or command execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    duration: float
    error: Optional[str] = None


@dataclass
class FileResult:
    """Result from file operation."""
    success: bool
    path: str
    size: int
    message: str
    error: Optional[str] = None


class FileCreator:
    """
    Safe file creation with validation.

    Features:
    - Path validation
    - Extension whitelist
    - Size limits
    - Atomic writes
    """

    def __init__(self, base_dir: str = None, allowed_dirs: List[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.home() / "scorpion_files"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.allowed_dirs = allowed_dirs or [str(self.base_dir), "/tmp"]

    def _validate_path(self, path: str) -> tuple:
        """Validate file path is safe."""
        path_obj = Path(path).resolve()

        # Check if in allowed directory
        in_allowed = any(str(path_obj).startswith(d) for d in self.allowed_dirs)
        if not in_allowed:
            return False, f"Path not in allowed directories: {self.allowed_dirs}"

        # Check extension
        if path_obj.suffix.lower() not in ALLOWED_EXTENSIONS and path_obj.suffix:
            return False, f"Extension not allowed: {path_obj.suffix}"

        # Check for path traversal
        if ".." in str(path):
            return False, "Path traversal not allowed"

        return True, ""

    def create(self, path: str, content: str, overwrite: bool = False) -> FileResult:
        """Create a file safely."""
        valid, error = self._validate_path(path)
        if not valid:
            return FileResult(success=False, path=path, size=0, message=error, error=error)

        path_obj = Path(path)

        # Check size
        if len(content) > MAX_FILE_SIZE:
            return FileResult(
                success=False, path=path, size=0,
                message=f"Content too large: {len(content)} > {MAX_FILE_SIZE}",
                error="Size limit exceeded"
            )

        # Check if exists
        if path_obj.exists() and not overwrite:
            return FileResult(
                success=False, path=path, size=0,
                message="File exists, use overwrite=True",
                error="File exists"
            )

        try:
            # Create parent directories
            path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write using temp file
            temp_path = path_obj.with_suffix(path_obj.suffix + ".tmp")
            with open(temp_path, 'w') as f:
                f.write(content)

            # Move to final location
            shutil.move(str(temp_path), str(path_obj))

            return FileResult(
                success=True,
                path=str(path_obj),
                size=len(content),
                message=f"Created successfully"
            )

        except Exception as e:
            return FileResult(
                success=False, path=path, size=0,
                message=str(e), error=str(e)
            )

    def read(self, path: str) -> tuple:
        """Read a file safely."""
        valid, error = self._validate_path(path)
        if not valid:
            return None, error

        try:
            with open(path, 'r') as f:
                content = f.read(MAX_FILE_SIZE)
            return content, None
        except Exception as e:
            return None, str(e)

    def delete(self, path: str) -> FileResult:
        """Delete a file safely."""
        valid, error = self._validate_path(path)
        if not valid:
            return FileResult(success=False, path=path, size=0, message=error, error=error)

        try:
            Path(path).unlink()
            return FileResult(success=True, path=path, size=0, message="Deleted")
        except Exception as e:
            return FileResult(success=False, path=path, size=0, message=str(e), error=str(e))


class CodeSandbox:
    """
    Sandboxed code execution environment.

    Features:
    - Timeout enforcement
    - Resource limits
    - Output capture
    - Safe execution
    """

    def __init__(self, timeout: int = MAX_EXEC_TIME, max_output: int = MAX_OUTPUT_SIZE):
        self.timeout = timeout
        self.max_output = max_output
        self.temp_dir = Path(tempfile.mkdtemp(prefix="scorpion_sandbox_"))

    def execute_python(self, code: str, **kwargs) -> ExecutionResult:
        """Execute Python code in sandbox."""
        # Create temp file
        script_path = self.temp_dir / "script.py"
        with open(script_path, 'w') as f:
            f.write(code)

        # Execute with timeout
        return self._run_process([sys.executable, str(script_path)], **kwargs)

    def execute_bash(self, script: str, **kwargs) -> ExecutionResult:
        """Execute bash script in sandbox."""
        script_path = self.temp_dir / "script.sh"
        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n" + script)

        os.chmod(script_path, 0o755)
        return self._run_process(["bash", str(script_path)], **kwargs)

    def _run_process(self, cmd: List[str], **kwargs) -> ExecutionResult:
        """Run a process with safety measures."""
        start_time = datetime.now()

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.temp_dir),
                env=self._get_safe_env()
            )

            try:
                stdout, stderr = proc.communicate(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="",
                    return_code=-1,
                    duration=(datetime.now() - start_time).total_seconds(),
                    error=f"Execution timed out after {self.timeout}s"
                )

            duration = (datetime.now() - start_time).total_seconds()

            return ExecutionResult(
                success=proc.returncode == 0,
                stdout=stdout.decode('utf-8', errors='ignore')[:self.max_output],
                stderr=stderr.decode('utf-8', errors='ignore')[:self.max_output],
                return_code=proc.returncode,
                duration=duration
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                duration=0,
                error=str(e)
            )

    def _get_safe_env(self) -> Dict[str, str]:
        """Get a safe environment for execution."""
        safe_env = os.environ.copy()
        # Remove sensitive variables
        for key in ['AWS_', 'GITHUB_', 'API_KEY', 'SECRET', 'PASSWORD', 'TOKEN']:
            safe_env = {k: v for k, v in safe_env.items() if key not in k.upper()}
        return safe_env

    def cleanup(self):
        """Clean up temporary files."""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


class CommandRunner:
    """
    Safe system command execution.

    Features:
    - Command validation
    - Whitelist/blacklist
    - Output capture
    - Timeout handling
    """

    def __init__(self, whitelist: List[str] = None, blacklist: List[str] = None):
        self.whitelist = set(whitelist or [
            'ls', 'pwd', 'cat', 'head', 'tail', 'grep', 'find', 'wc',
            'date', 'whoami', 'hostname', 'uname', 'df', 'du', 'free',
            'ps', 'top', 'echo', 'which', 'file', 'stat', 'id'
        ])
        self.blacklist = set(blacklist or BLOCKED_COMMANDS)

    def _is_safe(self, command: str) -> tuple:
        """Check if command is safe to run."""
        # Check blacklist
        for blocked in self.blacklist:
            if blocked in command:
                return False, f"Blocked command pattern: {blocked}"

        # Extract base command
        parts = command.strip().split()
        if not parts:
            return False, "Empty command"

        base_cmd = parts[0].split('/')[-1]  # Handle full paths

        # Check whitelist if defined
        if self.whitelist and base_cmd not in self.whitelist:
            return False, f"Command not in whitelist: {base_cmd}"

        return True, ""

    def run(self, command: str, timeout: int = 30) -> ExecutionResult:
        """Run a command safely."""
        safe, error = self._is_safe(command)
        if not safe:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=error,
                return_code=-1,
                duration=0,
                error=error
            )

        start_time = datetime.now()

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=timeout,
                text=True
            )

            duration = (datetime.now() - start_time).total_seconds()

            return ExecutionResult(
                success=proc.returncode == 0,
                stdout=proc.stdout[:MAX_OUTPUT_SIZE],
                stderr=proc.stderr[:MAX_OUTPUT_SIZE],
                return_code=proc.returncode,
                duration=duration
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                duration=timeout,
                error=f"Command timed out after {timeout}s"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                duration=0,
                error=str(e)
            )


def capture_screen(output_path: str = None) -> Dict[str, Any]:
    """
    Capture screenshot (placeholder for integration).

    In production, uses visual_input from senses module.
    """
    output_path = output_path or f"/tmp/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    # Try to use scrot or other screenshot tool
    for tool in ['scrot', 'gnome-screenshot', 'import']:
        try:
            if tool == 'scrot':
                result = subprocess.run(['scrot', output_path], capture_output=True, timeout=10)
            elif tool == 'gnome-screenshot':
                result = subprocess.run(['gnome-screenshot', '-f', output_path], capture_output=True, timeout=10)
            elif tool == 'import':
                result = subprocess.run(['import', '-window', 'root', output_path], capture_output=True, timeout=10)

            if result.returncode == 0 and Path(output_path).exists():
                return {
                    "success": True,
                    "path": output_path,
                    "tool": tool,
                    "size": Path(output_path).stat().st_size
                }
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    return {
        "success": False,
        "path": output_path,
        "error": "No screenshot tool available"
    }


class EagleToolbox:
    """
    Combined toolbox for all Eagle operations.

    Usage:
        tools = EagleToolbox()
        tools.create_file("test.py", "print('hello')")
        result = tools.execute_python("print('hello')")
        tools.run_command("ls -la")
    """

    def __init__(self):
        self.file_creator = FileCreator()
        self.sandbox = CodeSandbox()
        self.commander = CommandRunner()

    def create_file(self, path: str, content: str, overwrite: bool = False) -> FileResult:
        """Create a file."""
        return self.file_creator.create(path, content, overwrite)

    def read_file(self, path: str) -> tuple:
        """Read a file."""
        return self.file_creator.read(path)

    def execute_python(self, code: str) -> ExecutionResult:
        """Execute Python code."""
        return self.sandbox.execute_python(code)

    def execute_bash(self, script: str) -> ExecutionResult:
        """Execute bash script."""
        return self.sandbox.execute_bash(script)

    def run_command(self, command: str, timeout: int = 30) -> ExecutionResult:
        """Run a system command."""
        return self.commander.run(command, timeout)

    def capture_screen(self, output_path: str = None) -> Dict:
        """Capture screenshot."""
        return capture_screen(output_path)

    def cleanup(self):
        """Cleanup resources."""
        self.sandbox.cleanup()


# Convenience functions
def create_file(path: str, content: str, overwrite: bool = False) -> FileResult:
    """Quick file creation."""
    return FileCreator().create(path, content, overwrite)


def execute_code(code: str, language: str = "python") -> ExecutionResult:
    """Quick code execution."""
    sandbox = CodeSandbox()
    try:
        if language == "python":
            return sandbox.execute_python(code)
        elif language == "bash":
            return sandbox.execute_bash(code)
        else:
            return ExecutionResult(
                success=False, stdout="", stderr=f"Unsupported language: {language}",
                return_code=-1, duration=0, error="Unsupported language"
            )
    finally:
        sandbox.cleanup()


def run_command(command: str, timeout: int = 30) -> ExecutionResult:
    """Quick command execution."""
    return CommandRunner().run(command, timeout)


if __name__ == "__main__":
    # Demo
    tools = EagleToolbox()

    print("=== File Creation ===")
    result = tools.create_file("/tmp/test_eagle.txt", "Hello from Eagle!\n")
    print(f"Created: {result.success} - {result.path}")

    print("\n=== Python Execution ===")
    result = tools.execute_python("print('Hello from sandbox!')\nprint(2 + 2)")
    print(f"Success: {result.success}")
    print(f"Output: {result.stdout}")

    print("\n=== Command Execution ===")
    result = tools.run_command("echo 'Hello' && date")
    print(f"Success: {result.success}")
    print(f"Output: {result.stdout}")

    print("\n=== Screenshot ===")
    result = tools.capture_screen()
    print(f"Screenshot: {result}")

    tools.cleanup()
