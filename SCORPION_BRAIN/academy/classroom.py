"""
SCORPION_BRAIN Unified Classroom
================================
The central hub where 5 AI babies learn, collaborate, and grow.

Architecture:
- Each baby has specialties and learns from interactions
- Pipelines route tasks to appropriate babies
- Collaboration sessions enable multi-baby problem solving
- Service records track each baby's growth and capabilities
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BabyPersonality(Enum):
    """Core personality traits for each baby."""
    MARCUS = "logical_analytical"      # Deep thinker, methodical
    VULCAN = "builder_craftsman"       # Practical, pattern-focused
    HERMES = "communicator_diplomat"   # Expressive, context-aware
    ATHENA = "strategist_planner"      # Big picture, tactical
    PHOENIX = "learner_adapter"        # Curious, evolving


@dataclass
class Memory:
    """A single memory unit stored by a baby."""
    content: str
    memory_type: str  # "experience", "learned", "emotional", "factual"
    importance: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    associations: List[str] = field(default_factory=list)
    access_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "timestamp": self.timestamp.isoformat(),
            "associations": self.associations,
            "access_count": self.access_count
        }


@dataclass
class ServiceRecord:
    """Track a baby's growth, skills, and history."""
    baby_name: str
    creation_date: datetime = field(default_factory=datetime.now)
    tasks_completed: int = 0
    tasks_failed: int = 0
    collaborations: int = 0
    skills: Dict[str, float] = field(default_factory=dict)  # skill -> proficiency 0-1
    milestones: List[Dict] = field(default_factory=list)
    current_mood: str = "curious"
    energy_level: float = 1.0

    def record_task(self, success: bool, skill: str):
        """Record task completion and update skills."""
        if success:
            self.tasks_completed += 1
            # Increase skill proficiency
            current = self.skills.get(skill, 0.0)
            self.skills[skill] = min(1.0, current + 0.01)
        else:
            self.tasks_failed += 1

    def add_milestone(self, description: str):
        """Record a significant achievement."""
        self.milestones.append({
            "description": description,
            "date": datetime.now().isoformat(),
            "tasks_at_milestone": self.tasks_completed
        })

    def to_dict(self) -> Dict:
        return {
            "baby_name": self.baby_name,
            "creation_date": self.creation_date.isoformat(),
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "collaborations": self.collaborations,
            "skills": self.skills,
            "milestones": self.milestones,
            "current_mood": self.current_mood,
            "energy_level": self.energy_level
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ServiceRecord':
        record = cls(baby_name=data["baby_name"])
        record.creation_date = datetime.fromisoformat(data.get("creation_date", datetime.now().isoformat()))
        record.tasks_completed = data.get("tasks_completed", 0)
        record.tasks_failed = data.get("tasks_failed", 0)
        record.collaborations = data.get("collaborations", 0)
        record.skills = data.get("skills", {})
        record.milestones = data.get("milestones", [])
        record.current_mood = data.get("current_mood", "curious")
        record.energy_level = data.get("energy_level", 1.0)
        return record


class Baby:
    """
    An AI baby in the SCORPION_BRAIN academy.

    Each baby has:
    - Unique personality and specialties
    - Memory system for learning
    - Service record tracking growth
    - Connection to algorithms for processing
    """

    def __init__(
        self,
        name: str,
        personality: BabyPersonality,
        specialties: List[str],
        ollama_model: Optional[str] = None
    ):
        self.name = name
        self.personality = personality
        self.specialties = specialties
        self.ollama_model = ollama_model or "llama3.2"

        self.memories: List[Memory] = []
        self.service_record = ServiceRecord(baby_name=name)
        self.algorithms: Dict[str, Callable] = {}
        self.is_busy = False
        self.current_task: Optional[str] = None

        # Initialize default skills based on specialties
        for specialty in specialties:
            self.service_record.skills[specialty] = 0.1

        logger.info(f"🐣 Baby {name} initialized with personality: {personality.value}")

    def add_algorithm(self, name: str, func: Callable):
        """Register an algorithm this baby can use."""
        self.algorithms[name] = func
        logger.debug(f"{self.name} learned algorithm: {name}")

    def remember(self, content: str, memory_type: str = "experience", importance: float = 0.5):
        """Store a new memory."""
        memory = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance
        )
        self.memories.append(memory)

        # Prune low-importance old memories if we have too many
        if len(self.memories) > 1000:
            self.memories.sort(key=lambda m: m.importance, reverse=True)
            self.memories = self.memories[:800]

    def recall(self, query: str, limit: int = 5) -> List[Memory]:
        """Retrieve relevant memories based on query."""
        # Simple keyword matching - could be enhanced with embeddings
        relevant = []
        query_words = set(query.lower().split())

        for memory in self.memories:
            memory_words = set(memory.content.lower().split())
            overlap = len(query_words & memory_words)
            if overlap > 0:
                memory.access_count += 1
                relevant.append((overlap, memory))

        relevant.sort(key=lambda x: (x[0], x[1].importance), reverse=True)
        return [m for _, m in relevant[:limit]]

    async def process_task(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """Process a task using available algorithms."""
        self.is_busy = True
        self.current_task = task
        context = context or {}

        result = {
            "baby": self.name,
            "task": task,
            "status": "pending",
            "output": None,
            "algorithms_used": [],
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Recall relevant memories
            memories = self.recall(task)
            context["memories"] = [m.to_dict() for m in memories]

            # Select appropriate algorithm based on task
            algorithm_name = self._select_algorithm(task)
            if algorithm_name and algorithm_name in self.algorithms:
                output = await self._run_algorithm(algorithm_name, task, context)
                result["output"] = output
                result["algorithms_used"].append(algorithm_name)
                result["status"] = "completed"

                # Learn from the experience
                self.remember(f"Completed task: {task[:100]}", "experience", 0.6)
                self.service_record.record_task(True, algorithm_name)
            else:
                result["status"] = "no_algorithm"
                result["output"] = f"No suitable algorithm found for task"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self.service_record.record_task(False, "unknown")
            logger.error(f"{self.name} failed task: {e}")

        finally:
            self.is_busy = False
            self.current_task = None

        return result

    def _select_algorithm(self, task: str) -> Optional[str]:
        """Select the best algorithm for a task based on keywords."""
        task_lower = task.lower()

        algorithm_keywords = {
            "chain_of_thought": ["think", "reason", "analyze", "step by step"],
            "tree_of_thoughts": ["explore", "options", "alternatives", "branches"],
            "bayesian_reasoning": ["probability", "likely", "chance", "uncertain"],
            "cosine_similarity": ["similar", "match", "compare", "find like"],
            "graph_search": ["path", "connect", "network", "traverse"],
            "pattern_match": ["pattern", "template", "structure", "format"],
            "tf_idf": ["keywords", "important words", "extract terms"],
            "sentiment": ["feeling", "emotion", "positive", "negative"],
            "template_fill": ["fill", "template", "format", "generate text"],
            "embeddings": ["embed", "vector", "semantic", "meaning"],
            "chromadb_search": ["search", "find", "retrieve", "lookup"],
            "tool_call": ["execute", "run", "call", "invoke"]
        }

        best_match = None
        best_score = 0

        for algo, keywords in algorithm_keywords.items():
            if algo in self.algorithms:
                score = sum(1 for kw in keywords if kw in task_lower)
                if score > best_score:
                    best_score = score
                    best_match = algo

        # Default to first available algorithm if no match
        if not best_match and self.algorithms:
            best_match = list(self.algorithms.keys())[0]

        return best_match

    async def _run_algorithm(self, name: str, task: str, context: Dict) -> Any:
        """Execute an algorithm, handling both sync and async functions."""
        func = self.algorithms[name]
        if asyncio.iscoroutinefunction(func):
            return await func(task, context)
        else:
            return func(task, context)

    def save_service_record(self, path: Path):
        """Save service record to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.service_record.to_dict(), f, indent=2)

    def load_service_record(self, path: Path):
        """Load service record from JSON file."""
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                self.service_record = ServiceRecord.from_dict(data)

    def get_status(self) -> Dict:
        """Get current status of this baby."""
        return {
            "name": self.name,
            "personality": self.personality.value,
            "is_busy": self.is_busy,
            "current_task": self.current_task,
            "algorithms": list(self.algorithms.keys()),
            "memory_count": len(self.memories),
            "tasks_completed": self.service_record.tasks_completed,
            "mood": self.service_record.current_mood,
            "energy": self.service_record.energy_level
        }


@dataclass
class PipelineStage:
    """A single stage in a processing pipeline."""
    name: str
    baby_name: str
    algorithm: Optional[str] = None
    transform: Optional[Callable] = None
    required: bool = True


class Pipeline:
    """
    A processing pipeline that routes tasks through multiple babies.

    Pipelines enable:
    - Sequential processing (baby A -> baby B -> baby C)
    - Parallel processing (multiple babies at once)
    - Conditional routing based on task content
    """

    def __init__(self, name: str, stages: List[PipelineStage] = None):
        self.name = name
        self.stages = stages or []
        self.execution_history: List[Dict] = []

    def add_stage(self, stage: PipelineStage):
        """Add a stage to the pipeline."""
        self.stages.append(stage)

    async def execute(self, classroom: 'UnifiedClassroom', task: str, context: Dict = None) -> Dict:
        """Execute the pipeline with a task."""
        context = context or {}
        results = []
        current_output = task

        execution_record = {
            "pipeline": self.name,
            "task": task,
            "started": datetime.now().isoformat(),
            "stages": []
        }

        for stage in self.stages:
            baby = classroom.get_baby(stage.baby_name)
            if not baby:
                if stage.required:
                    raise ValueError(f"Required baby '{stage.baby_name}' not found")
                continue

            # Process through this baby
            stage_context = {**context, "pipeline_input": current_output}
            result = await baby.process_task(str(current_output), stage_context)

            # Apply transform if provided
            if stage.transform and result["status"] == "completed":
                result["output"] = stage.transform(result["output"])

            results.append(result)
            execution_record["stages"].append({
                "stage": stage.name,
                "baby": stage.baby_name,
                "status": result["status"]
            })

            # Pass output to next stage
            if result["status"] == "completed":
                current_output = result["output"]
            elif stage.required:
                execution_record["status"] = "failed"
                execution_record["failed_stage"] = stage.name
                break

        execution_record["completed"] = datetime.now().isoformat()
        execution_record["status"] = execution_record.get("status", "completed")
        execution_record["final_output"] = current_output

        self.execution_history.append(execution_record)

        return {
            "pipeline": self.name,
            "status": execution_record["status"],
            "stages_completed": len(results),
            "results": results,
            "final_output": current_output
        }


class CollaborationSession:
    """
    A session where multiple babies collaborate on a complex task.

    Collaboration modes:
    - ROUND_ROBIN: Each baby takes turns contributing
    - SPECIALIST: Route to specialist based on subtask
    - CONSENSUS: All babies vote/contribute, merge results
    - DEBATE: Babies argue different perspectives
    """

    def __init__(self, session_id: str, babies: List[Baby], mode: str = "ROUND_ROBIN"):
        self.session_id = session_id
        self.babies = babies
        self.mode = mode
        self.transcript: List[Dict] = []
        self.started = datetime.now()
        self.status = "active"

    async def collaborate(self, task: str, max_rounds: int = 5) -> Dict:
        """Run a collaboration session."""
        context = {
            "session_id": self.session_id,
            "mode": self.mode,
            "participants": [b.name for b in self.babies],
            "round": 0,
            "previous_contributions": []
        }

        contributions = []

        if self.mode == "ROUND_ROBIN":
            contributions = await self._round_robin(task, context, max_rounds)
        elif self.mode == "SPECIALIST":
            contributions = await self._specialist(task, context)
        elif self.mode == "CONSENSUS":
            contributions = await self._consensus(task, context)
        elif self.mode == "DEBATE":
            contributions = await self._debate(task, context, max_rounds)

        # Update collaboration counts
        for baby in self.babies:
            baby.service_record.collaborations += 1

        self.status = "completed"

        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "task": task,
            "contributions": contributions,
            "transcript": self.transcript,
            "duration": (datetime.now() - self.started).total_seconds()
        }

    async def _round_robin(self, task: str, context: Dict, max_rounds: int) -> List[Dict]:
        """Each baby takes turns contributing."""
        contributions = []
        current_input = task

        for round_num in range(max_rounds):
            context["round"] = round_num
            round_contributions = []

            for baby in self.babies:
                result = await baby.process_task(current_input, context)
                contribution = {
                    "round": round_num,
                    "baby": baby.name,
                    "input": current_input[:200],
                    "output": result.get("output"),
                    "status": result["status"]
                }
                round_contributions.append(contribution)
                self.transcript.append(contribution)

                if result["status"] == "completed" and result.get("output"):
                    current_input = str(result["output"])
                    context["previous_contributions"].append({
                        "baby": baby.name,
                        "output": result["output"]
                    })

            contributions.extend(round_contributions)

            # Check if we've reached a stable state
            if self._check_convergence(round_contributions):
                break

        return contributions

    async def _specialist(self, task: str, context: Dict) -> List[Dict]:
        """Route to specialist baby based on task content."""
        contributions = []

        # Find best specialist for this task
        best_baby = self._find_specialist(task)
        result = await best_baby.process_task(task, context)

        contributions.append({
            "baby": best_baby.name,
            "specialist_match": True,
            "output": result.get("output"),
            "status": result["status"]
        })

        return contributions

    async def _consensus(self, task: str, context: Dict) -> List[Dict]:
        """All babies contribute, then merge results."""
        contributions = []

        # Get contributions from all babies in parallel
        tasks = [baby.process_task(task, context) for baby in self.babies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        outputs = []
        for baby, result in zip(self.babies, results):
            if isinstance(result, Exception):
                contribution = {"baby": baby.name, "status": "error", "error": str(result)}
            else:
                contribution = {
                    "baby": baby.name,
                    "output": result.get("output"),
                    "status": result["status"]
                }
                if result["status"] == "completed":
                    outputs.append(result["output"])
            contributions.append(contribution)

        # Merge outputs (simple concatenation - could be more sophisticated)
        merged = self._merge_outputs(outputs)
        contributions.append({
            "type": "merged_consensus",
            "output": merged,
            "contributing_babies": len(outputs)
        })

        return contributions

    async def _debate(self, task: str, context: Dict, max_rounds: int) -> List[Dict]:
        """Babies debate different perspectives."""
        contributions = []
        positions = {}

        # Each baby takes an initial position
        for baby in self.babies:
            context["instruction"] = "Take a clear position on this task"
            result = await baby.process_task(task, context)
            positions[baby.name] = result.get("output", "")
            contributions.append({
                "round": 0,
                "baby": baby.name,
                "type": "initial_position",
                "output": result.get("output")
            })

        # Debate rounds
        for round_num in range(1, max_rounds):
            context["round"] = round_num
            context["other_positions"] = positions

            for baby in self.babies:
                context["instruction"] = f"Respond to other positions: {positions}"
                result = await baby.process_task(task, context)
                positions[baby.name] = result.get("output", "")
                contributions.append({
                    "round": round_num,
                    "baby": baby.name,
                    "type": "response",
                    "output": result.get("output")
                })

        return contributions

    def _find_specialist(self, task: str) -> Baby:
        """Find the baby most specialized for this task."""
        task_lower = task.lower()
        best_baby = self.babies[0]
        best_score = 0

        for baby in self.babies:
            score = sum(1 for s in baby.specialties if s.lower() in task_lower)
            if score > best_score:
                best_score = score
                best_baby = baby

        return best_baby

    def _merge_outputs(self, outputs: List[Any]) -> str:
        """Merge multiple outputs into one."""
        if not outputs:
            return ""
        if len(outputs) == 1:
            return str(outputs[0])
        return "\n---\n".join(str(o) for o in outputs if o)

    def _check_convergence(self, contributions: List[Dict]) -> bool:
        """Check if contributions have converged (similar outputs)."""
        outputs = [c.get("output", "") for c in contributions if c.get("output")]
        if len(outputs) < 2:
            return False
        # Simple check - if all outputs are similar length, might be converging
        lengths = [len(str(o)) for o in outputs]
        avg_len = sum(lengths) / len(lengths)
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        return variance < 100  # Low variance suggests convergence


class UnifiedClassroom:
    """
    The central hub managing all babies, pipelines, and collaboration.

    This is the main interface for the SCORPION_BRAIN academy.
    """

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("./academy_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.babies: Dict[str, Baby] = {}
        self.pipelines: Dict[str, Pipeline] = {}
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.ollama_bridge = None  # Set externally

        self._initialize_default_babies()

    def _initialize_default_babies(self):
        """Create the 5 default babies."""
        baby_configs = [
            {
                "name": "MARCUS",
                "personality": BabyPersonality.MARCUS,
                "specialties": ["reasoning", "logic", "analysis", "chain_of_thought", "bayesian"],
                "model": "llama3.2"
            },
            {
                "name": "VULCAN",
                "personality": BabyPersonality.VULCAN,
                "specialties": ["building", "patterns", "code", "similarity", "graph_search"],
                "model": "codellama"
            },
            {
                "name": "HERMES",
                "personality": BabyPersonality.HERMES,
                "specialties": ["communication", "text", "sentiment", "templates", "summarization"],
                "model": "llama3.2"
            },
            {
                "name": "ATHENA",
                "personality": BabyPersonality.ATHENA,
                "specialties": ["strategy", "planning", "tactics", "optimization", "decision"],
                "model": "llama3.2"
            },
            {
                "name": "PHOENIX",
                "personality": BabyPersonality.PHOENIX,
                "specialties": ["learning", "adaptation", "exploration", "creativity", "evolution"],
                "model": "llama3.2"
            }
        ]

        for config in baby_configs:
            baby = Baby(
                name=config["name"],
                personality=config["personality"],
                specialties=config["specialties"],
                ollama_model=config["model"]
            )
            self.babies[config["name"]] = baby

            # Load existing service record if available
            record_path = self.data_dir / "service_records" / f"{config['name'].lower()}_record.json"
            baby.load_service_record(record_path)

        logger.info(f"🏫 Classroom initialized with {len(self.babies)} babies")

    def get_baby(self, name: str) -> Optional[Baby]:
        """Get a baby by name."""
        return self.babies.get(name.upper())

    def register_algorithms(self, algorithm_map: Dict[str, Dict[str, Callable]]):
        """Register algorithms for each baby from algorithm_map."""
        for baby_name, algorithms in algorithm_map.items():
            baby = self.get_baby(baby_name)
            if baby:
                for algo_name, func in algorithms.items():
                    baby.add_algorithm(algo_name, func)

    def create_pipeline(self, name: str, stages: List[Dict]) -> Pipeline:
        """Create a new pipeline."""
        pipeline_stages = []
        for stage in stages:
            pipeline_stages.append(PipelineStage(
                name=stage["name"],
                baby_name=stage["baby"],
                algorithm=stage.get("algorithm"),
                required=stage.get("required", True)
            ))
        pipeline = Pipeline(name, pipeline_stages)
        self.pipelines[name] = pipeline
        return pipeline

    async def run_pipeline(self, pipeline_name: str, task: str, context: Dict = None) -> Dict:
        """Execute a named pipeline."""
        pipeline = self.pipelines.get(pipeline_name)
        if not pipeline:
            raise ValueError(f"Pipeline '{pipeline_name}' not found")
        return await pipeline.execute(self, task, context)

    def start_collaboration(
        self,
        baby_names: List[str],
        mode: str = "ROUND_ROBIN"
    ) -> CollaborationSession:
        """Start a new collaboration session."""
        session_id = f"collab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        babies = [self.get_baby(name) for name in baby_names]
        babies = [b for b in babies if b is not None]

        if not babies:
            raise ValueError("No valid babies found for collaboration")

        session = CollaborationSession(session_id, babies, mode)
        self.active_sessions[session_id] = session
        return session

    async def quick_task(self, task: str, baby_name: str = None) -> Dict:
        """Quick single-baby task execution."""
        if baby_name:
            baby = self.get_baby(baby_name)
        else:
            # Auto-select based on task
            baby = self._select_baby_for_task(task)

        if not baby:
            return {"status": "error", "error": "No suitable baby found"}

        return await baby.process_task(task)

    def _select_baby_for_task(self, task: str) -> Optional[Baby]:
        """Auto-select the best baby for a task."""
        task_lower = task.lower()
        best_baby = None
        best_score = 0

        for baby in self.babies.values():
            score = sum(1 for s in baby.specialties if s in task_lower)
            if score > best_score:
                best_score = score
                best_baby = baby

        return best_baby or list(self.babies.values())[0]

    def save_all_records(self):
        """Save all baby service records."""
        records_dir = self.data_dir / "service_records"
        records_dir.mkdir(parents=True, exist_ok=True)

        for baby in self.babies.values():
            record_path = records_dir / f"{baby.name.lower()}_record.json"
            baby.save_service_record(record_path)

        logger.info("💾 All service records saved")

    def get_classroom_status(self) -> Dict:
        """Get full classroom status."""
        return {
            "babies": {name: baby.get_status() for name, baby in self.babies.items()},
            "pipelines": list(self.pipelines.keys()),
            "active_sessions": list(self.active_sessions.keys()),
            "total_tasks_completed": sum(b.service_record.tasks_completed for b in self.babies.values()),
            "total_collaborations": sum(b.service_record.collaborations for b in self.babies.values())
        }

    def __repr__(self):
        return f"<UnifiedClassroom babies={list(self.babies.keys())}>"


# Convenience function for quick setup
def create_classroom(data_dir: str = None) -> UnifiedClassroom:
    """Create and return a configured classroom instance."""
    path = Path(data_dir) if data_dir else None
    classroom = UnifiedClassroom(data_dir=path)
    return classroom


if __name__ == "__main__":
    # Demo usage
    import asyncio

    async def demo():
        classroom = create_classroom()
        print(classroom.get_classroom_status())

        # Quick task
        result = await classroom.quick_task("Analyze this code for patterns")
        print(f"Result: {result}")

    asyncio.run(demo())
