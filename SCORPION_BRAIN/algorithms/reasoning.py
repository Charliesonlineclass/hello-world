"""
SCORPION_BRAIN Reasoning Algorithms
====================================
MARCUS specialty algorithms for logic and analysis.

Algorithms:
- chain_of_thought: Step-by-step reasoning
- tree_of_thoughts: Explore multiple reasoning paths
- bayesian_reasoning: Update beliefs based on evidence
"""

import re
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ThoughtType(Enum):
    """Types of thoughts in reasoning chains."""
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"
    DEDUCTION = "deduction"
    INDUCTION = "induction"
    CONCLUSION = "conclusion"
    QUESTION = "question"


@dataclass
class Thought:
    """A single thought in a reasoning chain."""
    content: str
    thought_type: ThoughtType
    confidence: float = 0.5  # 0-1
    supporting_evidence: List[str] = field(default_factory=list)
    depends_on: List[int] = field(default_factory=list)  # Indices of prior thoughts

    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "type": self.thought_type.value,
            "confidence": self.confidence,
            "evidence": self.supporting_evidence,
            "dependencies": self.depends_on
        }


@dataclass
class ThoughtNode:
    """Node in a tree of thoughts."""
    thought: Thought
    children: List['ThoughtNode'] = field(default_factory=list)
    score: float = 0.0
    depth: int = 0
    is_terminal: bool = False

    def add_child(self, child: 'ThoughtNode'):
        child.depth = self.depth + 1
        self.children.append(child)

    def get_path_to_root(self) -> List[Thought]:
        """Get the path from this node to root (in reverse)."""
        return [self.thought]  # Simplified - would need parent refs for full path


def chain_of_thought(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Implement chain-of-thought reasoning.

    Breaks down a problem into sequential reasoning steps,
    building from observations to conclusions.

    Args:
        task: The problem or question to reason about
        context: Optional context with additional information

    Returns:
        Dict with reasoning chain and final conclusion
    """
    context = context or {}
    thoughts: List[Thought] = []

    # Step 1: Initial observation
    observation = Thought(
        content=f"Analyzing the task: {task[:200]}",
        thought_type=ThoughtType.OBSERVATION,
        confidence=1.0
    )
    thoughts.append(observation)

    # Step 2: Extract key elements
    key_elements = _extract_key_elements(task)
    for element in key_elements[:5]:  # Limit to 5 elements
        thoughts.append(Thought(
            content=f"Key element identified: {element}",
            thought_type=ThoughtType.OBSERVATION,
            confidence=0.8,
            depends_on=[0]
        ))

    # Step 3: Generate hypotheses
    hypotheses = _generate_hypotheses(task, key_elements)
    hypothesis_start = len(thoughts)
    for hyp in hypotheses[:3]:  # Top 3 hypotheses
        thoughts.append(Thought(
            content=hyp,
            thought_type=ThoughtType.HYPOTHESIS,
            confidence=0.6,
            depends_on=list(range(1, hypothesis_start))
        ))

    # Step 4: Evaluate and deduce
    best_hypothesis = hypotheses[0] if hypotheses else "No clear hypothesis"
    deduction = Thought(
        content=f"Based on analysis, the most likely approach: {best_hypothesis}",
        thought_type=ThoughtType.DEDUCTION,
        confidence=0.7,
        depends_on=[hypothesis_start] if hypotheses else [0]
    )
    thoughts.append(deduction)

    # Step 5: Form conclusion
    conclusion = Thought(
        content=_form_conclusion(task, thoughts),
        thought_type=ThoughtType.CONCLUSION,
        confidence=0.75
    )
    thoughts.append(conclusion)

    return {
        "algorithm": "chain_of_thought",
        "task": task,
        "chain": [t.to_dict() for t in thoughts],
        "conclusion": conclusion.content,
        "confidence": conclusion.confidence,
        "step_count": len(thoughts)
    }


def tree_of_thoughts(task: str, context: Dict = None, max_branches: int = 3, max_depth: int = 3) -> Dict[str, Any]:
    """
    Implement tree-of-thoughts reasoning.

    Explores multiple reasoning paths simultaneously and
    selects the most promising one.

    Args:
        task: The problem to reason about
        context: Optional context
        max_branches: Maximum branches per node
        max_depth: Maximum tree depth

    Returns:
        Dict with tree structure and best path
    """
    context = context or {}

    # Create root
    root = ThoughtNode(
        thought=Thought(
            content=f"Root: {task[:100]}",
            thought_type=ThoughtType.OBSERVATION,
            confidence=1.0
        ),
        depth=0
    )

    # Build tree using BFS-style expansion
    frontier = [root]
    all_paths: List[Tuple[float, List[ThoughtNode]]] = []

    while frontier:
        current = frontier.pop(0)

        if current.depth >= max_depth:
            # Score terminal node
            score = _score_thought_path([current])
            all_paths.append((score, [current]))
            current.is_terminal = True
            continue

        # Generate branches
        branches = _generate_thought_branches(current.thought.content, max_branches)

        for i, branch_content in enumerate(branches):
            child = ThoughtNode(
                thought=Thought(
                    content=branch_content,
                    thought_type=ThoughtType.HYPOTHESIS if current.depth == 0 else ThoughtType.DEDUCTION,
                    confidence=0.7 - (current.depth * 0.1)  # Confidence decreases with depth
                ),
                depth=current.depth + 1
            )
            current.add_child(child)

            # Prune low-scoring branches early
            child.score = _score_thought(child.thought)
            if child.score > 0.3:  # Only explore promising branches
                frontier.append(child)

    # Find best path
    best_path = max(all_paths, key=lambda x: x[0]) if all_paths else (0.0, [root])

    # Generate conclusion from best path
    conclusion = _synthesize_from_path(best_path[1])

    return {
        "algorithm": "tree_of_thoughts",
        "task": task,
        "tree_depth": max_depth,
        "branches_explored": sum(len(n.children) for n in [root] + [c for c in root.children]),
        "best_path_score": best_path[0],
        "best_path": [n.thought.to_dict() for n in best_path[1]],
        "conclusion": conclusion,
        "alternative_count": len(all_paths)
    }


def bayesian_reasoning(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Implement Bayesian reasoning for belief updates.

    Updates probability estimates based on evidence.

    Args:
        task: The hypothesis or question to evaluate
        context: Should contain 'prior', 'evidence', 'likelihood' if available

    Returns:
        Dict with probability assessments
    """
    context = context or {}

    # Extract or set prior probability
    prior = context.get('prior', 0.5)

    # Extract evidence
    evidence = context.get('evidence', [])
    if isinstance(evidence, str):
        evidence = [evidence]

    # Process each piece of evidence
    current_belief = prior
    evidence_updates = []

    for ev in evidence:
        # Estimate likelihood based on evidence type
        likelihood = _estimate_likelihood(ev, task)
        evidence_strength = _estimate_evidence_strength(ev)

        # Simplified Bayesian update
        # P(H|E) ∝ P(E|H) * P(H)
        # We use a simplified version that adjusts belief based on evidence
        adjustment = (likelihood - 0.5) * evidence_strength
        new_belief = max(0.01, min(0.99, current_belief + adjustment))

        evidence_updates.append({
            "evidence": ev[:100],
            "likelihood": likelihood,
            "strength": evidence_strength,
            "prior_belief": current_belief,
            "posterior_belief": new_belief
        })

        current_belief = new_belief

    # Calculate confidence in our estimate
    confidence = min(0.9, 0.5 + (len(evidence) * 0.1))

    # Generate interpretation
    if current_belief > 0.7:
        interpretation = "High probability - evidence strongly supports this"
    elif current_belief > 0.5:
        interpretation = "Moderately likely - some supporting evidence"
    elif current_belief > 0.3:
        interpretation = "Uncertain - mixed evidence"
    else:
        interpretation = "Low probability - evidence suggests otherwise"

    return {
        "algorithm": "bayesian_reasoning",
        "task": task,
        "prior_probability": prior,
        "posterior_probability": current_belief,
        "evidence_count": len(evidence),
        "evidence_updates": evidence_updates,
        "interpretation": interpretation,
        "confidence": confidence,
        "odds_ratio": current_belief / (1 - current_belief) if current_belief < 0.99 else 99
    }


# Helper functions

def _extract_key_elements(text: str) -> List[str]:
    """Extract key elements from text for analysis."""
    # Simple keyword extraction
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    # Filter common words
    stopwords = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'what', 'when', 'where', 'which', 'their', 'there', 'would', 'could', 'should', 'about'}
    filtered = [w for w in words if w not in stopwords]
    # Return unique words by frequency
    word_counts = {}
    for w in filtered:
        word_counts[w] = word_counts.get(w, 0) + 1
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [w for w, c in sorted_words[:10]]


def _generate_hypotheses(task: str, elements: List[str]) -> List[str]:
    """Generate hypotheses based on task and elements."""
    hypotheses = []

    # Pattern-based hypothesis generation
    if any(w in task.lower() for w in ['why', 'cause', 'reason']):
        hypotheses.append(f"The cause may be related to: {', '.join(elements[:3])}")

    if any(w in task.lower() for w in ['how', 'method', 'way']):
        hypotheses.append(f"A potential method involves: {', '.join(elements[:3])}")

    if any(w in task.lower() for w in ['what', 'define', 'explain']):
        hypotheses.append(f"This can be defined through: {', '.join(elements[:3])}")

    # Default hypothesis if none generated
    if not hypotheses:
        hypotheses.append(f"Key factors to consider: {', '.join(elements[:3])}")
        hypotheses.append(f"Alternative perspective: analyze {', '.join(elements[3:6]) if len(elements) > 3 else elements[:3]}")

    return hypotheses


def _form_conclusion(task: str, thoughts: List[Thought]) -> str:
    """Form a conclusion based on the reasoning chain."""
    # Gather high-confidence deductions
    key_thoughts = [t for t in thoughts if t.confidence > 0.6 and t.thought_type in [ThoughtType.DEDUCTION, ThoughtType.HYPOTHESIS]]

    if key_thoughts:
        summary = "; ".join(t.content[:50] for t in key_thoughts[:2])
        return f"Based on analysis: {summary}"
    else:
        return f"Analysis complete for: {task[:100]}. Further investigation recommended."


def _generate_thought_branches(content: str, count: int) -> List[str]:
    """Generate branching thoughts from current thought."""
    branches = []
    prefixes = [
        "If we assume",
        "Alternatively",
        "Another possibility is",
        "This could lead to",
        "Consider that"
    ]

    for i in range(min(count, len(prefixes))):
        branches.append(f"{prefixes[i]}: extending from '{content[:50]}...'")

    return branches


def _score_thought(thought: Thought) -> float:
    """Score a thought based on various factors."""
    score = thought.confidence

    # Bonus for supported thoughts
    score += len(thought.supporting_evidence) * 0.1

    # Penalty for questions (uncertainty)
    if thought.thought_type == ThoughtType.QUESTION:
        score -= 0.2

    # Bonus for conclusions
    if thought.thought_type == ThoughtType.CONCLUSION:
        score += 0.1

    return max(0, min(1, score))


def _score_thought_path(path: List[ThoughtNode]) -> float:
    """Score a complete reasoning path."""
    if not path:
        return 0.0

    scores = [_score_thought(n.thought) for n in path]
    # Average score with bonus for longer coherent paths
    avg_score = sum(scores) / len(scores)
    length_bonus = min(0.2, len(path) * 0.05)

    return avg_score + length_bonus


def _synthesize_from_path(path: List[ThoughtNode]) -> str:
    """Synthesize a conclusion from a thought path."""
    if not path:
        return "No conclusion available"

    contents = [n.thought.content for n in path]
    return f"Conclusion via {len(path)} steps: {contents[-1][:100]}"


def _estimate_likelihood(evidence: str, hypothesis: str) -> float:
    """Estimate P(evidence | hypothesis)."""
    # Simple word overlap as proxy for relevance
    ev_words = set(evidence.lower().split())
    hyp_words = set(hypothesis.lower().split())

    overlap = len(ev_words & hyp_words)
    total = len(ev_words | hyp_words)

    if total == 0:
        return 0.5

    # Higher overlap = higher likelihood
    return 0.3 + (0.5 * overlap / total)


def _estimate_evidence_strength(evidence: str) -> float:
    """Estimate how strong a piece of evidence is."""
    # Longer, more detailed evidence is typically stronger
    length_factor = min(1.0, len(evidence) / 200)

    # Presence of numbers/data suggests stronger evidence
    has_numbers = bool(re.search(r'\d+', evidence))
    data_bonus = 0.2 if has_numbers else 0

    # Certainty words
    certainty_words = ['definitely', 'certainly', 'proven', 'confirmed', 'always', 'never']
    uncertainty_words = ['maybe', 'perhaps', 'possibly', 'might', 'could']

    certainty_score = sum(1 for w in certainty_words if w in evidence.lower()) * 0.1
    uncertainty_penalty = sum(1 for w in uncertainty_words if w in evidence.lower()) * 0.1

    strength = 0.5 + length_factor * 0.3 + data_bonus + certainty_score - uncertainty_penalty
    return max(0.1, min(0.9, strength))


class ReasoningEngine:
    """
    High-level interface for reasoning algorithms.

    Usage:
        engine = ReasoningEngine()
        result = engine.reason("Why does the sun rise?", method="chain")
    """

    def __init__(self):
        self.methods = {
            "chain": chain_of_thought,
            "tree": tree_of_thoughts,
            "bayesian": bayesian_reasoning
        }
        self.history: List[Dict] = []

    def reason(self, task: str, method: str = "chain", context: Dict = None) -> Dict:
        """Execute reasoning with specified method."""
        if method not in self.methods:
            raise ValueError(f"Unknown method: {method}. Use: {list(self.methods.keys())}")

        result = self.methods[method](task, context)
        self.history.append({
            "task": task,
            "method": method,
            "result": result
        })

        return result

    def get_history(self) -> List[Dict]:
        """Get reasoning history."""
        return self.history

    def clear_history(self):
        """Clear reasoning history."""
        self.history = []


if __name__ == "__main__":
    # Demo
    engine = ReasoningEngine()

    # Chain of thought
    result = engine.reason("Why do leaves change color in autumn?", "chain")
    print("Chain of Thought:")
    print(f"  Steps: {result['step_count']}")
    print(f"  Conclusion: {result['conclusion']}")

    # Tree of thoughts
    result = engine.reason("How can we reduce energy consumption?", "tree")
    print("\nTree of Thoughts:")
    print(f"  Branches explored: {result['branches_explored']}")
    print(f"  Best path score: {result['best_path_score']:.2f}")

    # Bayesian
    result = engine.reason(
        "Will it rain tomorrow?",
        "bayesian",
        {"prior": 0.3, "evidence": ["Dark clouds forming", "Humidity is high"]}
    )
    print("\nBayesian Reasoning:")
    print(f"  Prior: {result['prior_probability']:.2f}")
    print(f"  Posterior: {result['posterior_probability']:.2f}")
    print(f"  Interpretation: {result['interpretation']}")
