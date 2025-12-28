"""
SCORPION_BRAIN Building Algorithms
==================================
VULCAN specialty algorithms for patterns and construction.

Algorithms:
- cosine_similarity: Measure vector similarity
- graph_bfs: Breadth-first graph traversal
- graph_dfs: Depth-first graph traversal
- pattern_match: Match patterns in data
"""

import math
import re
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class Vector:
    """A simple vector class for similarity calculations."""
    values: List[float]

    def __len__(self):
        return len(self.values)

    def dot(self, other: 'Vector') -> float:
        """Compute dot product."""
        if len(self) != len(other):
            raise ValueError("Vectors must have same dimension")
        return sum(a * b for a, b in zip(self.values, other.values))

    def magnitude(self) -> float:
        """Compute magnitude (L2 norm)."""
        return math.sqrt(sum(v * v for v in self.values))

    def normalize(self) -> 'Vector':
        """Return normalized vector."""
        mag = self.magnitude()
        if mag == 0:
            return Vector([0.0] * len(self))
        return Vector([v / mag for v in self.values])


@dataclass
class GraphNode:
    """A node in a graph."""
    id: str
    data: Any = None
    edges: List[str] = field(default_factory=list)  # IDs of connected nodes
    weight: float = 1.0

    def add_edge(self, target_id: str):
        if target_id not in self.edges:
            self.edges.append(target_id)


@dataclass
class Graph:
    """A simple graph implementation."""
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    directed: bool = False

    def add_node(self, node_id: str, data: Any = None) -> GraphNode:
        """Add a node to the graph."""
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(id=node_id, data=data)
        return self.nodes[node_id]

    def add_edge(self, from_id: str, to_id: str):
        """Add an edge between nodes."""
        if from_id not in self.nodes:
            self.add_node(from_id)
        if to_id not in self.nodes:
            self.add_node(to_id)

        self.nodes[from_id].add_edge(to_id)
        if not self.directed:
            self.nodes[to_id].add_edge(from_id)

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get all neighbors of a node."""
        if node_id in self.nodes:
            return self.nodes[node_id].edges
        return []

    def __len__(self):
        return len(self.nodes)


@dataclass
class Pattern:
    """A pattern for matching."""
    template: str
    wildcards: Dict[str, str] = field(default_factory=dict)  # wildcard_name -> regex
    constraints: List[Callable] = field(default_factory=list)

    def __post_init__(self):
        # Default wildcards
        if not self.wildcards:
            self.wildcards = {
                '*': r'.*',          # Match anything
                '?': r'.',           # Match single char
                '{word}': r'\w+',    # Match word
                '{num}': r'\d+',     # Match number
                '{alpha}': r'[a-zA-Z]+',  # Match letters
            }


def cosine_similarity(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Calculate cosine similarity between vectors.

    Can work with:
    - Two vectors provided in context
    - Text converted to simple bag-of-words vectors

    Args:
        task: Description or text to process
        context: Should contain 'vector_a' and 'vector_b' or 'text_a' and 'text_b'

    Returns:
        Dict with similarity score and details
    """
    context = context or {}

    # Check if vectors are provided directly
    if 'vector_a' in context and 'vector_b' in context:
        vec_a = Vector(context['vector_a'])
        vec_b = Vector(context['vector_b'])
    elif 'text_a' in context and 'text_b' in context:
        # Convert text to bag-of-words vectors
        vec_a, vec_b, vocabulary = _text_to_vectors(
            context['text_a'],
            context['text_b']
        )
    else:
        # Use task as one text, look for comparison in context
        comparison = context.get('compare_to', 'default comparison text')
        vec_a, vec_b, vocabulary = _text_to_vectors(task, comparison)

    # Calculate cosine similarity
    dot_product = vec_a.dot(vec_b)
    magnitude_a = vec_a.magnitude()
    magnitude_b = vec_b.magnitude()

    if magnitude_a == 0 or magnitude_b == 0:
        similarity = 0.0
    else:
        similarity = dot_product / (magnitude_a * magnitude_b)

    # Interpret similarity
    if similarity > 0.8:
        interpretation = "Very similar"
    elif similarity > 0.6:
        interpretation = "Moderately similar"
    elif similarity > 0.4:
        interpretation = "Somewhat similar"
    elif similarity > 0.2:
        interpretation = "Slightly similar"
    else:
        interpretation = "Not similar"

    return {
        "algorithm": "cosine_similarity",
        "similarity": similarity,
        "dot_product": dot_product,
        "magnitude_a": magnitude_a,
        "magnitude_b": magnitude_b,
        "interpretation": interpretation,
        "dimension": len(vec_a)
    }


def graph_bfs(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Perform breadth-first search on a graph.

    Args:
        task: Description of search goal
        context: Should contain 'graph' (Graph or dict) and 'start' node

    Returns:
        Dict with traversal order and path information
    """
    context = context or {}

    # Get or create graph
    graph = _get_graph_from_context(context)
    start = context.get('start', list(graph.nodes.keys())[0] if graph.nodes else None)
    target = context.get('target')  # Optional target node

    if not start or start not in graph.nodes:
        return {
            "algorithm": "graph_bfs",
            "error": "Invalid start node",
            "traversal": []
        }

    # BFS implementation
    visited: Set[str] = set()
    queue = deque([(start, [start])])  # (node, path)
    traversal_order: List[str] = []
    paths: Dict[str, List[str]] = {}
    levels: Dict[str, int] = {start: 0}

    while queue:
        current, path = queue.popleft()

        if current in visited:
            continue

        visited.add(current)
        traversal_order.append(current)
        paths[current] = path

        # Check if we found target
        if target and current == target:
            break

        # Add neighbors to queue
        for neighbor in graph.get_neighbors(current):
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))
                if neighbor not in levels:
                    levels[neighbor] = levels[current] + 1

    result = {
        "algorithm": "graph_bfs",
        "start": start,
        "traversal_order": traversal_order,
        "nodes_visited": len(visited),
        "total_nodes": len(graph),
        "levels": levels
    }

    if target:
        result["target"] = target
        result["target_found"] = target in visited
        if target in paths:
            result["path_to_target"] = paths[target]
            result["path_length"] = len(paths[target]) - 1

    return result


def graph_dfs(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Perform depth-first search on a graph.

    Args:
        task: Description of search goal
        context: Should contain 'graph' and 'start' node

    Returns:
        Dict with traversal order and path information
    """
    context = context or {}

    graph = _get_graph_from_context(context)
    start = context.get('start', list(graph.nodes.keys())[0] if graph.nodes else None)
    target = context.get('target')

    if not start or start not in graph.nodes:
        return {
            "algorithm": "graph_dfs",
            "error": "Invalid start node",
            "traversal": []
        }

    # DFS implementation (iterative with stack)
    visited: Set[str] = set()
    stack = [(start, [start])]
    traversal_order: List[str] = []
    paths: Dict[str, List[str]] = {}
    max_depth = 0
    depths: Dict[str, int] = {start: 0}

    while stack:
        current, path = stack.pop()

        if current in visited:
            continue

        visited.add(current)
        traversal_order.append(current)
        paths[current] = path
        current_depth = len(path) - 1
        max_depth = max(max_depth, current_depth)

        if target and current == target:
            break

        # Add neighbors to stack (reverse to maintain order)
        neighbors = graph.get_neighbors(current)
        for neighbor in reversed(neighbors):
            if neighbor not in visited:
                stack.append((neighbor, path + [neighbor]))
                if neighbor not in depths:
                    depths[neighbor] = current_depth + 1

    result = {
        "algorithm": "graph_dfs",
        "start": start,
        "traversal_order": traversal_order,
        "nodes_visited": len(visited),
        "total_nodes": len(graph),
        "max_depth": max_depth,
        "depths": depths
    }

    if target:
        result["target"] = target
        result["target_found"] = target in visited
        if target in paths:
            result["path_to_target"] = paths[target]
            result["path_length"] = len(paths[target]) - 1

    return result


def pattern_match(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Match patterns in data.

    Supports:
    - Regex patterns
    - Template patterns with wildcards
    - Structural pattern matching

    Args:
        task: Text or data to search in
        context: Should contain 'pattern' (string or Pattern object)

    Returns:
        Dict with matches and positions
    """
    context = context or {}

    pattern_input = context.get('pattern', r'\w+')  # Default: match words
    text = context.get('text', task)

    # Convert to regex pattern if needed
    if isinstance(pattern_input, Pattern):
        regex_pattern = _pattern_to_regex(pattern_input)
    elif isinstance(pattern_input, str):
        # Check if it's a template pattern or raw regex
        if any(wc in pattern_input for wc in ['{word}', '{num}', '*', '?']):
            pattern_obj = Pattern(template=pattern_input)
            regex_pattern = _pattern_to_regex(pattern_obj)
        else:
            regex_pattern = pattern_input
    else:
        regex_pattern = str(pattern_input)

    # Find all matches
    matches = []
    try:
        for match in re.finditer(regex_pattern, text, re.IGNORECASE):
            matches.append({
                "match": match.group(),
                "start": match.start(),
                "end": match.end(),
                "groups": match.groups() if match.groups() else None
            })
    except re.error as e:
        return {
            "algorithm": "pattern_match",
            "error": f"Invalid regex: {e}",
            "pattern": regex_pattern,
            "matches": []
        }

    # Calculate coverage
    total_matched_chars = sum(m['end'] - m['start'] for m in matches)
    coverage = total_matched_chars / len(text) if text else 0

    return {
        "algorithm": "pattern_match",
        "pattern": regex_pattern,
        "text_length": len(text),
        "match_count": len(matches),
        "matches": matches[:50],  # Limit to first 50 matches
        "coverage": coverage,
        "unique_matches": list(set(m['match'] for m in matches))[:20]
    }


# Helper functions

def _text_to_vectors(text_a: str, text_b: str) -> Tuple[Vector, Vector, List[str]]:
    """Convert two texts to bag-of-words vectors."""
    # Tokenize
    words_a = set(re.findall(r'\b\w+\b', text_a.lower()))
    words_b = set(re.findall(r'\b\w+\b', text_b.lower()))

    # Create vocabulary
    vocabulary = sorted(words_a | words_b)

    # Create vectors
    vec_a_values = [1.0 if word in words_a else 0.0 for word in vocabulary]
    vec_b_values = [1.0 if word in words_b else 0.0 for word in vocabulary]

    return Vector(vec_a_values), Vector(vec_b_values), vocabulary


def _get_graph_from_context(context: Dict) -> Graph:
    """Extract or create a graph from context."""
    if 'graph' in context:
        graph_data = context['graph']
        if isinstance(graph_data, Graph):
            return graph_data
        elif isinstance(graph_data, dict):
            # Convert dict to Graph
            graph = Graph()
            for node_id, neighbors in graph_data.items():
                graph.add_node(node_id)
                if isinstance(neighbors, list):
                    for neighbor in neighbors:
                        graph.add_edge(node_id, neighbor)
            return graph

    # Create a sample graph if none provided
    graph = Graph()
    nodes = ['A', 'B', 'C', 'D', 'E', 'F']
    edges = [('A', 'B'), ('A', 'C'), ('B', 'D'), ('C', 'D'), ('C', 'E'), ('D', 'F'), ('E', 'F')]

    for node in nodes:
        graph.add_node(node)
    for from_node, to_node in edges:
        graph.add_edge(from_node, to_node)

    return graph


def _pattern_to_regex(pattern: Pattern) -> str:
    """Convert a Pattern object to regex string."""
    result = pattern.template

    # Escape regex special chars first (except our wildcards)
    for char in ['.', '^', '$', '+', '[', ']', '(', ')', '{', '}', '|', '\\']:
        if char not in ['*', '?', '{', '}']:
            result = result.replace(char, '\\' + char)

    # Replace wildcards with regex
    for wildcard, regex in pattern.wildcards.items():
        result = result.replace(wildcard, f'({regex})')

    return result


class BuildingEngine:
    """
    High-level interface for building/pattern algorithms.

    Usage:
        engine = BuildingEngine()
        result = engine.find_similar(text_a, text_b)
        result = engine.search_graph(graph, start, target)
    """

    def __init__(self):
        self.algorithms = {
            "similarity": cosine_similarity,
            "bfs": graph_bfs,
            "dfs": graph_dfs,
            "pattern": pattern_match
        }

    def find_similar(self, text_a: str, text_b: str) -> Dict:
        """Find similarity between two texts."""
        return cosine_similarity("", {"text_a": text_a, "text_b": text_b})

    def compare_vectors(self, vec_a: List[float], vec_b: List[float]) -> Dict:
        """Compare two vectors."""
        return cosine_similarity("", {"vector_a": vec_a, "vector_b": vec_b})

    def search_graph(self, graph: Any, start: str, target: str = None, method: str = "bfs") -> Dict:
        """Search a graph using BFS or DFS."""
        context = {"graph": graph, "start": start, "target": target}
        if method == "dfs":
            return graph_dfs("", context)
        return graph_bfs("", context)

    def find_patterns(self, text: str, pattern: str) -> Dict:
        """Find pattern matches in text."""
        return pattern_match("", {"text": text, "pattern": pattern})

    def create_graph(self, edges: List[Tuple[str, str]]) -> Graph:
        """Create a graph from edge list."""
        graph = Graph()
        for from_node, to_node in edges:
            graph.add_edge(from_node, to_node)
        return graph


# Utility functions for external use

def quick_similarity(text_a: str, text_b: str) -> float:
    """Quick helper to get similarity score."""
    result = cosine_similarity("", {"text_a": text_a, "text_b": text_b})
    return result["similarity"]


def find_path(graph_dict: Dict[str, List[str]], start: str, end: str) -> Optional[List[str]]:
    """Quick helper to find path between nodes."""
    result = graph_bfs("", {"graph": graph_dict, "start": start, "target": end})
    return result.get("path_to_target")


if __name__ == "__main__":
    # Demo
    engine = BuildingEngine()

    # Similarity
    print("=== Cosine Similarity ===")
    result = engine.find_similar(
        "The quick brown fox jumps",
        "A fast brown fox leaps"
    )
    print(f"Similarity: {result['similarity']:.3f} ({result['interpretation']})")

    # Graph search
    print("\n=== Graph Search ===")
    graph = {
        'A': ['B', 'C'],
        'B': ['D'],
        'C': ['D', 'E'],
        'D': ['F'],
        'E': ['F'],
        'F': []
    }

    bfs_result = engine.search_graph(graph, 'A', 'F', method='bfs')
    print(f"BFS path A->F: {bfs_result.get('path_to_target')}")

    dfs_result = engine.search_graph(graph, 'A', 'F', method='dfs')
    print(f"DFS path A->F: {dfs_result.get('path_to_target')}")

    # Pattern matching
    print("\n=== Pattern Matching ===")
    result = engine.find_patterns(
        "Error 404: Not found. Error 500: Server error.",
        r"Error \d+"
    )
    print(f"Found {result['match_count']} matches: {result['unique_matches']}")
