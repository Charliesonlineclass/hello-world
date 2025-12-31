"""
SCORPION Classroom
==================

Baby management, registration, and monitoring.
Tracks baby status, statistics, and enables collaboration.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import requests

from .prompts import SYSTEM_PROMPTS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCORPION-CLASSROOM")


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BabyConfig:
    """Configuration for an AI baby."""
    name: str
    model: str
    specialty: str
    port: int = 11434
    host: str = "localhost"
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = ""
    active: bool = True


@dataclass
class BabyStats:
    """Statistics for a baby's performance."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time_ms: float = 0.0
    avg_response_time_ms: float = 0.0
    last_used: Optional[str] = None
    tokens_generated: int = 0


@dataclass
class CollaborationTask:
    """Task for baby collaboration."""
    task_id: str
    prompt: str
    babies: List[str]
    current_baby_index: int = 0
    context: str = ""
    responses: Dict[str, str] = field(default_factory=dict)
    status: str = "pending"


# =============================================================================
# DEFAULT BABIES
# =============================================================================

DEFAULT_BABIES: Dict[str, BabyConfig] = {
    "MARCUS": BabyConfig(
        name="MARCUS",
        model="mistral",
        specialty="Strategy and Analysis",
        temperature=0.7,
        system_prompt=SYSTEM_PROMPTS.get("MARCUS", "")
    ),
    "VULCAN": BabyConfig(
        name="VULCAN",
        model="codellama",
        specialty="Code and Technical",
        temperature=0.3,
        system_prompt=SYSTEM_PROMPTS.get("VULCAN", "")
    ),
    "HERMES": BabyConfig(
        name="HERMES",
        model="phi",
        specialty="Quick Responses",
        temperature=0.5,
        max_tokens=1024,
        system_prompt=SYSTEM_PROMPTS.get("HERMES", "")
    ),
    "APOLLO": BabyConfig(
        name="APOLLO",
        model="llama2",
        specialty="Creative Writing",
        temperature=0.9,
        system_prompt=SYSTEM_PROMPTS.get("APOLLO", "")
    ),
    "ATHENA": BabyConfig(
        name="ATHENA",
        model="mistral",
        specialty="Research and Knowledge",
        temperature=0.5,
        system_prompt=SYSTEM_PROMPTS.get("ATHENA", "")
    ),
}


# =============================================================================
# CLASSROOM CLASS
# =============================================================================

class Classroom:
    """
    Manages all AI babies in the SCORPION system.

    Provides:
    - Baby registration and configuration
    - Online status checking
    - Request routing and execution
    - Performance statistics
    - Collaborative task management
    """

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.babies: Dict[str, BabyConfig] = DEFAULT_BABIES.copy()
        self.stats: Dict[str, BabyStats] = defaultdict(BabyStats)
        self.collaboration_tasks: Dict[str, CollaborationTask] = {}

        logger.info(f"Classroom initialized with {len(self.babies)} babies")

    # -------------------------------------------------------------------------
    # Baby Registration
    # -------------------------------------------------------------------------

    def register_baby(
        self,
        name: str,
        model: str,
        specialty: str,
        **kwargs
    ) -> BabyConfig:
        """Register a new baby."""
        config = BabyConfig(
            name=name,
            model=model,
            specialty=specialty,
            **kwargs
        )

        self.babies[name] = config
        self.stats[name] = BabyStats()

        logger.info(f"Registered baby: {name} ({model})")
        return config

    def unregister_baby(self, name: str) -> bool:
        """Unregister a baby."""
        if name in self.babies:
            del self.babies[name]
            if name in self.stats:
                del self.stats[name]
            logger.info(f"Unregistered baby: {name}")
            return True
        return False

    def get_baby(self, name: str) -> Optional[BabyConfig]:
        """Get baby configuration."""
        return self.babies.get(name)

    def update_baby(self, name: str, **kwargs) -> Optional[BabyConfig]:
        """Update baby configuration."""
        if name not in self.babies:
            return None

        config = self.babies[name]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        logger.info(f"Updated baby: {name}")
        return config

    # -------------------------------------------------------------------------
    # Status Checking
    # -------------------------------------------------------------------------

    def _check_baby_online(self, baby: BabyConfig) -> bool:
        """Check if a baby's model is available."""
        try:
            url = f"http://{baby.host}:{baby.port}/api/tags"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                models = [m["name"].split(":")[0] for m in data.get("models", [])]
                return baby.model in models

        except Exception:
            pass

        return False

    def list_online(self) -> List[str]:
        """Get list of online babies."""
        online = []

        for name, config in self.babies.items():
            if config.active and self._check_baby_online(config):
                online.append(name)

        return online

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all babies."""
        status = {}

        for name, config in self.babies.items():
            online = self._check_baby_online(config)
            stats = self.stats.get(name, BabyStats())

            status[name] = {
                "name": name,
                "model": config.model,
                "specialty": config.specialty,
                "online": online,
                "active": config.active,
                "stats": {
                    "total_requests": stats.total_requests,
                    "success_rate": (
                        stats.successful_requests / stats.total_requests * 100
                        if stats.total_requests > 0 else 0
                    ),
                    "avg_response_time_ms": stats.avg_response_time_ms,
                    "last_used": stats.last_used
                }
            }

        return status

    # -------------------------------------------------------------------------
    # Baby Communication
    # -------------------------------------------------------------------------

    def baby_ask(
        self,
        name: str,
        prompt: str,
        context: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Send a prompt to a specific baby."""
        if name not in self.babies:
            return {"success": False, "error": f"Unknown baby: {name}"}

        config = self.babies[name]

        if not config.active:
            return {"success": False, "error": f"Baby {name} is not active"}

        # Build full prompt
        full_prompt = ""
        if config.system_prompt:
            full_prompt += config.system_prompt + "\n\n"
        if context:
            full_prompt += f"Context: {context}\n\n"
        full_prompt += prompt

        try:
            start_time = time.time()

            response = requests.post(
                f"http://{config.host}:{config.port}/api/generate",
                json={
                    "model": config.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature or config.temperature,
                        "num_predict": config.max_tokens
                    }
                },
                timeout=120
            )

            elapsed_ms = (time.time() - start_time) * 1000

            # Update stats
            stats = self.stats[name]
            stats.total_requests += 1
            stats.last_used = datetime.now().isoformat()

            if response.status_code == 200:
                data = response.json()

                stats.successful_requests += 1
                stats.total_response_time_ms += elapsed_ms
                stats.avg_response_time_ms = (
                    stats.total_response_time_ms / stats.successful_requests
                )
                stats.tokens_generated += data.get("eval_count", 0)

                return {
                    "success": True,
                    "baby": name,
                    "response": data.get("response", ""),
                    "elapsed_ms": elapsed_ms,
                    "tokens": data.get("eval_count", 0)
                }
            else:
                stats.failed_requests += 1
                return {
                    "success": False,
                    "baby": name,
                    "error": f"HTTP {response.status_code}",
                    "elapsed_ms": elapsed_ms
                }

        except Exception as e:
            self.stats[name].failed_requests += 1
            return {
                "success": False,
                "baby": name,
                "error": str(e),
                "elapsed_ms": 0
            }

    # -------------------------------------------------------------------------
    # Collaboration
    # -------------------------------------------------------------------------

    def baby_collaborate(
        self,
        babies: List[str],
        initial_prompt: str,
        continuation_prompt: str = "Continue from the previous response:"
    ) -> Dict[str, Any]:
        """
        Have multiple babies process a task sequentially.
        Each baby builds on the previous one's response.
        """
        if not babies:
            return {"success": False, "error": "No babies specified"}

        responses = {}
        context = initial_prompt

        for i, baby in enumerate(babies):
            if i == 0:
                prompt = initial_prompt
            else:
                prompt = f"{continuation_prompt}\n\n{context}"

            result = self.baby_ask(baby, prompt)

            if result["success"]:
                responses[baby] = result["response"]
                context = result["response"]
            else:
                responses[baby] = f"Error: {result.get('error', 'Unknown')}"
                break

        return {
            "success": all(baby in responses for baby in babies),
            "responses": responses,
            "final_response": context
        }

    def start_collaboration_task(
        self,
        task_id: str,
        prompt: str,
        babies: List[str]
    ) -> CollaborationTask:
        """Start an async collaboration task."""
        task = CollaborationTask(
            task_id=task_id,
            prompt=prompt,
            babies=babies,
            status="in_progress"
        )

        self.collaboration_tasks[task_id] = task
        return task

    def process_collaboration_step(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Process the next step of a collaboration task."""
        if task_id not in self.collaboration_tasks:
            return None

        task = self.collaboration_tasks[task_id]

        if task.current_baby_index >= len(task.babies):
            task.status = "complete"
            return {"status": "complete", "responses": task.responses}

        current_baby = task.babies[task.current_baby_index]

        # Build prompt
        if task.current_baby_index == 0:
            prompt = task.prompt
        else:
            prompt = f"Continue from:\n{task.context}\n\nTask: {task.prompt}"

        result = self.baby_ask(current_baby, prompt)

        if result["success"]:
            task.responses[current_baby] = result["response"]
            task.context = result["response"]
            task.current_baby_index += 1

        return {
            "status": task.status,
            "current_baby": current_baby,
            "result": result
        }

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_baby_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific baby."""
        if name not in self.babies:
            return None

        stats = self.stats.get(name, BabyStats())

        return {
            "name": name,
            "total_requests": stats.total_requests,
            "successful_requests": stats.successful_requests,
            "failed_requests": stats.failed_requests,
            "success_rate": (
                stats.successful_requests / stats.total_requests * 100
                if stats.total_requests > 0 else 0
            ),
            "avg_response_time_ms": stats.avg_response_time_ms,
            "tokens_generated": stats.tokens_generated,
            "last_used": stats.last_used
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all babies."""
        return {name: self.get_baby_stats(name) for name in self.babies}

    def reset_stats(self, name: Optional[str] = None):
        """Reset statistics for a baby or all babies."""
        if name:
            if name in self.stats:
                self.stats[name] = BabyStats()
        else:
            self.stats = defaultdict(BabyStats)

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------

    def list_babies(self) -> List[Dict[str, Any]]:
        """List all registered babies."""
        return [
            {
                "name": name,
                "model": config.model,
                "specialty": config.specialty,
                "active": config.active
            }
            for name, config in self.babies.items()
        ]

    def print_status(self):
        """Print classroom status to console."""
        status = self.get_status()

        print("\n" + "=" * 50)
        print("  SCORPION CLASSROOM STATUS")
        print("=" * 50)

        for name, info in status.items():
            icon = "✓" if info["online"] else "✗"
            active = "" if info["active"] else " (inactive)"
            print(f"  {icon} {name} ({info['model']}){active}")
            print(f"      Specialty: {info['specialty']}")
            if info["stats"]["total_requests"] > 0:
                print(f"      Requests: {info['stats']['total_requests']} "
                      f"({info['stats']['success_rate']:.0f}% success)")
                print(f"      Avg time: {info['stats']['avg_response_time_ms']:.0f}ms")

        print("=" * 50 + "\n")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run classroom from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="SCORPION Classroom")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--list", action="store_true", help="List babies")
    parser.add_argument("--ask", help="Baby to ask")
    parser.add_argument("--prompt", help="Prompt to send")
    parser.add_argument("--stats", help="Show stats for baby")

    args = parser.parse_args()

    classroom = Classroom()

    if args.status:
        classroom.print_status()
    elif args.list:
        for baby in classroom.list_babies():
            print(f"{baby['name']} ({baby['model']}): {baby['specialty']}")
    elif args.ask and args.prompt:
        result = classroom.baby_ask(args.ask, args.prompt)
        if result["success"]:
            print(f"\n{args.ask}:")
            print(result["response"])
        else:
            print(f"Error: {result.get('error')}")
    elif args.stats:
        stats = classroom.get_baby_stats(args.stats)
        if stats:
            print(f"\n{args.stats} Stats:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print(f"Unknown baby: {args.stats}")
    else:
        classroom.print_status()


if __name__ == "__main__":
    main()
