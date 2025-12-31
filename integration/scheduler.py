#!/usr/bin/env python3
"""
SCORPION JARVIS Scheduler
=========================

Automated task scheduler for the SCORPION ecosystem.
Loads tasks from agenda.json and executes them at scheduled times.

USAGE:
    python -m integration.scheduler           # Run once
    python -m integration.scheduler --daemon  # Run continuously

AGENDA FORMAT (daemon/agenda.json):
    {
        "tasks": [
            {
                "id": "daily-backup",
                "name": "Daily Backup",
                "schedule": "0 2 * * *",    # Cron format or interval
                "baby": "marcus",
                "action": "backup",
                "params": {"include_chromadb": true},
                "enabled": true
            }
        ]
    }

SCHEDULE FORMATS:
    - Cron: "0 2 * * *" (at 2:00 AM daily)
    - Interval: "every 5 minutes"
    - Time: "at 14:30"

Requirements:
    pip install schedule apscheduler
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
import threading
import signal

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import schedule
except ImportError:
    print("schedule not installed. Run: pip install schedule")
    schedule = None

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("JARVIS")

# Configuration
AGENDA_FILE = os.environ.get("JARVIS_AGENDA", "daemon/agenda.json")
LOG_DIR = os.environ.get("JARVIS_LOG_DIR", "logs/scheduler")


@dataclass
class Task:
    """Scheduled task definition."""
    id: str
    name: str
    schedule: str
    action: str
    baby: str = "marcus"
    params: Dict = field(default_factory=dict)
    enabled: bool = True
    last_run: Optional[str] = None
    last_result: Optional[str] = None
    run_count: int = 0


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    started_at: str = ""
    completed_at: str = ""
    duration_seconds: float = 0


class JarvisScheduler:
    """
    JARVIS - Just A Rather Very Intelligent Scheduler

    The automated task execution system for SCORPION.

    Usage:
        jarvis = JarvisScheduler()
        jarvis.load_agenda("daemon/agenda.json")
        jarvis.run_daemon()  # Or jarvis.run_once()
    """

    def __init__(self, agenda_file: str = AGENDA_FILE):
        self.agenda_file = Path(agenda_file)
        self.tasks: Dict[str, Task] = {}
        self.results: List[TaskResult] = []
        self._running = False
        self._scheduler = None

        # Ensure log directory exists
        Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

        # Action handlers
        self._actions: Dict[str, Callable] = {
            "ask": self._action_ask,
            "backup": self._action_backup,
            "health_check": self._action_health_check,
            "send_reminder": self._action_send_reminder,
            "generate_report": self._action_generate_report,
            "sync_data": self._action_sync_data,
            "cleanup": self._action_cleanup,
            "custom": self._action_custom
        }

        logger.info("JARVIS Scheduler initialized")

    def load_agenda(self, agenda_file: Optional[str] = None) -> bool:
        """
        Load tasks from agenda file.

        Args:
            agenda_file: Path to agenda JSON file

        Returns:
            True if loaded successfully
        """
        if agenda_file:
            self.agenda_file = Path(agenda_file)

        if not self.agenda_file.exists():
            logger.warning(f"Agenda file not found: {self.agenda_file}")
            self._create_default_agenda()
            return False

        try:
            data = json.loads(self.agenda_file.read_text())
            tasks_data = data.get("tasks", [])

            for task_data in tasks_data:
                task = Task(**task_data)
                self.tasks[task.id] = task
                logger.info(f"Loaded task: {task.id} ({task.name})")

            logger.info(f"Loaded {len(self.tasks)} tasks from {self.agenda_file}")
            return True

        except Exception as e:
            logger.error(f"Error loading agenda: {e}")
            return False

    def _create_default_agenda(self):
        """Create a default agenda file."""
        self.agenda_file.parent.mkdir(parents=True, exist_ok=True)

        default_agenda = {
            "version": "1.0",
            "description": "JARVIS Task Agenda",
            "tasks": [
                {
                    "id": "morning-health-check",
                    "name": "Morning Health Check",
                    "schedule": "0 8 * * *",
                    "action": "health_check",
                    "baby": "marcus",
                    "params": {},
                    "enabled": True
                },
                {
                    "id": "daily-backup",
                    "name": "Daily Backup",
                    "schedule": "0 2 * * *",
                    "action": "backup",
                    "baby": "marcus",
                    "params": {"include_chromadb": True},
                    "enabled": True
                },
                {
                    "id": "weekly-report",
                    "name": "Weekly Summary Report",
                    "schedule": "0 18 * * 5",
                    "action": "generate_report",
                    "baby": "marcus",
                    "params": {"report_type": "weekly"},
                    "enabled": True
                }
            ]
        }

        self.agenda_file.write_text(json.dumps(default_agenda, indent=2))
        logger.info(f"Created default agenda at {self.agenda_file}")

    def add_task(self, task: Task):
        """Add a task to the scheduler."""
        self.tasks[task.id] = task
        logger.info(f"Added task: {task.id}")

    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the scheduler."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Removed task: {task_id}")
            return True
        return False

    def execute_task(self, task: Task) -> TaskResult:
        """
        Execute a single task.

        Args:
            task: Task to execute

        Returns:
            TaskResult with execution details
        """
        logger.info(f"Executing task: {task.id} ({task.name})")
        started_at = datetime.now()

        result = TaskResult(
            task_id=task.id,
            success=False,
            output=None,
            started_at=started_at.isoformat()
        )

        try:
            # Get action handler
            action_handler = self._actions.get(task.action)
            if not action_handler:
                raise ValueError(f"Unknown action: {task.action}")

            # Execute action
            output = action_handler(task)

            result.success = True
            result.output = output

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            result.error = str(e)

        completed_at = datetime.now()
        result.completed_at = completed_at.isoformat()
        result.duration_seconds = (completed_at - started_at).total_seconds()

        # Update task stats
        task.last_run = completed_at.isoformat()
        task.last_result = "success" if result.success else "failed"
        task.run_count += 1

        # Store result
        self.results.append(result)
        self._log_result(result)

        status = "✓" if result.success else "✗"
        logger.info(f"Task {task.id} {status} ({result.duration_seconds:.2f}s)")

        return result

    def _log_result(self, result: TaskResult):
        """Log task result to file."""
        log_file = Path(LOG_DIR) / f"{result.task_id}.log"

        entry = {
            "timestamp": result.completed_at,
            "success": result.success,
            "duration": result.duration_seconds,
            "output": str(result.output)[:500] if result.output else None,
            "error": result.error
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    # =========================================================================
    # ACTION HANDLERS
    # =========================================================================

    def _action_ask(self, task: Task) -> str:
        """Ask an AI baby a question."""
        prompt = task.params.get("prompt", "What is your status?")
        baby = task.baby

        try:
            import requests
            response = requests.post(
                f"{os.environ.get('SCORPION_API_HOST', 'http://localhost:8080')}/ask",
                json={"baby": baby, "prompt": prompt},
                headers={"X-API-Key": os.environ.get("SCORPION_API_KEY", "scorpion-key")},
                timeout=120
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            return f"Error: {response.status_code}"
        except Exception as e:
            return f"Failed: {e}"

    def _action_backup(self, task: Task) -> Dict:
        """Run system backup."""
        results = {"backed_up": [], "errors": []}

        try:
            import subprocess
            script_path = Path(__file__).parent.parent / "scripts" / "backup.sh"
            if script_path.exists():
                result = subprocess.run(
                    ["bash", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                results["backed_up"].append("backup.sh executed")
                if result.returncode != 0:
                    results["errors"].append(result.stderr)
            else:
                results["errors"].append("backup.sh not found")
        except Exception as e:
            results["errors"].append(str(e))

        return results

    def _action_health_check(self, task: Task) -> Dict:
        """Run health check on all services."""
        try:
            from monitoring.health_check import HealthChecker
            checker = HealthChecker()
            return checker.run_all_checks()
        except ImportError:
            return {"error": "health_check module not available"}
        except Exception as e:
            return {"error": str(e)}

    def _action_send_reminder(self, task: Task) -> Dict:
        """Send scheduled reminders."""
        reminder_type = task.params.get("type", "appointment")
        results = {"sent": 0, "failed": 0}

        try:
            if reminder_type == "appointment":
                from nsipa.appointment_tracker import AppointmentTracker
                tracker = AppointmentTracker()
                appointments = tracker.get_needing_reminder(hours_before=24)

                for appt in appointments:
                    result = tracker.send_reminder(appt.id)
                    if result.get("email_sent") or result.get("sms_sent"):
                        results["sent"] += 1
                    else:
                        results["failed"] += 1

        except Exception as e:
            results["error"] = str(e)

        return results

    def _action_generate_report(self, task: Task) -> Dict:
        """Generate scheduled reports."""
        report_type = task.params.get("report_type", "daily")
        report_data = {"type": report_type, "generated_at": datetime.now().isoformat()}

        try:
            # Collect stats from various modules
            from claw1.crm.pipeline import Pipeline
            pipeline = Pipeline()
            report_data["pipeline"] = pipeline.get_pipeline_stats()
        except:
            pass

        try:
            from nsipa.call_logger import CallLogger
            logger = CallLogger()
            report_data["calls"] = logger.daily_summary()
        except:
            pass

        # Save report
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        report_file = reports_dir / f"{report_type}_{datetime.now().strftime('%Y%m%d')}.json"
        report_file.write_text(json.dumps(report_data, indent=2))

        return {"report_file": str(report_file)}

    def _action_sync_data(self, task: Task) -> Dict:
        """Sync data between services."""
        return {"status": "sync not implemented"}

    def _action_cleanup(self, task: Task) -> Dict:
        """Clean up old files and data."""
        cleaned = {"files_deleted": 0, "space_freed_mb": 0}

        # Clean old logs
        log_dir = Path(LOG_DIR)
        if log_dir.exists():
            import time
            cutoff = time.time() - (30 * 24 * 60 * 60)  # 30 days
            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff:
                    size = log_file.stat().st_size
                    log_file.unlink()
                    cleaned["files_deleted"] += 1
                    cleaned["space_freed_mb"] += size / (1024 * 1024)

        cleaned["space_freed_mb"] = round(cleaned["space_freed_mb"], 2)
        return cleaned

    def _action_custom(self, task: Task) -> Any:
        """Execute custom Python code."""
        code = task.params.get("code", "")
        if not code:
            return {"error": "No code provided"}

        # Security: Only allow whitelisted operations
        result = {"warning": "Custom code execution disabled for security"}
        return result

    # =========================================================================
    # SCHEDULER CONTROL
    # =========================================================================

    def run_once(self):
        """Run all enabled tasks once immediately."""
        logger.info("Running all tasks once...")

        for task in self.tasks.values():
            if task.enabled:
                self.execute_task(task)

        logger.info(f"Completed {len(self.tasks)} tasks")

    def run_daemon(self):
        """Run scheduler in daemon mode (continuously)."""
        if not APSCHEDULER_AVAILABLE:
            logger.error("APScheduler not installed. Run: pip install apscheduler")
            return

        self._running = True
        self._scheduler = BackgroundScheduler()

        # Schedule all tasks
        for task in self.tasks.values():
            if not task.enabled:
                continue

            try:
                trigger = self._parse_schedule(task.schedule)
                self._scheduler.add_job(
                    self.execute_task,
                    trigger=trigger,
                    args=[task],
                    id=task.id,
                    name=task.name,
                    replace_existing=True
                )
                logger.info(f"Scheduled: {task.id} ({task.schedule})")
            except Exception as e:
                logger.error(f"Failed to schedule {task.id}: {e}")

        # Start scheduler
        self._scheduler.start()
        logger.info("JARVIS Scheduler running (Ctrl+C to stop)")

        # Handle shutdown
        def signal_handler(signum, frame):
            logger.info("Shutting down...")
            self._running = False
            self._scheduler.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Keep running
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        logger.info("JARVIS Scheduler stopped")

    def _parse_schedule(self, schedule_str: str):
        """Parse schedule string into APScheduler trigger."""
        schedule_str = schedule_str.strip()

        # Cron format (5 fields)
        parts = schedule_str.split()
        if len(parts) == 5:
            return CronTrigger.from_crontab(schedule_str)

        # Interval format
        if schedule_str.startswith("every "):
            interval_str = schedule_str[6:]
            if "minute" in interval_str:
                minutes = int(interval_str.split()[0])
                return IntervalTrigger(minutes=minutes)
            elif "hour" in interval_str:
                hours = int(interval_str.split()[0])
                return IntervalTrigger(hours=hours)
            elif "day" in interval_str:
                days = int(interval_str.split()[0])
                return IntervalTrigger(days=days)

        raise ValueError(f"Cannot parse schedule: {schedule_str}")

    def get_status(self) -> Dict:
        """Get scheduler status."""
        return {
            "running": self._running,
            "tasks_count": len(self.tasks),
            "tasks_enabled": len([t for t in self.tasks.values() if t.enabled]),
            "total_runs": sum(t.run_count for t in self.tasks.values()),
            "recent_results": [
                {
                    "task_id": r.task_id,
                    "success": r.success,
                    "completed_at": r.completed_at
                }
                for r in self.results[-10:]
            ]
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="JARVIS Task Scheduler")
    parser.add_argument("--agenda", "-a", default=AGENDA_FILE, help="Agenda file path")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run in daemon mode")
    parser.add_argument("--task", "-t", help="Run specific task by ID")
    parser.add_argument("--list", "-l", action="store_true", help="List all tasks")

    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════════════╗
║                    JARVIS SCHEDULER                           ║
║            Just A Rather Very Intelligent Scheduler           ║
╚══════════════════════════════════════════════════════════════╝
    """)

    jarvis = JarvisScheduler(args.agenda)
    jarvis.load_agenda()

    if args.list:
        print("\nScheduled Tasks:")
        print("-" * 60)
        for task in jarvis.tasks.values():
            status = "✓" if task.enabled else "○"
            print(f"  {status} [{task.id}] {task.name}")
            print(f"      Schedule: {task.schedule}")
            print(f"      Action: {task.action} (via {task.baby})")
        return

    if args.task:
        task = jarvis.tasks.get(args.task)
        if task:
            jarvis.execute_task(task)
        else:
            print(f"Task not found: {args.task}")
        return

    if args.daemon:
        jarvis.run_daemon()
    else:
        jarvis.run_once()


if __name__ == "__main__":
    main()
