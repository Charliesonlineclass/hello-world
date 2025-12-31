"""
SCORPION Baby Council
=====================

Routes tasks to the appropriate AI baby based on task type and complexity.
Enables multi-baby collaboration and consensus building.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import requests

from .prompts import SYSTEM_PROMPTS, get_prompt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCORPION-COUNCIL")


# =============================================================================
# CONFIGURATION
# =============================================================================

class TaskType(Enum):
    """Types of tasks for routing."""
    ANALYSIS = "analysis"
    STRATEGY = "strategy"
    CODE = "code"
    TECHNICAL = "technical"
    QUICK = "quick"
    CREATIVE = "creative"
    RESEARCH = "research"
    GENERAL = "general"


# Baby specialties for task routing
BABY_SPECIALTIES: Dict[str, List[TaskType]] = {
    "MARCUS": [TaskType.ANALYSIS, TaskType.STRATEGY, TaskType.GENERAL],
    "VULCAN": [TaskType.CODE, TaskType.TECHNICAL],
    "HERMES": [TaskType.QUICK],
    "APOLLO": [TaskType.CREATIVE],
    "ATHENA": [TaskType.RESEARCH, TaskType.ANALYSIS],
}

# Baby models
BABY_MODELS: Dict[str, str] = {
    "MARCUS": "mistral",
    "VULCAN": "codellama",
    "HERMES": "phi",
    "APOLLO": "llama2",
    "ATHENA": "mistral",
}

# Keywords for task type detection
TASK_KEYWORDS: Dict[TaskType, List[str]] = {
    TaskType.ANALYSIS: ["analyze", "examine", "evaluate", "assess", "review", "breakdown"],
    TaskType.STRATEGY: ["strategy", "plan", "approach", "recommend", "advise", "suggest"],
    TaskType.CODE: ["code", "function", "program", "debug", "implement", "script", "python", "javascript"],
    TaskType.TECHNICAL: ["technical", "system", "architecture", "configure", "setup", "install"],
    TaskType.QUICK: ["quick", "fast", "simple", "yes or no", "one word", "briefly"],
    TaskType.CREATIVE: ["write", "story", "creative", "poem", "slogan", "content", "blog", "article"],
    TaskType.RESEARCH: ["research", "explain", "what is", "how does", "define", "history", "facts"],
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TaskRequest:
    """Incoming task request."""
    prompt: str
    task_type: Optional[TaskType] = None
    preferred_baby: Optional[str] = None
    context: Optional[str] = None
    require_consensus: bool = False


@dataclass
class TaskResponse:
    """Response from a baby."""
    baby: str
    response: str
    response_time_ms: float
    task_type: TaskType
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConsensusResult:
    """Result of multi-baby consensus."""
    question: str
    votes: Dict[str, str]
    consensus: Optional[str]
    agreement_rate: float
    responses: Dict[str, str]


# =============================================================================
# BABY COUNCIL CLASS
# =============================================================================

class BabyCouncil:
    """
    Routes tasks to the most appropriate AI baby.

    Features:
    - Automatic task type detection
    - Baby specialty matching
    - Multi-baby collaboration
    - Consensus building
    - Task escalation between babies
    """

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.specialties = BABY_SPECIALTIES.copy()
        self.models = BABY_MODELS.copy()

        logger.info("BabyCouncil initialized")

    # -------------------------------------------------------------------------
    # Task Type Detection
    # -------------------------------------------------------------------------

    def detect_task_type(self, prompt: str) -> TaskType:
        """Detect the task type from the prompt."""
        prompt_lower = prompt.lower()

        # Score each task type
        scores: Dict[TaskType, int] = {t: 0 for t in TaskType}

        for task_type, keywords in TASK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    scores[task_type] += 1

        # Get highest scoring type
        max_score = max(scores.values())
        if max_score > 0:
            for task_type, score in scores.items():
                if score == max_score:
                    return task_type

        return TaskType.GENERAL

    def select_baby(self, task_type: TaskType) -> str:
        """Select the best baby for a task type."""
        for baby, specialties in self.specialties.items():
            if task_type in specialties:
                return baby

        # Default to MARCUS
        return "MARCUS"

    # -------------------------------------------------------------------------
    # Task Routing
    # -------------------------------------------------------------------------

    def route_task(self, prompt: str, task_type: Optional[TaskType] = None) -> Tuple[str, TaskType]:
        """
        Route a task to the appropriate baby.

        Returns:
            Tuple of (baby_name, task_type)
        """
        if task_type is None:
            task_type = self.detect_task_type(prompt)

        baby = self.select_baby(task_type)

        logger.info(f"Routing task to {baby} (type: {task_type.value})")
        return baby, task_type

    # -------------------------------------------------------------------------
    # Baby Communication
    # -------------------------------------------------------------------------

    def _ask_baby(self, baby: str, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Send a prompt to a specific baby."""
        import time

        model = self.models.get(baby, "mistral")

        if system_prompt is None:
            system_prompt = SYSTEM_PROMPTS.get(baby, "")

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        try:
            start_time = time.time()

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=120
            )

            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "elapsed_ms": elapsed_ms,
                    "baby": baby
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "elapsed_ms": elapsed_ms,
                    "baby": baby
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_ms": 0,
                "baby": baby
            }

    # -------------------------------------------------------------------------
    # Main Task Execution
    # -------------------------------------------------------------------------

    def ask(self, request: TaskRequest) -> TaskResponse:
        """
        Process a task request and get a response.
        """
        # Determine baby and task type
        if request.preferred_baby:
            baby = request.preferred_baby
            task_type = request.task_type or self.detect_task_type(request.prompt)
        else:
            baby, task_type = self.route_task(request.prompt, request.task_type)

        # Build prompt with context
        prompt = request.prompt
        if request.context:
            prompt = f"Context: {request.context}\n\nTask: {prompt}"

        # Ask the baby
        result = self._ask_baby(baby, prompt)

        if result["success"]:
            return TaskResponse(
                baby=baby,
                response=result["response"],
                response_time_ms=result["elapsed_ms"],
                task_type=task_type
            )
        else:
            # Try fallback to MARCUS
            if baby != "MARCUS":
                logger.warning(f"{baby} failed, falling back to MARCUS")
                result = self._ask_baby("MARCUS", prompt)

                if result["success"]:
                    return TaskResponse(
                        baby="MARCUS",
                        response=result["response"],
                        response_time_ms=result["elapsed_ms"],
                        task_type=task_type
                    )

            return TaskResponse(
                baby=baby,
                response=f"Error: {result.get('error', 'Unknown error')}",
                response_time_ms=result.get("elapsed_ms", 0),
                task_type=task_type
            )

    # -------------------------------------------------------------------------
    # Multi-Baby Collaboration
    # -------------------------------------------------------------------------

    def ask_council(self, prompt: str, babies: Optional[List[str]] = None) -> Dict[str, TaskResponse]:
        """
        Ask multiple babies the same question for collaborative input.
        """
        if babies is None:
            babies = list(self.models.keys())

        responses = {}

        for baby in babies:
            result = self._ask_baby(baby, prompt)

            responses[baby] = TaskResponse(
                baby=baby,
                response=result.get("response", result.get("error", "")),
                response_time_ms=result.get("elapsed_ms", 0),
                task_type=TaskType.GENERAL
            )

        return responses

    def get_consensus(self, question: str, babies: Optional[List[str]] = None) -> ConsensusResult:
        """
        Get consensus from multiple babies on a question.
        Useful for decisions or verification.
        """
        if babies is None:
            babies = ["MARCUS", "ATHENA", "HERMES"]

        # Ask for concise answers
        prompt = f"""Answer this question with a single word or short phrase.
Question: {question}

Give only the answer, no explanation."""

        votes: Dict[str, str] = {}
        full_responses: Dict[str, str] = {}

        for baby in babies:
            result = self._ask_baby(baby, prompt)

            if result["success"]:
                answer = result["response"].strip().split("\n")[0].strip()
                votes[baby] = answer.lower()
                full_responses[baby] = result["response"]

        # Find consensus
        if not votes:
            return ConsensusResult(
                question=question,
                votes={},
                consensus=None,
                agreement_rate=0.0,
                responses={}
            )

        # Count votes
        vote_counts: Dict[str, int] = {}
        for vote in votes.values():
            vote_counts[vote] = vote_counts.get(vote, 0) + 1

        # Get most common vote
        max_votes = max(vote_counts.values())
        consensus = None
        for vote, count in vote_counts.items():
            if count == max_votes:
                consensus = vote
                break

        agreement_rate = max_votes / len(votes)

        return ConsensusResult(
            question=question,
            votes=votes,
            consensus=consensus if agreement_rate > 0.5 else None,
            agreement_rate=agreement_rate,
            responses=full_responses
        )

    # -------------------------------------------------------------------------
    # Task Escalation
    # -------------------------------------------------------------------------

    def escalate(self, from_baby: str, to_baby: str, context: str, new_task: str) -> TaskResponse:
        """
        Escalate a task from one baby to another with context.
        """
        escalation_prompt = f"""You are receiving a task escalated from {from_baby}.

Previous context:
{context}

New task:
{new_task}

Please continue from where {from_baby} left off."""

        result = self._ask_baby(to_baby, escalation_prompt)

        return TaskResponse(
            baby=to_baby,
            response=result.get("response", result.get("error", "")),
            response_time_ms=result.get("elapsed_ms", 0),
            task_type=TaskType.GENERAL
        )

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def get_baby_info(self, baby: str) -> Dict[str, Any]:
        """Get information about a baby."""
        if baby not in self.models:
            return {"error": f"Unknown baby: {baby}"}

        return {
            "name": baby,
            "model": self.models[baby],
            "specialties": [s.value for s in self.specialties.get(baby, [])],
            "system_prompt": SYSTEM_PROMPTS.get(baby, "")[:200] + "..."
        }

    def list_babies(self) -> List[Dict[str, Any]]:
        """List all available babies."""
        return [self.get_baby_info(baby) for baby in self.models.keys()]


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run council from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="SCORPION Baby Council")
    parser.add_argument("prompt", nargs="?", help="Prompt to send")
    parser.add_argument("--baby", help="Specific baby to use")
    parser.add_argument("--council", action="store_true", help="Ask all babies")
    parser.add_argument("--consensus", action="store_true", help="Get consensus")
    parser.add_argument("--list", action="store_true", help="List babies")

    args = parser.parse_args()

    council = BabyCouncil()

    if args.list:
        for baby in council.list_babies():
            print(f"{baby['name']} ({baby['model']}): {', '.join(baby['specialties'])}")
        return

    if not args.prompt:
        print("Please provide a prompt")
        return

    if args.council:
        responses = council.ask_council(args.prompt)
        for baby, response in responses.items():
            print(f"\n{baby}:")
            print(response.response[:500])
    elif args.consensus:
        result = council.get_consensus(args.prompt)
        print(f"Consensus: {result.consensus} ({result.agreement_rate*100:.0f}% agreement)")
        for baby, vote in result.votes.items():
            print(f"  {baby}: {vote}")
    else:
        request = TaskRequest(
            prompt=args.prompt,
            preferred_baby=args.baby
        )
        response = council.ask(request)
        print(f"\n{response.baby} ({response.task_type.value}):")
        print(response.response)


if __name__ == "__main__":
    main()
