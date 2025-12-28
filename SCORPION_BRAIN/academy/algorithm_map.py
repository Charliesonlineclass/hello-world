"""
SCORPION_BRAIN Algorithm Map
============================
Maps 13 algorithms to baby specialties.

Algorithm Categories:
- Reasoning (MARCUS): chain_of_thought, tree_of_thoughts, bayesian_reasoning
- Building (VULCAN): cosine_similarity, graph_bfs, graph_dfs, pattern_match
- Communication (HERMES): tf_idf, sentiment_analysis, template_fill
- Universal (ALL): embeddings, chromadb_search, tool_call
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AlgorithmCategory(Enum):
    """Categories of algorithms."""
    REASONING = "reasoning"      # MARCUS specialty
    BUILDING = "building"        # VULCAN specialty
    COMMUNICATION = "communication"  # HERMES specialty
    UNIVERSAL = "universal"      # All babies can use


@dataclass
class AlgorithmSpec:
    """Specification for an algorithm."""
    name: str
    category: AlgorithmCategory
    description: str
    primary_baby: str  # Main baby that uses this
    secondary_babies: List[str]  # Other babies that can use it
    input_type: str
    output_type: str
    complexity: str  # "low", "medium", "high"


# The 13 core algorithms mapped to babies
ALGORITHM_SPECS: Dict[str, AlgorithmSpec] = {
    # MARCUS - Reasoning algorithms
    "chain_of_thought": AlgorithmSpec(
        name="chain_of_thought",
        category=AlgorithmCategory.REASONING,
        description="Step-by-step reasoning through a problem",
        primary_baby="MARCUS",
        secondary_babies=["ATHENA"],
        input_type="problem_statement",
        output_type="reasoned_solution",
        complexity="medium"
    ),
    "tree_of_thoughts": AlgorithmSpec(
        name="tree_of_thoughts",
        category=AlgorithmCategory.REASONING,
        description="Explore multiple reasoning paths and select best",
        primary_baby="MARCUS",
        secondary_babies=["ATHENA", "PHOENIX"],
        input_type="problem_statement",
        output_type="explored_solutions",
        complexity="high"
    ),
    "bayesian_reasoning": AlgorithmSpec(
        name="bayesian_reasoning",
        category=AlgorithmCategory.REASONING,
        description="Update beliefs based on evidence",
        primary_baby="MARCUS",
        secondary_babies=["ATHENA"],
        input_type="hypothesis_and_evidence",
        output_type="probability_assessment",
        complexity="high"
    ),

    # VULCAN - Building algorithms
    "cosine_similarity": AlgorithmSpec(
        name="cosine_similarity",
        category=AlgorithmCategory.BUILDING,
        description="Measure similarity between vectors",
        primary_baby="VULCAN",
        secondary_babies=["MARCUS"],
        input_type="vector_pair",
        output_type="similarity_score",
        complexity="low"
    ),
    "graph_bfs": AlgorithmSpec(
        name="graph_bfs",
        category=AlgorithmCategory.BUILDING,
        description="Breadth-first search through a graph",
        primary_baby="VULCAN",
        secondary_babies=["ATHENA"],
        input_type="graph_and_start",
        output_type="traversal_path",
        complexity="medium"
    ),
    "graph_dfs": AlgorithmSpec(
        name="graph_dfs",
        category=AlgorithmCategory.BUILDING,
        description="Depth-first search through a graph",
        primary_baby="VULCAN",
        secondary_babies=["ATHENA"],
        input_type="graph_and_start",
        output_type="traversal_path",
        complexity="medium"
    ),
    "pattern_match": AlgorithmSpec(
        name="pattern_match",
        category=AlgorithmCategory.BUILDING,
        description="Match patterns in structured data",
        primary_baby="VULCAN",
        secondary_babies=["HERMES"],
        input_type="pattern_and_data",
        output_type="matches",
        complexity="medium"
    ),

    # HERMES - Communication algorithms
    "tf_idf": AlgorithmSpec(
        name="tf_idf",
        category=AlgorithmCategory.COMMUNICATION,
        description="Extract important terms from text",
        primary_baby="HERMES",
        secondary_babies=["MARCUS"],
        input_type="text_corpus",
        output_type="weighted_terms",
        complexity="medium"
    ),
    "sentiment_analysis": AlgorithmSpec(
        name="sentiment_analysis",
        category=AlgorithmCategory.COMMUNICATION,
        description="Analyze emotional content of text",
        primary_baby="HERMES",
        secondary_babies=["PHOENIX"],
        input_type="text",
        output_type="sentiment_scores",
        complexity="medium"
    ),
    "template_fill": AlgorithmSpec(
        name="template_fill",
        category=AlgorithmCategory.COMMUNICATION,
        description="Fill templates with dynamic content",
        primary_baby="HERMES",
        secondary_babies=["VULCAN"],
        input_type="template_and_values",
        output_type="filled_text",
        complexity="low"
    ),

    # UNIVERSAL - All babies can use
    "embeddings": AlgorithmSpec(
        name="embeddings",
        category=AlgorithmCategory.UNIVERSAL,
        description="Generate vector embeddings for text",
        primary_baby="ALL",
        secondary_babies=["MARCUS", "VULCAN", "HERMES", "ATHENA", "PHOENIX"],
        input_type="text",
        output_type="vector",
        complexity="low"
    ),
    "chromadb_search": AlgorithmSpec(
        name="chromadb_search",
        category=AlgorithmCategory.UNIVERSAL,
        description="Search vector database for similar content",
        primary_baby="ALL",
        secondary_babies=["MARCUS", "VULCAN", "HERMES", "ATHENA", "PHOENIX"],
        input_type="query_vector",
        output_type="search_results",
        complexity="low"
    ),
    "tool_call": AlgorithmSpec(
        name="tool_call",
        category=AlgorithmCategory.UNIVERSAL,
        description="Execute external tools and functions",
        primary_baby="ALL",
        secondary_babies=["MARCUS", "VULCAN", "HERMES", "ATHENA", "PHOENIX"],
        input_type="tool_spec",
        output_type="tool_result",
        complexity="variable"
    ),
}


# Baby specialties mapping - which algorithms each baby excels at
BABY_SPECIALTIES: Dict[str, Dict[str, Any]] = {
    "MARCUS": {
        "primary_algorithms": ["chain_of_thought", "tree_of_thoughts", "bayesian_reasoning"],
        "secondary_algorithms": ["cosine_similarity", "tf_idf"],
        "universal_algorithms": ["embeddings", "chromadb_search", "tool_call"],
        "personality_traits": ["analytical", "methodical", "thorough"],
        "preferred_tasks": ["reasoning", "analysis", "logic puzzles", "decision making"],
        "learning_style": "deductive"
    },
    "VULCAN": {
        "primary_algorithms": ["cosine_similarity", "graph_bfs", "graph_dfs", "pattern_match"],
        "secondary_algorithms": ["template_fill"],
        "universal_algorithms": ["embeddings", "chromadb_search", "tool_call"],
        "personality_traits": ["practical", "precise", "structured"],
        "preferred_tasks": ["building", "coding", "pattern recognition", "data structures"],
        "learning_style": "hands-on"
    },
    "HERMES": {
        "primary_algorithms": ["tf_idf", "sentiment_analysis", "template_fill"],
        "secondary_algorithms": ["pattern_match"],
        "universal_algorithms": ["embeddings", "chromadb_search", "tool_call"],
        "personality_traits": ["expressive", "empathetic", "articulate"],
        "preferred_tasks": ["communication", "summarization", "translation", "explanation"],
        "learning_style": "social"
    },
    "ATHENA": {
        "primary_algorithms": ["chain_of_thought", "tree_of_thoughts"],
        "secondary_algorithms": ["graph_bfs", "graph_dfs", "bayesian_reasoning"],
        "universal_algorithms": ["embeddings", "chromadb_search", "tool_call"],
        "personality_traits": ["strategic", "farsighted", "tactical"],
        "preferred_tasks": ["planning", "optimization", "strategy", "resource allocation"],
        "learning_style": "strategic"
    },
    "PHOENIX": {
        "primary_algorithms": ["tree_of_thoughts", "sentiment_analysis"],
        "secondary_algorithms": ["chain_of_thought"],
        "universal_algorithms": ["embeddings", "chromadb_search", "tool_call"],
        "personality_traits": ["curious", "adaptive", "creative"],
        "preferred_tasks": ["learning", "exploration", "creativity", "adaptation"],
        "learning_style": "experiential"
    }
}


class AlgorithmMap:
    """
    Maps algorithms to babies and provides lookup functionality.

    Usage:
        algo_map = AlgorithmMap()
        algorithms = algo_map.get_algorithms_for_baby("MARCUS")
        baby = algo_map.find_best_baby_for_algorithm("chain_of_thought")
    """

    def __init__(self):
        self.specs = ALGORITHM_SPECS
        self.specialties = BABY_SPECIALTIES
        self._algorithm_implementations: Dict[str, Callable] = {}

    def register_implementation(self, algorithm_name: str, func: Callable):
        """Register an actual implementation for an algorithm."""
        if algorithm_name not in self.specs:
            raise ValueError(f"Unknown algorithm: {algorithm_name}")
        self._algorithm_implementations[algorithm_name] = func

    def get_implementation(self, algorithm_name: str) -> Optional[Callable]:
        """Get the implementation for an algorithm."""
        return self._algorithm_implementations.get(algorithm_name)

    def get_algorithms_for_baby(self, baby_name: str) -> Dict[str, List[str]]:
        """Get all algorithms available to a baby."""
        baby_name = baby_name.upper()
        if baby_name not in self.specialties:
            return {}

        specialty = self.specialties[baby_name]
        return {
            "primary": specialty.get("primary_algorithms", []),
            "secondary": specialty.get("secondary_algorithms", []),
            "universal": specialty.get("universal_algorithms", [])
        }

    def get_all_baby_algorithms(self, baby_name: str) -> List[str]:
        """Get flat list of all algorithms for a baby."""
        algos = self.get_algorithms_for_baby(baby_name)
        return (
            algos.get("primary", []) +
            algos.get("secondary", []) +
            algos.get("universal", [])
        )

    def find_best_baby_for_algorithm(self, algorithm_name: str) -> Optional[str]:
        """Find the baby that's best at a specific algorithm."""
        if algorithm_name not in self.specs:
            return None

        spec = self.specs[algorithm_name]
        if spec.primary_baby == "ALL":
            # Universal algorithm - return first baby
            return "MARCUS"
        return spec.primary_baby

    def find_babies_for_algorithm(self, algorithm_name: str) -> List[str]:
        """Find all babies that can use an algorithm."""
        if algorithm_name not in self.specs:
            return []

        spec = self.specs[algorithm_name]
        if spec.primary_baby == "ALL":
            return list(self.specialties.keys())

        babies = [spec.primary_baby] + spec.secondary_babies
        return list(set(babies))

    def get_algorithm_spec(self, algorithm_name: str) -> Optional[AlgorithmSpec]:
        """Get the specification for an algorithm."""
        return self.specs.get(algorithm_name)

    def get_algorithms_by_category(self, category: AlgorithmCategory) -> List[str]:
        """Get all algorithms in a category."""
        return [
            name for name, spec in self.specs.items()
            if spec.category == category
        ]

    def get_baby_traits(self, baby_name: str) -> Dict[str, Any]:
        """Get personality and learning info for a baby."""
        baby_name = baby_name.upper()
        if baby_name not in self.specialties:
            return {}

        specialty = self.specialties[baby_name]
        return {
            "personality_traits": specialty.get("personality_traits", []),
            "preferred_tasks": specialty.get("preferred_tasks", []),
            "learning_style": specialty.get("learning_style", "")
        }

    def suggest_collaboration(self, task: str) -> List[str]:
        """Suggest which babies should collaborate on a task."""
        task_lower = task.lower()
        suggested = set()

        # Check each baby's preferred tasks
        for baby_name, specialty in self.specialties.items():
            for task_type in specialty.get("preferred_tasks", []):
                if task_type in task_lower:
                    suggested.add(baby_name)

        # Always suggest at least 2 babies for collaboration
        if len(suggested) < 2:
            suggested.add("MARCUS")  # Always good for reasoning
            suggested.add("HERMES")  # Always good for communication

        return list(suggested)

    def get_pipeline_suggestion(self, task: str) -> List[Dict]:
        """Suggest a pipeline of babies for a complex task."""
        task_lower = task.lower()
        stages = []

        # Analyze task requirements
        needs_reasoning = any(w in task_lower for w in ["think", "analyze", "reason", "why"])
        needs_building = any(w in task_lower for w in ["build", "code", "create", "pattern"])
        needs_communication = any(w in task_lower for w in ["explain", "summarize", "tell", "describe"])
        needs_planning = any(w in task_lower for w in ["plan", "strategy", "optimize", "decide"])

        # Build pipeline based on needs
        if needs_reasoning or needs_planning:
            stages.append({"name": "analysis", "baby": "MARCUS", "algorithm": "chain_of_thought"})

        if needs_planning:
            stages.append({"name": "strategy", "baby": "ATHENA", "algorithm": "tree_of_thoughts"})

        if needs_building:
            stages.append({"name": "construction", "baby": "VULCAN", "algorithm": "pattern_match"})

        if needs_communication:
            stages.append({"name": "presentation", "baby": "HERMES", "algorithm": "template_fill"})

        # Default pipeline if nothing matched
        if not stages:
            stages = [
                {"name": "understand", "baby": "MARCUS", "algorithm": "chain_of_thought"},
                {"name": "respond", "baby": "HERMES", "algorithm": "template_fill"}
            ]

        return stages

    def create_algorithm_registry(self) -> Dict[str, Dict[str, Callable]]:
        """
        Create a registry mapping babies to their algorithm implementations.
        Returns format suitable for UnifiedClassroom.register_algorithms()
        """
        registry = {}

        for baby_name in self.specialties:
            baby_algos = {}
            all_algos = self.get_all_baby_algorithms(baby_name)

            for algo_name in all_algos:
                impl = self.get_implementation(algo_name)
                if impl:
                    baby_algos[algo_name] = impl

            registry[baby_name] = baby_algos

        return registry

    def summary(self) -> str:
        """Generate a summary of the algorithm map."""
        lines = ["SCORPION_BRAIN Algorithm Map", "=" * 40]

        for category in AlgorithmCategory:
            algos = self.get_algorithms_by_category(category)
            lines.append(f"\n{category.value.upper()}:")
            for algo in algos:
                spec = self.specs[algo]
                lines.append(f"  - {algo}: {spec.description} (primary: {spec.primary_baby})")

        lines.append("\n" + "=" * 40)
        lines.append("BABY SPECIALTIES:")

        for baby, specialty in self.specialties.items():
            lines.append(f"\n{baby}:")
            lines.append(f"  Primary: {', '.join(specialty['primary_algorithms'])}")
            lines.append(f"  Traits: {', '.join(specialty['personality_traits'])}")

        return "\n".join(lines)


# Singleton instance for easy access
_default_map: Optional[AlgorithmMap] = None


def get_algorithm_map() -> AlgorithmMap:
    """Get the default algorithm map instance."""
    global _default_map
    if _default_map is None:
        _default_map = AlgorithmMap()
    return _default_map


if __name__ == "__main__":
    # Demo
    algo_map = get_algorithm_map()
    print(algo_map.summary())

    print("\n\nSuggested collaboration for 'analyze this code and explain it':")
    print(algo_map.suggest_collaboration("analyze this code and explain it"))

    print("\n\nSuggested pipeline for 'build a plan and explain strategy':")
    for stage in algo_map.get_pipeline_suggestion("build a plan and explain strategy"):
        print(f"  {stage['name']}: {stage['baby']} using {stage['algorithm']}")
